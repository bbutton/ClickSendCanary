import boto3
import os
import json
import time
import logging
from typing import Dict, Any

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class AthenaQueryError(Exception):
    """Exception raised for errors during Athena query execution."""
    pass


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler function that executes MSCK REPAIR TABLE on an Athena table.

    Args:
        event: The event dict that contains parameters passed to the function
        context: The context object with runtime information

    Returns:
        A dictionary containing the execution status and details
    """
    try:
        logger.info("Starting Athena MSCK REPAIR Lambda execution")

        # Get configuration from environment variables
        config = get_configuration()
        logger.info(f"Using configuration: {config}")

        # Execute the MSCK REPAIR query
        query_execution_id = execute_msck_repair(config)

        # Wait for and check query completion
        final_state = wait_for_query_completion(query_execution_id, config)

        # Log and return the results
        logger.info(f"MSCK REPAIR completed successfully. Query ID: {query_execution_id}")
        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "MSCK REPAIR executed successfully",
                "queryExecutionId": query_execution_id,
                "state": final_state
            })
        }

    except AthenaQueryError as e:
        logger.error(f"Error executing Athena query: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "Failed to execute MSCK REPAIR query",
                "details": str(e)
            })
        }
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "Unexpected error occurred",
                "details": str(e)
            })
        }


def get_configuration() -> Dict[str, str]:
    """
    Get configuration from environment variables.

    Returns:
        Dictionary containing the configuration values

    Raises:
        ValueError: If required environment variables are missing
    """
    required_vars = [
        "ATHENA_DATABASE",
        "ATHENA_TABLE",
        "ATHENA_WORKGROUP",
        "S3_OUTPUT_BUCKET",
        "S3_OUTPUT_PREFIX"
    ]

    config = {}
    missing_vars = []

    for var in required_vars:
        value = os.environ.get(var)
        if value:
            config[var] = value
        else:
            missing_vars.append(var)

    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

    return config


def execute_msck_repair(config: Dict[str, str]) -> str:
    """
    Execute the MSCK REPAIR TABLE query in Athena.

    Args:
        config: Dictionary containing configuration values

    Returns:
        The Athena query execution ID

    Raises:
        AthenaQueryError: If the Athena query cannot be started
    """
    try:
        # Create Athena client
        athena_client = boto3.client('athena')

        # Construct MSCK REPAIR query
        query = f"MSCK REPAIR TABLE {config['ATHENA_DATABASE']}.{config['ATHENA_TABLE']};"
        logger.info(f"Executing query: {query}")

        # Construct S3 output location
        s3_output_location = f"s3://{config['S3_OUTPUT_BUCKET']}/{config['S3_OUTPUT_PREFIX']}"

        # Execute the query
        response = athena_client.start_query_execution(
            QueryString=query,
            QueryExecutionContext={
                'Database': config['ATHENA_DATABASE']
            },
            ResultConfiguration={
                'OutputLocation': s3_output_location
            },
            WorkGroup=config['ATHENA_WORKGROUP']
        )

        query_execution_id = response['QueryExecutionId']
        logger.info(f"Started query execution with ID: {query_execution_id}")

        return query_execution_id

    except Exception as e:
        logger.error(f"Failed to execute Athena query: {str(e)}", exc_info=True)
        raise AthenaQueryError(f"Failed to execute Athena query: {str(e)}")


def wait_for_query_completion(query_execution_id: str, config: Dict[str, str],
                              max_wait_seconds: int = 180, polling_interval: int = 2) -> str:
    """
    Wait for an Athena query to complete and return its final state.

    Args:
        query_execution_id: The Athena query execution ID
        config: Dictionary containing configuration values
        max_wait_seconds: Maximum time to wait for query completion in seconds
        polling_interval: Time between status checks in seconds

    Returns:
        The final query state (SUCCEEDED, FAILED, CANCELLED)

    Raises:
        AthenaQueryError: If the query fails or times out
    """
    try:
        # Create Athena client
        athena_client = boto3.client('athena')

        wait_time = 0
        previous_state = None

        while wait_time < max_wait_seconds:
            # Get query execution status
            response = athena_client.get_query_execution(
                QueryExecutionId=query_execution_id
            )

            # Extract current state
            current_state = response['QueryExecution']['Status']['State']

            # Log state changes
            if current_state != previous_state:
                logger.info(f"Query execution state: {current_state}")
                previous_state = current_state

            # Check if query completed
            if current_state in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
                # If query failed, include error information
                if current_state != 'SUCCEEDED':
                    error_info = response['QueryExecution']['Status'].get('StateChangeReason', 'Unknown error')
                    logger.error(f"Query failed: {error_info}")
                    raise AthenaQueryError(f"Query execution failed: {error_info}")

                return current_state

            # Wait before checking again
            time.sleep(polling_interval)
            wait_time += polling_interval

        # If we get here, the query timed out
        logger.error(f"Query execution timed out after {max_wait_seconds} seconds")
        raise AthenaQueryError(f"Query execution timed out after {max_wait_seconds} seconds")

    except AthenaQueryError:
        # Re-raise AthenaQueryError exceptions
        raise
    except Exception as e:
        logger.error(f"Error checking query execution status: {str(e)}", exc_info=True)
        raise AthenaQueryError(f"Error checking query execution: {str(e)}")
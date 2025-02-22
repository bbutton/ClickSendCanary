import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Insert the repository root into sys.path.
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

# Import MySQLConnector from the src folder.
try:
    from src.mysql_connector import MySQLConnector
except ModuleNotFoundError as e:
    print("Error importing MySQLConnector:", e)
    raise

class TestMySQLConnectorInitialization(unittest.TestCase):
    @patch('src.mysql_connector.mysql.connector.connect')
    def test_initialization(self, mock_connect):
        # Set up dummy environment variables.
        os.environ["MYSQL_USER"] = "dummy_user"
        os.environ["MYSQL_PASSWORD"] = "dummy_password"
        os.environ["MYSQL_HOST"] = "dummy_host"
        os.environ["MYSQL_DATABASE"] = "dummy_database"

        # Create a mock connection and cursor.
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection

        # Instantiate the connector.
        connector = MySQLConnector()

        # Verify that mysql.connector.connect was called with the expected arguments.
        mock_connect.assert_called_once_with(
            user="dummy_user",
            password="dummy_password",
            host="dummy_host",
            database="dummy_database"
        )

        # Verify that the connector has set its attributes correctly.
        self.assertEqual(connector.cnx, mock_connection)
        self.assertEqual(connector.cursor, mock_cursor)

class TestMySQLConnectorInsertData(unittest.TestCase):
    @patch('src.mysql_connector.mysql.connector.connect')
    def test_insert_data(self, mock_connect):
        # Set up dummy environment variables.
        os.environ["MYSQL_USER"] = "dummy_user"
        os.environ["MYSQL_PASSWORD"] = "dummy_password"
        os.environ["MYSQL_HOST"] = "dummy_host"
        os.environ["MYSQL_DATABASE"] = "dummy_database"

        # Create a mock connection and cursor.
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection

        # Instantiate the connector.
        connector = MySQLConnector()

        # Define a sample history record.
        sample_history = [{
            'message_id': 'msg001',
            'date': '1609459200',         # string; should be converted to int 1609459200
            'to': '+1234567890',
            'status': 'SUCCESS',
            'schedule': '1609459300',       # string; should be converted to int 1609459300
            'status_code': '200',
            'status_text': 'OK',
            'error_code': None,
            'error_text': None,
            'message_parts': '1',           # string; should be converted to int 1
            'message_price': '0.05',        # string; should be converted to float 0.05
            'from_email': 'sender@example.com',
            'list_id': 'list001',
            'carrier': 'TestCarrier',
            'body': 'Test Body'
        }]

        # Call insert_data with the sample history.
        connector.insert_data(sample_history)

        # Expected SQL statement.
        expected_sql = (
            "INSERT INTO clicksend_messages "
            "(message_id, `date`, `to`, status, schedule, status_code, status_text, error_code, error_text, message_parts, message_price, from_email, list_id, carrier, body) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        )

        # Expected parameter tuple.
        expected_tuple = (
            'msg001',
            1609459200,
            '+1234567890',
            'SUCCESS',
            1609459300,
            '200',
            'OK',
            None,
            None,
            1,
            0.05,
            'sender@example.com',
            'list001',
            'TestCarrier',
            'Test Body'
        )

        # Verify that cursor.execute was called once with the expected SQL and parameters.
        self.assertEqual(mock_cursor.execute.call_count, len(sample_history))
        actual_calls = mock_cursor.execute.call_args_list
        self.assertEqual(len(actual_calls), 1)
        call_args, call_kwargs = actual_calls[0]
        self.assertEqual(call_args[0], expected_sql)
        self.assertEqual(call_args[1], expected_tuple)

        # Verify that commit was called once.
        mock_connection.commit.assert_called_once()

class TestMySQLConnectorClose(unittest.TestCase):
    @patch('src.mysql_connector.mysql.connector.connect')
    def test_close_method(self, mock_connect):
        # Set up dummy environment variables.
        os.environ["MYSQL_USER"] = "dummy_user"
        os.environ["MYSQL_PASSWORD"] = "dummy_password"
        os.environ["MYSQL_HOST"] = "dummy_host"
        os.environ["MYSQL_DATABASE"] = "dummy_database"

        # Create a mock connection and cursor.
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection

        # Instantiate the connector.
        connector = MySQLConnector()

        # Call the close method.
        connector.close()

        # Verify that both the cursor's and connection's close methods were called once.
        mock_cursor.close.assert_called_once()
        mock_connection.close.assert_called_once()

if __name__ == '__main__':
    unittest.main()

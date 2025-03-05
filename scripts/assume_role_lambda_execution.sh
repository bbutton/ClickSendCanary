echo "Always dot this, as you want it to apply to your working shell!!!!"

unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN

CREDENTIALS=$(aws sts assume-role --role-arn arn:aws:iam::095750864911:role/athena-failure-lambda-role --role-session-name failure-lambda-role --query "Credentials")
export AWS_ACCESS_KEY_ID=$(echo $CREDENTIALS | jq -r '.AccessKeyId')
export AWS_SECRET_ACCESS_KEY=$(echo $CREDENTIALS | jq -r '.SecretAccessKey')
export AWS_SESSION_TOKEN=$(echo $CREDENTIALS | jq -r '.SessionToken')


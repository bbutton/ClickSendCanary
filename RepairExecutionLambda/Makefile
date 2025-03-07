# AWS and Terraform Settings
AWS_REGION=us-east-1
S3_BUCKET=clicksend-canary-data
LAMBDA_ZIP=athena_repair_lambda.zip
LAMBDA_SRC=athena_repair_lambda.py
TERRAFORM_DIR=../terraform

.PHONY: all build upload deploy clean terraform

## 📌 Build the Lambda ZIP file
build:
	@echo "📦 Packaging Lambda function..."
	zip -r $(LAMBDA_ZIP) $(LAMBDA_SRC)

## 🚀 Upload ZIP to S3
upload: build
	@echo "☁ Uploading $(LAMBDA_ZIP) to S3..."
	aws s3 cp $(LAMBDA_ZIP) s3://$(S3_BUCKET)/

## 🔄 Deploy Lambda using Terraform
deploy: upload
	@echo "🔄 Running Terraform apply..."
	cd $(TERRAFORM_DIR) && terraform taint aws_lambda_function.athena_repair_lambda
	cd $(TERRAFORM_DIR) && terraform init && terraform plan -out apply.plan && terraform apply apply.plan

## 🗑️ Clean up local files
clean:
	@echo "🧹 Cleaning up..."
	rm -f $(LAMBDA_ZIP)

## 🌍 Run full pipeline (build → upload → deploy)
all: build upload deploy
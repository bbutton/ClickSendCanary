# AWS Lambda function name
LAMBDA_NAME = ClickSendCanary
PACKAGE_NAME = lambda.zip
PACKAGE_DIR = package/
REQUIREMENTS_FILE = requirements.txt
INSTALL_MARKER = .installed-dependencies

# Default target
all: clean install package deploy logs

# Install dependencies (runs only if INSTALL_MARKER doesn't exist)
install: $(INSTALL_MARKER)

$(INSTALL_MARKER): $(REQUIREMENTS_FILE)
	@echo "📦 Installing dependencies..."
	@if [ -f $(REQUIREMENTS_FILE) ]; then \
		pip install --target $(PACKAGE_DIR) -r $(REQUIREMENTS_FILE); \
		touch $(INSTALL_MARKER); \
	else \
		echo "⚠️ No requirements.txt found, skipping dependency installation."; \
	fi

# Create the Lambda package (depends on install)
package: install
	@echo "📦 Creating Lambda package..."
	rm -f $(PACKAGE_NAME)  # Ensure old zip is removed
	@if [ -d $(PACKAGE_DIR) ]; then cd $(PACKAGE_DIR) && zip -r9 ../$(PACKAGE_NAME) .; fi
	zip -r9 $(PACKAGE_NAME) src/ main.py

# Upload package to AWS Lambda
deploy: package
	@echo "🚀 Deploying to AWS Lambda..."
	aws lambda update-function-code --function-name $(LAMBDA_NAME) --zip-file fileb://$(PACKAGE_NAME)

# Invoke Lambda function
invoke:
	@echo "🔄 Invoking Lambda function..."
	aws lambda invoke --function-name $(LAMBDA_NAME) response.json
	@echo "📄 Response:"
	cat response.json

# Tail Lambda logs
logs:
	@echo "📜 Fetching Lambda logs..."
	aws logs tail /aws/lambda/$(LAMBDA_NAME) --follow

# Cleanup old ZIP & dependencies
clean:
	@echo "🧹 Cleaning up..."
	rm -f $(PACKAGE_NAME) $(INSTALL_MARKER)
	rm -rf $(PACKAGE_DIR)

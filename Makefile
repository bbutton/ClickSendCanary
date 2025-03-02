ECR_REPO=095750864911.dkr.ecr.us-east-1.amazonaws.com/clicksend-canary
IMAGE_TAG=latest

all: build push deploy

build:
	docker buildx build --platform linux/amd64 -t $(ECR_REPO):$(IMAGE_TAG) .

push: build
	aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $(ECR_REPO)
	docker push $(ECR_REPO):$(IMAGE_TAG)

deploy: push
	aws lambda update-function-code --function-name ClickSendCanary --image-uri $(ECR_REPO):$(IMAGE_TAG)

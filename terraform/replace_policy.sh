#!/bin/bash

unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN

aws iam detach-role-policy \
    --role-name terraform-deployer \
    --policy-arn arn:aws:iam::095750864911:policy/TerraformDeployerPolicy

aws iam delete-policy \
    --policy-arn arn:aws:iam::095750864911:policy/TerraformDeployerPolicy

aws iam create-policy \
    --policy-name TerraformDeployerPolicy \
    --policy-document file://terraform-deployer-policy.json

aws iam attach-role-policy \
    --role-name terraform-deployer \
    --policy-arn arn:aws:iam::095750864911:policy/TerraformDeployerPolicy

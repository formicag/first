# Claude Code Integration Testing

This project demonstrates Claude Code integration with GitHub, AWS, and Google Workspace through practical implementations.

## Overview

Testing environment showcasing Claude Code's capabilities across major development and cloud platforms, including infrastructure as code, billing management, and static website hosting.

## What We Built

### GitHub Integration
- Initialized Git repository with Python `.gitignore`
- Created and pushed repository to GitHub: [formicag/first](https://github.com/formicag/first)
- Automated commits and push workflows using GitHub CLI (`gh`)

### AWS Integration
- **SSO Authentication**: Connected AWS CLI with Google Workspace as IdP via AWS Identity Center
- **S3 Static Website**: Deployed static website to S3
  - Bucket: `first-static-website-1759349027`
  - URL: http://first-static-website-1759349027.s3-website-eu-west-1.amazonaws.com
  - Public access configured with bucket policy
- **CloudFormation Template**: Created `s3-static-website.yaml` for infrastructure as code
  - Parameterized S3 bucket configuration
  - Static website hosting setup
  - Public read access policy
  - Exportable outputs (WebsiteURL, BucketName)
- **Billing Alerts**: Set up CloudWatch alarms with SNS notifications
  - Alert thresholds: £10, £20, £30, £50, £100
  - Email notifications to gianluca.formica@nasstar.com
  - SNS Topic: `billing-alerts`

### Google Workspace Integration
- Configured as Identity Provider (IdP) for AWS Identity Center
- SSO authentication for AWS services

## Project Files

- `README.md` - This file
- `.gitignore` - Python project exclusions
- `index.html` - Static website landing page
- `s3-static-website.yaml` - CloudFormation template for S3 static website hosting

## AWS Resources Created

### S3
- Bucket: `first-static-website-1759349027` (eu-west-1)

### CloudWatch
- Billing-Alert-10GBP
- Billing-Alert-20GBP
- Billing-Alert-30GBP
- Billing-Alert-50GBP
- Billing-Alert-100GBP

### SNS
- Topic: `arn:aws:sns:us-east-1:016164185850:billing-alerts`
- Email subscription: gianluca.formica@nasstar.com

## CloudFormation Template

The `s3-static-website.yaml` template provides:

```yaml
Parameters:
  - BucketName: Customizable S3 bucket name

Resources:
  - WebsiteBucket: S3 bucket with static website hosting
  - WebsiteBucketPolicy: Public read access policy

Outputs:
  - WebsiteURL: S3 website endpoint
  - BucketName: Created bucket name
```

### Deploy the Template

```bash
aws cloudformation create-stack \
  --stack-name my-static-website \
  --template-body file://s3-static-website.yaml \
  --parameters ParameterKey=BucketName,ParameterValue=my-unique-bucket-name \
  --profile AdministratorAccess-016164185850 \
  --region eu-west-1
```

## Prerequisites

- AWS CLI v2
- GitHub CLI (`gh`)
- AWS account with AdministratorAccess
- Google Workspace configured as AWS SSO IdP

## AWS Profile Setup

```bash
export AWS_PROFILE=AdministratorAccess-016164185850
aws sso login --profile AdministratorAccess-016164185850
```

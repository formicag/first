# Shopping List Application - CloudFormation Deployment Guide

This guide explains how to deploy the Shopping List application infrastructure using AWS CloudFormation nested stacks.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Architecture Overview](#architecture-overview)
- [Stack Structure](#stack-structure)
- [Deployment Steps](#deployment-steps)
- [Post-Deployment Configuration](#post-deployment-configuration)
- [Updating Stacks](#updating-stacks)
- [Deleting Stacks](#deleting-stacks)
- [Estimated Costs](#estimated-costs)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### AWS Account Requirements
- AWS Account with administrative access
- AWS CLI installed and configured
- AWS profile configured: `AdministratorAccess-016164185850`

### Tools Required
- AWS CLI version 2.x or later
- Git
- Python 3.11 (for Lambda function code)
- A verified email address for SES
- (Optional) A custom domain and ACM certificate in us-east-1

### Permissions Required
The IAM user/role deploying the stacks needs permissions for:
- CloudFormation (full access)
- S3 (create buckets, upload objects)
- DynamoDB (create tables)
- Lambda (create functions, roles)
- API Gateway (create APIs)
- Cognito (create user pools)
- SES (create identities)
- CloudWatch (create alarms)
- SNS (create topics)
- CloudFront (create distributions)
- IAM (create roles and policies)

## Architecture Overview

The application uses a modular nested stack architecture:

```
main-stack.yaml (Root Stack)
├── storage-stack.yaml (DynamoDB)
├── auth-stack.yaml (Cognito User Pool)
├── email-stack.yaml (SES)
├── monitoring-stack.yaml (CloudWatch + SNS)
├── compute-stack.yaml (6 Lambda Functions)
├── api-stack.yaml (API Gateway)
└── frontend-stack.yaml (S3 + CloudFront)
```

### Stack Dependencies
1. **Storage Stack** - No dependencies
2. **Auth Stack** - No dependencies
3. **Email Stack** - No dependencies
4. **Monitoring Stack** - No dependencies
5. **Compute Stack** - Depends on Storage
6. **API Stack** - Depends on Auth, Compute
7. **Frontend Stack** - No dependencies

## Stack Structure

### 1. Storage Stack (`storage-stack.yaml`)
- **Resources**: DynamoDB table
- **Outputs**: TableName, TableArn
- **Features**:
  - Point-in-time recovery enabled
  - Server-side encryption enabled
  - Pay-per-request or provisioned billing

### 2. Auth Stack (`auth-stack.yaml`)
- **Resources**: Cognito User Pool, User Pool Client
- **Outputs**: UserPoolId, UserPoolArn, UserPoolClientId
- **Features**:
  - Email-based authentication
  - Custom displayName attribute
  - Password policy configuration

### 3. Email Stack (`email-stack.yaml`)
- **Resources**: SES Email Identity
- **Outputs**: EmailIdentity, NotificationEmail
- **Note**: Email must be verified before use

### 4. Monitoring Stack (`monitoring-stack.yaml`)
- **Resources**: SNS Topic, 5 CloudWatch Billing Alarms
- **Outputs**: BillingAlertTopicArn
- **Features**: Configurable billing thresholds

### 5. Compute Stack (`compute-stack.yaml`)
- **Resources**:
  - IAM execution role
  - 6 Lambda functions (CreateItem, GetItems, UpdateItem, DeleteItem, EmailList, CategorizeItems)
- **Outputs**: Function ARNs, Role ARN
- **Note**: Contains placeholder code - actual code must be deployed separately

### 6. API Stack (`api-stack.yaml`)
- **Resources**:
  - API Gateway REST API
  - Cognito Authorizer
  - 6 Resources with Methods
  - Lambda Permissions
- **Outputs**: ApiId, ApiEndpoint, AuthorizerId
- **Features**: CORS-enabled, Cognito authentication

### 7. Frontend Stack (`frontend-stack.yaml`)
- **Resources**: S3 bucket, CloudFront distribution
- **Outputs**: BucketName, DistributionId, WebsiteURL
- **Features**: Custom domain support, HTTPS redirect

## Deployment Steps

### Step 1: Prepare S3 Bucket for Templates

Create an S3 bucket to store the nested stack templates:

```bash
# Create bucket (use a unique name)
TEMPLATES_BUCKET="my-cloudformation-templates-$(date +%s)"
aws s3 mb s3://${TEMPLATES_BUCKET} \
  --region eu-west-1 \
  --profile AdministratorAccess-016164185850
```

### Step 2: Upload Nested Stack Templates

Upload all nested stack templates to S3:

```bash
cd cloudformation

# Upload all nested stacks
aws s3 cp storage-stack.yaml s3://${TEMPLATES_BUCKET}/ --profile AdministratorAccess-016164185850
aws s3 cp auth-stack.yaml s3://${TEMPLATES_BUCKET}/ --profile AdministratorAccess-016164185850
aws s3 cp email-stack.yaml s3://${TEMPLATES_BUCKET}/ --profile AdministratorAccess-016164185850
aws s3 cp monitoring-stack.yaml s3://${TEMPLATES_BUCKET}/ --profile AdministratorAccess-016164185850
aws s3 cp compute-stack.yaml s3://${TEMPLATES_BUCKET}/ --profile AdministratorAccess-016164185850
aws s3 cp api-stack.yaml s3://${TEMPLATES_BUCKET}/ --profile AdministratorAccess-016164185850
aws s3 cp frontend-stack.yaml s3://${TEMPLATES_BUCKET}/ --profile AdministratorAccess-016164185850
```

### Step 3: Configure Parameters

Edit `parameters.json` with your specific values:

```json
{
  "ParameterKey": "TemplatesBucketName",
  "ParameterValue": "your-templates-bucket-name"
},
{
  "ParameterKey": "NotificationEmail",
  "ParameterValue": "your-email@example.com"
},
{
  "ParameterKey": "DomainName",
  "ParameterValue": "shoppinglist.yourdomain.com"
},
{
  "ParameterKey": "AcmCertificateArn",
  "ParameterValue": "arn:aws:acm:us-east-1:123456789012:certificate/..."
}
```

**Important**: Update `TemplatesBucketName` to match the bucket created in Step 1.

### Step 4: Deploy Main Stack

Deploy the main stack which will create all nested stacks:

```bash
aws cloudformation create-stack \
  --stack-name ShoppingList-Dev \
  --template-body file://main-stack.yaml \
  --parameters file://parameters.json \
  --capabilities CAPABILITY_NAMED_IAM \
  --region eu-west-1 \
  --profile AdministratorAccess-016164185850
```

Monitor deployment progress:

```bash
aws cloudformation describe-stacks \
  --stack-name ShoppingList-Dev \
  --region eu-west-1 \
  --profile AdministratorAccess-016164185850 \
  --query 'Stacks[0].StackStatus'
```

Or watch events in real-time:

```bash
aws cloudformation describe-stack-events \
  --stack-name ShoppingList-Dev \
  --region eu-west-1 \
  --profile AdministratorAccess-016164185850 \
  --max-items 20
```

**Expected Duration**: 10-15 minutes for complete deployment.

### Step 5: Deploy Lambda Function Code

The Lambda functions are created with placeholder code. Deploy actual code:

```bash
cd ../lambda

# Package and deploy each function
for func in createItem getItems updateItem deleteItem emailList categorizeItems; do
  # Create deployment package
  zip ${func}.zip ${func}.py cognito_helper.py

  # Update function code
  aws lambda update-function-code \
    --function-name ShoppingList-Dev-${func^} \
    --zip-file fileb://${func}.zip \
    --region eu-west-1 \
    --profile AdministratorAccess-016164185850
done
```

Note: Function names follow pattern: `{ProjectName}-{Environment}-{FunctionName}`

### Step 6: Upload Website Files

Upload frontend files to the S3 bucket:

```bash
# Get bucket name from stack outputs
BUCKET_NAME=$(aws cloudformation describe-stacks \
  --stack-name ShoppingList-Dev \
  --region eu-west-1 \
  --profile AdministratorAccess-016164185850 \
  --query 'Stacks[0].Outputs[?OutputKey==`S3BucketName`].OutputValue' \
  --output text)

# Upload website files
cd ../website
aws s3 sync . s3://${BUCKET_NAME}/ --profile AdministratorAccess-016164185850
```

### Step 7: Invalidate CloudFront Cache

```bash
# Get distribution ID
DIST_ID=$(aws cloudformation describe-stacks \
  --stack-name ShoppingList-Dev \
  --region eu-west-1 \
  --profile AdministratorAccess-016164185850 \
  --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontDistributionDomain`].OutputValue' \
  --output text | cut -d'.' -f1)

# Create invalidation
aws cloudfront create-invalidation \
  --distribution-id ${DIST_ID} \
  --paths "/*" \
  --profile AdministratorAccess-016164185850
```

## Post-Deployment Configuration

### 1. Verify SES Email Identity

```bash
# Check email identity status
aws ses get-identity-verification-attributes \
  --identities your-email@example.com \
  --region eu-west-1 \
  --profile AdministratorAccess-016164185850
```

Check your email for a verification link from AWS SES.

### 2. Confirm SNS Subscription

Check your email for SNS subscription confirmation for billing alerts.

### 3. Create Cognito Users

```bash
# Get User Pool ID
USER_POOL_ID=$(aws cloudformation describe-stacks \
  --stack-name ShoppingList-Dev \
  --region eu-west-1 \
  --profile AdministratorAccess-016164185850 \
  --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' \
  --output text)

# Create a user
aws cognito-idp admin-create-user \
  --user-pool-id ${USER_POOL_ID} \
  --username user@example.com \
  --user-attributes \
    Name=email,Value=user@example.com \
    Name=email_verified,Value=true \
    Name=custom:displayName,Value=UserName \
  --message-action SUPPRESS \
  --region eu-west-1 \
  --profile AdministratorAccess-016164185850

# Set permanent password
aws cognito-idp admin-set-user-password \
  --user-pool-id ${USER_POOL_ID} \
  --username user@example.com \
  --password 'YourSecurePassword123!' \
  --permanent \
  --region eu-west-1 \
  --profile AdministratorAccess-016164185850
```

### 4. Configure DNS (If Using Custom Domain)

Get the CloudFront distribution domain name:

```bash
aws cloudformation describe-stacks \
  --stack-name ShoppingList-Dev \
  --region eu-west-1 \
  --profile AdministratorAccess-016164185850 \
  --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontDistributionDomain`].OutputValue' \
  --output text
```

Add a CNAME record in your DNS provider:
- **Type**: CNAME
- **Name**: shoppinglist (or your subdomain)
- **Value**: `d1234567890abc.cloudfront.net` (from above command)
- **TTL**: 3600

### 5. Update Frontend Configuration

Update `website/auth.js` with your Cognito configuration:

```javascript
const COGNITO_CONFIG = {
    userPoolId: 'YOUR_USER_POOL_ID',  // From stack outputs
    clientId: 'YOUR_CLIENT_ID',        // From stack outputs
    region: 'eu-west-1'
};
```

Update `website/app.js` with your API endpoint:

```javascript
const API_BASE_URL = 'YOUR_API_ENDPOINT';  // From stack outputs
```

Then re-upload to S3 and invalidate CloudFront cache.

### 6. Enable Bedrock Model Access

For the categorizeItems function to work, enable Bedrock model access:

1. Go to AWS Bedrock console
2. Navigate to "Model access"
3. Request access to "Claude 3 Haiku"
4. Wait for approval (usually instant)

## Updating Stacks

### Update Nested Stack Templates

1. Upload updated template to S3:
```bash
aws s3 cp storage-stack.yaml s3://${TEMPLATES_BUCKET}/ --profile AdministratorAccess-016164185850
```

2. Update the main stack:
```bash
aws cloudformation update-stack \
  --stack-name ShoppingList-Dev \
  --template-body file://main-stack.yaml \
  --parameters file://parameters.json \
  --capabilities CAPABILITY_NAMED_IAM \
  --region eu-west-1 \
  --profile AdministratorAccess-016164185850
```

### Update Lambda Code

```bash
cd lambda
zip functionName.zip functionName.py cognito_helper.py

aws lambda update-function-code \
  --function-name ShoppingList-Dev-FunctionName \
  --zip-file fileb://functionName.zip \
  --region eu-west-1 \
  --profile AdministratorAccess-016164185850
```

### Update Website Files

```bash
cd website
aws s3 sync . s3://${BUCKET_NAME}/ --profile AdministratorAccess-016164185850

# Invalidate CloudFront
aws cloudfront create-invalidation \
  --distribution-id ${DIST_ID} \
  --paths "/*" \
  --profile AdministratorAccess-016164185850
```

## Deleting Stacks

### Important Notes
- Deleting stacks will **permanently delete all data**
- DynamoDB tables will be deleted
- S3 buckets must be emptied before deletion
- CloudFront distributions can take 15+ minutes to delete

### Delete Order

1. **Empty S3 buckets**:
```bash
aws s3 rm s3://${BUCKET_NAME} --recursive --profile AdministratorAccess-016164185850
```

2. **Delete main stack** (deletes all nested stacks):
```bash
aws cloudformation delete-stack \
  --stack-name ShoppingList-Dev \
  --region eu-west-1 \
  --profile AdministratorAccess-016164185850
```

3. **Monitor deletion**:
```bash
aws cloudformation describe-stacks \
  --stack-name ShoppingList-Dev \
  --region eu-west-1 \
  --profile AdministratorAccess-016164185850
```

Stack will show `DELETE_COMPLETE` when finished, then disappear from the list.

## Estimated Costs

### Monthly Cost Breakdown (Approximate)

**Free Tier Eligible** (first 12 months):
- DynamoDB: 25 GB storage, 200M requests/month
- Lambda: 1M requests, 400,000 GB-seconds
- API Gateway: 1M requests
- CloudFront: 50 GB data transfer
- Cognito: 50,000 MAU

**After Free Tier** (Low Usage - ~100 users, 1000 requests/day):
- DynamoDB (On-Demand): $1-5/month
- Lambda: $0.50-2/month
- API Gateway: $3-10/month
- CloudFront: $1-5/month
- S3: $0.50-1/month
- Cognito: Free (first 50,000 MAU)
- SES: $0.10 per 1,000 emails
- Bedrock (Claude 3 Haiku): $0.00025 per 1K input tokens, $0.00125 per 1K output tokens

**Estimated Total**: $5-25/month for low usage

**High Usage** (1000 users, 10,000 requests/day):
- Total: $50-150/month

**CloudWatch Billing Alarms**: Configured at $10, $20, $30, $50, $100

### Cost Optimization Tips
1. Use DynamoDB on-demand billing for variable workloads
2. Set Lambda memory to minimum required
3. Enable CloudFront compression
4. Use Route 53 alias records (free) instead of CNAME
5. Delete unused CloudWatch logs
6. Enable S3 lifecycle policies for old logs

## Troubleshooting

### Stack Creation Fails

**Check Events**:
```bash
aws cloudformation describe-stack-events \
  --stack-name ShoppingList-Dev \
  --region eu-west-1 \
  --profile AdministratorAccess-016164185850 \
  --max-items 50
```

**Common Issues**:
- **S3 bucket name taken**: Bucket names must be globally unique
- **Certificate in wrong region**: ACM cert for CloudFront must be in us-east-1
- **Insufficient permissions**: Ensure IAM user has required permissions
- **Template bucket not accessible**: Verify nested templates uploaded to S3

### Lambda Functions Not Working

**Check Logs**:
```bash
aws logs tail /aws/lambda/ShoppingList-Dev-CreateItem \
  --follow \
  --region eu-west-1 \
  --profile AdministratorAccess-016164185850
```

**Common Issues**:
- **Placeholder code deployed**: Update function code (see Step 5)
- **DynamoDB permissions**: Check IAM role policy
- **Environment variables missing**: Verify in Lambda console

### API Gateway 401 Errors

**Check**:
- Cognito User Pool ID matches in frontend
- JWT token included in Authorization header
- User exists in Cognito User Pool
- Token not expired (1 hour validity)

### CloudFront Not Serving Updated Content

**Solution**:
```bash
aws cloudfront create-invalidation \
  --distribution-id ${DIST_ID} \
  --paths "/*" \
  --profile AdministratorAccess-016164185850
```

### SES Emails Not Sending

**Check**:
- Email identity verified
- Account not in SES sandbox (for production)
- Correct email in Lambda environment variable

## Support

For issues or questions:
1. Check CloudFormation stack events
2. Review CloudWatch Logs
3. Verify all post-deployment steps completed
4. Check AWS Service Health Dashboard

## Additional Resources

- [AWS CloudFormation Documentation](https://docs.aws.amazon.com/cloudformation/)
- [AWS Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
- [Amazon Cognito Developer Guide](https://docs.aws.amazon.com/cognito/)
- [API Gateway Developer Guide](https://docs.aws.amazon.com/apigateway/)

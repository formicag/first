# Decommissioning Guide

Complete guide to safely tear down the Shopping List Application infrastructure.

## Overview

This guide provides step-by-step instructions to decommission all AWS resources and stop incurring costs. The application uses CloudFormation nested stacks, which must be deleted in the correct order.

**Estimated Time:** 15-20 minutes
**Final Cost After Decommissioning:** £0/month

## Prerequisites

- AWS CLI v2 with SSO configured
- AWS profile: `AdministratorAccess-016164185850`
- Access to GitHub repository (optional - for CI/CD cleanup)

## AWS Authentication

```bash
# Login via SSO
aws sso login --profile AdministratorAccess-016164185850

# Verify authentication
aws sts get-caller-identity --profile AdministratorAccess-016164185850
```

## Step 1: Backup Data (Optional but Recommended)

Before deleting anything, backup your DynamoDB data if you want to keep records.

### Backup Shopping List Table

```bash
# Export all items
aws dynamodb scan \
  --table-name ShoppingList \
  --region eu-west-1 \
  --profile AdministratorAccess-016164185850 \
  > backup-shopping-list-$(date +%Y%m%d).json

echo "Shopping list backed up to: backup-shopping-list-$(date +%Y%m%d).json"
```

### Backup Shop History Table

```bash
# Export all shop history
aws dynamodb scan \
  --table-name ShoppingList-ShopHistory-Dev \
  --region eu-west-1 \
  --profile AdministratorAccess-016164185850 \
  > backup-shop-history-$(date +%Y%m%d).json

echo "Shop history backed up to: backup-shop-history-$(date +%Y%m%d).json"
```

## Step 2: Empty S3 Bucket

CloudFormation cannot delete non-empty S3 buckets. Must empty first.

```bash
# Empty the S3 bucket
aws s3 rm s3://shoppinglist.gianlucaformica.net --recursive \
  --region eu-west-1 \
  --profile AdministratorAccess-016164185850

# Verify bucket is empty
aws s3 ls s3://shoppinglist.gianlucaformica.net \
  --region eu-west-1 \
  --profile AdministratorAccess-016164185850
```

**Expected Output:** Empty (no files listed)

## Step 3: Delete CloudFormation Stacks

Delete in reverse order of dependencies.

### Option A: Delete Main Stack (Recommended - Deletes All Nested Stacks)

```bash
# Delete main stack (automatically deletes nested stacks)
aws cloudformation delete-stack \
  --stack-name ShoppingList-Main-Stack \
  --region eu-west-1 \
  --profile AdministratorAccess-016164185850

# Monitor deletion progress
aws cloudformation describe-stacks \
  --stack-name ShoppingList-Main-Stack \
  --region eu-west-1 \
  --profile AdministratorAccess-016164185850 \
  --query 'Stacks[0].StackStatus' \
  --output text

# Or watch in real-time
aws cloudformation wait stack-delete-complete \
  --stack-name ShoppingList-Main-Stack \
  --region eu-west-1 \
  --profile AdministratorAccess-016164185850

echo "Main stack deletion complete"
```

**Wait Time:** 5-10 minutes for complete deletion

### Option B: Delete Nested Stacks Individually (If Main Stack Fails)

If the main stack deletion fails, delete nested stacks manually:

```bash
# 1. Delete S3 Stack (frontend)
aws cloudformation delete-stack \
  --stack-name ShoppingList-S3-Stack \
  --region eu-west-1 \
  --profile AdministratorAccess-016164185850

# Wait for completion
aws cloudformation wait stack-delete-complete \
  --stack-name ShoppingList-S3-Stack \
  --region eu-west-1 \
  --profile AdministratorAccess-016164185850

# 2. Delete API Stack
aws cloudformation delete-stack \
  --stack-name ShoppingList-API-Stack \
  --region eu-west-1 \
  --profile AdministratorAccess-016164185850

aws cloudformation wait stack-delete-complete \
  --stack-name ShoppingList-API-Stack \
  --region eu-west-1 \
  --profile AdministratorAccess-016164185850

# 3. Delete Compute Stack (Lambda functions)
aws cloudformation delete-stack \
  --stack-name ShoppingList-Compute-Stack \
  --region eu-west-1 \
  --profile AdministratorAccess-016164185850

aws cloudformation wait stack-delete-complete \
  --stack-name ShoppingList-Compute-Stack \
  --region eu-west-1 \
  --profile AdministratorAccess-016164185850

# 4. Delete DynamoDB Stack
aws cloudformation delete-stack \
  --stack-name ShoppingList-DynamoDB-Stack \
  --region eu-west-1 \
  --profile AdministratorAccess-016164185850

aws cloudformation wait stack-delete-complete \
  --stack-name ShoppingList-DynamoDB-Stack \
  --region eu-west-1 \
  --profile AdministratorAccess-016164185850

# 5. Finally, delete main stack
aws cloudformation delete-stack \
  --stack-name ShoppingList-Main-Stack \
  --region eu-west-1 \
  --profile AdministratorAccess-016164185850

aws cloudformation wait stack-delete-complete \
  --stack-name ShoppingList-Main-Stack \
  --region eu-west-1 \
  --profile AdministratorAccess-016164185850

echo "All stacks deleted successfully"
```

## Step 4: Verify Stack Deletion

```bash
# List all ShoppingList stacks (should return empty or "does not exist")
aws cloudformation list-stacks \
  --stack-status-filter DELETE_COMPLETE \
  --region eu-west-1 \
  --profile AdministratorAccess-016164185850 \
  --query 'StackSummaries[?contains(StackName, `ShoppingList`)].[StackName, StackStatus]' \
  --output table
```

## Step 5: Clean Up Remaining Resources

### Check for Orphaned Lambda Functions

```bash
# List Lambda functions
aws lambda list-functions \
  --region eu-west-1 \
  --profile AdministratorAccess-016164185850 \
  --query 'Functions[?contains(FunctionName, `ShoppingList`)].[FunctionName]' \
  --output table

# If any exist, delete them
aws lambda delete-function \
  --function-name ShoppingList-CreateItem \
  --region eu-west-1 \
  --profile AdministratorAccess-016164185850
# Repeat for each function
```

### Check for Orphaned DynamoDB Tables

```bash
# List tables
aws dynamodb list-tables \
  --region eu-west-1 \
  --profile AdministratorAccess-016164185850 \
  --query 'TableNames[?contains(@, `ShoppingList`)]' \
  --output table

# If any exist, delete them
aws dynamodb delete-table \
  --table-name ShoppingList \
  --region eu-west-1 \
  --profile AdministratorAccess-016164185850

aws dynamodb delete-table \
  --table-name ShoppingList-ShopHistory-Dev \
  --region eu-west-1 \
  --profile AdministratorAccess-016164185850
```

### Check for Orphaned API Gateway APIs

```bash
# List REST APIs
aws apigateway get-rest-apis \
  --region eu-west-1 \
  --profile AdministratorAccess-016164185850 \
  --query 'items[?contains(name, `ShoppingList`)].[id, name]' \
  --output table

# If any exist, delete them
aws apigateway delete-rest-api \
  --rest-api-id <API_ID> \
  --region eu-west-1 \
  --profile AdministratorAccess-016164185850
```

### Check for Orphaned S3 Buckets

```bash
# List buckets
aws s3 ls --profile AdministratorAccess-016164185850 | grep shoppinglist

# If any exist, force delete (use with caution)
aws s3 rb s3://shoppinglist.gianlucaformica.net --force \
  --region eu-west-1 \
  --profile AdministratorAccess-016164185850
```

### Check for Orphaned CloudFront Distributions

```bash
# List distributions
aws cloudfront list-distributions \
  --profile AdministratorAccess-016164185850 \
  --query 'DistributionList.Items[?contains(Comment, `ShoppingList`) || contains(DomainName, `shoppinglist`)].[Id, DomainName, Status]' \
  --output table

# If any exist:
# 1. Disable distribution first
aws cloudfront get-distribution-config \
  --id <DISTRIBUTION_ID> \
  --profile AdministratorAccess-016164185850 \
  > dist-config.json

# Edit dist-config.json: set "Enabled": false
# Save ETag value from previous command

aws cloudfront update-distribution \
  --id <DISTRIBUTION_ID> \
  --if-match <ETAG> \
  --distribution-config file://dist-config.json \
  --profile AdministratorAccess-016164185850

# 2. Wait 15-20 minutes for deployment
# 3. Delete distribution
aws cloudfront delete-distribution \
  --id <DISTRIBUTION_ID> \
  --if-match <NEW_ETAG> \
  --profile AdministratorAccess-016164185850
```

### Check for CloudWatch Log Groups

```bash
# List log groups
aws logs describe-log-groups \
  --region eu-west-1 \
  --profile AdministratorAccess-016164185850 \
  --query 'logGroups[?contains(logGroupName, `ShoppingList`)].[logGroupName]' \
  --output table

# Delete log groups (optional - they're cheap and auto-expire)
aws logs delete-log-group \
  --log-group-name /aws/lambda/ShoppingList-CreateItem \
  --region eu-west-1 \
  --profile AdministratorAccess-016164185850
# Repeat for each log group
```

## Step 6: Clean Up IAM Roles and Policies

### Delete Lambda Execution Role

```bash
# List attached policies
aws iam list-attached-role-policies \
  --role-name ShoppingListLambdaRole \
  --profile AdministratorAccess-016164185850

# Detach managed policies (if any)
aws iam detach-role-policy \
  --role-name ShoppingListLambdaRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole \
  --profile AdministratorAccess-016164185850

# List inline policies
aws iam list-role-policies \
  --role-name ShoppingListLambdaRole \
  --profile AdministratorAccess-016164185850

# Delete inline policies
aws iam delete-role-policy \
  --role-name ShoppingListLambdaRole \
  --policy-name ShoppingListDynamoDBPolicy \
  --profile AdministratorAccess-016164185850

# Delete role
aws iam delete-role \
  --role-name ShoppingListLambdaRole \
  --profile AdministratorAccess-016164185850
```

### Delete GitHub Actions OIDC Role (Optional)

Only if you want to completely remove CI/CD access:

```bash
# Delete GitHub Actions role
aws iam delete-role \
  --role-name GitHubActionsDeployRole \
  --profile AdministratorAccess-016164185850
```

## Step 7: GitHub Repository Cleanup (Optional)

### Disable GitHub Actions

1. Go to https://github.com/formicag/first/settings/actions
2. Click "Disable Actions for this repository"

### Delete GitHub Secrets

1. Go to https://github.com/formicag/first/settings/secrets/actions
2. Delete secrets:
   - `AWS_REGION`
   - `AWS_ACCOUNT_ID`
   - Any other ShoppingList-related secrets

### Archive or Delete Repository

**Option A - Archive (keeps history, makes read-only):**
1. Go to https://github.com/formicag/first/settings
2. Scroll to "Danger Zone"
3. Click "Archive this repository"

**Option B - Delete (permanent):**
1. Go to https://github.com/formicag/first/settings
2. Scroll to "Danger Zone"
3. Click "Delete this repository"
4. Type `formicag/first` to confirm

## Step 8: Verify Complete Decommissioning

Run this comprehensive check:

```bash
#!/bin/bash

echo "=== Checking for ShoppingList Resources ==="

echo "\n1. CloudFormation Stacks:"
aws cloudformation list-stacks \
  --region eu-west-1 \
  --profile AdministratorAccess-016164185850 \
  --query 'StackSummaries[?contains(StackName, `ShoppingList`) && StackStatus != `DELETE_COMPLETE`].[StackName, StackStatus]' \
  --output table

echo "\n2. Lambda Functions:"
aws lambda list-functions \
  --region eu-west-1 \
  --profile AdministratorAccess-016164185850 \
  --query 'Functions[?contains(FunctionName, `ShoppingList`)].[FunctionName]' \
  --output table

echo "\n3. DynamoDB Tables:"
aws dynamodb list-tables \
  --region eu-west-1 \
  --profile AdministratorAccess-016164185850 \
  --query 'TableNames[?contains(@, `ShoppingList`)]' \
  --output table

echo "\n4. API Gateway APIs:"
aws apigateway get-rest-apis \
  --region eu-west-1 \
  --profile AdministratorAccess-016164185850 \
  --query 'items[?contains(name, `ShoppingList`)].[name]' \
  --output table

echo "\n5. S3 Buckets:"
aws s3 ls --profile AdministratorAccess-016164185850 | grep shoppinglist

echo "\n6. CloudFront Distributions:"
aws cloudfront list-distributions \
  --profile AdministratorAccess-016164185850 \
  --query 'DistributionList.Items[?contains(Comment, `ShoppingList`)].[Id, Status]' \
  --output table

echo "\n7. IAM Roles:"
aws iam list-roles \
  --profile AdministratorAccess-016164185850 \
  --query 'Roles[?contains(RoleName, `ShoppingList`)].[RoleName]' \
  --output table

echo "\n=== Check Complete ==="
echo "If all sections are empty or show 'None', decommissioning is successful!"
```

Save this as `check-decommission.sh`, make executable, and run:

```bash
chmod +x check-decommission.sh
./check-decommission.sh
```

## Step 9: Verify Costs Have Stopped

Wait 24-48 hours, then check AWS Cost Explorer:

1. Go to https://console.aws.amazon.com/cost-management/home#/cost-explorer
2. Select "Last 7 days"
3. Group by: Service
4. Verify no charges for:
   - DynamoDB
   - Lambda
   - API Gateway
   - S3
   - CloudFront
   - Bedrock

**Expected Cost After Decommissioning:** £0/month

## Rollback Plan (If You Change Your Mind)

If you want to redeploy later:

1. **Restore from Git:**
   ```bash
   git clone https://github.com/formicag/first.git
   cd first
   ```

2. **Redeploy Infrastructure:**
   ```bash
   # Follow cloudformation/README-deployment.md
   aws cloudformation create-stack \
     --stack-name ShoppingList-Main-Stack \
     --template-body file://cloudformation/main-stack.yaml \
     --capabilities CAPABILITY_IAM \
     --region eu-west-1 \
     --profile AdministratorAccess-016164185850
   ```

3. **Restore Data (if backed up):**
   ```bash
   # Restore shopping list items
   aws dynamodb batch-write-item \
     --request-items file://backup-shopping-list-YYYYMMDD.json \
     --region eu-west-1 \
     --profile AdministratorAccess-016164185850

   # Restore shop history
   aws dynamodb batch-write-item \
     --request-items file://backup-shop-history-YYYYMMDD.json \
     --region eu-west-1 \
     --profile AdministratorAccess-016164185850
   ```

## Troubleshooting

### Stack Deletion Stuck "IN_PROGRESS"

```bash
# Check events to see what's blocking
aws cloudformation describe-stack-events \
  --stack-name ShoppingList-Main-Stack \
  --region eu-west-1 \
  --profile AdministratorAccess-016164185850 \
  --query 'StackEvents[?ResourceStatus==`DELETE_FAILED`]' \
  --output table
```

**Common Issues:**
- S3 bucket not empty → Empty bucket manually (Step 2)
- CloudFront distribution enabled → Disable first, wait 15 mins
- Lambda has dependencies → Delete API Gateway first

### "Role is in use" Error

IAM roles may take 5-10 minutes to fully detach. Wait and retry.

### Cost Still Showing After 48 Hours

Check:
1. CloudWatch Logs (cheap but adds up): Delete log groups
2. Bedrock cache (if implemented): Verify AICache table deleted
3. S3 versioning: Check for versioned objects

## Summary

After completing all steps:

- All AWS resources deleted
- Monthly cost: £0
- Data backed up locally (optional)
- GitHub Actions disabled
- Infrastructure can be redeployed anytime from Git

**Decommissioning Complete! 🎉**

---

**Questions or Issues?**
- Check CloudWatch logs for error details
- Review CloudFormation events for deletion failures
- Ensure AWS CLI profile has admin permissions

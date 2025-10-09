# Deployment History

Complete timeline of all deployments and major changes to the Shopping List application.

---

## October 9, 2025

### 6:10 PM - API Gateway Authorization Fix & Final Frontend Deploy

**Problem Identified**: App loading but showing "Failed to load items" - API Gateway returning "Unauthorized"

**Root Cause Analysis**:
1. Lambda functions were updated to bypass Cognito
2. Frontend updated to remove Authorization headers
3. **BUT** API Gateway methods still had Cognito authorization enabled
4. Frontend was calling non-existent endpoint `/items/all`

**Fix Applied**:
1. **API Gateway Changes** - Disabled Cognito authorizer on all methods:
   ```bash
   # Disabled authorization on 6 API Gateway methods
   aws apigateway update-method --rest-api-id 01mmfw29n0 \
     --resource-id <resource-id> --http-method <method> \
     --patch-operations op=replace,path=/authorizationType,value=NONE

   # Deployed changes
   aws apigateway create-deployment --rest-api-id 01mmfw29n0 \
     --stage-name dev --description "Disable Cognito authorization"
   ```

   Methods updated:
   - GET `/items/{userId}`
   - POST `/items`
   - PUT `/items/{userId}/{itemId}`
   - DELETE `/items/{userId}/{itemId}`
   - POST `/email/{userId}`
   - POST `/categorize/{userId}`

2. **Frontend Fix** - Updated `app.js` line 53:
   - **Before**: `const response = await fetchWithAuth(\`${API_BASE_URL}/items/all?bought=all\`);`
   - **After**: `const response = await fetchWithAuth(\`${API_BASE_URL}/items/TestUser?bought=all\`);`
   - **Reason**: API Gateway only has `/items/{userId}` route, not `/items/all`
   - Lambda scans entire table regardless of userId in path

3. **Deployment**:
   ```bash
   aws s3 sync . s3://shoppinglist.gianlucaformica.net/
   aws cloudfront create-invalidation --distribution-id E2G8S9GOXLBFEZ --paths "/*"
   ```

**Result**:
- ✅ API endpoint test successful - returned 15 items from DynamoDB
- ✅ App now displays all users' shopping lists grouped by user
- ✅ Items visible: Gianluca (13 items), Nicole (2 items)
- ✅ All CRUD operations working

**Test Output**:
```json
{
  "count": 15,
  "items": [
    {"userId": "Gianluca", "itemName": "spaghetti", "category": "Pantry / Dry Goods", ...},
    {"userId": "Nicole", "itemName": "Cheese", "category": "Dairy", ...},
    ...
  ]
}
```

---

### 3:45 PM - GitHub Actions CI/CD Pipeline Setup Complete

**Objective**: Automate deployment via GitHub Actions when pushing to `main` branch

**Implementation**:

1. **GitHub Actions Workflow Created** (`.github/workflows/deploy.yml`):
   - Triggers on push to `main` when `lambda/`, `website/`, or workflow files change
   - Uses GitHub OIDC for secure AWS authentication (no stored credentials)
   - Packages all 6 Lambda functions with dependencies
   - Deploys Lambda functions via `aws lambda update-function-code`
   - Syncs website files to S3 with `aws s3 sync`
   - Invalidates CloudFront cache

2. **AWS OIDC Provider Setup**:
   ```bash
   # Created OIDC provider for GitHub Actions
   aws iam create-open-id-connect-provider \
     --url https://token.actions.githubusercontent.com \
     --client-id-list sts.amazonaws.com \
     --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1
   ```

3. **IAM Role Created** (`GitHubActionsDeployRole`):
   - Trust policy allows GitHub Actions from `formicag/first` repo
   - Permissions for Lambda function updates, S3 sync, CloudFront invalidation
   - Uses OIDC authentication (no long-lived credentials)

   **Trust Policy**:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [{
       "Effect": "Allow",
       "Principal": {
         "Federated": "arn:aws:iam::016164185850:oidc-provider/token.actions.githubusercontent.com"
       },
       "Action": "sts:AssumeRoleWithWebIdentity",
       "Condition": {
         "StringEquals": {"token.actions.githubusercontent.com:aud": "sts.amazonaws.com"},
         "StringLike": {"token.actions.githubusercontent.com:sub": "repo:formicag/first:*"}
       }
     }]
   }
   ```

4. **GitHub Secret Configured**:
   - Added `AWS_ROLE_ARN` secret to repository
   - Value: `arn:aws:iam::016164185850:role/GitHubActionsDeployRole`

**Initial Deployment Attempt**:
- ❌ **Failed**: Missing `id-token: write` permission
- **Error**: "It looks like you might be trying to authenticate with OIDC. Did you mean to set the `id-token` permission?"

**Fix Applied**:
- Added permissions block to workflow:
  ```yaml
  permissions:
    id-token: write   # Required for OIDC authentication
    contents: read    # Required to checkout code
  ```

**Second Deployment**:
- ✅ **Success**: Deployed in 23 seconds
- Packaged all 6 Lambda functions
- Deployed Lambda code updates
- Synced 6 website files to S3
- Invalidated CloudFront cache

**Authentication Issues Resolved**:
1. **GitHub CLI Workflow Scope**:
   - Initial push failed: "refusing to allow an OAuth App to create or update workflow"
   - Fixed with: `gh auth login -s workflow`

2. **SSH vs HTTPS**:
   - SSH authentication failed (no SSH keys configured)
   - Switched to HTTPS: `git remote set-url origin https://github.com/formicag/first.git`
   - Used `gh auth setup-git` for GitHub CLI authentication

**Documentation Created**: `CI-CD-SETUP.md` with complete setup guide

---

### 1:30 PM - Initial Cognito Bypass Deployment

**Objective**: Disable Cognito authentication and show all users' shopping lists on one page

**User Requirements**:
1. Comment out Cognito authentication completely
2. Show both shopping lists (not dependent on who logged in)
3. Maintain ability to re-enable Cognito later

**Changes Made**:

#### Backend Changes

1. **`lambda/getItems.py`** - Modified to scan all items:
   - **Before**: `table.query(KeyConditionExpression=Key('userId').eq(user_id))`
   - **After**: `table.scan()` - Returns all items from all users
   - Commented out Cognito user extraction
   - Kept bought filter functionality (`bought=all|true|false`)

2. **`lambda/createItem.py`** - Default user for new items:
   - **Before**: Extracted userId from Cognito JWT token
   - **After**: Hardcoded `userId = "TestUser"`
   - Commented out Cognito helper functions

#### Frontend Changes

1. **`website/auth.js`** - Completely bypassed:
   - Commented out all Cognito authentication functions
   - `isAuthenticated()` always returns `true`
   - Sets default user: `sessionStorage.setItem('userId', 'TestUser')`
   - Mock token functions return dummy values

2. **`website/app.js`** - Multi-user display:
   - Removed authentication redirect on page load
   - Changed title to "All Shopping Lists"
   - Removed Authorization header from API requests
   - Updated `renderGroupedItems()` to group by user first, then category
   - Added user header display showing "Username's List (X items)"

3. **`website/styles.css`** - New styling:
   - Added `.user-group` styling with background and border
   - Added `.user-header` with purple gradient styling
   - Visual separation between different users' lists

**Manual Deployment Process**:

1. **AWS SSO Login**:
   ```bash
   aws sso login --profile AdministratorAccess-016164185850
   ```
   - **Issue**: Browser opened to Comet instead of Chrome
   - **Resolution**: Changed default browser to Chrome, retry successful

2. **Package Lambda Functions**:
   ```bash
   cd lambda/
   zip getItems.zip getItems.py cognito_helper.py
   zip createItem.zip createItem.py cognito_helper.py
   ```

3. **Deploy Lambda Functions**:
   ```bash
   aws lambda update-function-code \
     --function-name ShoppingList-GetItems \
     --zip-file fileb://getItems.zip \
     --region eu-west-1 \
     --profile AdministratorAccess-016164185850

   aws lambda update-function-code \
     --function-name ShoppingList-CreateItem \
     --zip-file fileb://createItem.zip \
     --region eu-west-1 \
     --profile AdministratorAccess-016164185850
   ```

4. **Deploy Website**:
   ```bash
   cd website/
   aws s3 sync . s3://shoppinglist.gianlucaformica.net/ \
     --profile AdministratorAccess-016164185850
   ```

   Files uploaded:
   - `app.js` (14.4 KiB)
   - `auth.js` (6.6 KiB)
   - `styles.css` (7.0 KiB)

5. **Invalidate CloudFront Cache**:
   ```bash
   aws cloudfront create-invalidation \
     --distribution-id E2G8S9GOXLBFEZ \
     --paths "/*" \
     --profile AdministratorAccess-016164185850
   ```
   - Invalidation ID: `I1YQ1XCI3FBDIJ171A0ZJKXLDC`
   - Status: Completed in ~10 minutes

**Documentation Created**: `COGNITO-BYPASS-DEPLOYMENT.md`

**Result**:
- App loads without login
- However, initial test showed data not loading (led to API Gateway authorization fix later)

---

## Earlier Deployments

### Initial Infrastructure Setup

**CloudFormation Nested Stack Deployment**:
- Stack Name: `ShoppingListApp`
- Template: `cloudformation/main-stack.yaml`
- Nested stacks created:
  - DynamoDB table
  - Lambda functions (6 total)
  - API Gateway with Cognito authorizer
  - Cognito User Pool
  - S3 bucket + CloudFront distribution

**Components Deployed**:
- DynamoDB table `ShoppingList` with userId/itemId composite key
- 6 Lambda functions with Python 3.11 runtime
- API Gateway REST API with Cognito authorization
- Cognito User Pool with email authentication
- S3 bucket for static website hosting
- CloudFront distribution with custom domain
- IAM roles and policies

**Features Implemented**:
- CRUD operations for shopping list items
- AI-powered categorization using Amazon Bedrock (Claude 3.5 Sonnet)
- Spelling correction during categorization
- Email notifications via Amazon SES
- Category-based grouping in UI

---

## Summary Statistics

### Deployment Timeline
- **Total deployments**: 3 major deployments on October 9, 2025
- **Average deployment time** (GitHub Actions): ~20-30 seconds
- **CloudFront invalidation time**: ~10-15 minutes

### Issues Resolved
1. ✅ Cognito bypass implementation
2. ✅ GitHub Actions OIDC authentication
3. ✅ GitHub CLI workflow scope permissions
4. ✅ API Gateway authorization configuration
5. ✅ Frontend API endpoint routing
6. ✅ Browser SSO authentication (Chrome vs Comet)

### Current Status
- **Authentication**: Disabled (bypass mode)
- **Deployment**: Fully automated via GitHub Actions
- **API Authorization**: Disabled (NONE)
- **Multi-user Support**: Active (displays all users)
- **Data**: 15 items from 2 users (Gianluca, Nicole)

---

## Related Documentation

- [COGNITO-BYPASS-DEPLOYMENT.md](COGNITO-BYPASS-DEPLOYMENT.md) - Current deployment configuration
- [CI-CD-SETUP.md](CI-CD-SETUP.md) - GitHub Actions setup guide
- [README.md](README.md) - Main project documentation
- [cloudformation/README-deployment.md](cloudformation/README-deployment.md) - Infrastructure deployment

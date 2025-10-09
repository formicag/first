# Cognito Bypass Mode - Deployment Documentation

**Date**: October 9, 2025
**Purpose**: Disable Cognito authentication and display all users' shopping lists

## Overview

This deployment disabled Cognito authentication throughout the shopping list application and modified it to display all users' lists on a single page. The app now operates in "bypass mode" with no authentication required.

## Changes Made

### Backend Changes

#### 1. Lambda Functions Modified

**getItems.py** (`lambda/getItems.py`)
- Changed from querying by specific userId to scanning all items
- Removed Cognito authentication requirement
- Now returns all items from all users
- Key changes at lines 45-95

**createItem.py** (`lambda/createItem.py`)
- Commented out Cognito user extraction
- Uses "TestUser" as default userId for new items
- Bypasses authentication checks
- Key changes at lines 40-62

### Frontend Changes

#### 2. Authentication Module Modified

**auth.js** (`website/auth.js`)
- Commented out all Cognito authentication code
- `isAuthenticated()` now always returns `true`
- Added mock token functions for bypass mode
- Sets default "TestUser" automatically
- Key changes at lines 1-193

#### 3. Application Logic Modified

**app.js** (`website/app.js`)
- Removed authentication redirect to login page (lines 6-13)
- Changed page title to "All Shopping Lists" (line 19)
- Updated API call to fetch from `/items/TestUser?bought=all` (line 53)
- Removed Authorization header from API requests (line 117)
- Updated rendering to group items by user first, then by category (lines 123-183)

#### 4. Styling Updated

**styles.css** (`website/styles.css`)
- Added styling for `.user-group` and `.user-header` (lines 242-258)
- Each user's list is now visually separated with distinct headers

## Deployment Process

### Method 1: Automatic Deployment (Recommended)

**GitHub Actions CI/CD is now configured** - simply push changes to the `main` branch:

```bash
git add .
git commit -m "Description of changes"
git push origin main
```

The GitHub Actions workflow automatically:
1. Packages all Lambda functions
2. Deploys Lambda functions to AWS
3. Syncs website files to S3
4. Invalidates CloudFront cache

**Workflow file**: `.github/workflows/deploy.yml`
**View deployments**: https://github.com/formicag/first/actions

See [CI-CD-SETUP.md](CI-CD-SETUP.md) for full setup details.

### Method 2: Manual Deployment

If you need to deploy manually without GitHub Actions:

#### Prerequisites
- AWS CLI configured with SSO profile `AdministratorAccess-016164185850`
- Active AWS SSO session via Google Workspace IdP
- Access to account `016164185850` in region `eu-west-1`

#### Step 1: AWS SSO Login

```bash
aws sso login --profile AdministratorAccess-016164185850
```

**SSO Configuration:**
- Start URL: `https://d-9367adb3a7.awsapps.com/start`
- Region: `eu-west-1`
- User: `gf@gianlucaformica.net`
- Identity Provider: Google Workspace

#### Step 2: Package Lambda Functions

```bash
cd /Users/gianlucaformica/Projects/first/lambda

# Package getItems
zip getItems.zip getItems.py cognito_helper.py

# Package createItem
zip createItem.zip createItem.py cognito_helper.py
```

**Result:**
- `getItems.zip` created (2,183 bytes)
- `createItem.zip` created (2,240 bytes)

#### Step 3: Update Lambda Functions on AWS

```bash
# Update getItems function
aws lambda update-function-code \
  --function-name ShoppingList-GetItems \
  --zip-file fileb:///Users/gianlucaformica/Projects/first/lambda/getItems.zip \
  --region eu-west-1 \
  --profile AdministratorAccess-016164185850

# Update createItem function
aws lambda update-function-code \
  --function-name ShoppingList-CreateItem \
  --zip-file fileb:///Users/gianlucaformica/Projects/first/lambda/createItem.zip \
  --region eu-west-1 \
  --profile AdministratorAccess-016164185850
```

**Lambda Function Names:**
- `ShoppingList-GetItems`
- `ShoppingList-CreateItem`
- `ShoppingList-UpdateItem` (not modified)
- `ShoppingList-DeleteItem` (not modified)
- `ShoppingList-EmailList` (not modified)
- `ShoppingList-CategorizeItems` (not modified)

#### Step 4: Upload Updated Website Files to S3

```bash
cd /Users/gianlucaformica/Projects/first/website

aws s3 sync . s3://shoppinglist.gianlucaformica.net/ \
  --profile AdministratorAccess-016164185850
```

**S3 Bucket:** `shoppinglist.gianlucaformica.net`

**Files Uploaded:**
- `app.js` (14.4 KiB)
- `auth.js` (6.6 KiB)
- `styles.css` (7.0 KiB)
- `index.html` (unchanged)
- `login.html` (unchanged)

#### Step 5: Invalidate CloudFront Cache

```bash
aws cloudfront create-invalidation \
  --distribution-id E2G8S9GOXLBFEZ \
  --paths "/*" \
  --profile AdministratorAccess-016164185850
```

**CloudFront Distribution ID:** `E2G8S9GOXLBFEZ`
**Invalidation ID:** `I1YQ1XCI3FBDIJ171A0ZJKXLDC`
**Status:** InProgress (typically completes in 5-15 minutes)

## Result

### What Works Now

✅ **No Authentication Required**
- App loads without login
- No Cognito tokens needed
- Login page bypassed

✅ **Multi-User View**
- All users' shopping lists displayed on one page
- Items grouped by:
  1. User (with purple header showing "Username's List")
  2. Category (within each user's section)

✅ **CRUD Operations**
- New items assigned to "TestUser" by default
- Update/delete operations work for all users
- Email and categorize functions still work (pass userId in path)

### API Behavior

All API Gateway methods have **authorization disabled** (set to NONE).

**GET /items/{userId}?bought=all**
- Returns all items from all users (DynamoDB table scan)
- userId path parameter is ignored (Lambda scans entire table)
- No authentication required
- Example: `GET /items/TestUser?bought=all`

**POST /items**
- Creates items under "TestUser"
- No authentication required

**PUT /items/{userId}/{itemId}**
- Updates items (userId from path parameter)
- No authentication required

**DELETE /items/{userId}/{itemId}**
- Deletes items (userId from path parameter)
- No authentication required

**POST /email/{userId}**
- Sends email with shopping list
- No authentication required

**POST /categorize/{userId}**
- Auto-categorizes items using AI
- No authentication required

## Re-enabling Cognito (Future)

To re-enable Cognito authentication, you'll need to:

### 1. Backend Changes
- `lambda/getItems.py` - Uncomment Cognito user extraction (lines 47-64)
- `lambda/getItems.py` - Change from table.scan() to table.query() with userId (lines 88-95)
- `lambda/createItem.py` - Uncomment Cognito user extraction (lines 43-59)

### 2. Frontend Changes
- `website/auth.js` - Uncomment all Cognito authentication functions (lines 7-60, 118-130, 142-185)
- `website/app.js` - Uncomment authentication redirect (lines 8-12)
- `website/app.js` - Uncomment 401 error handling (lines 50-55)
- `website/app.js` - Uncomment Authorization header (lines 81-98)

### 3. API Gateway Changes
Re-enable Cognito authorizer on all methods:
```bash
# For each method, update the authorization type back to COGNITO_USER_POOLS
aws apigateway update-method \
  --rest-api-id 01mmfw29n0 \
  --resource-id <resource-id> \
  --http-method <method> \
  --patch-operations op=replace,path=/authorizationType,value=COGNITO_USER_POOLS \
  --profile AdministratorAccess-016164185850

# Deploy the changes
aws apigateway create-deployment \
  --rest-api-id 01mmfw29n0 \
  --stage-name dev \
  --description "Re-enable Cognito authorization" \
  --profile AdministratorAccess-016164185850
```

### 4. Redeploy
Push changes to GitHub (automatic deployment) or use manual deployment steps above.

## Infrastructure Details

### AWS Resources
- **DynamoDB Table:** `ShoppingList`
- **API Gateway:** `https://01mmfw29n0.execute-api.eu-west-1.amazonaws.com/dev` (API ID: `01mmfw29n0`)
- **Cognito User Pool:** `eu-west-1_IennWZZNL` (bypassed but still exists)
- **CloudFront Distribution:** `E2G8S9GOXLBFEZ`
- **CloudFront Domain:** `https://shoppinglist.gianlucaformica.net`
- **S3 Bucket:** `shoppinglist.gianlucaformica.net`
- **IAM Role (Lambda):** `ShoppingListLambdaRole`
- **IAM Role (GitHub Actions):** `GitHubActionsDeployRole`

### Lambda Function Configuration
- **Runtime:** Python 3.11
- **Memory:** 128 MB
- **Timeout:** 30 seconds
- **Architecture:** x86_64
- **Region:** eu-west-1

## Testing

After deployment, verify:

1. **Website loads without login**: Visit `https://shoppinglist.gianlucaformica.net`
2. **All users visible**: Check that multiple users' lists are displayed
3. **Add items**: New items should be created under "TestUser"
4. **Update/delete**: Existing items can be modified
5. **Categorization**: Auto-categorize button should work
6. **Email**: Email list button should work (sends to configured SES email)

## Troubleshooting

### CloudFront Cache Not Cleared
If changes don't appear immediately, wait 5-15 minutes for invalidation to complete or check status:
```bash
aws cloudfront get-invalidation \
  --distribution-id E2G8S9GOXLBFEZ \
  --id I1YQ1XCI3FBDIJ171A0ZJKXLDC \
  --profile AdministratorAccess-016164185850
```

### Lambda Function Not Updated
Check function version:
```bash
aws lambda get-function \
  --function-name ShoppingList-GetItems \
  --region eu-west-1 \
  --profile AdministratorAccess-016164185850
```

### SSO Token Expired
Re-authenticate:
```bash
aws sso login --profile AdministratorAccess-016164185850
```

## Deployment History

### October 9, 2025 - API Gateway Authorization Fix
**Issue**: App was loading but couldn't fetch data from DynamoDB - API returned "Unauthorized"

**Root Cause**: API Gateway methods still had Cognito authorization enabled despite Lambda functions being updated

**Fix Applied**:
1. Disabled Cognito authorizer on all 6 API Gateway methods (set to NONE):
   - GET `/items/{userId}`
   - POST `/items`
   - PUT `/items/{userId}/{itemId}`
   - DELETE `/items/{userId}/{itemId}`
   - POST `/email/{userId}`
   - POST `/categorize/{userId}`

2. Fixed frontend API endpoint from `/items/all` to `/items/TestUser?bought=all`

3. Deployed API Gateway changes: `aws apigateway create-deployment --rest-api-id 01mmfw29n0 --stage-name dev`

**Result**: App now successfully loads all 15 items from DynamoDB and displays them grouped by user

### October 9, 2025 - GitHub Actions CI/CD Setup
**Setup**: Configured automated deployment pipeline using GitHub Actions with AWS OIDC

**Components Created**:
1. GitHub Actions workflow (`.github/workflows/deploy.yml`)
2. AWS OIDC provider for GitHub
3. IAM role `GitHubActionsDeployRole` with deployment permissions
4. GitHub repository secret `AWS_ROLE_ARN`

**Features**:
- Automatic deployment on push to `main` branch
- Triggers when files in `lambda/`, `website/`, or workflow change
- No stored AWS credentials (uses OIDC for secure authentication)
- Deploys Lambda functions, S3 files, and invalidates CloudFront

**First Deployment**: Successfully deployed in 23 seconds after adding `id-token: write` permission

### October 9, 2025 - Initial Cognito Bypass
**Purpose**: Disable Cognito authentication to display all users' shopping lists on one page

**Changes Made**:
- Modified Lambda functions (`getItems.py`, `createItem.py`)
- Updated frontend (`auth.js`, `app.js`, `styles.css`)
- Deployed via manual AWS CLI commands

## Notes

- **Default Browser Issue**: Encountered issue with Comet browser; switching to Chrome resolved SSO login
- **Function Naming**: Lambda functions use pattern `ShoppingList-{FunctionName}` (no environment suffix)
- **API Gateway Authorization**: Completely disabled (NONE) - no authentication required
- **Data Persistence**: All existing user data (Gianluca, Nicole, etc.) remains in DynamoDB
- **CI/CD**: All deployments now automated via GitHub Actions

## References

- Original deployment docs: `/cloudformation/README-deployment.md`
- Lambda deployment docs: `/lambda/README.md`
- Main project README: `/README.md`

# Shopping List Application

A serverless shopping list web application built with AWS services, featuring AI-powered categorization, email notifications, and multi-user support.

**Live Application**: https://shoppinglist.gianlucaformica.net

## Overview

Full-stack serverless application demonstrating AWS cloud architecture, CI/CD automation, and modern web development practices. Features include real-time CRUD operations, AI-powered item categorization, and automatic deployment via GitHub Actions.

## Features

### Core Functionality
- ✅ **Multi-User Shopping Lists**: View and manage shopping lists for multiple users
- ✅ **Real-time CRUD Operations**: Add, update, mark as bought, and delete items
- ✅ **Smart Categorization**: AI-powered automatic categorization using Amazon Bedrock (Claude 3.5 Sonnet)
- ✅ **Spelling Correction**: Automatic spelling fixes during categorization
- ✅ **Email Lists**: Send shopping lists via Amazon SES
- ✅ **Grouped Display**: Items organized by user and category
- ✅ **Responsive Design**: Clean, modern UI with gradient styling

### Technical Features
- ✅ **Serverless Architecture**: Built entirely on AWS serverless services
- ✅ **CI/CD Pipeline**: Automated deployment via GitHub Actions with OIDC authentication
- ✅ **Infrastructure as Code**: Complete CloudFormation templates with nested stacks
- ✅ **No Authentication Mode**: Currently running in bypass mode (Cognito disabled)
- ✅ **Global CDN**: CloudFront distribution for fast worldwide access
- ✅ **API Gateway**: RESTful API with no authorization required

## Architecture

### Frontend
- **Technology**: Vanilla JavaScript, HTML5, CSS3
- **Hosting**: Amazon S3 static website hosting
- **CDN**: Amazon CloudFront distribution
- **Domain**: Custom domain via CloudFront

### Backend
- **Compute**: AWS Lambda (Python 3.11)
- **Database**: Amazon DynamoDB (ShoppingList table)
- **API**: Amazon API Gateway (REST API)
- **AI/ML**: Amazon Bedrock (Claude 3.5 Sonnet for categorization)
- **Email**: Amazon SES
- **Authentication**: Amazon Cognito (currently bypassed)

### DevOps
- **Version Control**: GitHub ([formicag/first](https://github.com/formicag/first))
- **CI/CD**: GitHub Actions with AWS OIDC
- **IAC**: AWS CloudFormation with nested stacks
- **Monitoring**: CloudWatch Logs

## Project Structure

```
first/
├── website/                    # Frontend application
│   ├── index.html             # Main shopping list page
│   ├── login.html             # Login page (bypassed)
│   ├── app.js                 # Main application logic
│   ├── auth.js                # Authentication (bypassed)
│   └── styles.css             # Styling
├── lambda/                     # Backend Lambda functions
│   ├── createItem.py          # Create new shopping list items
│   ├── getItems.py            # Retrieve items (scans all users)
│   ├── updateItem.py          # Update item status
│   ├── deleteItem.py          # Delete items
│   ├── emailList.py           # Send email with shopping list
│   ├── categorizeItems.py     # AI-powered categorization
│   └── cognito_helper.py      # Cognito utilities (bypassed)
├── cloudformation/             # Infrastructure as Code
│   ├── main-stack.yaml        # Main nested stack
│   ├── dynamodb-stack.yaml    # DynamoDB table
│   ├── lambda-stack.yaml      # Lambda functions
│   ├── api-gateway-stack.yaml # API Gateway
│   ├── cognito-stack.yaml     # Cognito User Pool
│   ├── s3-cloudfront-stack.yaml # Frontend hosting
│   └── README-deployment.md   # Original deployment docs
├── .github/
│   └── workflows/
│       └── deploy.yml         # GitHub Actions CI/CD workflow
├── COGNITO-BYPASS-DEPLOYMENT.md  # Bypass mode documentation
├── CI-CD-SETUP.md             # CI/CD setup guide
└── README.md                  # This file
```

## AWS Resources

### DynamoDB
- **Table**: `ShoppingList`
- **Partition Key**: `userId` (String)
- **Sort Key**: `itemId` (String)
- **Attributes**: itemName, quantity, category, bought, addedDate, boughtDate

### Lambda Functions
- `ShoppingList-CreateItem` - Create new items
- `ShoppingList-GetItems` - Retrieve all items (table scan)
- `ShoppingList-UpdateItem` - Update item properties
- `ShoppingList-DeleteItem` - Delete items
- `ShoppingList-EmailList` - Send email notifications
- `ShoppingList-CategorizeItems` - AI categorization with Bedrock

### API Gateway
- **API ID**: `01mmfw29n0`
- **Stage**: `dev`
- **Base URL**: `https://01mmfw29n0.execute-api.eu-west-1.amazonaws.com/dev`
- **Authorization**: NONE (Cognito bypassed)
- **Endpoints**:
  - `GET /items/{userId}` - Get items
  - `POST /items` - Create item
  - `PUT /items/{userId}/{itemId}` - Update item
  - `DELETE /items/{userId}/{itemId}` - Delete item
  - `POST /email/{userId}` - Send email
  - `POST /categorize/{userId}` - Categorize items

### S3 & CloudFront
- **S3 Bucket**: `shoppinglist.gianlucaformica.net`
- **CloudFront Distribution**: `E2G8S9GOXLBFEZ`
- **Domain**: https://shoppinglist.gianlucaformica.net

### Cognito
- **User Pool**: `eu-west-1_IennWZZNL`
- **Status**: Exists but bypassed (authentication disabled)

### IAM Roles
- **Lambda Execution**: `ShoppingListLambdaRole`
- **GitHub Actions**: `GitHubActionsDeployRole` (OIDC)

## Deployment

### Automatic Deployment (Current Method)

The application uses **GitHub Actions** for automated deployment:

1. Make changes to code
2. Commit and push to `main` branch:
   ```bash
   git add .
   git commit -m "Your changes"
   git push origin main
   ```
3. GitHub Actions automatically:
   - Packages Lambda functions
   - Deploys to AWS Lambda
   - Syncs website files to S3
   - Invalidates CloudFront cache

**View deployments**: https://github.com/formicag/first/actions

**Deployment time**: ~20-30 seconds

### Manual Deployment

See [COGNITO-BYPASS-DEPLOYMENT.md](COGNITO-BYPASS-DEPLOYMENT.md) for manual AWS CLI deployment instructions.

### Initial Infrastructure Setup

The complete infrastructure was deployed using CloudFormation nested stacks:

```bash
aws cloudformation create-stack \
  --stack-name ShoppingListApp \
  --template-body file://cloudformation/main-stack.yaml \
  --capabilities CAPABILITY_NAMED_IAM \
  --profile AdministratorAccess-016164185850 \
  --region eu-west-1
```

See [cloudformation/README-deployment.md](cloudformation/README-deployment.md) for full infrastructure deployment details.

## Getting Started

### Prerequisites

- AWS CLI v2 with SSO configured
- GitHub account
- AWS account (Account ID: `016164185850`)
- Google Workspace configured as AWS SSO IdP

### AWS Authentication

```bash
# Login via SSO
aws sso login --profile AdministratorAccess-016164185850

# Verify authentication
aws sts get-caller-identity --profile AdministratorAccess-016164185850
```

### Local Development

1. Clone the repository:
   ```bash
   git clone https://github.com/formicag/first.git
   cd first
   ```

2. Make changes to files in `website/` or `lambda/`

3. Test locally (Lambda functions can be tested with sample events)

4. Push to GitHub to deploy:
   ```bash
   git add .
   git commit -m "Description of changes"
   git push origin main
   ```

## Documentation

- **[COGNITO-BYPASS-DEPLOYMENT.md](COGNITO-BYPASS-DEPLOYMENT.md)** - Current deployment configuration (Cognito disabled)
- **[CI-CD-SETUP.md](CI-CD-SETUP.md)** - GitHub Actions CI/CD setup guide
- **[cloudformation/README-deployment.md](cloudformation/README-deployment.md)** - Original infrastructure deployment
- **[lambda/README.md](lambda/README.md)** - Lambda function documentation

## Current Status

### Authentication: Bypassed
The application currently runs **without authentication**:
- Cognito User Pool exists but is not enforced
- API Gateway has authorization disabled (NONE)
- All users' shopping lists are visible on one page
- New items are created under "TestUser"

To re-enable Cognito authentication, see [COGNITO-BYPASS-DEPLOYMENT.md](COGNITO-BYPASS-DEPLOYMENT.md#re-enabling-cognito-future).

### CI/CD: Active
- ✅ GitHub Actions workflow configured
- ✅ OIDC authentication with AWS (no stored credentials)
- ✅ Automatic deployment on push to `main`
- ✅ Deploys Lambda functions and frontend in ~20-30 seconds

## Key Technologies

- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **Backend**: Python 3.11, AWS Lambda
- **Database**: DynamoDB
- **API**: API Gateway REST API
- **AI/ML**: Amazon Bedrock (Claude 3.5 Sonnet)
- **Email**: Amazon SES
- **Hosting**: S3 + CloudFront
- **CI/CD**: GitHub Actions
- **IAC**: CloudFormation

## License

This is a demonstration project for educational purposes.

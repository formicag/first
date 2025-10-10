# Shopping List Application

A serverless shopping list web application built with AWS services, featuring AI-powered categorization, email notifications, and multi-user support.

**Live Application**: https://shoppinglist.gianlucaformica.net

## Overview

Full-stack serverless application demonstrating AWS cloud architecture, CI/CD automation, and modern web development practices. Features include real-time CRUD operations, AI-powered item categorization, and automatic deployment via GitHub Actions.

## Features

### Core Functionality
- ✅ **Multi-User Shopping Lists**: View and manage shopping lists for multiple users (Gianluca & Nicole)
- ✅ **Real-time CRUD Operations**: Add, update, mark as bought, and delete items
- ✅ **AI-Powered Item Processing**: Amazon Bedrock (Claude 3 Haiku) automatically:
  - Corrects spelling mistakes
  - Capitalizes item names
  - Assigns emojis to items
  - Estimates Sainsbury's UK prices
  - Categorizes into UK supermarket aisles
- ✅ **Price Management**:
  - Automatic price estimation when adding items
  - Bulk price recalculation for all items
  - Real-time total price calculation per user and combined
  - Total prices displayed in header row for quick visibility
- ✅ **Shop History**: Store complete shopping list snapshots with date, time, items, and total price
  - One-click "Store Today's Shop" button in header
  - Preserves complete state of shopping list at time of storage
- ✅ **Customizable AI Prompts**: Configure custom instructions and household-specific terminology
- ✅ **Email Lists**: Send shopping lists via Amazon SES
- ✅ **Grouped Display**: Items organized by user and category
- ✅ **Dark Theme UI**: Modern GitHub-inspired dark theme across all pages
  - Main shopping list page
  - Login page
  - AI Prompt Manager page
  - Consistent color scheme: #0d1117 background, #c9d1d9 text, #8957e5 purple accents

### Technical Features
- ✅ **Serverless Architecture**: Built entirely on AWS serverless services
- ✅ **CI/CD Pipeline**: Automated deployment via GitHub Actions with OIDC authentication
- ✅ **Infrastructure as Code**: Complete CloudFormation templates with nested stacks
- ✅ **No Authentication Mode**: Currently running in bypass mode (Cognito disabled)
- ✅ **Global CDN**: CloudFront distribution for fast worldwide access
- ✅ **API Gateway**: RESTful API with no authorization required
- ✅ **Future-Ready Optimizations**: AI caching and modular prompts ready when scale increases
- ✅ **Configurable AI Model**: Switch Bedrock models via environment variables

## Architecture

### Frontend
- **Technology**: Vanilla JavaScript, HTML5, CSS3
- **Hosting**: Amazon S3 static website hosting
- **CDN**: Amazon CloudFront distribution
- **Domain**: Custom domain via CloudFront

### Backend
- **Compute**: AWS Lambda (Python 3.11)
- **Database**: Amazon DynamoDB
  - `ShoppingList` - Active shopping list items
  - `ShoppingList-ShopHistory-Dev` - Historical shop snapshots
- **API**: Amazon API Gateway (REST API)
- **AI/ML**: Amazon Bedrock (Claude 3 Haiku for item processing, categorization, and price estimation)
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
├── website/                    # Frontend application (all pages use dark theme)
│   ├── index.html             # Main shopping list page (dark theme)
│   ├── login.html             # Login page (bypassed, dark theme)
│   ├── prompt-manager.html    # AI prompt configuration page (dark theme)
│   ├── app.js                 # Main application logic
│   ├── auth.js                # Authentication (bypassed)
│   └── styles.css             # Dark theme styling (GitHub-inspired)
├── lambda/                     # Backend Lambda functions
│   ├── createItem.py          # Create new items with AI processing (spell check, emoji, price, category)
│   ├── getItems.py            # Retrieve items (scans all users)
│   ├── updateItem.py          # Update item status
│   ├── deleteItem.py          # Delete items
│   ├── emailList.py           # Send email with shopping list
│   ├── categorizeItems.py     # AI-powered bulk categorization
│   ├── improvePrompt.py       # AI prompt enrichment system
│   ├── recalculatePrices.py   # Bulk price recalculation with AI
│   ├── storeShop.py           # Store shop history snapshot
│   ├── ai_cache.py            # AI response caching utility (ready for activation)
│   ├── prompt_utils.py        # Modular prompt builder (ready for use)
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
├── OPTIMIZATION-OPPORTUNITIES.md # Future optimization strategies
└── README.md                  # This file
```

## AWS Resources

### DynamoDB Tables

**ShoppingList** - Active shopping list items
- **Partition Key**: `userId` (String)
- **Sort Key**: `itemId` (String)
- **Attributes**:
  - `itemName` - Item name (AI spell-checked and capitalized)
  - `emoji` - AI-assigned emoji for the item
  - `quantity` - Quantity of items
  - `estimatedPrice` - Sainsbury's UK price estimate (Decimal)
  - `category` - UK supermarket aisle category
  - `bought` - Boolean flag for purchased items
  - `addedDate` - ISO timestamp when item was added

**ShoppingList-ShopHistory-Dev** - Historical shop snapshots
- **Partition Key**: `shopId` (String - UUID)
- **Sort Key**: `shopDate` (String - ISO timestamp)
- **Attributes**:
  - `totalItems` - Number of items in shop
  - `totalPrice` - Total estimated price (Decimal)
  - `items` - Array of all items with full details (userId, itemName, emoji, quantity, estimatedPrice, category, bought)

### Lambda Functions
- `ShoppingList-CreateItem` - Create new items with full AI processing (spell check, emoji, price, category)
- `ShoppingList-GetItems` - Retrieve all items (table scan)
- `ShoppingList-UpdateItem` - Update item properties
- `ShoppingList-DeleteItem` - Delete items
- `ShoppingList-EmailList` - Send email notifications via SES
- `ShoppingList-CategorizeItems` - AI bulk categorization with Bedrock
- `ShoppingList-ImprovePrompt` - AI prompt enrichment system
- `ShoppingList-RecalculatePrices` - Bulk price recalculation with AI (Sainsbury's UK estimates)
- `ShoppingList-StoreShop` - Store complete shopping list snapshot to history

### API Gateway
- **API ID**: `01mmfw29n0`
- **Stage**: `dev`
- **Base URL**: `https://01mmfw29n0.execute-api.eu-west-1.amazonaws.com/dev`
- **Authorization**: NONE (Cognito bypassed)
- **Endpoints**:
  - `GET /items/{userId}?bought=all` - Get items (scans all users)
  - `POST /items` - Create item with AI processing (spell check, emoji, price, category)
  - `PUT /items/{userId}/{itemId}` - Update item
  - `DELETE /items/{userId}/{itemId}` - Delete item
  - `POST /email/{userId}` - Send email with shopping list
  - `POST /categorize/{userId}` - AI bulk categorization
  - `POST /improve-prompt` - AI prompt enrichment
  - `POST /prices/recalculate` - Recalculate all item prices with AI
  - `POST /shop/store` - Store shop snapshot to history

### S3 & CloudFront
- **S3 Bucket**: `shoppinglist.gianlucaformica.net`
- **CloudFront Distribution**: `E2G8S9GOXLBFEZ`
- **Domain**: https://shoppinglist.gianlucaformica.net

### Cognito
- **User Pool**: `eu-west-1_IennWZZNL`
- **Status**: Exists but bypassed (authentication disabled)

### IAM Roles
- **Lambda Execution**: `ShoppingListLambdaRole`
  - DynamoDB access (ShoppingList and ShoppingList-ShopHistory-Dev tables)
  - Bedrock model invocation (Claude 3 Haiku)
  - SES email sending
  - CloudWatch Logs
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
- **[OPTIMIZATION-OPPORTUNITIES.md](OPTIMIZATION-OPPORTUNITIES.md)** - Future optimization strategies and cost monitoring
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

### AI Configuration
- **Model**: Claude 3 Haiku (configurable via `BEDROCK_MODEL` environment variable)
- **Region**: eu-west-1
- **Features**: Spell checking, emoji assignment, price estimation, categorization
- **Cost Optimization**:
  - AI caching utility ready for activation (see `lambda/ai_cache.py`)
  - Modular prompt builder implemented (see `lambda/prompt_utils.py`)
  - Current costs: ~£2-3/month (well-optimized for current scale)
  - Comprehensive optimization guide: [OPTIMIZATION-OPPORTUNITIES.md](OPTIMIZATION-OPPORTUNITIES.md)

### UI/UX Design
- **Theme**: GitHub-inspired dark mode across all pages
- **Colors**:
  - Primary background: `#0d1117`
  - Card background: `#161b22`
  - Text: `#c9d1d9`
  - Accent purple: `#8957e5`
  - Success green: `#238636`
  - Error red: `#da3633`
- **Pages**:
  - `index.html` - Main shopping list with grouped items
  - `login.html` - Login page (currently bypassed)
  - `prompt-manager.html` - AI prompt configuration interface

## Key Technologies

- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **Backend**: Python 3.11, AWS Lambda
- **Database**: DynamoDB (2 tables)
- **API**: API Gateway REST API (9 endpoints)
- **AI/ML**: Amazon Bedrock (Claude 3 Haiku for spell check, emoji assignment, price estimation, categorization)
- **Email**: Amazon SES
- **Hosting**: S3 + CloudFront
- **CI/CD**: GitHub Actions with OIDC
- **IAC**: CloudFormation (nested stacks)

## License

This is a demonstration project for educational purposes.

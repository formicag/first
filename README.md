# Shopping List Application

A serverless shopping list web application built with AWS services, featuring AI-powered categorization, intelligent store layout ordering, and realistic shopping workflow management.

**Live Application**: https://shoppinglist.gianlucaformica.net

## Overview

Full-stack serverless application demonstrating AWS cloud architecture, CI/CD automation, and modern web development practices. Features include real-time CRUD operations, AI-powered item processing, store layout optimization, and a complete shopping workflow from list building to shop history tracking.

## Features

### Core Shopping Workflow
- ✅ **Realistic Shopping Experience**: Complete workflow matching real-world shopping:
  1. Build your shopping list
  2. Mark items "Save for Next Shop" (📌/🔖) for recurring items
  3. Tick items as you add them to your physical basket while shopping
  4. Click "Save My Shop" to:
     - Save ticked items to shop history
     - Remove purchased items from list
     - Keep "save for next" items for next week
     - Keep unticked items (things you didn't buy)
  5. List is ready for next shopping trip

- ✅ **Multi-User Shopping Lists**: Separate lists for Gianluca & Nicole
  - User-specific color coding (blue for Luca, pink for Nicole)
  - Per-user price totals and item counts
  - Combined household total in header

- ✅ **Store Layout Optimization**:
  - Items ordered by physical store layout (entrance to back of store)
  - Configurable via drag-and-drop Store Layout Settings page
  - Default Sainsbury's layout with 16 category positions
  - Items grouped by distance from entrance for efficient shopping
  - "Save for next shop" items automatically move to bottom

### AI-Powered Features
- ✅ **Intelligent Item Processing**: Amazon Bedrock (Claude 3 Haiku) automatically:
  - Corrects spelling mistakes
  - Capitalizes item names properly
  - Estimates Sainsbury's UK prices (2024-2025 pricing)
  - Categorizes into 16 UK supermarket aisles
  - Distinguishes between fresh, canned, and frozen items
  - Example: "tuna" → categorized as "Canned & Jarred" (not fresh fish)

- ✅ **Customizable AI Prompts**:
  - Configure custom instructions for categorization
  - Household-specific terminology support
  - UK English spelling enforcement
  - Accessible via "Configure AI Prompt" button

- ✅ **Bulk Operations**:
  - Recalculate all prices with one click
  - Recategorize all items with one click
  - AI updates prices and categories for all items in database

### Shop History & Analytics
- ✅ **Shop History Tracking**:
  - Complete snapshots of purchased items
  - Date, time, items, quantities, and total price
  - One shop per day (overwrites if shopping multiple times)
  - Accessible via Shopping Dashboard

- ✅ **Shopping Dashboard**:
  - View all saved shops (latest to oldest)
  - Delete individual shops
  - Last shop summary with total spending
  - Top 10 category spending analysis with visual bars
  - All-time statistics (total shops, spending, averages)

### Price Management
- ✅ **Automatic Price Estimation**:
  - AI estimates Sainsbury's UK prices when adding items
  - Considers typical package sizes
  - Real-time total calculation per user and combined
  - Price displayed next to each item

- ✅ **Price Recalculation**:
  - Bulk update all item prices via AI
  - Uses current Sainsbury's 2024-2025 pricing
  - Updates entire database with one click

### Store Layout Configuration
- ✅ **Store Layout Settings** (new dedicated page):
  - Drag-and-drop category reordering
  - Position 1 = entrance, Position 16 = back of store
  - Visual indicators (position numbers, category icons)
  - Save custom layout or reset to default Sainsbury's
  - Affects main list ordering automatically

### User Interface
- ✅ **Dark Theme UI**: Modern GitHub-inspired dark theme
  - Consistent across all pages
  - Primary: #0d1117, Cards: #161b22, Text: #c9d1d9
  - Purple accents (#8957e5), Green success, Red errors

- ✅ **Visual Item States**:
  - **Normal**: Full color, bright text
  - **Ticked (bought)**: Crossed out, very faded (opacity 0.5)
  - **Save for next shop**: Greyed out, bookmark icon (🔖), at bottom of list

- ✅ **Smart Sorting**:
  - Regular items: Store layout order (entrance → back)
  - Save for next items: Bottom of each user's list
  - Auto-resort when toggling save status

### Technical Features
- ✅ **Serverless Architecture**: 100% AWS serverless
- ✅ **CI/CD Pipeline**: GitHub Actions with OIDC (20-30 second deploys)
- ✅ **Infrastructure as Code**: CloudFormation nested stacks
- ✅ **No Authentication**: Simple public access
- ✅ **Global CDN**: CloudFront for worldwide performance
- ✅ **RESTful API**: API Gateway with 12 endpoints
- ✅ **Real-time Updates**: Instant UI refresh after operations

## Architecture

### Frontend
- **Technology**: Vanilla JavaScript, HTML5, CSS3
- **Pages**:
  - `index.html` - Main shopping list
  - `dashboard.html` - Shop history and analytics
  - `store-layout.html` - Store layout configuration
  - `prompt-manager.html` - AI prompt customization
- **Hosting**: Amazon S3 static website
- **CDN**: Amazon CloudFront
- **Domain**: Custom domain via CloudFront

### Backend
- **Compute**: AWS Lambda (Python 3.11)
- **Database**: Amazon DynamoDB
  - `ShoppingList` - Active shopping items (with saveForNext flag)
  - `ShoppingList-ShopHistory-Dev` - Historical shop snapshots
- **API**: Amazon API Gateway (REST API)
- **AI/ML**: Amazon Bedrock (Claude 3 Haiku)
- **Email**: Amazon SES

### DevOps
- **Version Control**: GitHub ([formicag/first](https://github.com/formicag/first))
- **CI/CD**: GitHub Actions with AWS OIDC
- **IAC**: AWS CloudFormation (nested stacks)
- **Monitoring**: CloudWatch Logs

## Project Structure

```
first/
├── website/                    # Frontend application
│   ├── index.html             # Main shopping list page
│   ├── dashboard.html         # Shop history & analytics
│   ├── store-layout.html      # Store layout configuration
│   ├── prompt-manager.html    # AI prompt customization
│   ├── app.js                 # Main application logic
│   ├── dashboard.js           # Dashboard logic
│   ├── store-layout.js        # Drag-and-drop layout manager
│   └── styles.css             # Dark theme styling
├── lambda/                     # Backend Lambda functions
│   ├── createItem.py          # Create items with AI processing
│   ├── getItems.py            # Retrieve items (sorted by store layout)
│   ├── updateItem.py          # Update item (supports saveForNext flag)
│   ├── deleteItem.py          # Delete items
│   ├── emailList.py           # Send email with shopping list
│   ├── categorizeItems.py     # AI bulk categorization (uncategorized only)
│   ├── recategorizeAllItems.py # AI recategorization (ALL items)
│   ├── improvePrompt.py       # AI prompt enrichment
│   ├── recalculatePrices.py   # Bulk AI price updates
│   ├── storeShop.py           # Store shop (NEW: only saves ticked items)
│   ├── getShopHistory.py      # Retrieve shop history
│   ├── deleteShop.py          # Delete individual shops
│   ├── store_layout.py        # Store layout sorting module
│   └── cognito_helper.py      # Cognito utilities (legacy)
├── cloudformation/             # Infrastructure as Code
│   ├── main-stack.yaml        # Main nested stack
│   ├── dynamodb-stack.yaml    # DynamoDB tables
│   ├── compute-stack.yaml     # Lambda functions
│   ├── api-stack.yaml         # API Gateway
│   └── s3-stack.yaml          # S3 & CloudFront
├── .github/
│   └── workflows/
│       └── deploy.yml         # CI/CD workflow
├── README.md                  # This file
├── CHANGELOG.md               # Version history
├── CI-CD-SETUP.md             # CI/CD setup guide
├── DECOMMISSIONING.md         # Decommissioning guide
└── OPTIMIZATION-OPPORTUNITIES.md # Future optimizations

Note: The filemgmt-and-duplicate-detector/ directory contains a separate
file management utility and is not part of the shopping list application.
```

## AWS Resources

### DynamoDB Tables

**ShoppingList** - Active shopping items
- **Partition Key**: `userId` (String)
- **Sort Key**: `itemId` (String)
- **Attributes**:
  - `itemName` - Item name (AI processed)
  - `quantity` - Quantity
  - `estimatedPrice` - Sainsbury's price (Decimal)
  - `category` - UK supermarket aisle (16 categories)
  - `bought` - Boolean (ticked in basket)
  - `saveForNext` - Boolean (save for next shop)
  - `addedDate` - ISO timestamp
  - `boughtDate` - ISO timestamp (when ticked)

**ShoppingList-ShopHistory-Dev** - Shop history
- **Partition Key**: `shopId` (String - UUID)
- **Sort Key**: `shopDate` (String - ISO timestamp)
- **Attributes**:
  - `totalItems` - Number of items purchased
  - `totalPrice` - Total price (Decimal)
  - `items` - Array of purchased items with full details

### Lambda Functions (13 total)
- `ShoppingList-CreateItem` - Create items with AI processing
- `ShoppingList-GetItems` - Retrieve items (sorted by store layout)
- `ShoppingList-UpdateItem` - Update items (supports saveForNext)
- `ShoppingList-DeleteItem` - Delete items
- `ShoppingList-EmailList` - Email lists via SES
- `ShoppingList-CategorizeItems` - AI bulk categorization (uncategorized only)
- `ShoppingList-RecategorizeAllItems` - AI recategorization (ALL items)
- `ShoppingList-ImprovePrompt` - AI prompt enrichment
- `ShoppingList-RecalculatePrices` - Bulk price updates
- `ShoppingList-StoreShop` - Save shop history (only ticked items)
- `ShoppingList-GetShopHistory` - Retrieve shop history
- `ShoppingList-DeleteShop` - Delete individual shops

### API Gateway Endpoints

**Base URL**: `https://01mmfw29n0.execute-api.eu-west-1.amazonaws.com/dev`

**Shopping List**:
- `GET /items/{userId}?bought=all` - Get items (sorted by store layout)
- `POST /items` - Create item with AI
- `PUT /items/{userId}/{itemId}` - Update item (supports saveForNext)
- `DELETE /items/{userId}/{itemId}` - Delete item

**Shop Operations**:
- `POST /shop/store` - Save shop (ticked items only)
- `GET /shop/history?limit=10` - Get shop history
- `DELETE /shop/{shopId}` - Delete shop

**AI & Utilities**:
- `POST /email/{userId}` - Send email
- `POST /categorize/{userId}` - AI categorization (uncategorized items)
- `POST /categorize/recalculate` - AI recategorization (ALL items)
- `POST /improve-prompt` - AI prompt improvement
- `POST /prices/recalculate` - Recalculate all prices

### Store Layout Categories (16 Total)

Default Sainsbury's layout (position 1 = entrance, 16 = back):

1. Health & Beauty
2. Fresh Produce - Herbs & Salads
3. Fresh Produce - Fruit
4. Fresh Produce - Vegetables
5. Meat & Poultry / Fish & Seafood
6. Household & Cleaning / Baby & Child
8. Dairy & Eggs
9. Beverages
10. Pantry & Dry Goods
11. Canned & Jarred
12. Bakery & Bread
13. Alcohol & Wine
14. Snacks & Confectionery
16. Frozen Foods

### S3 & CloudFront
- **S3 Bucket**: `shoppinglist.gianlucaformica.net`
- **CloudFront Distribution**: `E2G8S9GOXLBFEZ`
- **Domain**: https://shoppinglist.gianlucaformica.net

### IAM Roles
- **Lambda**: `ShoppingListLambdaRole`
  - DynamoDB access (both tables)
  - Bedrock invocation
  - SES email sending
  - CloudWatch Logs
- **GitHub Actions**: `GitHubActionsDeployRole` (OIDC)

## Deployment

### Automatic Deployment (Current)

GitHub Actions automatically deploys on push to `main`:

```bash
git add .
git commit -m "Your changes"
git push origin main
```

**What happens**:
1. Packages Lambda functions (includes dependencies like `store_layout.py`)
2. Deploys to AWS Lambda
3. Syncs website files to S3
4. Invalidates CloudFront cache

**View deployments**: https://github.com/formicag/first/actions

**Deployment time**: ~20-30 seconds

### Initial Infrastructure Setup

See [cloudformation/README-deployment.md](cloudformation/README-deployment.md) for full infrastructure deployment.

## Getting Started

### Prerequisites

- AWS CLI v2 with SSO configured
- GitHub account
- AWS account (Account ID: `016164185850`)

### AWS Authentication

```bash
# Login via SSO
aws sso login --profile AdministratorAccess-016164185850

# Verify
aws sts get-caller-identity --profile AdministratorAccess-016164185850
```

### Local Development

1. **Clone repository**:
   ```bash
   git clone https://github.com/formicag/first.git
   cd first
   ```

2. **Make changes** to `website/` or `lambda/`

3. **Deploy**:
   ```bash
   git add .
   git commit -m "Description"
   git push origin main
   ```

4. **Monitor**: Check GitHub Actions for deployment status

## Usage Guide

### Shopping Workflow

**1. Build Your List**:
- Click "Add Item" form
- Enter item name (AI will spell-check, price, and categorize)
- Select user (Luca or Nicole)
- Click "Add Item"

**2. Mark Recurring Items**:
- Click 📌 button on items you always need (e.g., milk, bread)
- Item turns grey with 🔖 bookmark and moves to bottom

**3. While Shopping**:
- Tick ☑ items as you add them to your physical basket
- Items get crossed out and fade

**4. After Shopping**:
- Click "💾 Save My Shop" button
- Ticked items → saved to history & removed from list
- Save for next items → kept at bottom
- Unticked items → kept on list (didn't purchase)

**5. View History**:
- Click "📊 Shopping Dashboard"
- See all previous shops with dates and totals
- Delete old shops if needed

### Configure Store Layout

1. Click "🏪 Store Layout Settings"
2. Drag categories to match your store
3. Position 1 = entrance, 16 = back
4. Click "💾 Save Layout"
5. Shopping list auto-updates to new order

### Customize AI Behavior

1. Click "⚙️ Configure AI Prompt"
2. Add custom instructions
3. Examples:
   - "Always categorize eggs as Dairy & Eggs"
   - "Treat gluten-free bread as Bakery & Bread"
4. Click "💾 Save Instructions"

## Documentation

- **[README.md](README.md)** - This file (main documentation)
- **[CHANGELOG.md](CHANGELOG.md)** - Version history and updates
- **[CI-CD-SETUP.md](CI-CD-SETUP.md)** - GitHub Actions CI/CD setup
- **[DECOMMISSIONING.md](DECOMMISSIONING.md)** - Tear down guide
- **[OPTIMIZATION-OPPORTUNITIES.md](OPTIMIZATION-OPPORTUNITIES.md)** - Future optimizations
- **[cloudformation/README-deployment.md](cloudformation/README-deployment.md)** - Infrastructure deployment
- **[lambda/README.md](lambda/README.md)** - Lambda function details

## Current Status

### ✅ Production Ready
- All features fully functional
- CI/CD pipeline active
- Store layout optimization live
- Shopping workflow complete
- Dashboard analytics working
- AI categorization accurate

### 💰 Costs
- **Current**: ~£2-3/month
- **Breakdown**:
  - DynamoDB: ~£0.50/month (on-demand)
  - Lambda: ~£0.30/month (generous free tier)
  - Bedrock: ~£1-2/month (Claude 3 Haiku)
  - S3/CloudFront: Minimal (~£0.10/month)
  - API Gateway: Free tier covers usage

### 📊 Scale
- **Current**: 2 users (Gianluca & Nicole)
- **Capacity**: Can handle 100+ users without changes
- **Optimization ready**: AI caching and modular prompts available

## Key Technologies

- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **Backend**: Python 3.11, AWS Lambda
- **Database**: DynamoDB (2 tables)
- **API**: API Gateway REST API (12 endpoints)
- **AI/ML**: Amazon Bedrock (Claude 3 Haiku)
- **Email**: Amazon SES
- **Hosting**: S3 + CloudFront
- **CI/CD**: GitHub Actions with OIDC
- **IAC**: CloudFormation (nested stacks)

## Recent Updates

**October 2025** - Major Shopping Workflow Redesign:
- Added "Save for Next Shop" functionality (📌/🔖)
- Implemented realistic shopping workflow (tick → save → clean)
- Store layout optimization with drag-and-drop configuration
- "Save My Shop" only saves ticked items (not everything)
- Automatic item sorting (regular items on top, saved items at bottom)
- Grey-out styling for saved items
- Shopping dashboard with history and analytics
- AI improvements: distinguish canned vs fresh items

See [CHANGELOG.md](CHANGELOG.md) for complete version history.

## License

This is a demonstration project for educational purposes.

## Support

For issues or questions:
- Check documentation in this repo
- Review CloudWatch logs for Lambda errors
- Check GitHub Actions for deployment issues

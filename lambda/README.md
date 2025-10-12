# Shopping List Lambda Functions

Python Lambda functions for the Shopping List application, providing CRUD operations, AI-powered features, and shop history management.

## Functions Overview (12 Total)

### Shopping List Operations

#### 1. createItem.py
Creates a new shopping list item with AI-powered processing via Amazon Bedrock (Claude 3 Haiku).

**AI Processing:**
- Spelling correction and proper capitalization
- UK supermarket aisle categorization (16 categories)
- Sainsbury's UK price estimation (2024-2025 pricing)
- Form-specific categorization (fresh vs canned vs frozen)

**Input:**
```json
{
  "userId": "Gianluca",
  "itemName": "tuna",
  "quantity": 2
}
```

**Output (201):**
```json
{
  "message": "Item created successfully",
  "item": {
    "userId": "Gianluca",
    "itemId": "550e8400-e29b-41d4-a716-446655440006",
    "itemName": "Tuna",
    "quantity": 2,
    "bought": false,
    "saveForNext": false,
    "category": "Canned & Jarred",
    "estimatedPrice": 1.20,
    "addedDate": "2025-10-12T20:30:00Z"
  }
}
```

#### 2. getItems.py
Retrieves shopping list items sorted by store layout (entrance to back of store).

**Features:**
- Automatic store layout sorting using `store_layout.py`
- Optional filtering by `bought` status
- Returns items in optimal shopping order
- Items with `saveForNext=True` maintained in results

**Query Parameters (API Gateway):**
- `userId` (required)
- `bought` (optional): "all", "true", or "false"

**Output (200):**
```json
{
  "userId": "Gianluca",
  "count": 3,
  "items": [
    {
      "userId": "Gianluca",
      "itemId": "550e8400-e29b-41d4-a716-446655440001",
      "itemName": "Milk",
      "quantity": 2,
      "bought": false,
      "saveForNext": false,
      "category": "Dairy & Eggs",
      "estimatedPrice": 1.30,
      "addedDate": "2025-10-12T10:30:00Z"
    }
  ]
}
```

**Dependencies:**
- `store_layout.py` - Store layout sorting module (must be packaged together)

#### 3. updateItem.py
Updates specified fields of an existing item with support for shopping workflow states.

**Supported Fields:**
- `itemName` - Item name
- `quantity` - Quantity
- `category` - Category
- `bought` - Boolean (automatically sets/clears `boughtDate`)
- `saveForNext` - Boolean (save item for next shop)

**Input:**
```json
{
  "userId": "Gianluca",
  "itemId": "550e8400-e29b-41d4-a716-446655440001",
  "bought": true,
  "saveForNext": false
}
```

**Output (200):**
```json
{
  "message": "Item updated successfully",
  "item": {
    "userId": "Gianluca",
    "itemId": "550e8400-e29b-41d4-a716-446655440001",
    "itemName": "Milk",
    "quantity": 2,
    "bought": true,
    "saveForNext": false,
    "category": "Dairy & Eggs",
    "estimatedPrice": 1.30,
    "addedDate": "2025-10-12T10:30:00Z",
    "boughtDate": "2025-10-12T21:00:00Z"
  }
}
```

#### 4. deleteItem.py
Deletes an item from the shopping list.

**Input:**
```json
{
  "userId": "Gianluca",
  "itemId": "550e8400-e29b-41d4-a716-446655440001"
}
```

**Output (200):**
```json
{
  "message": "Item deleted successfully",
  "deletedItem": {
    "userId": "Gianluca",
    "itemId": "550e8400-e29b-41d4-a716-446655440001",
    "itemName": "Milk"
  }
}
```

### Shop History Operations

#### 5. storeShop.py
Stores today's shop to history with NEW realistic shopping workflow.

**New Workflow (October 2025):**
1. Finds all items with `bought=True` (ticked items in basket)
2. Saves ONLY ticked items to shop history
3. DELETES ticked items from shopping list
4. KEEPS items with `saveForNext=True` (saved for next shop)
5. KEEPS items with `bought=False` (items not purchased)

**Input:**
```json
POST /shop/store
{}
```

**Output (201):**
```json
{
  "message": "Shop saved successfully",
  "shop": {
    "shopId": "123e4567-e89b-12d3-a456-426614174000",
    "shopDate": "2025-10-12T20:00:00Z",
    "totalItems": 12,
    "totalPrice": 45.60
  },
  "itemsDeleted": 12,
  "itemsKept": 5
}
```

**Features:**
- One shop per day (overwrites previous shops from same day)
- Only saves ticked items to history
- Prepares list for next shopping trip automatically
- Returns count of deleted and kept items

#### 6. getShopHistory.py
Retrieves historical shop records, sorted by date (latest first).

**Query Parameters:**
- `limit` (optional): Number of shops to return (default: 10)

**Input:**
```json
GET /shop/history?limit=10
```

**Output (200):**
```json
{
  "count": 3,
  "shops": [
    {
      "shopId": "123e4567-e89b-12d3-a456-426614174000",
      "shopDate": "2025-10-12T20:00:00Z",
      "totalItems": 12,
      "totalPrice": 45.60,
      "items": [
        {
          "userId": "Gianluca",
          "itemId": "550e8400-e29b-41d4-a716-446655440001",
          "itemName": "Milk",
          "quantity": 2,
          "estimatedPrice": 1.30,
          "category": "Dairy & Eggs",
          "bought": true
        }
      ]
    }
  ]
}
```

#### 7. deleteShop.py
Deletes a specific shop from history.

**Input:**
```json
DELETE /shop/{shopId}
```

**Output (200):**
```json
{
  "message": "Shop deleted successfully",
  "shopId": "123e4567-e89b-12d3-a456-426614174000"
}
```

### AI & Utility Functions

#### 8. categorizeItems.py
Bulk AI categorization for all items belonging to a user.

**Input:**
```json
POST /categorize/{userId}
```

**Output (200):**
```json
{
  "message": "Categorized 15 items successfully",
  "categorizedCount": 15,
  "items": [...]
}
```

#### 9. emailList.py
Sends shopping list via email using Amazon SES.

**Input:**
```json
POST /email/{userId}
{
  "recipientEmail": "user@example.com"
}
```

**Output (200):**
```json
{
  "message": "Email sent successfully",
  "messageId": "0000015e-abc123..."
}
```

#### 10. improvePrompt.py
AI-powered prompt enrichment for customizable categorization instructions.

**Input:**
```json
POST /improve-prompt
{
  "userInstructions": "Always categorize eggs as Dairy"
}
```

**Output (200):**
```json
{
  "improvedPrompt": "Enhanced prompt with user instructions...",
  "message": "Prompt improved successfully"
}
```

#### 11. recalculatePrices.py
Bulk price recalculation for all items using AI (Sainsbury's UK 2024-2025 pricing).

**Input:**
```json
POST /prices/recalculate
```

**Output (200):**
```json
{
  "message": "Recalculated prices for 25 items",
  "updatedCount": 25,
  "totalEstimatedPrice": 123.45
}
```

### Supporting Modules

#### 12. store_layout.py
Store layout sorting module (not a Lambda function, but a shared module).

**Features:**
- Maps 16 UK supermarket categories to store positions
- Position 1 = entrance, Position 16 = back of store
- Default Sainsbury's layout configuration
- Used by `getItems.py` for automatic sorting

**Category Mapping:**
```python
STORE_LAYOUT = {
    "Health & Beauty": 1,
    "Fresh Produce - Herbs & Salads": 2,
    "Fresh Produce - Fruit": 3,
    "Fresh Produce - Vegetables": 4,
    "Meat & Poultry / Fish & Seafood": 5,
    "Household & Cleaning / Baby & Child": 6,
    "Dairy & Eggs": 8,
    "Beverages": 9,
    "Pantry & Dry Goods": 10,
    "Canned & Jarred": 11,
    "Bakery & Bread": 12,
    "Alcohol & Wine": 13,
    "Snacks & Confectionery": 14,
    "Frozen Foods": 16
}
```

**Note:** Must be packaged with `getItems.py` Lambda function.

## Error Responses

All functions return consistent error responses:

**400 Bad Request:**
```json
{
  "error": "Missing required field: userId"
}
```

**404 Not Found:**
```json
{
  "error": "Item not found"
}
```

**500 Internal Server Error:**
```json
{
  "error": "Internal server error",
  "message": "Error details..."
}
```

## IAM Policy

The `iam-policy.json` file contains the required permissions for all Lambda functions:

- **DynamoDB Permissions:**
  - `PutItem` - Create new items (createItem)
  - `GetItem` - Retrieve specific items (updateItem, deleteItem)
  - `UpdateItem` - Update existing items (updateItem)
  - `DeleteItem` - Delete items (deleteItem)
  - `Query` - Query by partition key (getItems)
  - `Scan` - Full table scan if needed (getItems)

- **CloudWatch Logs Permissions:**
  - Create and write to log groups/streams for monitoring

## Deployment Instructions

### 1. Create IAM Role

```bash
# Create IAM role for Lambda
aws iam create-role \
  --role-name ShoppingListLambdaRole \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "lambda.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }' \
  --profile AdministratorAccess-016164185850

# Attach IAM policy
aws iam put-role-policy \
  --role-name ShoppingListLambdaRole \
  --policy-name ShoppingListDynamoDBPolicy \
  --policy-document file://iam-policy.json \
  --profile AdministratorAccess-016164185850
```

### 2. Package Lambda Functions

Each function needs to be packaged with dependencies:

```bash
# Create deployment package for each function
cd lambda

# For each Lambda function
for func in createItem getItems updateItem deleteItem; do
  zip ${func}.zip ${func}.py
done
```

### 3. Deploy Lambda Functions

```bash
# Get IAM role ARN
ROLE_ARN=$(aws iam get-role --role-name ShoppingListLambdaRole --query 'Role.Arn' --output text --profile AdministratorAccess-016164185850)

# Deploy createItem
aws lambda create-function \
  --function-name ShoppingList-CreateItem \
  --runtime python3.11 \
  --role $ROLE_ARN \
  --handler createItem.lambda_handler \
  --zip-file fileb://createItem.zip \
  --timeout 30 \
  --memory-size 128 \
  --region eu-west-1 \
  --profile AdministratorAccess-016164185850

# Deploy getItems
aws lambda create-function \
  --function-name ShoppingList-GetItems \
  --runtime python3.11 \
  --role $ROLE_ARN \
  --handler getItems.lambda_handler \
  --zip-file fileb://getItems.zip \
  --timeout 30 \
  --memory-size 128 \
  --region eu-west-1 \
  --profile AdministratorAccess-016164185850

# Deploy updateItem
aws lambda create-function \
  --function-name ShoppingList-UpdateItem \
  --runtime python3.11 \
  --role $ROLE_ARN \
  --handler updateItem.lambda_handler \
  --zip-file fileb://updateItem.zip \
  --timeout 30 \
  --memory-size 128 \
  --region eu-west-1 \
  --profile AdministratorAccess-016164185850

# Deploy deleteItem
aws lambda create-function \
  --function-name ShoppingList-DeleteItem \
  --runtime python3.11 \
  --role $ROLE_ARN \
  --handler deleteItem.lambda_handler \
  --zip-file fileb://deleteItem.zip \
  --timeout 30 \
  --memory-size 128 \
  --region eu-west-1 \
  --profile AdministratorAccess-016164185850
```

### 4. Test Lambda Functions

```bash
# Test createItem
aws lambda invoke \
  --function-name ShoppingList-CreateItem \
  --payload '{"userId":"TestUser","itemName":"Test Item","quantity":1,"category":"Test"}' \
  --region eu-west-1 \
  --profile AdministratorAccess-016164185850 \
  response.json

cat response.json
```

## API Gateway Integration (Optional)

To expose these Lambda functions via REST API:

1. Create API Gateway REST API
2. Create resources and methods (POST, GET, PUT, DELETE)
3. Integrate each method with corresponding Lambda function
4. Deploy API to stage
5. Enable CORS if needed for web applications

## Monitoring

View Lambda logs in CloudWatch:

```bash
aws logs tail /aws/lambda/ShoppingList-CreateItem --follow --region eu-west-1 --profile AdministratorAccess-016164185850
```

## Features

- **Input Validation:** All functions validate required fields and data types
- **Error Handling:** Comprehensive error handling with appropriate HTTP status codes
- **Logging:** Structured logging for debugging and monitoring
- **CORS Support:** Headers included for cross-origin requests
- **Atomic Operations:** Uses DynamoDB's atomic operations for data consistency
- **Timestamp Management:** Automatic timestamp generation for addedDate and boughtDate
- **UUID Generation:** Auto-generated unique identifiers for items

## DynamoDB Table Schema

### ShoppingList (Active Shopping Items)
**Table:** ShoppingList
**Region:** eu-west-1
**Partition Key:** userId (String)
**Sort Key:** itemId (String)

**Attributes:**
- `itemName` (String) - Item name (AI processed)
- `quantity` (Number) - Quantity
- `bought` (Boolean) - Ticked in basket
- `saveForNext` (Boolean) - Save for next shop
- `category` (String) - UK supermarket aisle
- `estimatedPrice` (Decimal) - Sainsbury's price estimate
- `addedDate` (String, ISO timestamp)
- `boughtDate` (String, ISO timestamp or null)

### ShoppingList-ShopHistory-Dev (Shop History)
**Table:** ShoppingList-ShopHistory-Dev
**Region:** eu-west-1
**Partition Key:** shopId (String - UUID)
**Sort Key:** shopDate (String - ISO timestamp)

**Attributes:**
- `totalItems` (Number) - Number of items purchased
- `totalPrice` (Decimal) - Total price of shop
- `items` (List) - Array of purchased items with full details

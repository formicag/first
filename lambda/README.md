# Shopping List Lambda Functions

Python Lambda functions for CRUD operations on the ShoppingList DynamoDB table.

## Functions Overview

### 1. createItem.py
Creates a new shopping list item with auto-generated UUID and timestamp.

**Input:**
```json
{
  "userId": "Gianluca",
  "itemName": "Eggs",
  "quantity": 12,
  "category": "Dairy"
}
```

**Output (201):**
```json
{
  "message": "Item created successfully",
  "item": {
    "userId": "Gianluca",
    "itemId": "550e8400-e29b-41d4-a716-446655440006",
    "itemName": "Eggs",
    "quantity": 12,
    "bought": false,
    "category": "Dairy",
    "addedDate": "2025-10-01T20:30:00Z"
  }
}
```

### 2. getItems.py
Retrieves shopping list items for a user with optional filtering.

**Input:**
```json
{
  "userId": "Gianluca",
  "boughtFilter": "false"
}
```

**Query Parameters (API Gateway):**
- `userId` (required)
- `boughtFilter` (optional): "all", "true", or "false"

**Output (200):**
```json
{
  "userId": "Gianluca",
  "count": 2,
  "items": [
    {
      "userId": "Gianluca",
      "itemId": "550e8400-e29b-41d4-a716-446655440001",
      "itemName": "Milk",
      "quantity": 2,
      "bought": false,
      "category": "Dairy",
      "addedDate": "2025-10-01T10:30:00Z"
    }
  ]
}
```

### 3. updateItem.py
Updates specified fields of an existing item. Automatically sets `boughtDate` when `bought` is set to true.

**Input:**
```json
{
  "userId": "Gianluca",
  "itemId": "550e8400-e29b-41d4-a716-446655440001",
  "bought": true,
  "quantity": 3
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
    "quantity": 3,
    "bought": true,
    "category": "Dairy",
    "addedDate": "2025-10-01T10:30:00Z",
    "boughtDate": "2025-10-01T21:00:00Z"
  }
}
```

### 4. deleteItem.py
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

**Table:** ShoppingList
**Region:** eu-west-1
**Partition Key:** userId (String)
**Sort Key:** itemId (String)

**Attributes:**
- itemName (String)
- quantity (Number)
- bought (Boolean)
- category (String, optional)
- addedDate (String, ISO timestamp)
- boughtDate (String, ISO timestamp or null)

#!/bin/bash

# Deploy DeleteShop Lambda function and API Gateway endpoint
# Run this script after refreshing AWS SSO credentials

set -e

REGION="eu-west-1"
PROFILE="AdministratorAccess-016164185850"
FUNCTION_NAME="ShoppingList-DeleteShop"
API_ID="01mmfw29n0"
ROLE_ARN="arn:aws:iam::016164185850:role/ShoppingListLambdaRole"

echo "📦 Creating Lambda function deployment package..."
cd lambda
zip -j /tmp/deleteShop.zip deleteShop.py
cd ..

echo "🔨 Creating Lambda function: ${FUNCTION_NAME}..."
aws lambda create-function \
  --function-name "${FUNCTION_NAME}" \
  --runtime python3.11 \
  --handler deleteShop.lambda_handler \
  --role "${ROLE_ARN}" \
  --zip-file fileb:///tmp/deleteShop.zip \
  --timeout 60 \
  --memory-size 256 \
  --environment "Variables={SHOP_HISTORY_TABLE=ShoppingList-ShopHistory-Dev}" \
  --region "${REGION}" \
  --profile "${PROFILE}" \
  --tags "Project=ShoppingList,Environment=Dev,ManagedBy=CloudFormation"

echo "✅ Lambda function created successfully!"

# Get Lambda function ARN
LAMBDA_ARN=$(aws lambda get-function \
  --function-name "${FUNCTION_NAME}" \
  --region "${REGION}" \
  --profile "${PROFILE}" \
  --query 'Configuration.FunctionArn' \
  --output text)

echo "Lambda ARN: ${LAMBDA_ARN}"

echo ""
echo "🌐 Creating API Gateway resources and methods..."

# Get /shop resource ID
SHOP_RESOURCE_ID=$(aws apigateway get-resources \
  --rest-api-id "${API_ID}" \
  --region "${REGION}" \
  --profile "${PROFILE}" \
  --query "items[?path=='/shop'].id" \
  --output text)

echo "Shop resource ID: ${SHOP_RESOURCE_ID}"

# Create /shop/{shopId} resource
SHOPID_RESOURCE_ID=$(aws apigateway create-resource \
  --rest-api-id "${API_ID}" \
  --parent-id "${SHOP_RESOURCE_ID}" \
  --path-part "{shopId}" \
  --region "${REGION}" \
  --profile "${PROFILE}" \
  --query 'id' \
  --output text)

echo "ShopId resource ID: ${SHOPID_RESOURCE_ID}"

# Create DELETE method
echo "Creating DELETE method on /shop/{shopId}..."
aws apigateway put-method \
  --rest-api-id "${API_ID}" \
  --resource-id "${SHOPID_RESOURCE_ID}" \
  --http-method DELETE \
  --authorization-type NONE \
  --region "${REGION}" \
  --profile "${PROFILE}"

# Create integration
echo "Creating Lambda integration..."
aws apigateway put-integration \
  --rest-api-id "${API_ID}" \
  --resource-id "${SHOPID_RESOURCE_ID}" \
  --http-method DELETE \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri "arn:aws:apigateway:${REGION}:lambda:path/2015-03-31/functions/${LAMBDA_ARN}/invocations" \
  --region "${REGION}" \
  --profile "${PROFILE}"

# Add Lambda permission for API Gateway
echo "Adding Lambda permission for API Gateway..."
aws lambda add-permission \
  --function-name "${FUNCTION_NAME}" \
  --statement-id apigateway-delete-shop \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:${REGION}:016164185850:${API_ID}/*/*" \
  --region "${REGION}" \
  --profile "${PROFILE}"

# Deploy API
echo "Deploying API to 'dev' stage..."
aws apigateway create-deployment \
  --rest-api-id "${API_ID}" \
  --stage-name dev \
  --description "Added DELETE /shop/{shopId} endpoint" \
  --region "${REGION}" \
  --profile "${PROFILE}"

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🎉 API endpoint is now available at:"
echo "DELETE https://${API_ID}.execute-api.${REGION}.amazonaws.com/dev/shop/{shopId}"
echo ""
echo "Test it with:"
echo "curl -X DELETE https://${API_ID}.execute-api.${REGION}.amazonaws.com/dev/shop/YOUR_SHOP_ID"

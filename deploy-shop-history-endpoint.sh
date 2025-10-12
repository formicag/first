#!/bin/bash

# Deploy GetShopHistory Lambda function and API Gateway endpoint
# Run this script after refreshing AWS SSO credentials

set -e

REGION="eu-west-1"
PROFILE="AdministratorAccess-016164185850"
FUNCTION_NAME="ShoppingList-GetShopHistory"
API_ID="01mmfw29n0"
ROLE_ARN="arn:aws:iam::016164185850:role/ShoppingList-Dev-LambdaRole"

echo "📦 Creating Lambda function deployment package..."
cd lambda
zip -j /tmp/getShopHistory.zip getShopHistory.py
cd ..

echo "🔨 Creating Lambda function: ${FUNCTION_NAME}..."
aws lambda create-function \
  --function-name "${FUNCTION_NAME}" \
  --runtime python3.11 \
  --handler getShopHistory.lambda_handler \
  --role "${ROLE_ARN}" \
  --zip-file fileb:///tmp/getShopHistory.zip \
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

# Create /shop/history resource
echo "Creating /shop/history resource..."

# Get /shop resource ID
SHOP_RESOURCE_ID=$(aws apigateway get-resources \
  --rest-api-id "${API_ID}" \
  --region "${REGION}" \
  --profile "${PROFILE}" \
  --query "items[?path=='/shop'].id" \
  --output text)

echo "Shop resource ID: ${SHOP_RESOURCE_ID}"

# Create /shop/history resource
HISTORY_RESOURCE_ID=$(aws apigateway create-resource \
  --rest-api-id "${API_ID}" \
  --parent-id "${SHOP_RESOURCE_ID}" \
  --path-part "history" \
  --region "${REGION}" \
  --profile "${PROFILE}" \
  --query 'id' \
  --output text)

echo "History resource ID: ${HISTORY_RESOURCE_ID}"

# Create GET method
echo "Creating GET method on /shop/history..."
aws apigateway put-method \
  --rest-api-id "${API_ID}" \
  --resource-id "${HISTORY_RESOURCE_ID}" \
  --http-method GET \
  --authorization-type NONE \
  --request-parameters "method.request.querystring.limit=false" \
  --region "${REGION}" \
  --profile "${PROFILE}"

# Create integration
echo "Creating Lambda integration..."
aws apigateway put-integration \
  --rest-api-id "${API_ID}" \
  --resource-id "${HISTORY_RESOURCE_ID}" \
  --http-method GET \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri "arn:aws:apigateway:${REGION}:lambda:path/2015-03-31/functions/${LAMBDA_ARN}/invocations" \
  --region "${REGION}" \
  --profile "${PROFILE}"

# Add Lambda permission for API Gateway
echo "Adding Lambda permission for API Gateway..."
aws lambda add-permission \
  --function-name "${FUNCTION_NAME}" \
  --statement-id apigateway-get-shop-history \
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
  --description "Added GET /shop/history endpoint" \
  --region "${REGION}" \
  --profile "${PROFILE}"

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🎉 API endpoint is now available at:"
echo "https://${API_ID}.execute-api.${REGION}.amazonaws.com/dev/shop/history"
echo ""
echo "Test it with:"
echo "curl https://${API_ID}.execute-api.${REGION}.amazonaws.com/dev/shop/history?limit=10"

#!/bin/bash

# Deploy RecategorizeAllItems Lambda function and API Gateway endpoint
# Run this script after refreshing AWS SSO credentials

set -e

REGION="eu-west-1"
PROFILE="AdministratorAccess-016164185850"
FUNCTION_NAME="ShoppingList-RecategorizeAllItems"
API_ID="01mmfw29n0"
ROLE_ARN="arn:aws:iam::016164185850:role/ShoppingListLambdaRole"

echo "📦 Creating Lambda function deployment package..."
cd lambda
zip -j /tmp/recategorizeAllItems.zip recategorizeAllItems.py
cd ..

echo "🔨 Creating Lambda function: ${FUNCTION_NAME}..."
aws lambda create-function \
  --function-name "${FUNCTION_NAME}" \
  --runtime python3.11 \
  --handler recategorizeAllItems.lambda_handler \
  --role "${ROLE_ARN}" \
  --zip-file fileb:///tmp/recategorizeAllItems.zip \
  --timeout 120 \
  --memory-size 512 \
  --environment "Variables={DYNAMODB_TABLE=ShoppingList}" \
  --region "${REGION}" \
  --profile "${PROFILE}" \
  --tags "Project=ShoppingList,Environment=Dev,ManagedBy=Manual"

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

# Get /categorize resource ID
echo "Getting /categorize resource..."
CATEGORIZE_RESOURCE_ID=$(aws apigateway get-resources \
  --rest-api-id "${API_ID}" \
  --region "${REGION}" \
  --profile "${PROFILE}" \
  --query "items[?path=='/categorize'].id" \
  --output text)

echo "Categorize resource ID: ${CATEGORIZE_RESOURCE_ID}"

# Create /categorize/recalculate resource
echo "Creating /categorize/recalculate resource..."
RECALCULATE_RESOURCE_ID=$(aws apigateway create-resource \
  --rest-api-id "${API_ID}" \
  --parent-id "${CATEGORIZE_RESOURCE_ID}" \
  --path-part "recalculate" \
  --region "${REGION}" \
  --profile "${PROFILE}" \
  --query 'id' \
  --output text)

echo "Recalculate resource ID: ${RECALCULATE_RESOURCE_ID}"

# Create POST method
echo "Creating POST method on /categorize/recalculate..."
aws apigateway put-method \
  --rest-api-id "${API_ID}" \
  --resource-id "${RECALCULATE_RESOURCE_ID}" \
  --http-method POST \
  --authorization-type NONE \
  --region "${REGION}" \
  --profile "${PROFILE}"

# Create integration
echo "Creating Lambda integration..."
aws apigateway put-integration \
  --rest-api-id "${API_ID}" \
  --resource-id "${RECALCULATE_RESOURCE_ID}" \
  --http-method POST \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri "arn:aws:apigateway:${REGION}:lambda:path/2015-03-31/functions/${LAMBDA_ARN}/invocations" \
  --region "${REGION}" \
  --profile "${PROFILE}"

# Enable CORS
echo "Enabling CORS..."
aws apigateway put-method \
  --rest-api-id "${API_ID}" \
  --resource-id "${RECALCULATE_RESOURCE_ID}" \
  --http-method OPTIONS \
  --authorization-type NONE \
  --region "${REGION}" \
  --profile "${PROFILE}"

aws apigateway put-integration \
  --rest-api-id "${API_ID}" \
  --resource-id "${RECALCULATE_RESOURCE_ID}" \
  --http-method OPTIONS \
  --type MOCK \
  --request-templates '{"application/json": "{\"statusCode\": 200}"}' \
  --region "${REGION}" \
  --profile "${PROFILE}"

aws apigateway put-integration-response \
  --rest-api-id "${API_ID}" \
  --resource-id "${RECALCULATE_RESOURCE_ID}" \
  --http-method OPTIONS \
  --status-code 200 \
  --response-parameters '{"method.response.header.Access-Control-Allow-Headers": "'"'"'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"'"'","method.response.header.Access-Control-Allow-Methods": "'"'"'POST,OPTIONS'"'"'","method.response.header.Access-Control-Allow-Origin": "'"'"'*'"'"'"}' \
  --region "${REGION}" \
  --profile "${PROFILE}"

aws apigateway put-method-response \
  --rest-api-id "${API_ID}" \
  --resource-id "${RECALCULATE_RESOURCE_ID}" \
  --http-method OPTIONS \
  --status-code 200 \
  --response-parameters '{"method.response.header.Access-Control-Allow-Headers": true,"method.response.header.Access-Control-Allow-Methods": true,"method.response.header.Access-Control-Allow-Origin": true}' \
  --region "${REGION}" \
  --profile "${PROFILE}"

# Add Lambda permission for API Gateway
echo "Adding Lambda permission for API Gateway..."
aws lambda add-permission \
  --function-name "${FUNCTION_NAME}" \
  --statement-id apigateway-recategorize-all \
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
  --description "Added POST /categorize/recalculate endpoint" \
  --region "${REGION}" \
  --profile "${PROFILE}"

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🎉 API endpoint is now available at:"
echo "https://${API_ID}.execute-api.${REGION}.amazonaws.com/dev/categorize/recalculate"
echo ""
echo "Test it with:"
echo "curl -X POST https://${API_ID}.execute-api.${REGION}.amazonaws.com/dev/categorize/recalculate"

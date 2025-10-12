#!/bin/bash

# Fix CORS for DELETE /shop/{shopId} endpoint
# This adds the OPTIONS method for CORS preflight requests

REGION="eu-west-1"
PROFILE="AdministratorAccess-016164185850"
API_ID="01mmfw29n0"

echo "Finding /shop/{shopId} resource..."
SHOPID_RESOURCE_ID=$(aws apigateway get-resources \
  --rest-api-id "${API_ID}" \
  --region "${REGION}" \
  --profile "${PROFILE}" \
  --query "items[?pathPart=='{shopId}' && parentId!=''].id" \
  --output text)

echo "ShopId resource ID: ${SHOPID_RESOURCE_ID}"

echo "Adding OPTIONS method for CORS..."
aws apigateway put-method \
  --rest-api-id "${API_ID}" \
  --resource-id "${SHOPID_RESOURCE_ID}" \
  --http-method OPTIONS \
  --authorization-type NONE \
  --region "${REGION}" \
  --profile "${PROFILE}"

echo "Adding MOCK integration..."
aws apigateway put-integration \
  --rest-api-id "${API_ID}" \
  --resource-id "${SHOPID_RESOURCE_ID}" \
  --http-method OPTIONS \
  --type MOCK \
  --request-templates '{"application/json": "{\"statusCode\": 200}"}' \
  --region "${REGION}" \
  --profile "${PROFILE}"

echo "Adding method response..."
aws apigateway put-method-response \
  --rest-api-id "${API_ID}" \
  --resource-id "${SHOPID_RESOURCE_ID}" \
  --http-method OPTIONS \
  --status-code 200 \
  --response-parameters '{"method.response.header.Access-Control-Allow-Headers":false,"method.response.header.Access-Control-Allow-Methods":false,"method.response.header.Access-Control-Allow-Origin":false}' \
  --region "${REGION}" \
  --profile "${PROFILE}"

echo "Adding integration response with CORS headers..."
aws apigateway put-integration-response \
  --rest-api-id "${API_ID}" \
  --resource-id "${SHOPID_RESOURCE_ID}" \
  --http-method OPTIONS \
  --status-code 200 \
  --response-parameters '{"method.response.header.Access-Control-Allow-Headers":"'"'"'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"'"'","method.response.header.Access-Control-Allow-Methods":"'"'"'DELETE,OPTIONS'"'"'","method.response.header.Access-Control-Allow-Origin":"'"'"'*'"'"'"}' \
  --region "${REGION}" \
  --profile "${PROFILE}"

echo "Deploying API..."
aws apigateway create-deployment \
  --rest-api-id "${API_ID}" \
  --stage-name dev \
  --description "Added CORS OPTIONS for DELETE /shop/{shopId}" \
  --region "${REGION}" \
  --profile "${PROFILE}"

echo "✅ CORS fix applied successfully!"
echo "The delete button should now work in the browser."

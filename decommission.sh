#!/bin/bash

################################################################################
# Shopping List Application - AWS Resource Decommissioning Script
################################################################################
#
# This script safely removes ALL AWS resources for the Shopping List application.
#
# USAGE:
#   ./decommission.sh --profile AdministratorAccess-016164185850 [--confirm]
#
# OPTIONS:
#   --profile PROFILE_NAME    AWS CLI profile to use (required)
#   --confirm                 Skip confirmation prompt (dangerous!)
#   --dry-run                 Show what would be deleted without deleting
#
# WHAT THIS SCRIPT DELETES:
#   - CloudFront Distribution (E2G8S9GOXLBFEZ)
#   - S3 Bucket and all contents (shoppinglist.gianlucaformica.net)
#   - API Gateway (01mmfw29n0)
#   - Lambda Functions (6 total)
#   - DynamoDB Table (ShoppingList)
#   - Cognito User Pool (eu-west-1_IennWZZNL)
#   - IAM Role (GitHubActionsDeployRole)
#   - CloudWatch Log Groups
#   - GitHub OIDC Provider (if no other roles use it)
#
# WARNING: This action is IRREVERSIBLE. All data will be permanently deleted.
#
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REGION="eu-west-1"
PROFILE=""
CONFIRM=false
DRY_RUN=false

# Resource identifiers
CLOUDFRONT_DISTRIBUTION_ID="E2G8S9GOXLBFEZ"
S3_BUCKET="shoppinglist.gianlucaformica.net"
API_GATEWAY_ID="01mmfw29n0"
DYNAMODB_TABLE="ShoppingList"
COGNITO_USER_POOL_ID="eu-west-1_IennWZZNL"
IAM_ROLE_NAME="GitHubActionsDeployRole"
GITHUB_OIDC_PROVIDER="arn:aws:iam::016164185850:oidc-provider/token.actions.githubusercontent.com"

# Lambda function names
LAMBDA_FUNCTIONS=(
    "ShoppingList-CreateItem"
    "ShoppingList-GetItems"
    "ShoppingList-UpdateItem"
    "ShoppingList-DeleteItem"
    "ShoppingList-EmailList"
    "ShoppingList-CategorizeItems"
)

################################################################################
# Helper Functions
################################################################################

print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --profile)
                PROFILE="$2"
                shift 2
                ;;
            --confirm)
                CONFIRM=true
                shift
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --help)
                head -n 30 "$0" | grep "^#" | sed 's/^# \?//'
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done

    if [ -z "$PROFILE" ]; then
        print_error "AWS profile is required. Use --profile option."
        exit 1
    fi
}

# Confirm deletion
confirm_deletion() {
    if [ "$CONFIRM" = true ]; then
        return 0
    fi

    print_header "⚠️  WARNING: DESTRUCTIVE OPERATION  ⚠️"

    echo -e "${RED}This script will PERMANENTLY DELETE the following AWS resources:${NC}\n"
    echo "  • CloudFront Distribution: $CLOUDFRONT_DISTRIBUTION_ID"
    echo "  • S3 Bucket: $S3_BUCKET (and ALL contents)"
    echo "  • API Gateway: $API_GATEWAY_ID"
    echo "  • DynamoDB Table: $DYNAMODB_TABLE (and ALL data)"
    echo "  • Cognito User Pool: $COGNITO_USER_POOL_ID"
    echo "  • 6 Lambda Functions"
    echo "  • IAM Role: $IAM_ROLE_NAME"
    echo "  • All CloudWatch Log Groups"
    echo "  • GitHub OIDC Provider (if not used elsewhere)"
    echo ""
    echo -e "${RED}THIS ACTION CANNOT BE UNDONE!${NC}\n"

    read -p "Type 'DELETE' to confirm: " confirmation

    if [ "$confirmation" != "DELETE" ]; then
        print_warning "Decommissioning cancelled."
        exit 0
    fi

    echo ""
    read -p "Are you absolutely sure? Type 'YES' to proceed: " final_confirmation

    if [ "$final_confirmation" != "YES" ]; then
        print_warning "Decommissioning cancelled."
        exit 0
    fi
}

# Execute AWS command
aws_cmd() {
    if [ "$DRY_RUN" = true ]; then
        echo "[DRY RUN] Would execute: aws $@"
        return 0
    else
        aws "$@" --profile "$PROFILE" --region "$REGION" 2>&1
    fi
}

################################################################################
# Deletion Functions
################################################################################

# 1. Disable and delete CloudFront distribution
delete_cloudfront() {
    print_header "1. CloudFront Distribution"

    print_info "Checking CloudFront distribution status..."

    if [ "$DRY_RUN" = false ]; then
        DISTRIBUTION_CONFIG=$(aws cloudfront get-distribution-config \
            --id "$CLOUDFRONT_DISTRIBUTION_ID" \
            --profile "$PROFILE" 2>&1 || echo "NOT_FOUND")

        if [[ "$DISTRIBUTION_CONFIG" == *"NOT_FOUND"* ]] || [[ "$DISTRIBUTION_CONFIG" == *"NoSuchDistribution"* ]]; then
            print_warning "CloudFront distribution not found (may already be deleted)"
            return 0
        fi

        # Extract ETag and current config
        ETAG=$(echo "$DISTRIBUTION_CONFIG" | jq -r '.ETag')

        # Check current status
        STATUS=$(echo "$DISTRIBUTION_CONFIG" | jq -r '.DistributionConfig.Enabled')

        if [ "$STATUS" = "true" ]; then
            print_info "Disabling CloudFront distribution..."

            # Disable distribution
            echo "$DISTRIBUTION_CONFIG" | jq '.DistributionConfig.Enabled = false | .DistributionConfig' > /tmp/cf-config.json

            aws cloudfront update-distribution \
                --id "$CLOUDFRONT_DISTRIBUTION_ID" \
                --if-match "$ETAG" \
                --distribution-config file:///tmp/cf-config.json \
                --profile "$PROFILE" > /dev/null

            print_info "Waiting for CloudFront distribution to be disabled (this may take 15-20 minutes)..."

            aws cloudfront wait distribution-deployed \
                --id "$CLOUDFRONT_DISTRIBUTION_ID" \
                --profile "$PROFILE"

            print_success "CloudFront distribution disabled"

            # Get new ETag after update
            sleep 5
            NEW_CONFIG=$(aws cloudfront get-distribution-config \
                --id "$CLOUDFRONT_DISTRIBUTION_ID" \
                --profile "$PROFILE")
            ETAG=$(echo "$NEW_CONFIG" | jq -r '.ETag')
        fi

        print_info "Deleting CloudFront distribution..."
        aws cloudfront delete-distribution \
            --id "$CLOUDFRONT_DISTRIBUTION_ID" \
            --if-match "$ETAG" \
            --profile "$PROFILE" > /dev/null

        print_success "CloudFront distribution deleted"
    else
        print_info "[DRY RUN] Would disable and delete CloudFront distribution: $CLOUDFRONT_DISTRIBUTION_ID"
    fi
}

# 2. Empty and delete S3 bucket
delete_s3_bucket() {
    print_header "2. S3 Bucket"

    print_info "Emptying S3 bucket: $S3_BUCKET"

    if [ "$DRY_RUN" = false ]; then
        # Check if bucket exists
        if aws s3 ls "s3://$S3_BUCKET" --profile "$PROFILE" --region "$REGION" 2>&1 | grep -q "NoSuchBucket"; then
            print_warning "S3 bucket not found (may already be deleted)"
            return 0
        fi

        # Delete all objects and versions
        aws s3 rm "s3://$S3_BUCKET" --recursive --profile "$PROFILE" --region "$REGION"

        print_info "Deleting S3 bucket..."
        aws s3 rb "s3://$S3_BUCKET" --profile "$PROFILE" --region "$REGION"

        print_success "S3 bucket deleted"
    else
        print_info "[DRY RUN] Would empty and delete S3 bucket: $S3_BUCKET"
    fi
}

# 3. Delete API Gateway
delete_api_gateway() {
    print_header "3. API Gateway"

    print_info "Deleting API Gateway: $API_GATEWAY_ID"

    if [ "$DRY_RUN" = false ]; then
        RESULT=$(aws apigateway delete-rest-api \
            --rest-api-id "$API_GATEWAY_ID" \
            --profile "$PROFILE" \
            --region "$REGION" 2>&1 || echo "NOT_FOUND")

        if [[ "$RESULT" == *"NotFoundException"* ]]; then
            print_warning "API Gateway not found (may already be deleted)"
        else
            print_success "API Gateway deleted"
        fi
    else
        print_info "[DRY RUN] Would delete API Gateway: $API_GATEWAY_ID"
    fi
}

# 4. Delete Lambda functions and log groups
delete_lambda_functions() {
    print_header "4. Lambda Functions"

    for func in "${LAMBDA_FUNCTIONS[@]}"; do
        print_info "Deleting Lambda function: $func"

        if [ "$DRY_RUN" = false ]; then
            RESULT=$(aws lambda delete-function \
                --function-name "$func" \
                --profile "$PROFILE" \
                --region "$REGION" 2>&1 || echo "NOT_FOUND")

            if [[ "$RESULT" == *"ResourceNotFoundException"* ]]; then
                print_warning "  Lambda function not found: $func"
            else
                print_success "  Deleted Lambda function: $func"
            fi

            # Delete CloudWatch log group
            LOG_GROUP="/aws/lambda/$func"
            print_info "  Deleting log group: $LOG_GROUP"

            RESULT=$(aws logs delete-log-group \
                --log-group-name "$LOG_GROUP" \
                --profile "$PROFILE" \
                --region "$REGION" 2>&1 || echo "NOT_FOUND")

            if [[ "$RESULT" == *"ResourceNotFoundException"* ]]; then
                print_warning "    Log group not found: $LOG_GROUP"
            else
                print_success "    Deleted log group: $LOG_GROUP"
            fi
        else
            print_info "[DRY RUN] Would delete Lambda function and logs: $func"
        fi
    done
}

# 5. Delete DynamoDB table
delete_dynamodb_table() {
    print_header "5. DynamoDB Table"

    print_info "Deleting DynamoDB table: $DYNAMODB_TABLE"

    if [ "$DRY_RUN" = false ]; then
        RESULT=$(aws dynamodb delete-table \
            --table-name "$DYNAMODB_TABLE" \
            --profile "$PROFILE" \
            --region "$REGION" 2>&1 || echo "NOT_FOUND")

        if [[ "$RESULT" == *"ResourceNotFoundException"* ]]; then
            print_warning "DynamoDB table not found (may already be deleted)"
        else
            print_info "Waiting for DynamoDB table deletion..."
            aws dynamodb wait table-not-exists \
                --table-name "$DYNAMODB_TABLE" \
                --profile "$PROFILE" \
                --region "$REGION"
            print_success "DynamoDB table deleted"
        fi
    else
        print_info "[DRY RUN] Would delete DynamoDB table: $DYNAMODB_TABLE"
    fi
}

# 6. Delete Cognito User Pool
delete_cognito_user_pool() {
    print_header "6. Cognito User Pool"

    print_info "Deleting Cognito User Pool: $COGNITO_USER_POOL_ID"

    if [ "$DRY_RUN" = false ]; then
        RESULT=$(aws cognito-idp delete-user-pool \
            --user-pool-id "$COGNITO_USER_POOL_ID" \
            --profile "$PROFILE" \
            --region "$REGION" 2>&1 || echo "NOT_FOUND")

        if [[ "$RESULT" == *"ResourceNotFoundException"* ]]; then
            print_warning "Cognito User Pool not found (may already be deleted)"
        else
            print_success "Cognito User Pool deleted"
        fi
    else
        print_info "[DRY RUN] Would delete Cognito User Pool: $COGNITO_USER_POOL_ID"
    fi
}

# 7. Delete IAM Role
delete_iam_role() {
    print_header "7. IAM Role (GitHub Actions)"

    print_info "Deleting IAM role: $IAM_ROLE_NAME"

    if [ "$DRY_RUN" = false ]; then
        # First, delete all inline policies
        POLICIES=$(aws iam list-role-policies \
            --role-name "$IAM_ROLE_NAME" \
            --profile "$PROFILE" 2>&1 || echo "NOT_FOUND")

        if [[ "$POLICIES" == *"NoSuchEntity"* ]]; then
            print_warning "IAM role not found (may already be deleted)"
            return 0
        fi

        echo "$POLICIES" | jq -r '.PolicyNames[]' | while read -r policy; do
            if [ -n "$policy" ]; then
                print_info "  Deleting inline policy: $policy"
                aws iam delete-role-policy \
                    --role-name "$IAM_ROLE_NAME" \
                    --policy-name "$policy" \
                    --profile "$PROFILE"
            fi
        done

        # Detach managed policies
        MANAGED_POLICIES=$(aws iam list-attached-role-policies \
            --role-name "$IAM_ROLE_NAME" \
            --profile "$PROFILE" 2>&1)

        echo "$MANAGED_POLICIES" | jq -r '.AttachedPolicies[].PolicyArn' | while read -r policy_arn; do
            if [ -n "$policy_arn" ]; then
                print_info "  Detaching managed policy: $policy_arn"
                aws iam detach-role-policy \
                    --role-name "$IAM_ROLE_NAME" \
                    --policy-arn "$policy_arn" \
                    --profile "$PROFILE"
            fi
        done

        # Delete the role
        aws iam delete-role \
            --role-name "$IAM_ROLE_NAME" \
            --profile "$PROFILE"

        print_success "IAM role deleted"
    else
        print_info "[DRY RUN] Would delete IAM role: $IAM_ROLE_NAME"
    fi
}

# 8. Check and optionally delete OIDC Provider
delete_oidc_provider() {
    print_header "8. GitHub OIDC Provider"

    print_info "Checking if OIDC provider is used by other roles..."

    if [ "$DRY_RUN" = false ]; then
        # Check if provider exists
        PROVIDER_EXISTS=$(aws iam get-open-id-connect-provider \
            --open-id-connect-provider-arn "$GITHUB_OIDC_PROVIDER" \
            --profile "$PROFILE" 2>&1 || echo "NOT_FOUND")

        if [[ "$PROVIDER_EXISTS" == *"NoSuchEntity"* ]]; then
            print_warning "OIDC provider not found (may already be deleted)"
            return 0
        fi

        # List all roles and check if any use this OIDC provider
        ROLES_USING_OIDC=$(aws iam list-roles --profile "$PROFILE" --output json | \
            jq -r --arg provider "$GITHUB_OIDC_PROVIDER" \
            '.Roles[] | select(.AssumeRolePolicyDocument | tostring | contains($provider)) | .RoleName')

        if [ -z "$ROLES_USING_OIDC" ]; then
            print_info "No other roles use this OIDC provider. Deleting..."
            aws iam delete-open-id-connect-provider \
                --open-id-connect-provider-arn "$GITHUB_OIDC_PROVIDER" \
                --profile "$PROFILE"
            print_success "OIDC provider deleted"
        else
            print_warning "OIDC provider is used by other roles. Skipping deletion."
            print_info "Roles using this provider:"
            echo "$ROLES_USING_OIDC" | while read -r role; do
                echo "    - $role"
            done
        fi
    else
        print_info "[DRY RUN] Would check and potentially delete OIDC provider"
    fi
}

# 9. Verify all resources are deleted
verify_deletion() {
    print_header "9. Verification"

    print_info "Verifying all resources are deleted...\n"

    ERRORS=0

    # Check CloudFront
    if [ "$DRY_RUN" = false ]; then
        if aws cloudfront get-distribution --id "$CLOUDFRONT_DISTRIBUTION_ID" --profile "$PROFILE" 2>&1 | grep -q "NoSuchDistribution"; then
            print_success "CloudFront: Deleted"
        else
            print_error "CloudFront: Still exists"
            ((ERRORS++))
        fi
    fi

    # Check S3
    if [ "$DRY_RUN" = false ]; then
        if aws s3 ls "s3://$S3_BUCKET" --profile "$PROFILE" --region "$REGION" 2>&1 | grep -q "NoSuchBucket"; then
            print_success "S3 Bucket: Deleted"
        else
            print_error "S3 Bucket: Still exists"
            ((ERRORS++))
        fi
    fi

    # Check API Gateway
    if [ "$DRY_RUN" = false ]; then
        if aws apigateway get-rest-api --rest-api-id "$API_GATEWAY_ID" --profile "$PROFILE" --region "$REGION" 2>&1 | grep -q "NotFoundException"; then
            print_success "API Gateway: Deleted"
        else
            print_error "API Gateway: Still exists"
            ((ERRORS++))
        fi
    fi

    # Check Lambda functions
    for func in "${LAMBDA_FUNCTIONS[@]}"; do
        if [ "$DRY_RUN" = false ]; then
            if aws lambda get-function --function-name "$func" --profile "$PROFILE" --region "$REGION" 2>&1 | grep -q "ResourceNotFoundException"; then
                print_success "Lambda ($func): Deleted"
            else
                print_error "Lambda ($func): Still exists"
                ((ERRORS++))
            fi
        fi
    done

    # Check DynamoDB
    if [ "$DRY_RUN" = false ]; then
        if aws dynamodb describe-table --table-name "$DYNAMODB_TABLE" --profile "$PROFILE" --region "$REGION" 2>&1 | grep -q "ResourceNotFoundException"; then
            print_success "DynamoDB Table: Deleted"
        else
            print_error "DynamoDB Table: Still exists"
            ((ERRORS++))
        fi
    fi

    # Check Cognito
    if [ "$DRY_RUN" = false ]; then
        if aws cognito-idp describe-user-pool --user-pool-id "$COGNITO_USER_POOL_ID" --profile "$PROFILE" --region "$REGION" 2>&1 | grep -q "ResourceNotFoundException"; then
            print_success "Cognito User Pool: Deleted"
        else
            print_error "Cognito User Pool: Still exists"
            ((ERRORS++))
        fi
    fi

    # Check IAM Role
    if [ "$DRY_RUN" = false ]; then
        if aws iam get-role --role-name "$IAM_ROLE_NAME" --profile "$PROFILE" 2>&1 | grep -q "NoSuchEntity"; then
            print_success "IAM Role: Deleted"
        else
            print_error "IAM Role: Still exists"
            ((ERRORS++))
        fi
    fi

    echo ""
    if [ $ERRORS -eq 0 ]; then
        print_success "All resources successfully deleted!"
    else
        print_error "Some resources may still exist. Check the errors above."
        exit 1
    fi
}

################################################################################
# Main Execution
################################################################################

main() {
    parse_args "$@"

    if [ "$DRY_RUN" = true ]; then
        print_warning "Running in DRY RUN mode - no resources will be deleted\n"
    fi

    confirm_deletion

    print_header "Starting Decommissioning Process"
    print_info "AWS Profile: $PROFILE"
    print_info "Region: $REGION"
    echo ""

    # Execute deletions in order
    # Note: CloudFront must be deleted first as it depends on S3
    delete_cloudfront
    delete_s3_bucket
    delete_api_gateway
    delete_lambda_functions
    delete_dynamodb_table
    delete_cognito_user_pool
    delete_iam_role
    delete_oidc_provider

    # Verify everything is gone
    verify_deletion

    print_header "🎉 Decommissioning Complete! 🎉"

    echo -e "\n${GREEN}All Shopping List application resources have been removed from AWS.${NC}\n"

    if [ "$DRY_RUN" = false ]; then
        print_info "Next steps:"
        echo "  1. Remove GitHub secret: AWS_ROLE_ARN"
        echo "  2. Delete GitHub Actions workflow: .github/workflows/deploy.yml"
        echo "  3. Delete local project files if no longer needed"
        echo ""
    fi
}

# Run main function
main "$@"

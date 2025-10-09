# CI/CD Setup Guide - Automatic Deployment to AWS

This guide covers multiple options for automatically deploying the Shopping List app when you push code to GitHub.

## Table of Contents
1. [GitHub Actions + AWS (Recommended)](#option-1-github-actions--aws-recommended)
2. [AWS Amplify](#option-2-aws-amplify)
3. [AWS CodePipeline](#option-3-aws-codepipeline)
4. [Comparison Table](#comparison-table)

---

## Option 1: GitHub Actions + AWS (Recommended)

**Best for:** Full control, flexibility, and cost-effectiveness

### Features
- ✅ Free for public repos, generous free tier for private repos
- ✅ Deploys Lambda functions and website automatically
- ✅ Invalidates CloudFront cache
- ✅ Easy to customize and debug
- ✅ Workflow file already created at `.github/workflows/deploy.yml`

### Setup Steps

#### Step 1: Create IAM Role for GitHub Actions (OIDC - No Credentials Needed!)

This is the **recommended secure approach** - no long-lived credentials stored in GitHub.

```bash
# 1. Create trust policy for GitHub OIDC
cat > /tmp/github-trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::016164185850:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:formicag/first:*"
        }
      }
    }
  ]
}
EOF

# 2. Create OIDC provider (only needed once per AWS account)
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1 \
  --profile AdministratorAccess-016164185850

# 3. Create IAM role for GitHub Actions
aws iam create-role \
  --role-name GitHubActionsDeployRole \
  --assume-role-policy-document file:///tmp/github-trust-policy.json \
  --profile AdministratorAccess-016164185850

# 4. Attach deployment permissions policy
cat > /tmp/github-deploy-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "lambda:UpdateFunctionCode",
        "lambda:GetFunction"
      ],
      "Resource": "arn:aws:lambda:eu-west-1:016164185850:function:ShoppingList-*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::shoppinglist.gianlucaformica.net",
        "arn:aws:s3:::shoppinglist.gianlucaformica.net/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "cloudfront:CreateInvalidation",
        "cloudfront:GetInvalidation"
      ],
      "Resource": "arn:aws:cloudfront::016164185850:distribution/E2G8S9GOXLBFEZ"
    }
  ]
}
EOF

aws iam put-role-policy \
  --role-name GitHubActionsDeployRole \
  --policy-name DeploymentPolicy \
  --policy-document file:///tmp/github-deploy-policy.json \
  --profile AdministratorAccess-016164185850
```

#### Step 2: Configure GitHub Repository Secrets

1. Go to your GitHub repository: `https://github.com/formicag/first`
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add the following secret:

   - **Name**: `AWS_ROLE_ARN`
   - **Value**: `arn:aws:iam::016164185850:role/GitHubActionsDeployRole`

#### Step 3: Test the Workflow

1. Make a change to any file in `lambda/` or `website/`
2. Commit and push to the `main` branch:
   ```bash
   git add .
   git commit -m "Test CI/CD deployment"
   git push origin main
   ```
3. Go to **Actions** tab in GitHub to watch the deployment

### Alternative: Using Access Keys (Less Secure)

If you can't use OIDC, you can use AWS access keys:

```bash
# Create a deployment user
aws iam create-user \
  --user-name github-actions-deploy \
  --profile AdministratorAccess-016164185850

# Attach the deployment policy (use the same policy from above)
aws iam put-user-policy \
  --user-name github-actions-deploy \
  --policy-name DeploymentPolicy \
  --policy-document file:///tmp/github-deploy-policy.json \
  --profile AdministratorAccess-016164185850

# Create access keys
aws iam create-access-key \
  --user-name github-actions-deploy \
  --profile AdministratorAccess-016164185850
```

Then add to GitHub Secrets:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

And update `.github/workflows/deploy.yml`:
```yaml
- name: Configure AWS credentials
  uses: aws-actions/configure-aws-credentials@v4
  with:
    aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
    aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
    aws-region: eu-west-1
```

---

## Option 2: AWS Amplify

**Best for:** Simple frontend-only deployments with minimal backend logic

### Features
- ✅ Managed by AWS
- ✅ Automatic builds and deployments
- ✅ Built-in preview for pull requests
- ❌ Less suitable for Lambda function deployments
- ❌ More expensive than GitHub Actions

### Setup Steps

```bash
# 1. Install Amplify CLI
npm install -g @aws-amplify/cli

# 2. Initialize Amplify in your project
cd /Users/gianlucaformica/Projects/first
amplify init

# 3. Connect to GitHub repository
amplify add hosting

# 4. Deploy
amplify publish
```

**Note:** Amplify is better suited for static sites. For this project with Lambda functions, GitHub Actions is recommended.

---

## Option 3: AWS CodePipeline

**Best for:** Complex enterprise deployments with multiple stages

### Features
- ✅ Fully AWS-native solution
- ✅ Integrates with CodeBuild, CodeDeploy
- ✅ Advanced deployment strategies (blue/green, canary)
- ❌ More complex to set up
- ❌ Costs money ($1/pipeline/month + build minutes)

### Setup Steps

```bash
# 1. Create CodePipeline via CloudFormation
cat > codepipeline-stack.yaml <<EOF
AWSTemplateFormatVersion: '2010-09-09'
Description: CodePipeline for Shopping List App

Parameters:
  GitHubToken:
    Type: String
    NoEcho: true
    Description: GitHub personal access token

Resources:
  Pipeline:
    Type: AWS::CodePipeline::Pipeline
    Properties:
      Name: ShoppingListPipeline
      RoleArn: !GetAtt PipelineRole.Arn
      ArtifactStore:
        Type: S3
        Location: !Ref ArtifactBucket
      Stages:
        - Name: Source
          Actions:
            - Name: SourceAction
              ActionTypeId:
                Category: Source
                Owner: ThirdParty
                Provider: GitHub
                Version: 1
              Configuration:
                Owner: formicag
                Repo: first
                Branch: main
                OAuthToken: !Ref GitHubToken
              OutputArtifacts:
                - Name: SourceOutput

        - Name: Build
          Actions:
            - Name: BuildAction
              ActionTypeId:
                Category: Build
                Owner: AWS
                Provider: CodeBuild
                Version: 1
              Configuration:
                ProjectName: !Ref BuildProject
              InputArtifacts:
                - Name: SourceOutput
              OutputArtifacts:
                - Name: BuildOutput

  BuildProject:
    Type: AWS::CodeBuild::Project
    Properties:
      Name: ShoppingListBuild
      ServiceRole: !GetAtt BuildRole.Arn
      Artifacts:
        Type: CODEPIPELINE
      Environment:
        Type: LINUX_CONTAINER
        ComputeType: BUILD_GENERAL1_SMALL
        Image: aws/codebuild/standard:5.0
      Source:
        Type: CODEPIPELINE
        BuildSpec: buildspec.yml

  ArtifactBucket:
    Type: AWS::S3::Bucket

  # IAM roles omitted for brevity
EOF

# 2. Deploy the stack
aws cloudformation create-stack \
  --stack-name ShoppingListPipeline \
  --template-body file://codepipeline-stack.yaml \
  --capabilities CAPABILITY_IAM \
  --parameters ParameterKey=GitHubToken,ParameterValue=YOUR_GITHUB_TOKEN \
  --region eu-west-1 \
  --profile AdministratorAccess-016164185850
```

Then create `buildspec.yml`:
```yaml
version: 0.2

phases:
  install:
    runtime-versions:
      python: 3.11
  build:
    commands:
      - cd lambda
      - for func in createItem getItems updateItem deleteItem emailList categorizeItems; do
          zip ${func}.zip ${func}.py cognito_helper.py;
          aws lambda update-function-code --function-name ShoppingList-${func^} --zip-file fileb://${func}.zip --region eu-west-1;
        done
      - cd ../website
      - aws s3 sync . s3://shoppinglist.gianlucaformica.net/
      - aws cloudfront create-invalidation --distribution-id E2G8S9GOXLBFEZ --paths "/*"
```

---

## Comparison Table

| Feature | GitHub Actions | AWS Amplify | AWS CodePipeline |
|---------|---------------|-------------|------------------|
| **Cost** | Free (2000 min/month) | ~$15-30/month | ~$1/month + build costs |
| **Setup Complexity** | ⭐⭐ Easy | ⭐⭐⭐ Medium | ⭐⭐⭐⭐ Complex |
| **Lambda Deployment** | ✅ Excellent | ❌ Limited | ✅ Excellent |
| **S3/CloudFront** | ✅ Excellent | ✅ Excellent | ✅ Excellent |
| **Customization** | ✅ Highly flexible | ❌ Limited | ✅ Very flexible |
| **PR Previews** | ✅ (with config) | ✅ Built-in | ✅ (with config) |
| **Secrets Management** | ✅ GitHub Secrets | ✅ AWS Secrets | ✅ AWS Secrets |
| **Build Logs** | ✅ GitHub UI | ✅ AWS Console | ✅ AWS Console |
| **Multi-stage Deploy** | ✅ (manual config) | ✅ Built-in | ✅ Built-in |

---

## Recommended Solution: GitHub Actions

**For this project, GitHub Actions is recommended because:**

1. ✅ **Free** - 2000 minutes/month is plenty for this app
2. ✅ **Already configured** - workflow file included in this repo
3. ✅ **Secure** - Uses OIDC (no long-lived credentials)
4. ✅ **Simple** - Easy to understand and modify
5. ✅ **Perfect fit** - Handles both Lambda and S3/CloudFront deployments

---

## Advanced: Deployment Environments

You can add staging and production environments:

### Update `.github/workflows/deploy.yml` for multi-environment:

```yaml
name: Deploy Shopping List App

on:
  push:
    branches:
      - main
      - develop

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set environment
        id: set-env
        run: |
          if [ "${{ github.ref }}" = "refs/heads/main" ]; then
            echo "ENV=prod" >> $GITHUB_OUTPUT
            echo "BUCKET=shoppinglist.gianlucaformica.net" >> $GITHUB_OUTPUT
            echo "DISTRIBUTION=E2G8S9GOXLBFEZ" >> $GITHUB_OUTPUT
          else
            echo "ENV=dev" >> $GITHUB_OUTPUT
            echo "BUCKET=dev.shoppinglist.gianlucaformica.net" >> $GITHUB_OUTPUT
            echo "DISTRIBUTION=E123456789DEV" >> $GITHUB_OUTPUT
          fi

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: eu-west-1

      - name: Deploy to ${{ steps.set-env.outputs.ENV }}
        run: |
          # Deploy Lambda functions with environment suffix
          cd lambda
          for func in createItem getItems updateItem deleteItem emailList categorizeItems; do
            zip ${func}.zip ${func}.py cognito_helper.py
            aws lambda update-function-code \
              --function-name ShoppingList-${{ steps.set-env.outputs.ENV }}-${func^} \
              --zip-file fileb://${func}.zip \
              --region eu-west-1
          done

          # Deploy website
          cd ../website
          aws s3 sync . s3://${{ steps.set-env.outputs.BUCKET }}/

          # Invalidate CloudFront
          aws cloudfront create-invalidation \
            --distribution-id ${{ steps.set-env.outputs.DISTRIBUTION }} \
            --paths "/*"
```

---

## Troubleshooting

### GitHub Actions Fails with "Access Denied"

**Solution:** Check IAM role permissions
```bash
aws iam get-role-policy \
  --role-name GitHubActionsDeployRole \
  --policy-name DeploymentPolicy \
  --profile AdministratorAccess-016164185850
```

### OIDC Provider Already Exists

**Solution:** Skip the create-open-id-connect-provider step if it already exists
```bash
aws iam list-open-id-connect-providers \
  --profile AdministratorAccess-016164185850
```

### CloudFront Invalidation Costs Too Much

**Solution:** Only invalidate specific paths
```yaml
- name: Invalidate CloudFront (specific files only)
  run: |
    aws cloudfront create-invalidation \
      --distribution-id E2G8S9GOXLBFEZ \
      --paths "/index.html" "/app.js" "/auth.js" "/styles.css"
```

First 1000 invalidation paths per month are free!

---

## Next Steps

1. ✅ Review the GitHub Actions workflow: `.github/workflows/deploy.yml`
2. ⬜ Set up IAM role using the commands above
3. ⬜ Add `AWS_ROLE_ARN` to GitHub Secrets
4. ⬜ Test deployment by pushing to main branch
5. ⬜ (Optional) Set up development environment

---

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [AWS OIDC with GitHub Actions](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services)
- [AWS Amplify Documentation](https://docs.amplify.aws/)
- [AWS CodePipeline Documentation](https://docs.aws.amazon.com/codepipeline/)

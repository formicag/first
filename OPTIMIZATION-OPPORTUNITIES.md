# 🚀 Optimization Opportunities

This document outlines potential optimizations for the Shopping List application, when they should be implemented, and their expected impact.

## Current Status: ✅ **Well-Optimized for Current Scale**

**Current Monthly Costs (Estimated)**:
- Lambda: ~£0.50-1.00
- DynamoDB: ~£0.50-1.00
- Bedrock (AI): ~£0.30-0.50
- API Gateway: ~£0.30-0.50
- **Total: ~£2-3/month**

**Recommendation**: No urgent optimizations needed. Focus on features and user experience first.

---

## 🎯 Optimization Tier 1: Implement When Costs Exceed £5/month

### 1. AI Response Caching

**What**: Cache AI results for common items to avoid repeated Bedrock API calls.

**Expected Savings**: 40-60% reduction in Bedrock costs (~£0.15-0.30/month)

**Implementation Complexity**: Low

**How**:
- Add DynamoDB table: `ShoppingList-AICache-Dev`
- Cache key: SHA256 hash of item name (normalized)
- TTL: 30 days
- Files created: `lambda/ai_cache.py`, `lambda/prompt_utils.py`

**When to Implement**:
- Bedrock costs exceed £2/month
- More than 100 items added per week
- Same items being added repeatedly

**Code Ready**: ✅ Yes, `lambda/ai_cache.py` implemented and ready to activate

**Status**: ✅ IMPLEMENTED (not yet activated)
- Code is production-ready
- Will activate when Bedrock costs exceed £2/month
- To activate: Create DynamoDB table `ShoppingList-AICache-Dev` and update Lambda functions

---

### 2. Modular Prompt Builder

**What**: Extract prompt building logic into reusable utilities.

**Expected Savings**: Minimal cost savings, improves maintainability

**Implementation Complexity**: Low

**Benefits**:
- Easier to update AI prompts
- Consistent prompts across all Lambda functions
- Simpler to test and debug

**When to Implement**:
- Planning to add more AI features
- Need to frequently update prompts
- Multiple developers working on codebase

**Code Ready**: ✅ Yes, `lambda/prompt_utils.py` exists

**Status**: ✅ IMPLEMENTED (ready to use)
- Code is production-ready
- Can be integrated into Lambda functions when needed
- Provides reusable prompt templates for all AI tasks

---

## 🎯 Optimization Tier 2: Implement When Scale Increases 10x

### 3. Unified CRUD Lambda Function

**What**: Merge createItem, getItems, updateItem, deleteItem into single Lambda.

**Expected Savings**: ~£0.20/month in Lambda costs

**Implementation Complexity**: High

**Risks**:
- ⚠️ Loses AI processing features if not careful
- ⚠️ Violates single responsibility principle
- ⚠️ Harder to debug and monitor
- ⚠️ Could break existing functionality

**When to Implement**:
- More than 10,000 requests per day
- Lambda costs exceed £5/month
- Need to reduce cold start times

**Recommendation**: ⛔ Skip unless absolutely necessary

---

### 4. API Gateway HTTP API (vs REST API)

**What**: Migrate from REST API to HTTP API for cost reduction.

**Expected Savings**: 70% reduction in API Gateway costs (~£0.20-0.30/month)

**Implementation Complexity**: High (requires complete API restructure)

**Risks**:
- ⚠️ Breaking change for frontend
- ⚠️ Different authentication flow
- ⚠️ Requires testing all endpoints

**When to Implement**:
- API Gateway costs exceed £3/month
- More than 1 million requests per month
- Undertaking major infrastructure refactor

**Current Status**: Not needed, REST API working fine

---

## 🎯 Optimization Tier 3: Advanced Features (Scale > 1000 users)

### 5. DynamoDB Global Secondary Indexes (GSI)

**What**: Add GSIs for faster queries on category, bought status.

**Expected Savings**: None (costs more, improves performance)

**Implementation Complexity**: Medium

**When to Implement**:
- Query latency > 500ms
- More than 10,000 items in database
- Need complex filtering and sorting

---

### 6. Lambda Reserved Concurrency

**What**: Reserve Lambda capacity for predictable workloads.

**Expected Savings**: 20-40% Lambda cost reduction at high scale

**Implementation Complexity**: Low

**When to Implement**:
- Lambda costs exceed £10/month
- Consistent traffic patterns
- Need guaranteed capacity

---

### 7. CloudFront Edge Caching for API

**What**: Cache GET requests at CloudFront edge locations.

**Expected Savings**: 50-70% API Gateway cost reduction

**Implementation Complexity**: Medium

**When to Implement**:
- API Gateway costs exceed £5/month
- Many users from different geographic regions
- Read-heavy workload (>80% GET requests)

---

## 📊 Implementation Priority Matrix

| Optimization | Cost Savings | Complexity | Priority | Trigger Point |
|-------------|--------------|------------|----------|---------------|
| **AI Caching** | ⭐⭐⭐ | 🔨 Low | **HIGH** | Bedrock > £2/mo |
| **Prompt Utils** | ⭐ | 🔨 Low | Medium | Multiple AI features |
| **Unified Lambda** | ⭐ | 🔨🔨🔨 High | **LOW** | Lambda > £5/mo |
| **HTTP API** | ⭐⭐ | 🔨🔨🔨 High | Low | API GW > £3/mo |
| **GSI** | 💰 Costs more | 🔨🔨 Medium | As needed | Query latency |
| **Reserved Capacity** | ⭐⭐⭐ | 🔨 Low | As needed | Lambda > £10/mo |
| **Edge Caching** | ⭐⭐⭐ | 🔨🔨 Medium | As needed | API GW > £5/mo |

---

## 🔍 Monitoring Thresholds

Set up CloudWatch Alarms for:

1. **Bedrock API Calls**: Alert if > 500 calls/day
2. **Lambda Invocations**: Alert if > 50,000/day
3. **DynamoDB Read/Write Units**: Alert if throttling occurs
4. **API Gateway Requests**: Alert if > 100,000/day
5. **Monthly Cost**: Alert if > £5, £10, £20

---

## ✅ Current Optimizations Already Implemented

1. ✅ **Configurable Bedrock Model** - Can switch models via `BEDROCK_MODEL` environment variable
2. ✅ **AI Caching Utility** - `lambda/ai_cache.py` ready to activate when needed
3. ✅ **Modular Prompt Builder** - `lambda/prompt_utils.py` ready for integration
4. ✅ **Pay-per-request DynamoDB** - Auto-scales, no wasted capacity
5. ✅ **Efficient Lambda memory** - 256 MB is optimal for workload
6. ✅ **Decimal type for prices** - Correct data types avoid conversion overhead
7. ✅ **CloudFront CDN** - Static assets served from edge locations
8. ✅ **GitHub Actions CI/CD** - Automated deployments, no manual overhead
9. ✅ **Dark Theme UI** - Consistent, accessible design across all pages

---

## 🎓 Key Learnings

1. **Premature optimization is the root of all evil** - Don't optimize until you have a problem
2. **Monitor first, optimize later** - Use AWS Cost Explorer to identify actual bottlenecks
3. **Simplicity > Complexity** - Current architecture is clean and maintainable
4. **Scale gradually** - Implement optimizations as needed, not all at once
5. **Cost vs Maintainability** - Saving £1/month isn't worth breaking a working system

---

## 📈 Next Steps

**Now**:
- ✅ Keep current architecture (it's working great!)
- ✅ Monitor costs monthly
- ✅ Focus on features and UX

**When Bedrock > £2/month**:
- Implement AI caching (files ready in repo)
- Use prompt utilities
- Expected time: 2-3 hours

**When Total > £10/month**:
- Review AWS Cost Explorer
- Identify actual bottleneck
- Implement targeted optimization

---

## 📚 References

- [AWS Lambda Pricing](https://aws.amazon.com/lambda/pricing/)
- [DynamoDB Pricing](https://aws.amazon.com/dynamodb/pricing/)
- [API Gateway Pricing](https://aws.amazon.com/api-gateway/pricing/)
- [Bedrock Pricing](https://aws.amazon.com/bedrock/pricing/)
- [AWS Well-Architected Framework - Cost Optimization](https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/welcome.html)

---

**Last Updated**: 2025-10-10
**Status**: Core optimizations implemented, ready for future activation
**Recent Changes**:
- ✅ Added AI caching utility (`lambda/ai_cache.py`)
- ✅ Added modular prompt builder (`lambda/prompt_utils.py`)
- ✅ Made Bedrock model configurable via environment variables
- ✅ Applied dark theme to all pages (index.html, login.html, prompt-manager.html)
- ✅ Moved "Store Today's Shop" button to header for better UX

**Review Next**: When monthly cost exceeds £5

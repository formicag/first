# AI Usage in Shopping List Application

This document explains how artificial intelligence is integrated into the Shopping List application.

## Overview

The application uses **Amazon Bedrock** with **Claude 3 Haiku** to provide intelligent categorization, spelling correction, and price estimation for shopping list items.

### AI Features

1. **Auto-Categorize Items** - Categorize only uncategorized items with AI
2. **Recategorize ALL Items** - Recategorize every item in the database using current AI logic
3. **Auto-Create Items** - AI processing when adding new items (spell-check, price estimate, categorize)
4. **Recalculate Prices** - Update all item prices using current Sainsbury's estimates

---

## AI Service: Amazon Bedrock

### What is Amazon Bedrock?

Amazon Bedrock is AWS's fully managed service that provides access to foundation models from leading AI companies, including Anthropic's Claude models, through a single API.

### Model Used

**Model ID**: `anthropic.claude-3-haiku-20240307-v1:0`

**Why Claude 3 Haiku?**
- ⚡ **Fast**: Sub-second response times for real-time categorization
- 💰 **Cost-effective**: Most affordable Claude model for production use
- 🎯 **Accurate**: Excellent at understanding context and categorization tasks
- 🔒 **Secure**: Runs in AWS infrastructure with no data retention by Anthropic

---

## Feature 1: Auto-Categorize Shopping Items (Uncategorized Only)

### Where It's Used

**Lambda Function**: `lambda/categorizeItems.py`

**API Endpoint**: `POST /categorize/{userId}`

**Frontend Button**: "🤖 Auto-Categorize Items" (legacy - not currently visible in UI)

### What It Does

When a user clicks the "Auto-Categorize" button, the AI performs **two tasks**:

#### 1. Spelling Correction
Automatically fixes common spelling mistakes in item names:
- "tomatoe" → "tomato"
- "Kambucha" → "Kombucha"
- "spagetti" → "spaghetti"

#### 2. Intelligent Categorization
Assigns items to appropriate grocery categories based on semantic understanding:
- "Beer" → "Beverages"
- "Rye Bread" → "Bakery"
- "Bounty" → "Household & Cleaning" (paper towels)
- "Flash" → "Household & Cleaning" (cleaning product)
- "Kombucha" → "Beverages"

---

## How It Works

### Step-by-Step Process

1. **User Action**
   - User clicks "🤖 Auto-Categorize Items" button
   - Frontend sends POST request to `/categorize/{userId}`

2. **Lambda Retrieves Uncategorized Items**
   ```python
   # Query DynamoDB for items without categories
   response = table.scan(
       FilterExpression=Attr('category').not_exists() | Attr('category').eq('')
   )
   ```

3. **AI Prompt Construction**
   For each item, the Lambda function creates a structured prompt:
   ```python
   prompt = f"""You are categorizing grocery items. For this item: '{item_name}'

   Task 1: Correct any spelling mistakes in the item name.
   Task 2: Categorize into ONE of these categories: {categories}

   Return ONLY valid JSON in this exact format:
   {{"correctedName": "corrected item name", "category": "category name"}}"""
   ```

4. **Bedrock API Call**
   ```python
   response = bedrock_runtime.invoke_model(
       modelId='anthropic.claude-3-haiku-20240307-v1:0',
       contentType='application/json',
       body=json.dumps({
           "anthropic_version": "bedrock-2023-05-31",
           "max_tokens": 100,
           "temperature": 0,  # Deterministic output
           "messages": [{"role": "user", "content": prompt}]
       })
   )
   ```

5. **Parse AI Response**
   ```python
   result = json.loads(response_text)
   corrected_name = result.get('correctedName', item_name)
   category = result.get('category', 'Unknown Category')
   ```

6. **Update DynamoDB**
   ```python
   table.update_item(
       Key={'userId': item['userId'], 'itemId': item['itemId']},
       UpdateExpression='SET category = :category, itemName = :itemName',
       ExpressionAttributeValues={
           ':category': result['category'],
           ':itemName': result['correctedName']
       }
   )
   ```

7. **Frontend Display**
   - Success message shows how many items were categorized
   - Lists spelling corrections: `'Kambucha' → 'Kombucha'`
   - Refreshes the view to show newly categorized items grouped by category

---

## Feature 2: Recategorize ALL Items

### Where It's Used

**Lambda Function**: `lambda/recategorizeAllItems.py`

**API Endpoint**: `POST /categorize/recalculate`

**Frontend Button**: "🏷️ Recategorize All Items" in `website/index.html`

### What It Does

When a user clicks the "Recategorize All Items" button, the AI recategorizes **EVERY item** in the database, not just uncategorized ones. This is useful for:
- Fixing incorrectly categorized items across the entire database
- Applying updated categorization logic to all existing items
- Cleaning up categories after AI prompt improvements

### How It Differs from Auto-Categorize

| Feature | Auto-Categorize | Recategorize ALL |
|---------|----------------|------------------|
| **Scope** | Only uncategorized items | ALL items in database |
| **Use Case** | Initial categorization | Bulk recategorization |
| **Lambda** | `categorizeItems.py` | `recategorizeAllItems.py` |
| **Endpoint** | `POST /categorize/{userId}` | `POST /categorize/recalculate` |
| **Spelling** | Corrects spelling | No spelling changes |
| **Output** | Spelling corrections + counts | Category changes + counts |

### Step-by-Step Process

1. **User Action**
   - User clicks "🏷️ Recategorize All Items" button
   - Confirms action in dialog
   - Frontend sends POST request to `/categorize/recalculate`

2. **Lambda Retrieves ALL Items**
   ```python
   # Get ALL items, regardless of category status
   response = table.scan()
   all_items = response.get('Items', [])
   ```

3. **AI Categorization Loop**
   For each item:
   ```python
   old_category = item.get('category', 'No category')
   result = categorize_item_with_bedrock(item_name)
   new_category = result['category']

   # Track changes
   if old_category != new_category:
       category_changes.append({
           'itemName': item_name,
           'oldCategory': old_category,
           'newCategory': new_category
       })
   ```

4. **Update DynamoDB**
   ```python
   table.update_item(
       Key={'userId': item['userId'], 'itemId': item['itemId']},
       UpdateExpression='SET category = :category',
       ExpressionAttributeValues={':category': result['category']}
   )
   ```

5. **Frontend Display**
   - Success message shows statistics:
     - Total items recategorized
     - Number of category changes
   - List auto-refreshes to show updated categories
   - Example: "✓ Recategorization complete! Updated 45 items (12 categories changed)."

### Performance Considerations

- **Processing Time**: ~0.5 seconds per item
  - 10 items: ~5 seconds
  - 50 items: ~25 seconds
  - 100 items: ~50 seconds

- **Cost**: Same as auto-categorize (~$0.0005 per item)

- **Lambda Configuration**:
  - Timeout: 120 seconds
  - Memory: 512 MB
  - Handles up to ~200 items in single execution

---

## Predefined Categories

The AI categorizes items into these standard grocery store sections:

| Category | Examples |
|----------|----------|
| **Fresh Produce - Fruit** | Apples, Bananas, Oranges |
| **Fresh Produce - Vegetables** | Tomatoes, Lettuce, Carrots |
| **Fresh Produce - Herbs** | Basil, Cilantro, Parsley |
| **Bakery** | Bread, Rye Bread, Croissants |
| **Meat Fish & Deli** | Chicken, Salmon, Ham |
| **Dairy & Eggs** | Milk, Butter, Cheese |
| **Frozen Foods** | Ice cream, Frozen vegetables |
| **Pantry / Dry Goods** | Pasta, Rice, Peanut Butter |
| **Snacks & Confectionery** | Chips, Chocolate, Candy |
| **Beverages** | Beer, Water, Kombucha |
| **Household & Cleaning** | Toilet Roll, Flash, Bounty |
| **Health & Beauty** | Shampoo, Soap, Toothpaste |

If the AI cannot determine a category, it assigns **"Unknown Category"**.

---

## Code Architecture

### File: `lambda/categorizeItems.py`

```python
# Key components:

# 1. AWS Clients
dynamodb = boto3.resource('dynamodb')
bedrock_runtime = boto3.client('bedrock-runtime', region_name='eu-west-1')

# 2. Main Handler
def lambda_handler(event, context):
    # Extract userId, get uncategorized items, categorize each

# 3. Database Query
def get_uncategorized_items(user_id):
    # Scan or query DynamoDB for items without categories

# 4. AI Categorization
def categorize_item_with_bedrock(item_name):
    # Call Bedrock API with structured prompt
    # Parse JSON response
    # Return corrected name and category
```

### Frontend Integration: `website/app.js`

```javascript
// Button handler
function setupCategorizeButtonHandler() {
    button.addEventListener('click', async () => {
        button.disabled = true;
        button.textContent = '🤖 Categorizing...';

        const response = await fetchWithAuth(
            `${API_BASE_URL}/categorize/${userId}`,
            { method: 'POST' }
        );

        const data = await response.json();

        // Show success message with spelling corrections
        let message = `✓ Categorized ${data.categorizedCount} items using AI!`;
        if (data.spellingCorrectedCount > 0) {
            const corrections = data.spellingCorrections
                .map(c => `'${c.original}' → '${c.corrected}'`)
                .join(', ');
            message += ` Corrected spelling for: ${corrections}`;
        }

        // Refresh the list to show categorized items
        await loadUserItems();
    });
}
```

---

## Real-World Example

### Before Categorization

DynamoDB items without categories:
```json
[
  {"userId": "Gianluca", "itemId": "abc123", "itemName": "Kambucha", "category": null},
  {"userId": "Gianluca", "itemId": "def456", "itemName": "tomatoe", "category": null},
  {"userId": "Gianluca", "itemId": "ghi789", "itemName": "Bounty", "category": null}
]
```

### AI Processing

**Item 1: "Kambucha"**
- AI detects spelling error
- Corrects to "Kombucha"
- Recognizes as fermented tea beverage
- Categorizes as "Beverages"

**Item 2: "tomatoe"**
- AI detects spelling error
- Corrects to "tomato"
- Recognizes as vegetable
- Categorizes as "Fresh Produce - Vegetables"

**Item 3: "Bounty"**
- No spelling errors
- AI understands context (paper towels brand)
- Categorizes as "Household & Cleaning"

### After Categorization

```json
[
  {"userId": "Gianluca", "itemId": "abc123", "itemName": "Kombucha", "category": "Beverages"},
  {"userId": "Gianluca", "itemId": "def456", "itemName": "tomato", "category": "Fresh Produce - Vegetables"},
  {"userId": "Gianluca", "itemId": "ghi789", "itemName": "Bounty", "category": "Household & Cleaning"}
]
```

### Frontend Display

Success message:
```
✓ Categorized 3 items using AI! Corrected spelling for: 'Kambucha' → 'Kombucha', 'tomatoe' → 'tomato'
```

Shopping list now grouped by category:
```
Gianluca's List (3 items)

  Beverages
    ☐ Kombucha (Qty: 1)

  Fresh Produce - Vegetables
    ☐ tomato (Qty: 1)

  Household & Cleaning
    ☐ Bounty (Qty: 1)
```

---

## Performance & Cost

### Response Times
- **Average**: 200-500ms per item
- **Batch processing**: Items categorized sequentially
- **User experience**: Button shows "🤖 Categorizing..." during processing

### Cost Optimization
- Uses **Claude 3 Haiku** (most affordable model)
- **Temperature: 0** for consistent, deterministic results
- **Max tokens: 100** (typical response is ~50 tokens)
- Only processes **uncategorized items** (not all items)

### Bedrock Pricing (as of 2025)
- **Input**: ~$0.00025 per 1,000 tokens
- **Output**: ~$0.00125 per 1,000 tokens
- **Example**: Categorizing 100 items costs approximately $0.02-0.05

---

## Error Handling

### Graceful Degradation

1. **Bedrock API Failure**
   ```python
   except Exception as e:
       logger.error(f"Error calling Bedrock: {str(e)}")
       return {
           'correctedName': item_name,  # Keep original
           'category': 'Unknown Category'  # Safe fallback
       }
   ```

2. **Invalid JSON Response**
   ```python
   try:
       result = json.loads(response_text)
   except json.JSONDecodeError:
       corrected_name = item_name
       category = 'Unknown Category'
   ```

3. **Invalid Category**
   ```python
   if category not in CATEGORIES and category != 'Unknown Category':
       logger.warning(f"Invalid category '{category}'")
       category = 'Unknown Category'
   ```

### User Feedback

If categorization fails:
```javascript
errorDiv.textContent = '✗ Failed to categorize items. Please try again.'
```

Partial success shows what worked:
```javascript
message = `✓ Categorized ${data.categorizedCount} items using AI!`;
if (data.errors) {
    message += ` (${data.errors.length} failed)`;
}
```

---

## IAM Permissions Required

The Lambda function needs Bedrock permissions:

```json
{
  "Effect": "Allow",
  "Action": [
    "bedrock:InvokeModel"
  ],
  "Resource": "arn:aws:bedrock:eu-west-1::foundation-model/anthropic.claude-3-haiku-20240307-v1:0"
}
```

---

## Why This Approach?

### Advantages

✅ **User Experience**
- No manual categorization required
- Automatic spelling correction
- One-click operation

✅ **Accuracy**
- Claude understands context (e.g., "Bounty" as paper towels)
- Handles brand names correctly
- Multi-lingual support

✅ **Scalability**
- Serverless architecture (Lambda + Bedrock)
- No AI model management
- Automatic scaling

✅ **Cost-Effective**
- Pay only for what you use
- Haiku model is very affordable
- Only processes uncategorized items

✅ **Maintainability**
- No ML training required
- No model updates needed
- Simple prompt-based approach

### Alternative Approaches (Not Used)

❌ **Rule-Based Categorization**
- Would require extensive keyword lists
- Can't handle spelling variations
- No understanding of context

❌ **Self-Hosted AI Models**
- Requires model hosting (EC2/SageMaker)
- Higher operational costs
- Model maintenance burden

❌ **Third-Party APIs**
- External dependencies
- Data privacy concerns
- Potential rate limits

---

## Future Enhancements

### Potential Improvements

1. **Learning from User Corrections**
   - Store user-corrected categories
   - Use few-shot learning with examples
   - Improve accuracy over time

2. **Batch Processing**
   - Categorize multiple items in single API call
   - Reduce Bedrock invocations
   - Lower costs and latency

3. **Smart Suggestions**
   - Suggest categories while user types
   - Auto-complete item names
   - Predictive categorization

4. **Multi-Language Support**
   - Detect item language
   - Categorize in user's language
   - Support international grocery terms

5. **Store-Specific Categories**
   - Learn user's preferred store layout
   - Map to actual aisle locations
   - Optimize shopping route

---

## Testing the AI Feature

### Manual Testing

1. Add items without categories:
   ```
   • "Kambucha" (misspelled)
   • "bred" (misspelled)
   • "tomatos" (misspelled)
   ```

2. Click "🤖 Auto-Categorize Items"

3. Verify:
   - Spelling corrections appear in success message
   - Items are grouped by category
   - Categories make sense

### Expected Results

- "Kambucha" → "Kombucha" (Beverages)
- "bred" → "bread" (Bakery)
- "tomatos" → "tomatoes" (Fresh Produce - Vegetables)

---

## Related Files

### Auto-Categorize (Uncategorized Only)
- **Lambda Function**: `lambda/categorizeItems.py`
- **Frontend Integration**: `website/app.js`
- **CloudFormation**: `cloudformation/compute-stack.yaml` (Bedrock permissions)

### Recategorize ALL Items
- **Lambda Function**: `lambda/recategorizeAllItems.py`
- **API Endpoint**: `POST /categorize/recalculate`
- **Frontend Integration**: `website/app.js:720` (setupRecategorizeItemsHandler)
- **UI Button**: `website/index.html:63`
- **Button Styling**: `website/styles.css:318`
- **Deployment Script**: `deploy-recategorize-endpoint.sh`

### Deployment
- **CI/CD**: Automatically deployed via GitHub Actions
- **Manual Deploy**: Use deployment scripts for new endpoints

---

## Resources

- [Amazon Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [Claude 3 Model Card](https://www.anthropic.com/claude/haiku)
- [Bedrock Pricing](https://aws.amazon.com/bedrock/pricing/)
- [Anthropic Messages API](https://docs.anthropic.com/en/api/messages)

---

## Summary

The Shopping List application uses **Amazon Bedrock with Claude 3 Haiku** to provide:

✅ **Automatic categorization** of grocery items into 12 standard categories
✅ **Bulk recategorization** of ALL items in database with one click
✅ **Spelling correction** for common typos and mistakes
✅ **Price estimation** for Sainsbury's UK items
✅ **Context understanding** (recognizes brand names and synonyms)
✅ **One-click operations** with real-time feedback
✅ **Cost-effective** processing (~$0.0005 per item)
✅ **Serverless** and scalable architecture

### AI-Powered Features Available

1. **Auto-Categorize Items** - Categorize uncategorized items only
2. **Recategorize ALL Items** - Recategorize entire database (NEW)
3. **Auto-Create with AI** - Spell-check, categorize, and price items on creation
4. **Recalculate Prices** - Update all item prices using current estimates

This demonstrates practical AI integration in a serverless web application using AWS managed services.

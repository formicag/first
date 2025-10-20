# Changelog

All notable changes to the Shopping List Application.

## [Recategorize All Items Feature] - 2025-10-20

### Added
- **Recategorize All Items Button** in main menu
  - New "🏷️ Recategorize All Items" button in action buttons section
  - Purple button styling to distinguish from other actions
  - One-click recategorization of ALL items in database using AI

- **New Lambda Function**: `recategorizeAllItems.py`
  - Retrieves ALL items from DynamoDB (not just uncategorized)
  - Uses Amazon Bedrock (Claude 3 Haiku) to recategorize each item
  - Tracks category changes and reports statistics
  - Located at `lambda/recategorizeAllItems.py`

- **New API Endpoint**: `POST /categorize/recalculate`
  - Deployed to API Gateway with CORS support
  - Returns count of recategorized items and category changes
  - Base URL: `https://01mmfw29n0.execute-api.eu-west-1.amazonaws.com/dev`

- **Deployment Script**: `deploy-recategorize-endpoint.sh`
  - Automated deployment for Lambda function and API endpoint
  - Creates Lambda function with proper IAM permissions
  - Configures API Gateway resources and CORS

### Enhanced
- **Frontend UI**
  - Added button to `website/index.html:63`
  - Implemented handler in `website/app.js:720`
  - Shows loading state: "🤖 AI Recategorizing..."
  - Displays success notification with statistics
  - Auto-refreshes list to show updated categories

- **Button Styling** in `website/styles.css:318`
  - Purple theme (#8957e5) matching dashboard accent color
  - Hover and active states for better UX
  - Disabled state during processing

### Use Case
- Allows bulk recategorization when category logic is updated
- Useful for fixing incorrectly categorized items across entire database
- Complements existing `categorizeItems.py` which only processes uncategorized items

## [Major Shopping Workflow Redesign] - 2025-10-12

### Added - Realistic Shopping Workflow
- **"Save for Next Shop" Feature** (📌/🔖 button on each item)
  - New `saveForNext` boolean field in DynamoDB schema
  - Click to mark recurring items (milk, bread, etc.)
  - Items marked saveForNext move to bottom of list
  - Auto-restore to proper position when unmarked

- **Complete Shopping Workflow**
  - 5-step realistic shopping process:
    1. Build list
    2. Mark recurring items (save for next shop)
    3. Tick items as you add to physical basket
    4. Click "Save My Shop" to finalize
    5. List is ready for next shopping trip

- **Visual Item States**
  - Normal items: Full color, bright text
  - Ticked items (bought): Crossed out, very faded (opacity 0.5)
  - Save for next items: Greyed out (opacity 0.6), bookmark icon (🔖), at bottom

- **Smart Sorting System**
  - Regular items: Store layout order (entrance → back)
  - Save for next items: Bottom of each user's list
  - Auto-resort when toggling save status

### Changed - Shop Storage Behavior
- **Complete Rewrite of `storeShop.py`**
  - NOW: Only saves TICKED items (bought=True) to shop history
  - NOW: DELETES ticked items from shopping list after saving
  - NOW: KEEPS items marked saveForNext (saved for next shop)
  - NOW: KEEPS items NOT ticked (items not purchased)
  - Result: List automatically ready for next shopping trip

- **Button Text Update**
  - Changed: "Store Today's Shop" → "💾 Save My Shop"
  - More intuitive for realistic shopping workflow

- **UI Organization**
  - Removed category headers from main list for cleaner UI
  - Items still sorted by store layout (entrance to back)
  - Category grouping removed, but optimal shopping order maintained

### Enhanced - AI Categorization
- **Form-Specific Categorization** in `createItem.py`
  - Distinguishes between fresh, canned, and frozen items
  - Example: "tuna" → "Canned & Jarred" (not Fish & Seafood)
  - Example: "frozen peas" → "Frozen Foods"
  - Example: "fresh salmon" → "Fish & Seafood"
  - Improved prompt with explicit form detection rules

### Fixed
- **Lambda Import Error** for `getItems.py`
  - Fixed GitHub Actions deployment to include `store_layout.py` dependency
  - Updated `.github/workflows/deploy.yml` packaging logic

- **Tuna Categorization Issue**
  - Fixed: "Tuna cans" now correctly categorized as "Canned & Jarred"
  - Enhanced AI prompt with form-specific rules
  - Manual recategorization of existing items

## [Store Layout Optimization] - 2025-10-10

### Added
- **AI Caching Utility** (`lambda/ai_cache.py`)
  - SHA256-based caching for AI responses
  - 30-day TTL for cached items
  - Ready to activate when Bedrock costs exceed £2/month
  - Reduces AI API calls by 40-60% for repeated items

- **Modular Prompt Builder** (`lambda/prompt_utils.py`)
  - Reusable prompt templates for AI tasks
  - Easier to maintain and update prompts
  - Consistent prompts across all Lambda functions
  - Functions: `build_item_processing_prompt()`, `build_bulk_price_prompt()`, `build_categorization_prompt()`

- **Configurable Bedrock Model**
  - Switch AI models via `BEDROCK_MODEL` environment variable
  - Updated `createItem.py` and `recalculatePrices.py`
  - Defaults to Claude 3 Haiku

- **Optimization Documentation** (`OPTIMIZATION-OPPORTUNITIES.md`)
  - Comprehensive optimization strategies
  - 3-tier implementation plan with triggers
  - Cost monitoring thresholds
  - Monitor-first philosophy

### Changed
- **Dark Theme Applied to All Pages**
  - `index.html` - Main shopping list (already had dark theme)
  - `login.html` - Login page now uses dark theme
  - `prompt-manager.html` - AI prompt manager now uses dark theme
  - Consistent GitHub-inspired color scheme across all pages:
    - Background: `#0d1117` and `#161b22`
    - Text: `#c9d1d9`
    - Borders: `#30363d`
    - Accent purple: `#8957e5`
    - Success green: `#238636`
    - Error red: `#da3633`

- **UI/UX Improvements**
  - Moved "Store Today's Shop" button to header (inline with title)
  - Total prices now displayed in header row for quick visibility
  - Improved button styling for better visual hierarchy

- **Documentation Updates**
  - Updated `README.md` with new features and optimizations
  - Added UI/UX Design section to README
  - Updated project structure with new files
  - Enhanced AI Configuration section

### Fixed
- Dark theme consistency across all pages
- Button positioning and layout in header

## [Previous Updates]

### Shop History Feature
- Added `storeShop.py` Lambda function
- Store complete shopping list snapshots with date, time, items, total price
- DynamoDB table: `ShoppingList-ShopHistory-Dev`

### Price Management
- Added `recalculatePrices.py` Lambda function
- Bulk price recalculation for all items
- Real-time total price calculation per user and combined
- Sainsbury's UK price estimates

### AI-Powered Features
- Automatic spell checking and capitalization
- Emoji assignment for items
- UK supermarket aisle categorization
- Price estimation via Amazon Bedrock (Claude 3 Haiku)

### Infrastructure
- CloudFormation nested stacks for complete infrastructure
- GitHub Actions CI/CD pipeline with OIDC authentication
- Cognito bypass mode for simplified access
- CloudFront CDN for fast worldwide access

---

## Upcoming Features

### When Bedrock Costs Exceed £2/month
- Activate AI caching (`lambda/ai_cache.py`)
- Create DynamoDB table: `ShoppingList-AICache-Dev`
- Integrate caching into `createItem.py`

### When Scale Increases 10x
- Consider HTTP API migration (if cost-effective)
- Add DynamoDB Global Secondary Indexes (if query latency increases)

### Future Enhancements
- Re-enable Cognito authentication (if needed)
- Add shop history viewing interface
- Export shopping lists to PDF/CSV
- Mobile app integration

---

**Current Version**: Stable with future-ready optimizations
**Status**: Production-ready, ~£2-3/month operating cost
**Last Updated**: 2025-10-10

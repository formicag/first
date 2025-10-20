/**
 * Shopping Dashboard - Analytics and Insights
 *
 * Displays shopping history with spending analysis by category
 */

// API Configuration
const API_BASE_URL = 'https://01mmfw29n0.execute-api.eu-west-1.amazonaws.com/dev';

/**
 * Initialize dashboard on page load
 */
document.addEventListener('DOMContentLoaded', () => {
    loadDashboardData();
});

/**
 * Load and display dashboard data
 */
async function loadDashboardData() {
    const contentContainer = document.getElementById('dashboard-content');

    try {
        // Fetch current shopping list items for all users (unbought only)
        const gianlucaItemsPromise = fetch(`${API_BASE_URL}/items/Gianluca?bought=unbought`).then(r => r.json());
        const nicoleItemsPromise = fetch(`${API_BASE_URL}/items/Nicole?bought=unbought`).then(r => r.json());

        // Fetch shop history (last 10 shops)
        const shopHistoryPromise = fetch(`${API_BASE_URL}/shop/history?limit=10`).then(r => r.json());

        // Wait for all requests
        const [gianlucaData, nicoleData, shopHistoryData] = await Promise.all([
            gianlucaItemsPromise,
            nicoleItemsPromise,
            shopHistoryPromise
        ]);

        // Combine items from both users
        const gianlucaItems = gianlucaData.items || [];
        const nicoleItems = nicoleData.items || [];
        const currentItems = [...gianlucaItems, ...nicoleItems];
        const shops = shopHistoryData.shops || [];

        // Analyze current shopping list by category
        const currentCategoryBreakdown = analyzeCurrentListByCategory(currentItems);
        const currentTotalPrice = currentCategoryBreakdown.reduce((sum, cat) => sum + cat.totalPrice, 0);
        const currentTotalItems = currentItems.length;

        // Check if we have any data to show
        if (shops.length === 0 && currentItems.length === 0) {
            contentContainer.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">📦</div>
                    <h2>No Data Available</h2>
                    <p>You haven't saved any shops yet and your current shopping list is empty.</p>
                    <p>Start by adding items to your shopping list from the main page!</p>
                </div>
            `;
            return;
        }

        // Get the most recent shop (if exists)
        const lastShop = shops.length > 0 ? shops[0] : null;

        // Analyze all shops for category spending
        const categoryAnalysis = shops.length > 0 ? analyzeCategorySpending(shops) : [];
        const totalSpending = categoryAnalysis.reduce((sum, cat) => sum + cat.totalPrice, 0);

        // Generate dashboard HTML
        contentContainer.innerHTML = `
            <!-- Current Shopping List Breakdown - Top Section -->
            ${currentItems.length > 0 ? `
            <div class="dashboard-card shop-history-section">
                <div class="card-header">
                    <span class="card-icon">🛒</span>
                    <span>Current Shopping List by Category</span>
                </div>
                <div class="stat-row" style="background: #0d1117; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
                    <span class="stat-label">Total Items</span>
                    <span class="stat-value highlight">${currentTotalItems}</span>
                </div>
                <div class="stat-row" style="background: #0d1117; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
                    <span class="stat-label">Estimated Total</span>
                    <span class="stat-value price">£${currentTotalPrice.toFixed(2)}</span>
                </div>
                <div class="category-list">
                    ${renderCategoryAnalysis(currentCategoryBreakdown)}
                </div>
            </div>
            ` : ''}

            <!-- Shop History List - Second Section -->
            ${shops.length > 0 ? `
            <div class="dashboard-card shop-history-section">
                <div class="card-header">
                    <span class="card-icon">📜</span>
                    <span>All Saved Shops</span>
                </div>
                <div id="message-container"></div>
                <div class="shop-history-list">
                    ${renderShopHistoryList(shops)}
                </div>
            </div>
            ` : ''}

            <div class="dashboard-grid">
                ${lastShop ? `
                <!-- Summary Stats -->
                <div class="dashboard-card">
                    <div class="card-header">
                        <span class="card-icon">💰</span>
                        <span>Last Shop Summary</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Date</span>
                        <span class="stat-value">${formatDate(lastShop.shopDate)}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Total Items</span>
                        <span class="stat-value highlight">${lastShop.totalItems || 0}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Total Price</span>
                        <span class="stat-value price">£${(lastShop.totalPrice || 0).toFixed(2)}</span>
                    </div>
                </div>

                <!-- All-Time Stats -->
                <div class="dashboard-card">
                    <div class="card-header">
                        <span class="card-icon">📈</span>
                        <span>All-Time Stats</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Total Shops Saved</span>
                        <span class="stat-value highlight">${shops.length}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Total Spending</span>
                        <span class="stat-value price">£${totalSpending.toFixed(2)}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Average Shop</span>
                        <span class="stat-value price">£${(totalSpending / shops.length).toFixed(2)}</span>
                    </div>
                </div>

                <!-- Top Categories -->
                <div class="dashboard-card last-shop-section">
                    <div class="card-header">
                        <span class="card-icon">🏆</span>
                        <span>Top Spending Categories (All Shops)</span>
                    </div>
                    <div class="category-list">
                        ${renderCategoryAnalysis(categoryAnalysis)}
                    </div>
                </div>

                <!-- Last Shop Details -->
                <div class="dashboard-card last-shop-section">
                    <div class="card-header">
                        <span class="card-icon">🛒</span>
                        <span>Last Shop Items (${formatDate(lastShop.shopDate)})</span>
                    </div>
                    <div class="shop-items-grid">
                        ${renderShopItems(lastShop.items || [])}
                    </div>
                </div>
                ` : ''}
            </div>
        `;

        // Attach delete event listeners after rendering
        if (shops.length > 0) {
            attachDeleteHandlers();
        }

    } catch (error) {
        console.error('Error loading dashboard:', error);
        contentContainer.innerHTML = `
            <div class="error-message">
                Failed to load dashboard data. Please try again later.
                <br><small>${error.message}</small>
            </div>
        `;
    }
}

/**
 * Analyze current shopping list by category
 * @param {Array} items - Array of shopping list items
 * @returns {Array} - Array of category analysis objects
 */
function analyzeCurrentListByCategory(items) {
    const categoryTotals = {};

    // Aggregate items by category
    items.forEach(item => {
        const category = item.category || 'Uncategorized';
        const price = parseFloat(item.estimatedPrice || 0);
        const quantity = parseInt(item.quantity || 1);

        if (!categoryTotals[category]) {
            categoryTotals[category] = {
                name: category,
                totalPrice: 0,
                itemCount: 0
            };
        }

        categoryTotals[category].totalPrice += (price * quantity);
        categoryTotals[category].itemCount += 1;
    });

    // Convert to array and sort by total price (descending)
    const categories = Object.values(categoryTotals);
    categories.sort((a, b) => b.totalPrice - a.totalPrice);

    return categories;
}

/**
 * Analyze spending by category across all shops
 * @param {Array} shops - Array of shop records
 * @returns {Array} - Array of category analysis objects
 */
function analyzeCategorySpending(shops) {
    const categoryTotals = {};

    // Aggregate spending by category
    shops.forEach(shop => {
        const items = shop.items || [];
        items.forEach(item => {
            const category = item.category || 'Uncategorized';
            const price = parseFloat(item.estimatedPrice || 0);

            if (!categoryTotals[category]) {
                categoryTotals[category] = {
                    name: category,
                    totalPrice: 0,
                    itemCount: 0
                };
            }

            categoryTotals[category].totalPrice += price;
            categoryTotals[category].itemCount += 1;
        });
    });

    // Convert to array and sort by total price (descending)
    const categories = Object.values(categoryTotals);
    categories.sort((a, b) => b.totalPrice - a.totalPrice);

    return categories;
}

/**
 * Render category analysis with visual bars
 * @param {Array} categories - Array of category analysis objects
 * @returns {string} - HTML string
 */
function renderCategoryAnalysis(categories) {
    if (categories.length === 0) {
        return '<p class="empty-state">No category data available</p>';
    }

    // Get max price for bar scaling
    const maxPrice = categories[0].totalPrice;

    // Show top 10 categories
    const topCategories = categories.slice(0, 10);

    return topCategories.map(cat => {
        const percentage = (cat.totalPrice / maxPrice) * 100;

        return `
            <div class="category-item">
                <div class="category-info">
                    <div class="category-name">${cat.name}</div>
                    <div class="category-count">${cat.itemCount} items</div>
                    <div class="category-bar">
                        <div class="category-bar-fill" style="width: ${percentage}%"></div>
                    </div>
                </div>
                <div class="category-price">£${cat.totalPrice.toFixed(2)}</div>
            </div>
        `;
    }).join('');
}

/**
 * Render shop items
 * @param {Array} items - Array of shop items
 * @returns {string} - HTML string
 */
function renderShopItems(items) {
    if (items.length === 0) {
        return '<p class="empty-state">No items in this shop</p>';
    }

    return items.map(item => `
        <div class="shop-item">
            <div>
                <span class="shop-item-name">${item.itemName || 'Unknown Item'}</span>
                <span class="shop-item-qty">×${item.quantity || 1}</span>
            </div>
            <div class="shop-item-price">£${(item.estimatedPrice || 0).toFixed(2)}</div>
        </div>
    `).join('');
}

/**
 * Render shop history list
 * @param {Array} shops - Array of shop records
 * @returns {string} - HTML string
 */
function renderShopHistoryList(shops) {
    if (shops.length === 0) {
        return '<p class="empty-state">No shops saved yet</p>';
    }

    return shops.map(shop => `
        <div class="shop-history-item" data-shop-id="${shop.shopId}">
            <div class="shop-history-info">
                <div class="shop-date">${formatDate(shop.shopDate)}</div>
                <div class="shop-meta">
                    <span class="shop-meta-item">📦 ${shop.totalItems} items</span>
                </div>
            </div>
            <div class="shop-price">£${(shop.totalPrice || 0).toFixed(2)}</div>
            <button class="btn-delete-shop" data-shop-id="${shop.shopId}" data-shop-date="${formatDate(shop.shopDate)}">
                🗑️ Delete
            </button>
        </div>
    `).join('');
}

/**
 * Attach delete event handlers to all delete buttons
 */
function attachDeleteHandlers() {
    const deleteButtons = document.querySelectorAll('.btn-delete-shop');
    deleteButtons.forEach(button => {
        button.addEventListener('click', handleDeleteShop);
    });
}

/**
 * Handle delete shop button click
 * @param {Event} event - Click event
 */
async function handleDeleteShop(event) {
    const button = event.currentTarget;
    const shopId = button.dataset.shopId;
    const shopDate = button.dataset.shopDate;

    // Confirm deletion
    if (!confirm(`Are you sure you want to delete the shop from ${shopDate}?`)) {
        return;
    }

    // Disable button during deletion
    button.disabled = true;
    button.textContent = '⏳ Deleting...';

    try {
        const response = await fetch(`${API_BASE_URL}/shop/${shopId}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        // Show success message
        showMessage('Shop deleted successfully!', 'success');

        // Reload dashboard data after short delay
        setTimeout(() => {
            loadDashboardData();
        }, 1000);

    } catch (error) {
        console.error('Error deleting shop:', error);
        showMessage('Failed to delete shop. Please try again.', 'error');

        // Re-enable button on error
        button.disabled = false;
        button.textContent = '🗑️ Delete';
    }
}

/**
 * Show message to user
 * @param {string} message - Message text
 * @param {string} type - Message type ('success' or 'error')
 */
function showMessage(message, type) {
    const container = document.getElementById('message-container');
    const className = type === 'success' ? 'success-message' : 'error-message';

    container.innerHTML = `<div class="${className}">${message}</div>`;

    // Auto-hide after 3 seconds
    setTimeout(() => {
        container.innerHTML = '';
    }, 3000);
}

/**
 * Format ISO date string to readable format
 * @param {string} isoDate - ISO date string
 * @returns {string} - Formatted date string
 */
function formatDate(isoDate) {
    const date = new Date(isoDate);
    const options = {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    };
    return date.toLocaleDateString('en-GB', options);
}

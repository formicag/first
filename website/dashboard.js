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
        // Fetch shop history (last 10 shops)
        const response = await fetch(`${API_BASE_URL}/shop/history?limit=10`);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        const shops = data.shops || [];

        if (shops.length === 0) {
            contentContainer.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">📦</div>
                    <h2>No Shopping History</h2>
                    <p>You haven't saved any shops yet. Start by storing your first shop from the main shopping list page!</p>
                </div>
            `;
            return;
        }

        // Get the most recent shop
        const lastShop = shops[0];

        // Analyze all shops for category spending
        const categoryAnalysis = analyzeCategorySpending(shops);
        const totalSpending = categoryAnalysis.reduce((sum, cat) => sum + cat.totalPrice, 0);

        // Generate dashboard HTML
        contentContainer.innerHTML = `
            <div class="dashboard-grid">
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
                        <span>Top Spending Categories</span>
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
            </div>
        `;

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

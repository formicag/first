// API Configuration
const API_BASE_URL = 'https://01mmfw29n0.execute-api.eu-west-1.amazonaws.com/dev';

// Check authentication on page load
document.addEventListener('DOMContentLoaded', () => {
    // BYPASS MODE: Authentication check disabled
    // Uncomment the lines below to re-enable Cognito authentication
    /*
    if (!isAuthenticated()) {
        window.location.href = 'login.html';
        return;
    }
    */

    // Ensure we have a default user set (for bypass mode)
    isAuthenticated(); // This will set default user if not set

    // BYPASS MODE: Show all lists
    document.getElementById('user-list-title').textContent = 'All Shopping Lists';

    // COGNITO MODE (commented out):
    // const userId = getUserId();
    // document.getElementById('user-list-title').textContent = `${userId}'s List`;

    // Load user's items
    loadUserItems();

    // Setup form handlers
    setupFormHandler();
    setupEmailButtonHandler();
    setupCategorizeButtonHandler();

    // Setup logout button
    document.getElementById('logout-btn').addEventListener('click', logout);
});

/**
 * Load items for all users (bypass mode - no user filtering)
 */
async function loadUserItems() {
    const itemsContainer = document.getElementById('items-list');
    const countElement = document.getElementById('item-count');

    // BYPASS MODE: Load all items from all users
    // For Cognito mode, uncomment the userId filtering:
    // const userId = getUserId();

    try {
        itemsContainer.innerHTML = '<div class="loading">Loading items...</div>';

        // BYPASS MODE: Load all items (use any userId - Lambda scans all)
        // The Lambda function has been modified to scan all items regardless of userId
        const response = await fetchWithAuth(`${API_BASE_URL}/items/TestUser?bought=all`);

        // COGNITO MODE (commented out):
        // const userId = getUserId();
        // const response = await fetchWithAuth(`${API_BASE_URL}/items/${userId}?bought=all`);

        if (!response.ok) {
            // BYPASS MODE: 401 check disabled
            // Uncomment to re-enable Cognito authentication
            /*
            if (response.status === 401) {
                logout();
                return;
            }
            */
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        const items = data.items || [];

        // Update count
        countElement.textContent = `${items.length} item${items.length !== 1 ? 's' : ''}`;

        // Render items
        if (items.length === 0) {
            itemsContainer.innerHTML = '<div class="empty-state">No items yet. Add your first item!</div>';
        } else {
            itemsContainer.innerHTML = renderGroupedItems(items);
            attachItemEventListeners();
        }

    } catch (error) {
        console.error('Error loading items:', error);
        itemsContainer.innerHTML = `<div class="error-message">Failed to load items. Please refresh the page.</div>`;
    }
}

/**
 * Fetch with authentication header
 */
async function fetchWithAuth(url, options = {}) {
    // BYPASS MODE: Authentication header disabled
    // Uncomment the code below to re-enable Cognito authentication
    /*
    const token = getIdToken();

    if (!token || !isAuthenticated()) {
        logout();
        return;
    }

    const headers = {
        ...options.headers,
        'Authorization': token
    };

    return fetch(url, {
        ...options,
        headers
    });
    */

    // Bypass mode: Make request without Authorization header
    return fetch(url, options);
}

/**
 * Group items by user, then by category, and render them
 */
function renderGroupedItems(items) {
    // BYPASS MODE: Group by user first, then by category
    // For single-user mode, remove the user grouping

    // Group by userId first
    const groupedByUser = {};

    items.forEach(item => {
        const userId = item.userId || 'Unknown User';
        if (!groupedByUser[userId]) {
            groupedByUser[userId] = [];
        }
        groupedByUser[userId].push(item);
    });

    // Sort users alphabetically
    const sortedUsers = Object.keys(groupedByUser).sort();

    let html = '';

    sortedUsers.forEach(userId => {
        const userItems = groupedByUser[userId];

        // Group items by category for this user
        const grouped = {};
        userItems.forEach(item => {
            const category = item.category || 'Uncategorized';
            if (!grouped[category]) {
                grouped[category] = [];
            }
            grouped[category].push(item);
        });

        const sortedCategories = Object.keys(grouped).sort((a, b) => {
            if (a === 'Uncategorized') return 1;
            if (b === 'Uncategorized') return -1;
            return a.localeCompare(b);
        });

        // Add user header
        html += `<div class="user-group">`;
        html += `<div class="user-header">${escapeHtml(userId)}'s List (${userItems.length} items)</div>`;

        // Add categories for this user
        sortedCategories.forEach(category => {
            const categoryItems = grouped[category].sort((a, b) => {
                if (a.bought === b.bought) return 0;
                return a.bought ? 1 : -1;
            });

            html += `<div class="category-group">`;
            html += `<div class="category-header">${escapeHtml(category)}</div>`;
            html += categoryItems.map(item => createItemHTML(item)).join('');
            html += `</div>`;
        });

        html += `</div>`; // Close user-group
    });

    return html;
}

/**
 * Create HTML for a shopping item
 */
function createItemHTML(item) {
    const boughtClass = item.bought ? 'bought' : '';
    const checkedAttr = item.bought ? 'checked' : '';

    return `
        <div class="shopping-item ${boughtClass}" data-item-id="${item.itemId}">
            <input
                type="checkbox"
                class="item-checkbox"
                ${checkedAttr}
                data-item-id="${item.itemId}"
            >
            <div class="item-details">
                <div class="item-name">${escapeHtml(item.itemName)}</div>
                <div class="item-meta">
                    <span class="item-quantity">Qty: ${item.quantity}</span>
                </div>
            </div>
            <button
                class="btn-delete"
                data-item-id="${item.itemId}"
            >
                Delete
            </button>
        </div>
    `;
}

/**
 * Attach event listeners to checkboxes and delete buttons
 */
function attachItemEventListeners() {
    const itemsContainer = document.getElementById('items-list');

    const checkboxes = itemsContainer.querySelectorAll('.item-checkbox');
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', handleCheckboxChange);
    });

    const deleteButtons = itemsContainer.querySelectorAll('.btn-delete');
    deleteButtons.forEach(button => {
        button.addEventListener('click', handleDeleteClick);
    });
}

/**
 * Handle checkbox change (mark item as bought/unbought)
 */
async function handleCheckboxChange(event) {
    const checkbox = event.target;
    const itemId = checkbox.dataset.itemId;
    const bought = checkbox.checked;
    const userId = getUserId();

    try {
        const response = await fetchWithAuth(`${API_BASE_URL}/items/${userId}/${itemId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ bought })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const itemElement = checkbox.closest('.shopping-item');
        if (bought) {
            itemElement.classList.add('bought');
        } else {
            itemElement.classList.remove('bought');
        }

    } catch (error) {
        console.error('Error updating item:', error);
        checkbox.checked = !bought;
        alert('Failed to update item. Please try again.');
    }
}

/**
 * Handle delete button click
 */
async function handleDeleteClick(event) {
    const button = event.target;
    const itemId = button.dataset.itemId;
    const userId = getUserId();

    if (!confirm('Are you sure you want to delete this item?')) {
        return;
    }

    try {
        const response = await fetchWithAuth(`${API_BASE_URL}/items/${userId}/${itemId}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        await loadUserItems();

    } catch (error) {
        console.error('Error deleting item:', error);
        alert('Failed to delete item. Please try again.');
    }
}

/**
 * Setup form submission handler
 */
function setupFormHandler() {
    const form = document.getElementById('add-item-form');

    form.addEventListener('submit', async (event) => {
        event.preventDefault();

        const itemName = document.getElementById('item-name').value.trim();
        const quantity = parseInt(document.getElementById('quantity').value);
        const category = document.getElementById('category').value.trim();

        if (!itemName || quantity < 1) {
            alert('Please enter a valid item name and quantity.');
            return;
        }

        try {
            const payload = {
                itemName,
                quantity
            };

            if (category) {
                payload.category = category;
            }

            const response = await fetchWithAuth(`${API_BASE_URL}/items`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            form.reset();
            document.getElementById('quantity').value = '1';

            await loadUserItems();

        } catch (error) {
            console.error('Error adding item:', error);
            alert('Failed to add item. Please try again.');
        }
    });
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Setup email button handler
 */
function setupEmailButtonHandler() {
    const button = document.getElementById('email-btn');

    button.addEventListener('click', async () => {
        const itemsContainer = document.getElementById('items-list');
        const userId = getUserId();

        const existingMessages = itemsContainer.parentElement.querySelectorAll('.success-message, .error-message');
        existingMessages.forEach(msg => msg.remove());

        button.disabled = true;
        button.textContent = '📧 Sending...';

        try {
            const response = await fetchWithAuth(`${API_BASE_URL}/email/${userId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            const successDiv = document.createElement('div');
            successDiv.className = 'success-message';
            successDiv.textContent = `✓ Email sent successfully! ${data.itemCount || 0} items included.`;
            itemsContainer.parentElement.insertBefore(successDiv, itemsContainer);

            setTimeout(() => {
                successDiv.remove();
            }, 5000);

        } catch (error) {
            console.error('Error sending email:', error);

            const errorDiv = document.createElement('div');
            errorDiv.className = 'error-message';
            errorDiv.textContent = '✗ Failed to send email. Please try again.';
            itemsContainer.parentElement.insertBefore(errorDiv, itemsContainer);

            setTimeout(() => {
                errorDiv.remove();
            }, 5000);

        } finally {
            button.disabled = false;
            button.textContent = '📧 Email My List';
        }
    });
}

/**
 * Setup categorize button handler
 */
function setupCategorizeButtonHandler() {
    const button = document.getElementById('categorize-btn');

    button.addEventListener('click', async () => {
        const itemsContainer = document.getElementById('items-list');
        const userId = getUserId();

        const existingMessages = itemsContainer.parentElement.querySelectorAll('.success-message, .error-message');
        existingMessages.forEach(msg => msg.remove());

        button.disabled = true;
        button.textContent = '🤖 Categorizing...';

        try {
            const response = await fetchWithAuth(`${API_BASE_URL}/categorize/${userId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            let message = `✓ Categorized ${data.categorizedCount || 0} items using AI!`;

            if (data.spellingCorrectedCount > 0) {
                const corrections = data.spellingCorrections || [];
                const correctionsList = corrections
                    .map(c => `'${c.original}' → '${c.corrected}'`)
                    .join(', ');
                message += ` Corrected spelling for: ${correctionsList}`;
            }

            const successDiv = document.createElement('div');
            successDiv.className = 'success-message';
            successDiv.textContent = message;
            itemsContainer.parentElement.insertBefore(successDiv, itemsContainer);

            await loadUserItems();

            setTimeout(() => {
                successDiv.remove();
            }, 8000);

        } catch (error) {
            console.error('Error categorizing items:', error);

            const errorDiv = document.createElement('div');
            errorDiv.className = 'error-message';
            errorDiv.textContent = '✗ Failed to categorize items. Please try again.';
            itemsContainer.parentElement.insertBefore(errorDiv, itemsContainer);

            setTimeout(() => {
                errorDiv.remove();
            }, 5000);

        } finally {
            button.disabled = false;
            button.textContent = '🤖 Auto-Categorize Items';
        }
    });
}

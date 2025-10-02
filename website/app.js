// API Configuration
const API_BASE_URL = 'https://01mmfw29n0.execute-api.eu-west-1.amazonaws.com/dev';

// User IDs
const USERS = {
    GIANLUCA: 'Gianluca',
    NICOLE: 'Nicole'
};

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Load both lists
    loadUserItems(USERS.GIANLUCA);
    loadUserItems(USERS.NICOLE);

    // Setup form handlers
    setupFormHandler(USERS.GIANLUCA);
    setupFormHandler(USERS.NICOLE);

    // Setup email button handlers
    setupEmailButtonHandler(USERS.GIANLUCA);
    setupEmailButtonHandler(USERS.NICOLE);

    // Setup categorize button handlers
    setupCategorizeButtonHandler(USERS.GIANLUCA);
    setupCategorizeButtonHandler(USERS.NICOLE);
});

/**
 * Load items for a specific user
 */
async function loadUserItems(userId) {
    const itemsContainer = document.getElementById(`${userId.toLowerCase()}-items`);
    const countElement = document.getElementById(`${userId.toLowerCase()}-count`);

    try {
        itemsContainer.innerHTML = '<div class="loading">Loading items...</div>';

        const response = await fetch(`${API_BASE_URL}/items/${userId}?bought=all`);

        if (!response.ok) {
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
            itemsContainer.innerHTML = renderGroupedItems(items, userId);

            // Attach event listeners
            attachItemEventListeners(userId);
        }

    } catch (error) {
        console.error('Error loading items:', error);
        itemsContainer.innerHTML = `<div class="error-message">Failed to load items. Please refresh the page.</div>`;
    }
}

/**
 * Group items by category and render them
 */
function renderGroupedItems(items, userId) {
    // Group items by category
    const grouped = {};

    items.forEach(item => {
        const category = item.category || 'Uncategorized';
        if (!grouped[category]) {
            grouped[category] = [];
        }
        grouped[category].push(item);
    });

    // Sort categories alphabetically, with Uncategorized last
    const sortedCategories = Object.keys(grouped).sort((a, b) => {
        if (a === 'Uncategorized') return 1;
        if (b === 'Uncategorized') return -1;
        return a.localeCompare(b);
    });

    // Build HTML for each category
    let html = '';
    sortedCategories.forEach(category => {
        // Sort items within category: unbought first, then bought
        const categoryItems = grouped[category].sort((a, b) => {
            if (a.bought === b.bought) return 0;
            return a.bought ? 1 : -1;
        });

        html += `<div class="category-group">`;
        html += `<div class="category-header">${escapeHtml(category)}</div>`;
        html += categoryItems.map(item => createItemHTML(item, userId)).join('');
        html += `</div>`;
    });

    return html;
}

/**
 * Create HTML for a shopping item
 */
function createItemHTML(item, userId) {
    const boughtClass = item.bought ? 'bought' : '';
    const checkedAttr = item.bought ? 'checked' : '';

    return `
        <div class="shopping-item ${boughtClass}" data-item-id="${item.itemId}">
            <input
                type="checkbox"
                class="item-checkbox"
                ${checkedAttr}
                data-user-id="${userId}"
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
                data-user-id="${userId}"
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
function attachItemEventListeners(userId) {
    const itemsContainer = document.getElementById(`${userId.toLowerCase()}-items`);

    // Checkbox listeners
    const checkboxes = itemsContainer.querySelectorAll('.item-checkbox');
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', handleCheckboxChange);
    });

    // Delete button listeners
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
    const userId = checkbox.dataset.userId;
    const itemId = checkbox.dataset.itemId;
    const bought = checkbox.checked;

    try {
        const response = await fetch(`${API_BASE_URL}/items/${userId}/${itemId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ bought })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        // Update UI
        const itemElement = checkbox.closest('.shopping-item');
        if (bought) {
            itemElement.classList.add('bought');
        } else {
            itemElement.classList.remove('bought');
        }

    } catch (error) {
        console.error('Error updating item:', error);
        // Revert checkbox state
        checkbox.checked = !bought;
        alert('Failed to update item. Please try again.');
    }
}

/**
 * Handle delete button click
 */
async function handleDeleteClick(event) {
    const button = event.target;
    const userId = button.dataset.userId;
    const itemId = button.dataset.itemId;

    if (!confirm('Are you sure you want to delete this item?')) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/items/${userId}/${itemId}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        // Reload the list
        await loadUserItems(userId);

    } catch (error) {
        console.error('Error deleting item:', error);
        alert('Failed to delete item. Please try again.');
    }
}

/**
 * Setup form submission handler
 */
function setupFormHandler(userId) {
    const formId = `${userId.toLowerCase()}-form`;
    const form = document.getElementById(formId);

    form.addEventListener('submit', async (event) => {
        event.preventDefault();

        const itemName = document.getElementById(`${userId.toLowerCase()}-item-name`).value.trim();
        const quantity = parseInt(document.getElementById(`${userId.toLowerCase()}-quantity`).value);
        const category = document.getElementById(`${userId.toLowerCase()}-category`).value.trim();

        if (!itemName || quantity < 1) {
            alert('Please enter a valid item name and quantity.');
            return;
        }

        try {
            const payload = {
                userId,
                itemName,
                quantity
            };

            if (category) {
                payload.category = category;
            }

            const response = await fetch(`${API_BASE_URL}/items`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            // Clear form
            form.reset();
            document.getElementById(`${userId.toLowerCase()}-quantity`).value = '1';

            // Reload the list
            await loadUserItems(userId);

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
function setupEmailButtonHandler(userId) {
    const buttonId = `${userId.toLowerCase()}-email-btn`;
    const button = document.getElementById(buttonId);

    button.addEventListener('click', async () => {
        const itemsContainer = document.getElementById(`${userId.toLowerCase()}-items`);

        // Remove any existing messages
        const existingMessages = itemsContainer.parentElement.querySelectorAll('.success-message, .error-message');
        existingMessages.forEach(msg => msg.remove());

        // Disable button
        button.disabled = true;
        button.textContent = '📧 Sending...';

        try {
            const response = await fetch(`${API_BASE_URL}/email/${userId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            // Show success message
            const successDiv = document.createElement('div');
            successDiv.className = 'success-message';
            successDiv.textContent = `✓ Email sent successfully! ${data.itemCount || 0} items included.`;
            itemsContainer.parentElement.insertBefore(successDiv, itemsContainer);

            // Remove message after 5 seconds
            setTimeout(() => {
                successDiv.remove();
            }, 5000);

        } catch (error) {
            console.error('Error sending email:', error);

            // Show error message
            const errorDiv = document.createElement('div');
            errorDiv.className = 'error-message';
            errorDiv.textContent = '✗ Failed to send email. Please try again.';
            itemsContainer.parentElement.insertBefore(errorDiv, itemsContainer);

            // Remove message after 5 seconds
            setTimeout(() => {
                errorDiv.remove();
            }, 5000);

        } finally {
            // Re-enable button
            button.disabled = false;
            button.textContent = '📧 Email My List';
        }
    });
}

/**
 * Setup categorize button handler
 */
function setupCategorizeButtonHandler(userId) {
    const buttonId = `${userId.toLowerCase()}-categorize-btn`;
    const button = document.getElementById(buttonId);

    button.addEventListener('click', async () => {
        const itemsContainer = document.getElementById(`${userId.toLowerCase()}-items`);

        // Remove any existing messages
        const existingMessages = itemsContainer.parentElement.querySelectorAll('.success-message, .error-message');
        existingMessages.forEach(msg => msg.remove());

        // Disable button
        button.disabled = true;
        button.textContent = '🤖 Categorizing...';

        try {
            const response = await fetch(`${API_BASE_URL}/categorize/${userId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            // Build success message
            let message = `✓ Categorized ${data.categorizedCount || 0} items using AI!`;

            // Add spelling correction info if any
            if (data.spellingCorrectedCount > 0) {
                const corrections = data.spellingCorrections || [];
                const correctionsList = corrections
                    .map(c => `'${c.original}' → '${c.corrected}'`)
                    .join(', ');
                message += ` Corrected spelling for: ${correctionsList}`;
            }

            // Show success message
            const successDiv = document.createElement('div');
            successDiv.className = 'success-message';
            successDiv.textContent = message;
            itemsContainer.parentElement.insertBefore(successDiv, itemsContainer);

            // Reload the list to show new categories
            await loadUserItems(userId);

            // Remove message after 8 seconds (longer for spelling corrections)
            setTimeout(() => {
                successDiv.remove();
            }, 8000);

        } catch (error) {
            console.error('Error categorizing items:', error);

            // Show error message
            const errorDiv = document.createElement('div');
            errorDiv.className = 'error-message';
            errorDiv.textContent = '✗ Failed to categorize items. Please try again.';
            itemsContainer.parentElement.insertBefore(errorDiv, itemsContainer);

            // Remove message after 5 seconds
            setTimeout(() => {
                errorDiv.remove();
            }, 5000);

        } finally {
            // Re-enable button
            button.disabled = false;
            button.textContent = '🤖 Auto-Categorize Items';
        }
    });
}

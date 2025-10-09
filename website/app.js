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
    setupAIConfigHandler();

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

        // Filter to only Gianluca and Nicole for count
        const allowedUsers = ['Gianluca', 'Nicole'];
        const filteredItems = items.filter(item => allowedUsers.includes(item.userId));

        // Update count
        countElement.textContent = `${filteredItems.length} item${filteredItems.length !== 1 ? 's' : ''}`;

        // Render items
        if (filteredItems.length === 0) {
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
    // Only show Gianluca and Nicole's lists

    // Filter to only include Gianluca and Nicole
    const allowedUsers = ['Gianluca', 'Nicole'];
    const filteredItems = items.filter(item => allowedUsers.includes(item.userId));

    // Group by userId first
    const groupedByUser = {};

    filteredItems.forEach(item => {
        const userId = item.userId || 'Unknown User';
        if (!groupedByUser[userId]) {
            groupedByUser[userId] = [];
        }
        groupedByUser[userId].push(item);
    });

    // Sort users: Gianluca first, then Nicole
    const sortedUsers = allowedUsers.filter(user => groupedByUser[user]);

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
        <div class="shopping-item ${boughtClass}"
             data-item-id="${item.itemId}"
             data-user-id="${escapeHtml(item.userId)}"
             data-item-name="${escapeHtml(item.itemName)}"
             data-quantity="${item.quantity}">
            <input
                type="checkbox"
                class="item-checkbox"
                ${checkedAttr}
                data-item-id="${item.itemId}"
            >
            <div class="item-details">
                <div class="item-name" data-item-id="${item.itemId}" title="Click to edit">${escapeHtml(item.itemName)}</div>
                <div class="item-meta">
                    <span class="item-quantity" data-item-id="${item.itemId}" title="Click to edit">Qty: ${item.quantity}</span>
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
 * Attach event listeners to checkboxes, delete buttons, and editable fields
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

    // Add edit listeners for item names
    const itemNames = itemsContainer.querySelectorAll('.item-name');
    itemNames.forEach(nameElement => {
        nameElement.addEventListener('click', handleItemNameEdit);
    });

    // Add edit listeners for quantities
    const quantities = itemsContainer.querySelectorAll('.item-quantity');
    quantities.forEach(qtyElement => {
        qtyElement.addEventListener('click', handleQuantityEdit);
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

        const selectedUser = document.getElementById('user-select').value;
        const itemName = document.getElementById('item-name').value.trim();
        const quantity = parseInt(document.getElementById('quantity').value);

        if (!itemName || quantity < 1) {
            alert('Please enter a valid item name and quantity.');
            return;
        }

        // Show loading state
        const submitButton = form.querySelector('button[type="submit"]');
        const originalButtonText = submitButton.textContent;
        submitButton.disabled = true;
        submitButton.textContent = '🤖 AI Processing...';

        try {
            // Get custom AI prompt and context from localStorage
            const customPrompt = localStorage.getItem('customAIPrompt') || '';
            const contextItems = JSON.parse(localStorage.getItem('contextItems') || '[]');
            const useUKEnglish = localStorage.getItem('useUKEnglish') !== 'false';
            const strictCategories = localStorage.getItem('strictCategories') !== 'false';

            const payload = {
                userId: selectedUser,
                itemName,
                quantity,
                customPrompt,        // Send custom prompt to Lambda
                contextItems,        // Send household context
                useUKEnglish,        // Send UK English preference
                strictCategories     // Send strict categories preference
            };

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

            const data = await response.json();

            // Show AI processing feedback
            if (data.aiProcessing) {
                const ai = data.aiProcessing;
                if (ai.wasSpellCorrected) {
                    showNotification(
                        `✓ Added "${ai.correctedName}" (corrected from "${ai.originalName}") to ${ai.category}`,
                        'success',
                        5000
                    );
                } else {
                    showNotification(
                        `✓ Added "${ai.correctedName}" to ${ai.category}`,
                        'success',
                        3000
                    );
                }
            }

            form.reset();
            document.getElementById('quantity').value = '1';
            // Reset user selector to default (Gianluca)
            document.getElementById('user-select').value = 'Gianluca';

            await loadUserItems();

        } catch (error) {
            console.error('Error adding item:', error);
            showNotification('✗ Failed to add item. Please try again.', 'error', 5000);
        } finally {
            submitButton.disabled = false;
            submitButton.textContent = originalButtonText;
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
 * Setup AI configuration handler
 */
function setupAIConfigHandler() {
    const button = document.getElementById('configure-ai-btn');
    const modal = document.getElementById('ai-config-modal');
    const closeBtn = document.getElementById('modal-close');
    const textarea = document.getElementById('custom-prompt');
    const charCount = document.getElementById('char-count');
    const saveBtn = document.getElementById('save-prompt-btn');
    const resetBtn = document.getElementById('reset-prompt-btn');

    // Load saved prompt on page load
    const savedPrompt = localStorage.getItem('customAIPrompt') || '';
    textarea.value = savedPrompt;
    updateCharCount();

    // Open modal
    button.addEventListener('click', () => {
        modal.style.display = 'flex';
    });

    // Close modal
    closeBtn.addEventListener('click', () => {
        modal.style.display = 'none';
    });

    // Close on outside click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.style.display = 'none';
        }
    });

    // Character count
    textarea.addEventListener('input', updateCharCount);

    function updateCharCount() {
        const count = textarea.value.length;
        charCount.textContent = `${count} / 500 characters`;
        if (count > 500) {
            charCount.style.color = '#ff4757';
            textarea.value = textarea.value.substring(0, 500);
        } else {
            charCount.style.color = '#666';
        }
    }

    // Save prompt
    saveBtn.addEventListener('click', () => {
        const prompt = textarea.value.trim();
        localStorage.setItem('customAIPrompt', prompt);
        showNotification('✓ AI instructions saved successfully!', 'success', 3000);
        modal.style.display = 'none';
    });

    // Reset prompt
    resetBtn.addEventListener('click', () => {
        if (confirm('Reset AI instructions to default? This will remove your custom instructions.')) {
            localStorage.removeItem('customAIPrompt');
            textarea.value = '';
            updateCharCount();
            showNotification('✓ AI instructions reset to default', 'success', 3000);
        }
    });
}

/**
 * Show notification message
 */
function showNotification(message, type = 'success', duration = 3000) {
    const itemsContainer = document.getElementById('items-list');

    // Remove existing notifications
    const existingNotifications = itemsContainer.parentElement.querySelectorAll('.success-message, .error-message');
    existingNotifications.forEach(msg => msg.remove());

    const div = document.createElement('div');
    div.className = type === 'success' ? 'success-message' : 'error-message';
    div.textContent = message;
    itemsContainer.parentElement.insertBefore(div, itemsContainer);

    setTimeout(() => {
        div.remove();
    }, duration);
}

/**
 * Handle item name editing (inline edit)
 */
function handleItemNameEdit(event) {
    const nameElement = event.target;
    const itemElement = nameElement.closest('.shopping-item');
    const itemId = nameElement.dataset.itemId;
    const userId = itemElement.dataset.userId;
    const currentName = itemElement.dataset.itemName;

    // Create input element
    const input = document.createElement('input');
    input.type = 'text';
    input.className = 'item-name-input';
    input.value = currentName;

    // Replace name with input
    nameElement.replaceWith(input);
    input.focus();
    input.select();

    // Handle save on blur or enter
    const saveEdit = async () => {
        const newName = input.value.trim();

        if (!newName) {
            // Restore original if empty
            input.replaceWith(nameElement);
            return;
        }

        if (newName === currentName) {
            // No change, just restore
            input.replaceWith(nameElement);
            return;
        }

        // Update via API
        try {
            const response = await fetchWithAuth(`${API_BASE_URL}/items/${userId}/${itemId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ itemName: newName })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            // Reload items to show updated name
            await loadUserItems();
            showNotification(`✓ Updated item name to "${newName}"`, 'success', 3000);

        } catch (error) {
            console.error('Error updating item name:', error);
            input.replaceWith(nameElement);
            showNotification('✗ Failed to update item name', 'error', 3000);
        }
    };

    input.addEventListener('blur', saveEdit);
    input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            input.blur();
        }
    });
}

/**
 * Handle quantity editing (inline edit)
 */
function handleQuantityEdit(event) {
    const qtyElement = event.target;
    const itemElement = qtyElement.closest('.shopping-item');
    const itemId = qtyElement.dataset.itemId;
    const userId = itemElement.dataset.userId;
    const currentQty = parseInt(itemElement.dataset.quantity);

    // Create input element
    const input = document.createElement('input');
    input.type = 'number';
    input.className = 'item-quantity-input';
    input.value = currentQty;
    input.min = '1';

    // Replace quantity with input
    qtyElement.replaceWith(input);
    input.focus();
    input.select();

    // Handle save on blur or enter
    const saveEdit = async () => {
        const newQty = parseInt(input.value);

        if (!newQty || newQty < 1) {
            // Restore original if invalid
            input.replaceWith(qtyElement);
            return;
        }

        if (newQty === currentQty) {
            // No change, just restore
            input.replaceWith(qtyElement);
            return;
        }

        // Update via API
        try {
            const response = await fetchWithAuth(`${API_BASE_URL}/items/${userId}/${itemId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ quantity: newQty })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            // Reload items to show updated quantity
            await loadUserItems();
            showNotification(`✓ Updated quantity to ${newQty}`, 'success', 3000);

        } catch (error) {
            console.error('Error updating quantity:', error);
            input.replaceWith(qtyElement);
            showNotification('✗ Failed to update quantity', 'error', 3000);
        }
    };

    input.addEventListener('blur', saveEdit);
    input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            input.blur();
        }
    });
}

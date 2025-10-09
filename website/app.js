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
    setupRecalculatePricesHandler();
    setupAIConfigHandler();
    setupUserDropdownHandler();

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

        // Update count with basket emoji
        countElement.textContent = `🛒 ${filteredItems.length}`;

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

// Global variable to track which user is selected in the dropdown
let selectedUserForDisplay = null;

/**
 * Set the selected user for display (from dropdown)
 */
function setSelectedUserForDisplay(userId) {
    selectedUserForDisplay = userId;
}

/**
 * Get the selected user for display
 */
function getSelectedUserForDisplay() {
    return selectedUserForDisplay;
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

    // Get which user is selected in the dropdown
    const selectedUser = getSelectedUserForDisplay();

    // Sort users: Put selected user first, otherwise Gianluca first, then Nicole
    let sortedUsers = allowedUsers.filter(user => groupedByUser[user]);

    if (selectedUser) {
        // Move the selected user to the front
        sortedUsers = sortedUsers.sort((a, b) => {
            if (a === selectedUser) return -1;
            if (b === selectedUser) return 1;
            return allowedUsers.indexOf(a) - allowedUsers.indexOf(b);
        });
    }

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

        // Add user header with basket emoji right-aligned and person emoji
        const userEmoji = userId === 'Gianluca' ? '👨' : '👩';
        const userColorClass = userId === 'Gianluca' ? 'user-gianluca' : 'user-nicole';

        // Calculate total price for this user
        const totalPrice = userItems.reduce((sum, item) => {
            const price = (item.estimatedPrice || 0) * item.quantity;
            return sum + price;
        }, 0);

        html += `<div class="user-group ${userColorClass}" data-user-id="${escapeHtml(userId)}">`;
        html += `<div class="user-header">`;
        html += `<span class="user-header-name">${userEmoji} ${escapeHtml(userId)}'s List</span>`;
        html += `<span class="user-header-count">🛒 ${userItems.length}</span>`;
        html += `</div>`;

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

        // Add total price footer for this user
        html += `<div class="user-total">`;
        html += `<span class="total-label">Estimated Total:</span>`;
        html += `<span class="total-price">£${totalPrice.toFixed(2)}</span>`;
        html += `</div>`;

        html += `</div>`; // Close user-group
    });

    return html;
}

/**
 * Create HTML for a shopping item
 */
function createItemHTML(item) {
    const boughtClass = item.bought ? 'bought' : '';
    const emoji = item.emoji || '🛒';  // Default to shopping cart if no emoji
    const estimatedPrice = item.estimatedPrice || 0;
    const totalPrice = estimatedPrice * item.quantity;

    return `
        <div class="shopping-item ${boughtClass}"
             data-item-id="${item.itemId}"
             data-user-id="${escapeHtml(item.userId)}"
             data-item-name="${escapeHtml(item.itemName)}"
             data-quantity="${item.quantity}">
            <input type="checkbox"
                   class="item-checkbox"
                   data-item-id="${item.itemId}"
                   ${item.bought ? 'checked' : ''}>
            <div class="item-details">
                <span class="item-emoji">${emoji}</span>
                <span class="item-name">${escapeHtml(item.itemName)}</span>
                <span class="item-quantity">Qty: ${item.quantity}</span>
                <span class="item-price">£${totalPrice.toFixed(2)}</span>
            </div>
            <button class="btn-edit" data-item-id="${item.itemId}" title="Edit item">✏️</button>
            <button class="btn-delete" data-item-id="${item.itemId}" title="Delete item">🗑️</button>
        </div>
    `;
}

/**
 * Attach event listeners to checkboxes, delete and edit buttons
 */
function attachItemEventListeners() {
    const itemsContainer = document.getElementById('items-list');

    // Checkbox listeners
    const checkboxes = itemsContainer.querySelectorAll('.item-checkbox');
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', handleCheckboxChange);
    });

    const deleteButtons = itemsContainer.querySelectorAll('.btn-delete');
    deleteButtons.forEach(button => {
        button.addEventListener('click', handleDeleteClick);
    });

    // Add edit listeners for edit buttons
    const editButtons = itemsContainer.querySelectorAll('.btn-edit');
    editButtons.forEach(button => {
        button.addEventListener('click', handleItemEdit);
    });
}

/**
 * Handle checkbox change (mark as bought/unbought)
 */
async function handleCheckboxChange(event) {
    const checkbox = event.target;
    const itemElement = checkbox.closest('.shopping-item');
    const itemId = checkbox.dataset.itemId;
    const userId = itemElement.dataset.userId;
    const bought = checkbox.checked;

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

        // Update UI
        if (bought) {
            itemElement.classList.add('bought');
        } else {
            itemElement.classList.remove('bought');
        }

    } catch (error) {
        console.error('Error updating item:', error);
        checkbox.checked = !bought; // Revert checkbox
        showNotification('✗ Failed to update item', 'error', 3000);
    }
}

/**
 * Handle item edit - edit both name and quantity
 */
function handleItemEdit(event) {
    const button = event.target;
    const itemElement = button.closest('.shopping-item');
    const itemId = button.dataset.itemId;
    const userId = itemElement.dataset.userId;
    const currentName = itemElement.dataset.itemName;
    const currentQty = parseInt(itemElement.dataset.quantity);

    const itemDetails = itemElement.querySelector('.item-details');

    // Create edit form
    const editForm = document.createElement('div');
    editForm.className = 'item-edit-form';
    editForm.innerHTML = `
        <input type="text" class="edit-name-input" value="${escapeHtml(currentName)}" placeholder="Item name">
        <input type="number" class="edit-qty-input" value="${currentQty}" min="1" placeholder="Qty">
        <button class="btn-save-edit">✓</button>
        <button class="btn-cancel-edit">✕</button>
    `;

    // Replace item details with edit form
    itemDetails.replaceWith(editForm);
    button.style.display = 'none';

    const nameInput = editForm.querySelector('.edit-name-input');
    const qtyInput = editForm.querySelector('.edit-qty-input');
    const saveBtn = editForm.querySelector('.btn-save-edit');
    const cancelBtn = editForm.querySelector('.btn-cancel-edit');

    nameInput.focus();
    nameInput.select();

    // Handle save
    const saveEdit = async () => {
        const newName = nameInput.value.trim();
        const newQty = parseInt(qtyInput.value);

        if (!newName || !newQty || newQty < 1) {
            showNotification('Please enter valid item name and quantity', 'error', 3000);
            return;
        }

        if (newName === currentName && newQty === currentQty) {
            // No changes, just restore
            await loadUserItems();
            return;
        }

        try {
            const updates = {};
            if (newName !== currentName) updates.itemName = newName;
            if (newQty !== currentQty) updates.quantity = newQty;

            const response = await fetchWithAuth(`${API_BASE_URL}/items/${userId}/${itemId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(updates)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            await loadUserItems();
            showNotification('✓ Item updated', 'success', 2000);

        } catch (error) {
            console.error('Error updating item:', error);
            showNotification('✗ Failed to update item', 'error', 3000);
            await loadUserItems();
        }
    };

    // Handle cancel
    const cancelEdit = () => {
        loadUserItems();
    };

    saveBtn.addEventListener('click', saveEdit);
    cancelBtn.addEventListener('click', cancelEdit);

    nameInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            saveEdit();
        } else if (e.key === 'Escape') {
            cancelEdit();
        }
    });

    qtyInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            saveEdit();
        } else if (e.key === 'Escape') {
            cancelEdit();
        }
    });
}

/**
 * Handle delete button click
 */
async function handleDeleteClick(event) {
    const button = event.target;
    const itemElement = button.closest('.shopping-item');
    const itemId = button.dataset.itemId;
    const userId = itemElement.dataset.userId;

    try {
        const response = await fetchWithAuth(`${API_BASE_URL}/items/${userId}/${itemId}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        await loadUserItems();
        showNotification('✓ Item deleted', 'success', 2000);

    } catch (error) {
        console.error('Error deleting item:', error);
        showNotification('✗ Failed to delete item. Please try again.', 'error', 3000);
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
 * Setup recalculate prices button handler
 */
function setupRecalculatePricesHandler() {
    const button = document.getElementById('recalculate-prices-btn');

    button.addEventListener('click', async () => {
        if (!confirm('Recalculate prices for all items using current Sainsbury\'s estimates? This will update ALL items in the database.')) {
            return;
        }

        button.disabled = true;
        button.textContent = '🤖 AI Recalculating...';

        try {
            const response = await fetchWithAuth(`${API_BASE_URL}/prices/recalculate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            // Reload items to show new prices
            await loadUserItems();

            showNotification(
                `✓ Price recalculation complete! Updated ${data.updatedCount} items.`,
                'success',
                5000
            );

        } catch (error) {
            console.error('Error recalculating prices:', error);
            showNotification('✗ Failed to recalculate prices. Please try again.', 'error', 5000);

        } finally {
            button.disabled = false;
            button.textContent = '💷 Recalculate All Prices';
        }
    });
}

/**
 * Setup user dropdown change handler to reorder lists
 */
function setupUserDropdownHandler() {
    const userSelect = document.getElementById('user-select');

    // Set initial selected user
    setSelectedUserForDisplay(userSelect.value);

    // Listen for changes
    userSelect.addEventListener('change', () => {
        const selectedUser = userSelect.value;
        setSelectedUserForDisplay(selectedUser);
        loadUserItems();  // Re-render with new order
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

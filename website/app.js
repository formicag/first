// API Configuration
const API_BASE_URL = 'https://01mmfw29n0.execute-api.eu-west-1.amazonaws.com/dev';

// Initialize app on page load
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('user-list-title').textContent = 'Shopping Lists';

    // Load items
    loadUserItems();

    // Setup form handlers
    setupFormHandler();
    setupStoreShopHandler();
    setupEmailButtonHandler();
    setupRecalculatePricesHandler();
    setupRecategorizeItemsHandler();
    setupAIConfigHandler();
    setupUserDropdownHandler();
});

/**
 * Load items for all users
 */
async function loadUserItems() {
    const itemsContainer = document.getElementById('items-list');
    const countElement = document.getElementById('item-count');

    try {
        itemsContainer.innerHTML = '<div class="loading">Loading items...</div>';

        // Load all items from all users
        const response = await fetch(`${API_BASE_URL}/items/TestUser?bought=all`);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        const items = data.items || [];

        // Filter to only Gianluca and Nicole for count
        const allowedUsers = ['Gianluca', 'Nicole'];
        const filteredItems = items.filter(item => allowedUsers.includes(item.userId));

        // Calculate combined total for both users
        const combinedTotal = filteredItems.reduce((sum, item) => {
            return sum + ((item.estimatedPrice || 0) * item.quantity);
        }, 0);

        // Update count with combined total and basket emoji
        countElement.innerHTML = `Est. Tot: £${combinedTotal.toFixed(2)} | 🛒 ${filteredItems.length}`;

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

        // Separate items: regular items (sorted by store layout) vs saveForNext items
        const regularItems = userItems.filter(item => !item.saveForNext);
        const savedForNextItems = userItems.filter(item => item.saveForNext);

        // Add user header with basket emoji right-aligned and person emoji
        const userEmoji = userId === 'Gianluca' ? '👨' : '👩';
        const userColorClass = userId === 'Gianluca' ? 'user-gianluca' : 'user-nicole';
        const displayName = userId === 'Gianluca' ? 'Luca' : userId;

        // Calculate total price for this user
        const totalPrice = userItems.reduce((sum, item) => {
            const price = (item.estimatedPrice || 0) * item.quantity;
            return sum + price;
        }, 0);

        html += `<div class="user-group ${userColorClass}" data-user-id="${escapeHtml(userId)}">`;
        html += `<div class="user-header">`;
        html += `<span class="user-header-name">${userEmoji} ${escapeHtml(displayName)}'s List</span>`;
        html += `<span class="user-header-total">Est. Tot: £${totalPrice.toFixed(2)}</span>`;
        html += `<span class="user-header-count">🛒 ${userItems.length}</span>`;
        html += `</div>`;

        // First, add regular items (sorted by store layout from API)
        regularItems.forEach(item => {
            html += createItemHTML(item);
        });

        // Then, add saved-for-next items at the bottom
        if (savedForNextItems.length > 0) {
            savedForNextItems.forEach(item => {
                html += createItemHTML(item);
            });
        }

        html += `</div>`; // Close user-group
    });

    return html;
}

/**
 * Create HTML for a shopping item
 */
function createItemHTML(item) {
    const boughtClass = item.bought ? 'bought' : '';
    const saveForNextClass = item.saveForNext ? 'save-for-next' : '';
    const estimatedPrice = item.estimatedPrice || 0;
    const totalPrice = estimatedPrice * item.quantity;

    return `
        <div class="shopping-item ${boughtClass} ${saveForNextClass}"
             data-item-id="${item.itemId}"
             data-user-id="${escapeHtml(item.userId)}"
             data-item-name="${escapeHtml(item.itemName)}"
             data-quantity="${item.quantity}">
            <input type="checkbox"
                   class="item-checkbox"
                   data-item-id="${item.itemId}"
                   ${item.bought ? 'checked' : ''}>
            <span class="item-name">${escapeHtml(item.itemName)}</span>
            <span class="item-quantity">x${item.quantity}</span>
            <span class="item-price">£${totalPrice.toFixed(2)}</span>
            <button class="btn-save-next" data-item-id="${item.itemId}" title="Save for next shop">
                ${item.saveForNext ? '🔖' : '📌'}
            </button>
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

    // Add save for next shop listeners
    const saveNextButtons = itemsContainer.querySelectorAll('.btn-save-next');
    saveNextButtons.forEach(button => {
        button.addEventListener('click', handleSaveForNextClick);
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

    // Hide all children and show edit form
    const checkbox = itemElement.querySelector('.item-checkbox');
    const itemName = itemElement.querySelector('.item-name');
    const editBtn = itemElement.querySelector('.btn-edit');
    const qtySpan = itemElement.querySelector('.item-quantity');
    const priceSpan = itemElement.querySelector('.item-price');
    const deleteBtn = itemElement.querySelector('.btn-delete');

    // Hide all elements
    checkbox.style.display = 'none';
    itemName.style.display = 'none';
    editBtn.style.display = 'none';
    qtySpan.style.display = 'none';
    priceSpan.style.display = 'none';
    deleteBtn.style.display = 'none';

    // Create inline edit form
    const nameInput = document.createElement('input');
    nameInput.type = 'text';
    nameInput.className = 'edit-name-input';
    nameInput.value = currentName;
    nameInput.placeholder = 'Item name';

    const qtyInput = document.createElement('input');
    qtyInput.type = 'number';
    qtyInput.className = 'edit-qty-input';
    qtyInput.value = currentQty;
    qtyInput.min = 1;
    qtyInput.placeholder = 'Qty';

    const saveBtn = document.createElement('button');
    saveBtn.className = 'btn-save-edit';
    saveBtn.textContent = '✓';

    const cancelBtn = document.createElement('button');
    cancelBtn.className = 'btn-cancel-edit';
    cancelBtn.textContent = '✕';

    // Insert edit elements
    itemElement.appendChild(nameInput);
    itemElement.appendChild(qtyInput);
    itemElement.appendChild(saveBtn);
    itemElement.appendChild(cancelBtn);

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

            const response = await fetch(`${API_BASE_URL}/items/${userId}/${itemId}`, {
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
        const response = await fetch(`${API_BASE_URL}/items/${userId}/${itemId}`, {
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
 * Handle save for next shop button click
 */
async function handleSaveForNextClick(event) {
    const button = event.target;
    const itemElement = button.closest('.shopping-item');
    const itemId = button.dataset.itemId;
    const userId = itemElement.dataset.userId;

    // Toggle saveForNext status
    const currentSaveForNext = itemElement.classList.contains('save-for-next');
    const newSaveForNext = !currentSaveForNext;

    try {
        const response = await fetch(`${API_BASE_URL}/items/${userId}/${itemId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ saveForNext: newSaveForNext })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        // Show notification and reload to re-sort items
        if (newSaveForNext) {
            showNotification('✓ Item saved for next shop (moved to bottom)', 'success', 2000);
        } else {
            showNotification('✓ Item removed from next shop (restored to list)', 'success', 2000);
        }

        // Reload the list to re-sort items (save-for-next go to bottom, others restore to store layout order)
        await loadUserItems();

    } catch (error) {
        console.error('Error updating saveForNext:', error);
        showNotification('✗ Failed to update item', 'error', 3000);
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

            const response = await fetch(`${API_BASE_URL}/items`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            // Handle duplicate item error (409 Conflict)
            if (response.status === 409) {
                const errorData = await response.json();
                showDuplicateModal(errorData.message);
                return;
            }

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
        const userId = 'Gianluca';  // Default user for email

        const existingMessages = itemsContainer.parentElement.querySelectorAll('.success-message, .error-message');
        existingMessages.forEach(msg => msg.remove());

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
 * Setup store shop button handler
 */
function setupStoreShopHandler() {
    const button = document.getElementById('store-shop-btn');

    button.addEventListener('click', async () => {
        if (!confirm('Save your shop? This will:\n\n✓ Save ticked items (in basket) to shop history\n✓ Untick items and keep them on your list for next time\n✓ All items stay on your shopping list')) {
            return;
        }

        button.disabled = true;
        button.textContent = '💾 Saving...';

        try {
            const response = await fetch(`${API_BASE_URL}/shop/store`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            showNotification(
                `✓ Shop saved! ${data.shop.totalItems} items purchased, £${data.shop.totalPrice.toFixed(2)} total.`,
                'success',
                5000
            );

            // Reload items to show updated list
            await loadUserItems();

        } catch (error) {
            console.error('Error storing shop:', error);
            showNotification('✗ Failed to save shop. Please try again.', 'error', 5000);

        } finally {
            button.disabled = false;
            button.textContent = '💾 Save My Shop';
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
            const response = await fetch(`${API_BASE_URL}/prices/recalculate`, {
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
 * Setup recategorize items button handler
 */
function setupRecategorizeItemsHandler() {
    const button = document.getElementById('recategorize-items-btn');

    button.addEventListener('click', async () => {
        if (!confirm('Recategorize ALL items using AI? This will update the category for every item in your database based on current AI categorization logic.')) {
            return;
        }

        button.disabled = true;
        button.textContent = '🤖 AI Recategorizing...';

        try {
            const response = await fetch(`${API_BASE_URL}/categorize/recalculate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            // Reload items to show new categories
            await loadUserItems();

            // Build detailed message
            let message = '';
            if (data.completed) {
                // All items processed successfully
                message = `✓ Successfully processed ${data.successfulItems} of ${data.totalItems} items!\n`;
                message += `   ${data.categoryChangesCount} categories were updated.`;
            } else {
                // Some items failed
                message = `⚠ Processed ${data.successfulItems} of ${data.totalItems} items.\n`;
                message += `   ${data.failedItems} items failed or were skipped.\n`;
                message += `   ${data.categoryChangesCount} categories were updated.`;
            }

            showNotification(
                message,
                data.completed ? 'success' : 'warning',
                7000
            );

        } catch (error) {
            console.error('Error recategorizing items:', error);
            showNotification('✗ Failed to recategorize items. Please try again.', 'error', 5000);

        } finally {
            button.disabled = false;
            button.textContent = '🏷️ Recategorize All Items';
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

/**
 * Show duplicate item modal
 */
function showDuplicateModal(message) {
    // Create modal overlay
    const overlay = document.createElement('div');
    overlay.className = 'duplicate-modal-overlay';
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(0, 0, 0, 0.5);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 10000;
    `;

    // Create modal content
    const modal = document.createElement('div');
    modal.className = 'duplicate-modal';
    modal.style.cssText = `
        background: white;
        padding: 30px;
        border-radius: 10px;
        max-width: 400px;
        text-align: center;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    `;

    // Add warning icon and message
    modal.innerHTML = `
        <div style="font-size: 48px; margin-bottom: 15px;">⚠️</div>
        <h2 style="margin: 0 0 15px 0; color: #ff4757;">Item Already Exists</h2>
        <p style="margin: 0 0 25px 0; font-size: 16px; color: #2c3e50;">${escapeHtml(message)}</p>
        <button id="duplicate-ok-btn" style="
            background-color: #3498db;
            color: white;
            border: none;
            padding: 12px 40px;
            font-size: 16px;
            border-radius: 5px;
            cursor: pointer;
            font-weight: 600;
        ">OK</button>
    `;

    overlay.appendChild(modal);
    document.body.appendChild(overlay);

    // Handle OK button click
    const okBtn = document.getElementById('duplicate-ok-btn');
    okBtn.addEventListener('click', () => {
        document.body.removeChild(overlay);
    });

    // Handle clicking outside modal
    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) {
            document.body.removeChild(overlay);
        }
    });
}

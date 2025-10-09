// API Configuration
const API_BASE_URL = 'https://01mmfw29n0.execute-api.eu-west-1.amazonaws.com/dev';

// Initialize page
document.addEventListener('DOMContentLoaded', () => {
    loadPrompt();
    loadContextItems();
    loadPreferences();
    updateStats();

    // Event listeners
    document.getElementById('refresh-prompt-btn').addEventListener('click', loadPrompt);
    document.getElementById('copy-prompt-btn').addEventListener('click', copyPromptToClipboard);
    document.getElementById('improve-prompt-btn').addEventListener('click', improvePromptWithAI);
    document.getElementById('add-context-btn').addEventListener('click', addContextItem);
    document.getElementById('save-preferences-btn').addEventListener('click', savePreferences);

    // Enter key on context form
    document.getElementById('context-meaning').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            addContextItem();
        }
    });

    // Enter key on feedback
    document.getElementById('feedback-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && e.ctrlKey) {
            improvePromptWithAI();
        }
    });
});

/**
 * Load and display the current AI prompt
 */
function loadPrompt() {
    const customPrompt = localStorage.getItem('customAIPrompt') || '';
    const contextItems = JSON.parse(localStorage.getItem('contextItems') || '[]');
    const useUKEnglish = localStorage.getItem('useUKEnglish') !== 'false';
    const strictCategories = localStorage.getItem('strictCategories') !== 'false';

    // Build the full prompt that will be sent to the AI
    let fullPrompt = '=== BASE INSTRUCTIONS ===\n';
    fullPrompt += 'You are a UK shopping assistant helping to process grocery items.\n\n';

    if (useUKEnglish) {
        fullPrompt += 'IMPORTANT: Use UK English spelling and terminology.\n';
        fullPrompt += 'Examples: colour (not color), flavour (not flavor), courgette (not zucchini), aubergine (not eggplant)\n\n';
    }

    if (strictCategories) {
        fullPrompt += 'Use UK supermarket category names as found in Tesco, Sainsbury\'s, Asda.\n\n';
    }

    // Add household context
    if (contextItems.length > 0) {
        fullPrompt += '=== HOUSEHOLD CONTEXT ===\n';
        fullPrompt += 'Gianluca and Nicole\'s specific meanings:\n\n';
        contextItems.forEach(item => {
            fullPrompt += `"${item.term}" = ${item.meaning}\n`;
        });
        fullPrompt += '\n';
    }

    // Add custom instructions
    if (customPrompt.trim()) {
        fullPrompt += '=== CUSTOM INSTRUCTIONS ===\n';
        fullPrompt += customPrompt.trim() + '\n\n';
    }

    // Add standard categories
    fullPrompt += '=== UK SUPERMARKET CATEGORIES ===\n';
    fullPrompt += 'Fresh Produce - Fruit, Fresh Produce - Vegetables, Fresh Produce - Herbs & Salads, ';
    fullPrompt += 'Meat & Poultry, Fish & Seafood, Dairy & Eggs, Bakery & Bread, Frozen Foods, ';
    fullPrompt += 'Pantry & Dry Goods, Canned & Jarred, Snacks & Confectionery, Beverages, ';
    fullPrompt += 'Alcohol & Wine, Health & Beauty, Household & Cleaning, Baby & Child';

    document.getElementById('current-prompt').textContent = fullPrompt;

    // Update stats
    document.getElementById('prompt-length').textContent = fullPrompt.length;
}

/**
 * Copy prompt to clipboard
 */
async function copyPromptToClipboard() {
    const promptText = document.getElementById('current-prompt').textContent;
    try {
        await navigator.clipboard.writeText(promptText);
        showStatus('preferences-status', 'Prompt copied to clipboard!', 'success');
    } catch (err) {
        showStatus('preferences-status', 'Failed to copy to clipboard', 'error');
    }
}

/**
 * Improve prompt using AI feedback
 */
async function improvePromptWithAI() {
    const feedback = document.getElementById('feedback-input').value.trim();

    if (!feedback) {
        showStatus('feedback-status', 'Please enter some feedback', 'error');
        return;
    }

    const button = document.getElementById('improve-prompt-btn');
    const originalText = button.textContent;
    button.disabled = true;
    button.textContent = '🤖 AI is thinking...';

    try {
        // Get current prompt
        const currentPrompt = localStorage.getItem('customAIPrompt') || '';
        const contextItems = JSON.parse(localStorage.getItem('contextItems') || '[]');

        // Call Lambda function to improve prompt
        const response = await fetch(`${API_BASE_URL}/improve-prompt`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                currentPrompt,
                contextItems,
                feedback
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        // Update prompt
        if (data.improvedPrompt) {
            localStorage.setItem('customAIPrompt', data.improvedPrompt);
        }

        // Add any new context items
        if (data.newContextItems && data.newContextItems.length > 0) {
            const existingItems = JSON.parse(localStorage.getItem('contextItems') || '[]');
            const allItems = [...existingItems, ...data.newContextItems];

            // Remove duplicates
            const uniqueItems = allItems.filter((item, index, self) =>
                index === self.findIndex(t => t.term.toLowerCase() === item.term.toLowerCase())
            );

            localStorage.setItem('contextItems', JSON.stringify(uniqueItems));
            loadContextItems();
        }

        // Update last modified
        localStorage.setItem('promptLastUpdated', new Date().toISOString());

        // Reload everything
        loadPrompt();
        updateStats();

        // Clear feedback input
        document.getElementById('feedback-input').value = '';

        showStatus('feedback-status',
            `✓ Prompt improved! ${data.newContextItems ? data.newContextItems.length + ' context items added.' : ''}`,
            'success'
        );
    } catch (error) {
        console.error('Error improving prompt:', error);
        showStatus('feedback-status',
            '✗ Failed to improve prompt. The AI service may not be available yet.',
            'error'
        );
    } finally {
        button.disabled = false;
        button.textContent = originalText;
    }
}

/**
 * Load and display context items
 */
function loadContextItems() {
    const contextItems = JSON.parse(localStorage.getItem('contextItems') || '[]');
    const container = document.getElementById('context-list');

    if (contextItems.length === 0) {
        container.innerHTML = '<p style="color: #999; font-style: italic;">No context items yet. Add some below!</p>';
        return;
    }

    container.innerHTML = contextItems.map((item, index) => `
        <div class="context-item">
            <div class="context-item-content">
                <strong>${escapeHtml(item.term)}</strong>
                <div class="meaning">${escapeHtml(item.meaning)}</div>
            </div>
            <button class="btn-delete-context" onclick="deleteContextItem(${index})">Delete</button>
        </div>
    `).join('');

    // Update count
    document.getElementById('context-count').textContent = contextItems.length;
}

/**
 * Add new context item
 */
function addContextItem() {
    const termInput = document.getElementById('context-term');
    const meaningInput = document.getElementById('context-meaning');

    const term = termInput.value.trim();
    const meaning = meaningInput.value.trim();

    if (!term || !meaning) {
        alert('Please fill in both fields');
        return;
    }

    const contextItems = JSON.parse(localStorage.getItem('contextItems') || '[]');

    // Check for duplicates
    const exists = contextItems.find(item => item.term.toLowerCase() === term.toLowerCase());
    if (exists) {
        if (confirm(`"${term}" already exists. Replace it?`)) {
            contextItems.splice(contextItems.findIndex(i => i.term.toLowerCase() === term.toLowerCase()), 1);
        } else {
            return;
        }
    }

    contextItems.push({ term, meaning });
    localStorage.setItem('contextItems', JSON.stringify(contextItems));

    // Update last modified
    localStorage.setItem('promptLastUpdated', new Date().toISOString());

    // Clear inputs
    termInput.value = '';
    meaningInput.value = '';

    // Reload
    loadContextItems();
    loadPrompt();
    updateStats();
}

/**
 * Delete context item
 */
function deleteContextItem(index) {
    const contextItems = JSON.parse(localStorage.getItem('contextItems') || '[]');

    if (confirm(`Delete "${contextItems[index].term}"?`)) {
        contextItems.splice(index, 1);
        localStorage.setItem('contextItems', JSON.stringify(contextItems));

        // Update last modified
        localStorage.setItem('promptLastUpdated', new Date().toISOString());

        loadContextItems();
        loadPrompt();
        updateStats();
    }
}

/**
 * Load preferences
 */
function loadPreferences() {
    const useUKEnglish = localStorage.getItem('useUKEnglish') !== 'false';
    const strictCategories = localStorage.getItem('strictCategories') !== 'false';

    document.getElementById('uk-english-toggle').checked = useUKEnglish;
    document.getElementById('strict-categories-toggle').checked = strictCategories;
}

/**
 * Save preferences
 */
function savePreferences() {
    const useUKEnglish = document.getElementById('uk-english-toggle').checked;
    const strictCategories = document.getElementById('strict-categories-toggle').checked;

    localStorage.setItem('useUKEnglish', useUKEnglish);
    localStorage.setItem('strictCategories', strictCategories);
    localStorage.setItem('promptLastUpdated', new Date().toISOString());

    loadPrompt();
    updateStats();

    showStatus('preferences-status', '✓ Preferences saved!', 'success');
}

/**
 * Update statistics
 */
function updateStats() {
    const contextItems = JSON.parse(localStorage.getItem('contextItems') || '[]');
    const lastUpdated = localStorage.getItem('promptLastUpdated');

    document.getElementById('context-count').textContent = contextItems.length;

    if (lastUpdated) {
        const date = new Date(lastUpdated);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);

        if (diffMins < 1) {
            document.getElementById('last-updated').textContent = 'Just now';
        } else if (diffMins < 60) {
            document.getElementById('last-updated').textContent = `${diffMins}m ago`;
        } else if (diffMins < 1440) {
            document.getElementById('last-updated').textContent = `${Math.floor(diffMins / 60)}h ago`;
        } else {
            document.getElementById('last-updated').textContent = date.toLocaleDateString();
        }
    } else {
        document.getElementById('last-updated').textContent = 'Never';
    }
}

/**
 * Show status message
 */
function showStatus(elementId, message, type = 'success') {
    const container = document.getElementById(elementId);
    container.innerHTML = `<div class="status-message status-${type}">${message}</div>`;

    setTimeout(() => {
        container.innerHTML = '';
    }, 5000);
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

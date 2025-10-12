/**
 * Store Layout Configuration
 *
 * Allows users to configure the order of categories based on store layout
 */

// Default store layout based on Sainsbury's
const DEFAULT_LAYOUT = [
    { name: "Health & Beauty", icon: "🧴", position: 1 },
    { name: "Fresh Produce - Herbs & Salads", icon: "🌿", position: 2 },
    { name: "Fresh Produce - Fruit", icon: "🍎", position: 3 },
    { name: "Fresh Produce - Vegetables", icon: "🥕", position: 4 },
    { name: "Meat & Poultry", icon: "🍖", position: 5 },
    { name: "Fish & Seafood", icon: "🐟", position: 5 },
    { name: "Household & Cleaning", icon: "🧽", position: 6 },
    { name: "Baby & Child", icon: "👶", position: 6 },
    { name: "Dairy & Eggs", icon: "🥛", position: 8 },
    { name: "Beverages", icon: "☕", position: 9 },
    { name: "Pantry & Dry Goods", icon: "🌾", position: 10 },
    { name: "Canned & Jarred", icon: "🥫", position: 11 },
    { name: "Bakery & Bread", icon: "🍞", position: 12 },
    { name: "Alcohol & Wine", icon: "🍷", position: 13 },
    { name: "Snacks & Confectionery", icon: "🍫", position: 14 },
    { name: "Frozen Foods", icon: "❄️", position: 16 }
];

let currentLayout = [];
let draggedElement = null;

/**
 * Initialize page
 */
document.addEventListener('DOMContentLoaded', () => {
    loadLayout();
    setupEventListeners();
});

/**
 * Load current layout from localStorage or use default
 */
function loadLayout() {
    const saved = localStorage.getItem('storeLayout');
    if (saved) {
        try {
            currentLayout = JSON.parse(saved);
        } catch (e) {
            console.error('Error loading saved layout:', e);
            currentLayout = [...DEFAULT_LAYOUT];
        }
    } else {
        currentLayout = [...DEFAULT_LAYOUT];
    }

    // Sort by position
    currentLayout.sort((a, b) => a.position - b.position);
    renderLayout();
}

/**
 * Render the category list
 */
function renderLayout() {
    const container = document.getElementById('categories-list');

    container.innerHTML = currentLayout.map((category, index) => `
        <div class="category-item" draggable="true" data-index="${index}">
            <span class="drag-handle">⋮⋮</span>
            <span class="position-number">${index + 1}</span>
            <span class="category-icon">${category.icon}</span>
            <span class="category-name">${category.name}</span>
        </div>
    `).join('');

    // Attach drag event listeners
    setupDragAndDrop();
}

/**
 * Setup drag and drop functionality
 */
function setupDragAndDrop() {
    const items = document.querySelectorAll('.category-item');

    items.forEach(item => {
        item.addEventListener('dragstart', handleDragStart);
        item.addEventListener('dragend', handleDragEnd);
        item.addEventListener('dragover', handleDragOver);
        item.addEventListener('drop', handleDrop);
        item.addEventListener('dragenter', handleDragEnter);
        item.addEventListener('dragleave', handleDragLeave);
    });
}

/**
 * Handle drag start
 */
function handleDragStart(e) {
    draggedElement = this;
    this.classList.add('dragging');
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/html', this.innerHTML);
}

/**
 * Handle drag end
 */
function handleDragEnd(e) {
    this.classList.remove('dragging');

    // Remove all drag-over classes
    document.querySelectorAll('.category-item').forEach(item => {
        item.classList.remove('drag-over');
    });
}

/**
 * Handle drag over
 */
function handleDragOver(e) {
    if (e.preventDefault) {
        e.preventDefault();
    }
    e.dataTransfer.dropEffect = 'move';
    return false;
}

/**
 * Handle drag enter
 */
function handleDragEnter(e) {
    if (this !== draggedElement) {
        this.classList.add('drag-over');
    }
}

/**
 * Handle drag leave
 */
function handleDragLeave(e) {
    this.classList.remove('drag-over');
}

/**
 * Handle drop
 */
function handleDrop(e) {
    if (e.stopPropagation) {
        e.stopPropagation();
    }

    if (draggedElement !== this) {
        const draggedIndex = parseInt(draggedElement.getAttribute('data-index'));
        const targetIndex = parseInt(this.getAttribute('data-index'));

        // Reorder the array
        const [removed] = currentLayout.splice(draggedIndex, 1);
        currentLayout.splice(targetIndex, 0, removed);

        // Update positions
        currentLayout.forEach((cat, idx) => {
            cat.position = idx + 1;
        });

        // Re-render
        renderLayout();
    }

    return false;
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
    document.getElementById('save-layout-btn').addEventListener('click', saveLayout);
    document.getElementById('reset-layout-btn').addEventListener('click', resetLayout);
}

/**
 * Save layout to localStorage
 */
function saveLayout() {
    try {
        localStorage.setItem('storeLayout', JSON.stringify(currentLayout));
        showMessage('Layout saved successfully! Your shopping list will now be ordered by this layout.', 'success');
    } catch (e) {
        console.error('Error saving layout:', e);
        showMessage('Failed to save layout. Please try again.', 'error');
    }
}

/**
 * Reset layout to default
 */
function resetLayout() {
    if (confirm('Are you sure you want to reset to the default Sainsbury\'s layout?')) {
        currentLayout = [...DEFAULT_LAYOUT];
        currentLayout.sort((a, b) => a.position - b.position);
        renderLayout();
        localStorage.removeItem('storeLayout');
        showMessage('Layout reset to default!', 'success');
    }
}

/**
 * Show message to user
 */
function showMessage(message, type) {
    const container = document.getElementById('message-container');
    container.innerHTML = `<div class="message ${type}">${message}</div>`;

    // Auto-hide after 3 seconds
    setTimeout(() => {
        container.innerHTML = '';
    }, 3000);
}

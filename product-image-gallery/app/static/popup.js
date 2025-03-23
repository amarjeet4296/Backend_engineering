// Popup functionality for product image grid
document.addEventListener('DOMContentLoaded', () => {
    setupPopupOnClick();
});

/**
 * Setup popup functionality that triggers on click instead of hover
 */
function setupPopupOnClick() {
    // Event delegation for performance
    document.addEventListener('click', (e) => {
        // Check if clicked on a product image
        const productImage = e.target.closest('.product-image');
        if (productImage) {
            e.preventDefault();
            
            // Find the product card and popup
            const productCard = productImage.closest('.product-card');
            const popup = productCard.querySelector('.product-popup');
            
            // Show the popup
            if (popup) {
                // Hide any other visible popups first
                document.querySelectorAll('.product-popup.active').forEach(p => {
                    if (p !== popup) {
                        p.classList.remove('active');
                    }
                });
                
                // Toggle this popup
                popup.classList.toggle('active');
            }
        }
        
        // Check if clicked outside a popup to close it
        if (!e.target.closest('.product-popup') && !e.target.closest('.product-image')) {
            document.querySelectorAll('.product-popup.active').forEach(popup => {
                popup.classList.remove('active');
            });
        }
    });
}

/**
 * Function to save product data and update the database
 * 
 * @param {number|string} productId - The ID of the product to update
 * @returns {Promise<boolean>} - Success or failure
 */
async function saveProductData(productId) {
    const form = document.querySelector(`.popup-form[data-product-id="${productId}"]`);
    if (!form) return false;
    
    const nameInput = form.querySelector('input[name="name"]');
    const descInput = form.querySelector('textarea[name="description"]');
    const priceInput = form.querySelector('input[name="price"]');
    
    if (!nameInput || !descInput || !priceInput) return false;
    
    const productData = {
        name: nameInput.value,
        description: descInput.value,
        price: parseFloat(priceInput.value)
    };
    
    try {
        const response = await fetch(`/api/products/${productId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(productData)
        });
        
        if (!response.ok) {
            throw new Error(`Failed to update product: ${response.statusText}`);
        }
        
        // Get the updated product data
        const updatedProduct = await response.json();
        
        // Close the popup
        const popup = document.querySelector(`.product-popup[data-product-id="${productId}"]`);
        if (popup) {
            popup.classList.remove('active');
        }
        
        // Update the UI with new data
        updateProductUI(updatedProduct);
        
        return true;
    } catch (error) {
        console.error('Error saving product data:', error);
        return false;
    }
}

/**
 * Update the product display in the UI
 * 
 * @param {Object} product - The updated product data
 */
function updateProductUI(product) {
    const productCard = document.querySelector(`.product-card[data-product-id="${product.id}"]`);
    if (!productCard) return;
    
    // Update product details in the card
    const nameElement = productCard.querySelector('.product-name');
    const descElement = productCard.querySelector('.product-desc');
    const priceElement = productCard.querySelector('.product-price');
    
    if (nameElement) nameElement.textContent = product.name;
    if (descElement) descElement.textContent = product.description;
    if (priceElement) priceElement.textContent = `$${product.price.toFixed(2)}`;
} 
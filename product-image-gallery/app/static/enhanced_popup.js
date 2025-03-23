/**
 * Enhanced Popup API Integration
 * 
 * This file provides functions to interact with the popup API and display
 * more sophisticated popups with additional information and image galleries.
 */

// Initialize when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
    initializeEnhancedPopups();
});

/**
 * Initialize enhanced popup functionality
 */
function initializeEnhancedPopups() {
    // Add event listeners for product cards
    const productCards = document.querySelectorAll('.product-card');
    productCards.forEach(card => {
        // Get product ID from the card
        const productId = card.getAttribute('data-product-id');
        if (!productId) return;
        
        // Add click handler for all product images
        const productImages = card.querySelectorAll('.product-image');
        productImages.forEach(img => {
            img.addEventListener('click', async (e) => {
                e.preventDefault();
                await showEnhancedProductPopup(productId);
            });
        });
    });
    
    // Add global click handler to close popups when clicking outside
    document.addEventListener('click', (e) => {
        if (e.target.classList.contains('enhanced-popup-overlay')) {
            closeAllEnhancedPopups();
        }
    });
    
    // Add escape key handler to close popups
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeAllEnhancedPopups();
        }
    });
}

/**
 * Display an enhanced product popup using the popup API
 * 
 * @param {string|number} productId - ID of the product to display
 */
async function showEnhancedProductPopup(productId) {
    try {
        // Show loading indicator
        showLoadingOverlay();
        
        // Fetch popup data from API
        const response = await fetch(`/api/popups/product/${productId}`);
        if (!response.ok) {
            throw new Error(`Failed to fetch popup data: ${response.statusText}`);
        }
        
        const popupData = await response.json();
        
        // Create popup HTML
        const popupHtml = createProductPopupHtml(popupData);
        
        // Add popup to the DOM
        const popupOverlay = document.createElement('div');
        popupOverlay.className = 'enhanced-popup-overlay';
        popupOverlay.innerHTML = popupHtml;
        document.body.appendChild(popupOverlay);
        
        // Add animation classes after a brief delay (for transition effect)
        setTimeout(() => {
            popupOverlay.classList.add('active');
            const popupContent = popupOverlay.querySelector('.enhanced-popup-content');
            if (popupContent) {
                popupContent.classList.add('active');
            }
        }, 10);
        
        // Hide loading indicator
        hideLoadingOverlay();
        
        // Setup event listeners for the popup
        setupPopupEventListeners(popupOverlay, popupData);
        
    } catch (error) {
        console.error('Error displaying product popup:', error);
        hideLoadingOverlay();
        
        // Show error message to user
        showNotification('Error', 'Could not load product details. Please try again.');
    }
}

/**
 * Display an enhanced image popup using the popup API
 * 
 * @param {string|number} imageId - ID of the image to display
 */
async function showEnhancedImagePopup(imageId) {
    try {
        // Show loading indicator
        showLoadingOverlay();
        
        // Fetch popup data from API
        const response = await fetch(`/api/popups/image/${imageId}`);
        if (!response.ok) {
            throw new Error(`Failed to fetch image popup data: ${response.statusText}`);
        }
        
        const popupData = await response.json();
        
        // Create popup HTML
        const popupHtml = createImagePopupHtml(popupData);
        
        // Add popup to the DOM
        const popupOverlay = document.createElement('div');
        popupOverlay.className = 'enhanced-popup-overlay';
        popupOverlay.innerHTML = popupHtml;
        document.body.appendChild(popupOverlay);
        
        // Add animation classes after a brief delay (for transition effect)
        setTimeout(() => {
            popupOverlay.classList.add('active');
            const popupContent = popupOverlay.querySelector('.enhanced-popup-content');
            if (popupContent) {
                popupContent.classList.add('active');
            }
        }, 10);
        
        // Hide loading indicator
        hideLoadingOverlay();
        
        // Setup event listeners for the popup
        setupImagePopupEventListeners(popupOverlay, popupData);
        
    } catch (error) {
        console.error('Error displaying image popup:', error);
        hideLoadingOverlay();
        
        // Show error message to user
        showNotification('Error', 'Could not load image details. Please try again.');
    }
}

/**
 * Create HTML for a product popup
 * 
 * @param {Object} popupData - Data from the popup API
 * @returns {string} HTML for the popup
 */
function createProductPopupHtml(popupData) {
    const { data } = popupData;
    
    // Convert additional images to gallery items
    let galleryHtml = '';
    if (data.additional_images && data.additional_images.length > 0) {
        galleryHtml = `
            <div class="enhanced-popup-gallery">
                <h4>Additional Images</h4>
                <div class="gallery-container">
                    ${data.additional_images.map(imgUrl => `
                        <div class="gallery-item">
                            <img src="${imgUrl}" alt="${data.title}" class="gallery-image">
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }
    
    // Get product name (strip the "Product: " prefix if present)
    const productName = data.title.replace('Product: ', '');
    
    return `
        <div class="enhanced-popup-content product-popup-type" data-popup-id="${popupData.popup_id}">
            <div class="enhanced-popup-header">
                <h3>${data.title}</h3>
                <button class="close-btn">&times;</button>
            </div>
            <div class="enhanced-popup-body">
                <div class="popup-main-image">
                    <img src="${data.image_url || '/static/placeholder.png'}" alt="${data.title}">
                </div>
                <div class="popup-details">
                    <div class="form-group">
                        <label for="popup-name-${data.product_id}">Product Name:</label>
                        <input type="text" id="popup-name-${data.product_id}" class="popup-field" name="name" value="${productName}">
                    </div>
                    <div class="detail-group">
                        <label>Description:</label>
                        <p>${data.description || 'No description available'}</p>
                    </div>
                    <div class="popup-actions">
                        <button class="btn-save-popup" data-product-id="${data.product_id}">Save Changes</button>
                        <button class="btn-view-all" data-product-id="${data.product_id}">View All Images</button>
                        <button class="btn-cancel-popup" data-product-id="${data.product_id}">Cancel</button>
                    </div>
                </div>
            </div>
            ${galleryHtml}
        </div>
    `;
}

/**
 * Create HTML for an image popup
 * 
 * @param {Object} popupData - Data from the popup API
 * @returns {string} HTML for the popup
 */
function createImagePopupHtml(popupData) {
    const { data } = popupData;
    
    return `
        <div class="popup-header">
            <h3>${data.product_name}</h3>
            <button class="popup-close">&times;</button>
        </div>
        <div class="popup-content">
            <div class="popup-image-container">
                <img src="${data.url}" alt="${data.alt_text}" class="popup-image">
            </div>
            <div class="detail-section">
                <div class="form-group">
                    <label for="alt-text">Alt Text:</label>
                    <input type="text" id="alt-text" value="${data.alt_text || ''}">
                </div>
                <div class="form-group">
                    <label for="image-type">Image Type:</label>
                    <select id="image-type">
                        <option value="main" ${data.image_type === 'main' ? 'selected' : ''}>Main</option>
                        <option value="detail" ${data.image_type === 'detail' ? 'selected' : ''}>Detail</option>
                        <option value="package" ${data.image_type === 'package' ? 'selected' : ''}>Package</option>
                        <option value="lifestyle" ${data.image_type === 'lifestyle' ? 'selected' : ''}>Lifestyle</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="is-primary">
                        <input type="checkbox" id="is-primary" ${data.is_primary ? 'checked' : ''}>
                        Primary Image
                    </label>
                </div>
            </div>
            <div class="popup-actions">
                <button class="btn-back">Back to Product</button>
                <button class="btn-delete">Delete Image</button>
                <button class="btn-save">Save Changes</button>
            </div>
        </div>
    `;
}

/**
 * Setup event listeners for product popup elements
 * 
 * @param {HTMLElement} popupOverlay - The popup overlay element
 * @param {Object} popupData - Data from the popup API
 */
function setupPopupEventListeners(popupOverlay, popupData) {
    // Close button
    const closeBtn = popupOverlay.querySelector('.close-btn');
    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            closeAllEnhancedPopups();
        });
    }
    
    // Save button
    const saveBtn = popupOverlay.querySelector('.btn-save-popup');
    if (saveBtn) {
        saveBtn.addEventListener('click', async () => {
            const productId = saveBtn.getAttribute('data-product-id');
            if (productId) {
                await savePopupChanges(popupOverlay, productId);
            }
        });
    }
    
    // Cancel button
    const cancelBtn = popupOverlay.querySelector('.btn-cancel-popup');
    if (cancelBtn) {
        cancelBtn.addEventListener('click', () => {
            closeAllEnhancedPopups();
        });
    }
    
    // View all images button
    const viewAllBtn = popupOverlay.querySelector('.btn-view-all');
    if (viewAllBtn) {
        viewAllBtn.addEventListener('click', async () => {
            const productId = viewAllBtn.getAttribute('data-product-id');
            if (productId) {
                closeAllEnhancedPopups();
                await showProductGalleryPopup(productId);
            }
        });
    }
    
    // Gallery image clicks
    const galleryImages = popupOverlay.querySelectorAll('.gallery-image');
    galleryImages.forEach(img => {
        img.addEventListener('click', () => {
            // Open full-size image viewer
            const imgSrc = img.getAttribute('src');
            if (imgSrc) {
                showFullSizeImageViewer(imgSrc, img.getAttribute('alt') || 'Product image');
            }
        });
    });
}

/**
 * Setup event listeners for image popup elements
 * 
 * @param {HTMLElement} popupOverlay - The popup overlay element
 * @param {Object} popupData - Data from the popup API
 */
function setupImagePopupEventListeners(popupOverlay, popupData) {
    const closeButton = popupOverlay.querySelector('.popup-close');
    closeButton.addEventListener('click', () => {
        popupOverlay.remove();
    });
    
    const backButton = popupOverlay.querySelector('.btn-back');
    backButton.addEventListener('click', () => {
        popupOverlay.remove();
        showProductGalleryPopup(popupData.product_id);
    });
    
    const saveButton = popupOverlay.querySelector('.btn-save');
    saveButton.addEventListener('click', () => {
        saveImageChanges(popupOverlay, popupData.product_id, popupData.id);
    });
    
    const deleteButton = popupOverlay.querySelector('.btn-delete');
    deleteButton.addEventListener('click', () => {
        if (confirm('Are you sure you want to delete this image? This action cannot be undone.')) {
            deleteImage(popupOverlay, popupData.product_id, popupData.id);
        }
    });
}

/**
 * Display a gallery of all product images
 * 
 * @param {string|number} productId - ID of the product
 */
async function showProductGalleryPopup(productId) {
    // Show loading overlay while fetching data
    showLoadingOverlay();
    
    // Fetch product data and gallery images from the server
    Promise.all([
        fetch(`/api/popups/product/${productId}`).then(res => res.json()),
        fetch(`/api/popups/product/${productId}/gallery`).then(res => res.json())
    ])
    .then(([productData, galleryData]) => {
        // Create popup overlay
        const popupOverlay = document.createElement('div');
        popupOverlay.className = 'enhanced-popup-overlay';
        
        // Create popup container
        const popupContainer = document.createElement('div');
        popupContainer.className = 'enhanced-popup-container';
        
        // Add product popup HTML
        popupContainer.innerHTML = createProductPopupHtml(productData.popup_data);
        
        // Add gallery HTML to the popup
        const popupContent = popupContainer.querySelector('.popup-content');
        
        // Create gallery section
        const gallerySection = document.createElement('div');
        gallerySection.className = 'enhanced-popup-gallery';
        gallerySection.innerHTML = `
            <h4>Product Images</h4>
            <div class="gallery-controls">
                <button class="btn-add-image">Add New Image</button>
            </div>
            <div class="gallery-container">
                ${galleryData.images.length > 0 ? 
                    galleryData.images.map(image => `
                        <div class="gallery-item" data-image-id="${image.id}" data-product-id="${productId}">
                            <img src="${image.thumbnail_url || image.url}" alt="${image.alt_text || 'Product image'}" class="gallery-image">
                            ${image.is_primary ? '<span class="primary-badge">Primary</span>' : ''}
                        </div>
                    `).join('') : 
                    '<div class="no-images-message">No images available for this product</div>'
                }
            </div>
        `;
        
        // Create image upload panel (hidden by default)
        const uploadPanel = document.createElement('div');
        uploadPanel.className = 'image-upload-panel';
        uploadPanel.style.display = 'none';
        uploadPanel.innerHTML = `
            <div class="form-header">
                <h4>Upload New Image</h4>
                <button class="btn-close-upload">&times;</button>
            </div>
            <form id="image-upload-form">
                <div class="form-group">
                    <label for="image-file">Select Image:</label>
                    <input type="file" id="image-file" accept="image/*" required>
                </div>
                <div class="image-preview-container" style="display: none;">
                    <img class="image-preview" src="" alt="Image preview">
                </div>
                <div class="form-group">
                    <label for="alt-text-upload">Alt Text:</label>
                    <input type="text" id="alt-text-upload">
                </div>
                <div class="form-group">
                    <label for="image-type-upload">Image Type:</label>
                    <select id="image-type-upload">
                        <option value="main">Main</option>
                        <option value="detail">Detail</option>
                        <option value="package">Package</option>
                        <option value="lifestyle">Lifestyle</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="is-primary-upload">
                        <input type="checkbox" id="is-primary-upload">
                        Primary Image
                    </label>
                </div>
                <div class="form-actions">
                    <button type="button" class="btn-cancel-upload">Cancel</button>
                    <button type="submit" class="btn-upload-image">Upload</button>
                </div>
            </form>
        `;
        
        // Add gallery and upload panel to popup content
        popupContent.appendChild(gallerySection);
        popupContainer.appendChild(uploadPanel);
        
        // Add to DOM
        popupOverlay.appendChild(popupContainer);
        document.body.appendChild(popupOverlay);
        
        // Setup event listeners
        setupProductPopupEventListeners(popupOverlay, productData.popup_data);
        
        // Gallery item click event (to show image popup)
        const galleryItems = popupOverlay.querySelectorAll('.gallery-item');
        galleryItems.forEach(item => {
            item.addEventListener('click', () => {
                const imageId = item.getAttribute('data-image-id');
                const productId = item.getAttribute('data-product-id');
                popupOverlay.remove();
                showImagePopup(imageId, productId);
            });
        });
        
        // Add Image button click event
        const addImageBtn = popupOverlay.querySelector('.btn-add-image');
        if (addImageBtn) {
            addImageBtn.addEventListener('click', () => {
                const uploadPanel = popupOverlay.querySelector('.image-upload-panel');
                uploadPanel.style.display = 'block';
            });
        }
        
        // Close upload panel
        const closeUploadBtn = popupOverlay.querySelector('.btn-close-upload');
        const cancelUploadBtn = popupOverlay.querySelector('.btn-cancel-upload');
        
        const closeUploadPanel = () => {
            const uploadPanel = popupOverlay.querySelector('.image-upload-panel');
            uploadPanel.style.display = 'none';
            
            // Reset form
            const uploadForm = popupOverlay.querySelector('#image-upload-form');
            uploadForm.reset();
            
            // Reset preview
            const previewContainer = popupOverlay.querySelector('.image-preview-container');
            previewContainer.style.display = 'none';
        };
        
        if (closeUploadBtn) {
            closeUploadBtn.addEventListener('click', closeUploadPanel);
        }
        
        if (cancelUploadBtn) {
            cancelUploadBtn.addEventListener('click', closeUploadPanel);
        }
        
        // Image file input change (for preview)
        const imageFileInput = popupOverlay.querySelector('#image-file');
        if (imageFileInput) {
            imageFileInput.addEventListener('change', (e) => {
                const file = e.target.files[0];
                if (file) {
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        const previewContainer = popupOverlay.querySelector('.image-preview-container');
                        const previewImage = popupOverlay.querySelector('.image-preview');
                        
                        previewImage.src = e.target.result;
                        previewContainer.style.display = 'block';
                    };
                    reader.readAsDataURL(file);
                }
            });
        }
        
        // Upload form submit
        const uploadForm = popupOverlay.querySelector('#image-upload-form');
        if (uploadForm) {
            uploadForm.addEventListener('submit', (e) => {
                e.preventDefault();
                
                const fileInput = popupOverlay.querySelector('#image-file');
                const altTextInput = popupOverlay.querySelector('#alt-text-upload');
                const imageTypeSelect = popupOverlay.querySelector('#image-type-upload');
                const isPrimaryCheckbox = popupOverlay.querySelector('#is-primary-upload');
                
                if (!fileInput.files.length) {
                    showNotification('Please select an image file', 'warning');
                    return;
                }
                
                // Create FormData
                const formData = new FormData();
                formData.append('file', fileInput.files[0]);
                formData.append('alt_text', altTextInput.value);
                formData.append('image_type', imageTypeSelect.value);
                formData.append('is_primary', isPrimaryCheckbox.checked);
                
                // Show loading overlay
                showLoadingOverlay();
                
                // Upload the image
                fetch(`/api/popups/product/${productId}/image`, {
                    method: 'POST',
                    body: formData
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Failed to upload image');
                    }
                    return response.json();
                })
                .then(data => {
                    // Hide loading overlay
                    hideLoadingOverlay();
                    
                    // Show success message
                    showNotification('Image uploaded successfully!', 'success');
                    
                    // Close the upload panel
                    closeUploadPanel();
                    
                    // Refresh the popup to show the new image
                    popupOverlay.remove();
                    showProductGalleryPopup(productId);
                })
                .catch(error => {
                    console.error('Error uploading image:', error);
                    hideLoadingOverlay();
                    showNotification('Failed to upload image. Please try again.', 'error');
                });
            });
        }
        
        // Hide loading overlay
        hideLoadingOverlay();
    })
    .catch(error => {
        console.error('Error loading product gallery popup:', error);
        hideLoadingOverlay();
        showNotification('Failed to load product gallery. Please try again.', 'error');
    });
}

/**
 * Show a full-size image viewer
 * 
 * @param {string} imageSrc - Source URL of the image
 * @param {string} altText - Alt text for the image
 */
function showFullSizeImageViewer(imageSrc, altText) {
    // Create viewer HTML
    const viewerHtml = `
        <div class="fullsize-image-viewer">
            <button class="close-viewer-btn">&times;</button>
            <img src="${imageSrc}" alt="${altText || 'Product image'}" class="fullsize-image">
        </div>
    `;
    
    // Add viewer to the DOM
    const viewerOverlay = document.createElement('div');
    viewerOverlay.className = 'fullsize-viewer-overlay';
    viewerOverlay.innerHTML = viewerHtml;
    document.body.appendChild(viewerOverlay);
    
    // Add animation classes
    setTimeout(() => {
        viewerOverlay.classList.add('active');
    }, 10);
    
    // Setup event listeners
    const closeBtn = viewerOverlay.querySelector('.close-viewer-btn');
    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            viewerOverlay.classList.remove('active');
            setTimeout(() => {
                viewerOverlay.remove();
            }, 300);
        });
    }
    
    // Close on click outside image
    viewerOverlay.addEventListener('click', (e) => {
        if (e.target === viewerOverlay) {
            viewerOverlay.classList.remove('active');
            setTimeout(() => {
                viewerOverlay.remove();
            }, 300);
        }
    });
}

/**
 * Close all enhanced popups
 */
function closeAllEnhancedPopups() {
    document.querySelectorAll('.enhanced-popup-overlay').forEach(overlay => {
        overlay.classList.remove('active');
        const content = overlay.querySelector('.enhanced-popup-content');
        if (content) {
            content.classList.remove('active');
        }
        
        // Remove after animation completes
        setTimeout(() => {
            overlay.remove();
        }, 300);
    });
}

/**
 * Show loading overlay
 */
function showLoadingOverlay() {
    let loadingOverlay = document.querySelector('.loading-overlay');
    
    if (!loadingOverlay) {
        loadingOverlay = document.createElement('div');
        loadingOverlay.className = 'loading-overlay';
        loadingOverlay.innerHTML = `
            <div class="loading-spinner"></div>
            <p>Loading...</p>
        `;
        document.body.appendChild(loadingOverlay);
    }
    
    // Show with animation
    setTimeout(() => {
        loadingOverlay.classList.add('active');
    }, 10);
}

/**
 * Hide loading overlay
 */
function hideLoadingOverlay() {
    const loadingOverlay = document.querySelector('.loading-overlay');
    if (loadingOverlay) {
        loadingOverlay.classList.remove('active');
        
        // Remove after animation completes
        setTimeout(() => {
            loadingOverlay.remove();
        }, 300);
    }
}

/**
 * Show notification message
 * 
 * @param {string} title - Notification title
 * @param {string} message - Notification message
 */
function showNotification(title, message) {
    const notificationId = `notification-${Date.now()}`;
    
    const notificationHtml = `
        <div class="notification" id="${notificationId}">
            <div class="notification-header">
                <h4>${title}</h4>
                <button class="notification-close">&times;</button>
            </div>
            <div class="notification-body">
                <p>${message}</p>
            </div>
        </div>
    `;
    
    // Create or get notification container
    let notificationContainer = document.querySelector('.notification-container');
    if (!notificationContainer) {
        notificationContainer = document.createElement('div');
        notificationContainer.className = 'notification-container';
        document.body.appendChild(notificationContainer);
    }
    
    // Add notification
    notificationContainer.insertAdjacentHTML('beforeend', notificationHtml);
    
    // Get the notification element
    const notification = document.getElementById(notificationId);
    
    // Add active class after a brief delay (for animation)
    setTimeout(() => {
        notification.classList.add('active');
    }, 10);
    
    // Setup close button
    const closeBtn = notification.querySelector('.notification-close');
    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            closeNotification(notificationId);
        });
    }
    
    // Auto-close after 5 seconds
    setTimeout(() => {
        closeNotification(notificationId);
    }, 5000);
}

/**
 * Close a notification
 * 
 * @param {string} notificationId - ID of the notification to close
 */
function closeNotification(notificationId) {
    const notification = document.getElementById(notificationId);
    if (notification) {
        notification.classList.remove('active');
        
        // Remove after animation completes
        setTimeout(() => {
            notification.remove();
            
            // Remove container if empty
            const container = document.querySelector('.notification-container');
            if (container && container.children.length === 0) {
                container.remove();
            }
        }, 300);
    }
}

/**
 * Save changes made in the popup
 * 
 * @param {HTMLElement} popupOverlay - The popup overlay element
 * @param {string|number} productId - ID of the product to update
 */
async function savePopupChanges(popupOverlay, productId) {
    try {
        // Show loading indicator
        showLoadingOverlay();
        
        // Collect data from the popup form
        const nameInput = popupOverlay.querySelector(`#popup-name-${productId}`);
        const priceInput = popupOverlay.querySelector(`#popup-price-${productId}`);
        const descInput = popupOverlay.querySelector(`#popup-desc-${productId}`);
        
        // Prepare the changes object
        const changes = {
            product_changes: {
                name: nameInput ? nameInput.value : undefined,
                description: descInput ? descInput.value : undefined,
                price: priceInput ? parseFloat(priceInput.value) : undefined
            },
            image_changes: {} // We'll collect image changes if available
        };
        
        // Look for any image-related checkboxes or fields
        const imageFields = popupOverlay.querySelectorAll('[data-image-id]');
        imageFields.forEach(field => {
            const imageId = field.getAttribute('data-image-id');
            if (!imageId) return;
            
            // Initialize image entry if it doesn't exist
            if (!changes.image_changes[imageId]) {
                changes.image_changes[imageId] = {};
            }
            
            // Collect different types of fields
            if (field.type === 'checkbox') {
                changes.image_changes[imageId][field.name] = field.checked;
            } else if (field.tagName === 'SELECT' || field.tagName === 'INPUT' || field.tagName === 'TEXTAREA') {
                changes.image_changes[imageId][field.name] = field.value;
            }
        });
        
        // Send updates to the server
        const response = await fetch(`/api/popups/product/${productId}/save`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(changes)
        });
        
        if (!response.ok) {
            throw new Error(`Failed to save changes: ${response.statusText}`);
        }
        
        const result = await response.json();
        
        // Hide loading and show success message
        hideLoadingOverlay();
        showNotification('Success', 'Changes saved successfully');
        
        // Close the popup
        closeAllEnhancedPopups();
        
        // Refresh the product display
        setTimeout(() => {
            // Find product card and update it if possible
            const productCard = document.querySelector(`.product-card[data-product-id="${productId}"]`);
            if (productCard) {
                // Get product details again
                fetch(`/api/products/${productId}`)
                    .then(response => response.json())
                    .then(updatedProduct => {
                        // Update card with new data
                        const nameElement = productCard.querySelector('.product-name');
                        const descElement = productCard.querySelector('.product-desc');
                        const priceElement = productCard.querySelector('.product-price');
                        
                        if (nameElement) nameElement.textContent = updatedProduct.name;
                        if (descElement) descElement.textContent = updatedProduct.description;
                        if (priceElement) priceElement.textContent = `$${updatedProduct.price.toFixed(2)}`;
                    })
                    .catch(error => console.error('Error updating product card:', error));
            }
        }, 500);
        
    } catch (error) {
        console.error('Error saving popup changes:', error);
        hideLoadingOverlay();
        showNotification('Error', 'Could not save changes. Please try again.');
    }
}

/**
 * Save changes made to an image
 * 
 * @param {HTMLElement} popupOverlay - The popup overlay element
 * @param {string|number} productId - ID of the product
 * @param {string|number} imageId - ID of the image to update
 */
async function saveImageChanges(popupOverlay, productId, imageId) {
    try {
        // Show loading indicator
        showLoadingOverlay();
        
        // Collect data from the form fields
        const altTextInput = popupOverlay.querySelector(`#alt-text`);
        const imageTypeSelect = popupOverlay.querySelector(`#image-type`);
        const isPrimaryCheckbox = popupOverlay.querySelector(`#is-primary`);
        
        // Prepare the changes object
        const changes = {
            product_changes: {}, // No product changes when updating an image
            image_changes: {}
        };
        
        // Add image data to changes
        changes.image_changes[imageId] = {
            alt_text: altTextInput ? altTextInput.value : undefined,
            image_type: imageTypeSelect ? imageTypeSelect.value : undefined,
            is_primary: isPrimaryCheckbox ? isPrimaryCheckbox.checked : undefined
        };
        
        // Show loading indicator or disable button
        const saveButton = popupOverlay.querySelector('.btn-save');
        saveButton.textContent = 'Saving...';
        saveButton.disabled = true;
        
        // Send updates to the server
        const response = await fetch(`/api/popups/product/${productId}/image/${imageId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(changes)
        });
        
        if (!response.ok) {
            throw new Error(`Failed to save image changes: ${response.statusText}`);
        }
        
        const result = await response.json();
        
        // Hide loading and show success message
        hideLoadingOverlay();
        showNotification('Image updated successfully!', 'success');
        
        // If the image is set as primary and the operation was successful, refresh the popup
        // to show the updated status
        if (isPrimaryCheckbox && isPrimaryCheckbox.checked && result.images_updated) {
            closeAllEnhancedPopups();
            await showEnhancedImagePopup(imageId);
        }
        
    } catch (error) {
        console.error('Error saving image changes:', error);
        hideLoadingOverlay();
        showNotification('Failed to update image. Please try again.', 'error');
    } finally {
        // Reset button state
        saveButton.textContent = 'Save Changes';
        saveButton.disabled = false;
    }
}

function deleteImage(popupOverlay, productId, imageId) {
    // Show loading indicator
    const deleteButton = popupOverlay.querySelector('.btn-delete');
    deleteButton.textContent = 'Deleting...';
    deleteButton.disabled = true;
    
    fetch(`/api/popups/product/${productId}/image/${imageId}`, {
        method: 'DELETE'
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Error: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        // Show success message
        showNotification('Image deleted successfully!', 'success');
        
        // Close the popup and refresh the product gallery
        popupOverlay.remove();
        showProductGalleryPopup(productId);
    })
    .catch(error => {
        console.error('Error deleting image:', error);
        showNotification('Failed to delete image. Please try again.', 'error');
    })
    .finally(() => {
        // Reset button state
        deleteButton.textContent = 'Delete Image';
        deleteButton.disabled = false;
    });
}

// Function to show image popup
function showImagePopup(imageId, productId) {
    // Show loading overlay while fetching data
    showLoadingOverlay();
    
    // Fetch image data from the server
    fetch(`/api/popups/image/${imageId}?product_id=${productId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`Error: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            // Create popup overlay
            const popupOverlay = document.createElement('div');
            popupOverlay.className = 'enhanced-popup-overlay';
            
            // Create popup container
            const popupContainer = document.createElement('div');
            popupContainer.className = 'enhanced-popup-container';
            
            // Add popup HTML
            popupContainer.innerHTML = createImagePopupHtml(data.popup_data);
            
            // Add to DOM
            popupOverlay.appendChild(popupContainer);
            document.body.appendChild(popupOverlay);
            
            // Setup event listeners
            setupImagePopupEventListeners(popupOverlay, data.popup_data);
            
            // Hide loading overlay
            hideLoadingOverlay();
        })
        .catch(error => {
            console.error('Error loading image popup:', error);
            hideLoadingOverlay();
            showNotification('Failed to load image details. Please try again.', 'error');
        });
} 
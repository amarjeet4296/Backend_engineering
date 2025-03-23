const express = require('express');
const router = express.Router();

// Mock data - in a real application, this would come from a database
let products = [
  {
    id: 1,
    name: 'Product 1',
    description: 'This is product 1',
    price: 19.99,
    imageUrl: '/images/product1.jpg',
    thumbnailUrl: '/images/thumbnails/product1.jpg'
  },
  {
    id: 2,
    name: 'Product 2',
    description: 'This is product 2',
    price: 29.99,
    imageUrl: '/images/product2.jpg',
    thumbnailUrl: '/images/thumbnails/product2.jpg'
  },
  {
    id: 3,
    name: 'Product 3',
    description: 'This is product 3',
    price: 39.99,
    imageUrl: '/images/product3.jpg',
    thumbnailUrl: '/images/thumbnails/product3.jpg'
  }
];

// Get all products
router.get('/', (req, res) => {
  res.json(products);
});

// Get a single product
router.get('/:id', (req, res) => {
  const product = products.find(p => p.id === parseInt(req.params.id));
  if (!product) {
    return res.status(404).json({ message: 'Product not found' });
  }
  res.json(product);
});

// Create a product
router.post('/', (req, res) => {
  const newProduct = {
    id: products.length + 1,
    name: req.body.name,
    description: req.body.description,
    price: req.body.price,
    imageUrl: req.body.imageUrl || '/images/placeholder.jpg',
    thumbnailUrl: req.body.thumbnailUrl || '/images/thumbnails/placeholder.jpg'
  };
  
  products.push(newProduct);
  res.status(201).json(newProduct);
});

// Update a product - this is what will happen when user edits in the popup
router.put('/:id', (req, res) => {
  const productId = parseInt(req.params.id);
  const productIndex = products.findIndex(p => p.id === productId);
  
  if (productIndex === -1) {
    return res.status(404).json({ message: 'Product not found' });
  }
  
  // Update product fields
  const updatedProduct = {
    ...products[productIndex],
    name: req.body.name || products[productIndex].name,
    description: req.body.description || products[productIndex].description,
    price: req.body.price || products[productIndex].price,
    imageUrl: req.body.imageUrl || products[productIndex].imageUrl,
    thumbnailUrl: req.body.thumbnailUrl || products[productIndex].thumbnailUrl
  };
  
  products[productIndex] = updatedProduct;
  res.json(updatedProduct);
});

// Delete a product
router.delete('/:id', (req, res) => {
  const productId = parseInt(req.params.id);
  const productIndex = products.findIndex(p => p.id === productId);
  
  if (productIndex === -1) {
    return res.status(404).json({ message: 'Product not found' });
  }
  
  products = products.filter(p => p.id !== productId);
  res.json({ message: 'Product deleted successfully' });
});

module.exports = router; 
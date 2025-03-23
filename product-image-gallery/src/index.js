const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
const dotenv = require('dotenv');

// Load environment variables
dotenv.config();

// Import routes
const productRoutes = require('./api/productRoutes');
const imageRoutes = require('./api/imageRoutes');

// Initialize express app
const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

// Static files directory
app.use(express.static('public'));

// Routes
app.use('/api/products', productRoutes);
app.use('/api/images', imageRoutes);

// Root route
app.get('/', (req, res) => {
  res.send('Product Image Gallery API is running');
});

// Start server
app.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
}); 
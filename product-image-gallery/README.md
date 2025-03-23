# Product Image Gallery

This application provides a grid-based product image gallery with local file storage for images.

## Technology Stack

- **Backend**: Python FastAPI
- **Storage**: Local file storage
- **Image Processing**: Pillow for automatic thumbnail generation
- **Database**: In-memory data (for development)

## Architecture Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  Frontend UI    │────▶│  Backend API    │────▶│  Database       │
│  (Image Grid)   │     │  (FastAPI)      │     │  (Products &    │
│                 │     │                 │     │   Images)       │
└────────┬────────┘     └────────┬────────┘     └─────────────────┘
         │                       │
         │                       │
         │               ┌───────▼───────┐
         │               │               │
         └──────────────▶│  Local File   │
                         │  Storage      │
                         │               │
                         └───────────────┘
```

## Key Features

1. **Image Grid Display**: Products are displayed in a grid layout
2. **Click Popup**: Detailed view appears when clicking on product images
3. **CRUD Operations**: Create, Read, Update, Delete products and images
4. **Dynamic Thumbnails**: Thumbnails are automatically generated from original images
5. **Local Storage**: Images stored in local file system

## Installation and Setup

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Start the server:
   ```
   python run.py
   ```
4. Access the API at `http://127.0.0.1:8000`
5. Access API documentation at `http://127.0.0.1:8000/docs`

## How Thumbnails Work

The application now automatically generates thumbnails from original images:

1. When images are uploaded, a thumbnail is created and stored
2. When loading existing images without thumbnails, the system generates thumbnails on-the-fly
3. Thumbnails are cached in the thumbnails directory for future use
4. No manual thumbnail creation is required

## Database Design Options

### Option 1: Single Table Approach
```
Products Table
- id (PK)
- name
- description
- price
- imageUrl (main image URL)
- thumbnailUrl (thumbnail URL)
- other product attributes...
```

**Pros:**
- Simpler queries for basic operations
- No joins needed for common operations
- Better performance for simple read operations

**Cons:**
- Limited flexibility if a product needs multiple images
- Data redundancy if product details are repeated

### Option 2: Two Table Approach
```
Products Table
- id (PK)
- name
- description
- price
- other product attributes...

Images Table
- id (PK)
- productId (FK)
- imageUrl (URL to image)
- thumbnailUrl (URL to thumbnail)
- isPrimary (boolean to indicate main product image)
- imageType (main, thumbnail, gallery, etc.)
```

**Pros:**
- Support for multiple images per product
- Better data organization and reduced redundancy
- More flexible for future extensions

**Cons:**
- Requires joins for complete product information
- Slightly more complex queries

## Recommendation

For a product catalog where each product might have multiple images and different image types (main, thumbnails, gallery), the **two-table approach** provides better flexibility and scalability. This approach allows for:

1. Adding multiple images per product
2. Designating different image types
3. Better organization of the image data
4. Easier management of the image files

The separation also makes it cleaner to manage the lifecycle of products and images independently.

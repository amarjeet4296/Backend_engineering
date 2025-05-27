# Image Metadata API

A FastAPI-based web application for storing and managing image metadata.

## Features

- Store image metadata in a SQL database
- API endpoints for fetching images and their details
- Update image details via API
- Automatic handling of NULL reference IDs

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure database:
Update the `app/database/config.py` file with your database credentials.

3. Run migrations:
```bash
alembic upgrade head
```

4. Start the application:
```bash
uvicorn app.main:app --reload
```

## API Endpoints

- `GET /images`: Fetch all images from the database
- `GET /popup/{filename}`: Fetch image details by filename
- `POST /update`: Update image details (referenceid, thumbnail, gtinnumber)

## Database Schema

- `filename`: Primary Key, stores the image name
- `thumbnail`: URL to the image
- `referenceid`: nullable, initially NULL
- `gtinnumber`: Product GTIN number
- `itemdesc`: Item description 
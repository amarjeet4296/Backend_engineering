from sqlalchemy.orm import Session
from app.database.config import SessionLocal
from app.models.image import ImageMetadata
import traceback

# Sample data for testing
sample_images = [
    {
        "filename": "product1.jpg",
        "thumbnail": "https://via.placeholder.com/200x200?text=Product1",
        "referenceid": None,
        "gtinnumber": "12345678901234",
        "itemdesc": "Sample Product 1"
    },
    {
        "filename": "product2.jpg",
        "thumbnail": "https://via.placeholder.com/200x200?text=Product2",
        "referenceid": "REF-002",
        "gtinnumber": "12345678901235",
        "itemdesc": "Sample Product 2"
    },
    {
        "filename": "product3.jpg",
        "thumbnail": "https://via.placeholder.com/200x200?text=Product3",
        "referenceid": None,
        "gtinnumber": "12345678901236",
        "itemdesc": "Sample Product 3"
    },
    {
        "filename": "product4.jpg",
        "thumbnail": "https://via.placeholder.com/200x200?text=Product4",
        "referenceid": "REF-004",
        "gtinnumber": "12345678901237",
        "itemdesc": "Sample Product 4"
    },
    {
        "filename": "product5.jpg",
        "thumbnail": "https://via.placeholder.com/200x200?text=Product5",
        "referenceid": None,
        "gtinnumber": "12345678901238",
        "itemdesc": "Sample Product 5"
    }
]

def seed_db():
    db = SessionLocal()
    try:
        # Check if we already have data
        try:
            existing_count = db.query(ImageMetadata).count()
            if existing_count > 0:
                print(f"Database already contains {existing_count} records. Skipping seed.")
                return
        except Exception:
            # If table doesn't exist yet, assume we need to seed
            pass
        
        # Add sample data
        for image_data in sample_images:
            # Check if record already exists to avoid duplicates
            existing = db.query(ImageMetadata).filter(
                ImageMetadata.filename == image_data["filename"]
            ).first()
            
            if not existing:
                db_image = ImageMetadata(**image_data)
                db.add(db_image)
        
        db.commit()
        print(f"Successfully added sample images to the database.")
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    seed_db() 
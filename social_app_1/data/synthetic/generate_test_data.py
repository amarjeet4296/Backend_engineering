"""
Synthetic Test Data Generator Script
Generates test data for the social security application system.
"""

import os
import logging
import pandas as pd
import json
from data.synthetic.data_generator import SyntheticDataGenerator
from data.db_connector import DatabaseConnector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """
    Generate and save synthetic data for testing the application.
    """
    # Create output directories
    os.makedirs("data/synthetic/output", exist_ok=True)
    os.makedirs("data/synthetic/output/documents", exist_ok=True)
    
    logger.info("Starting synthetic data generation")
    
    # Initialize generator with fixed seed for reproducibility
    generator = SyntheticDataGenerator(seed=42)
    
    # Generate application data
    logger.info("Generating synthetic applications")
    applications = generator.generate_application_data(count=100)
    
    # Save to CSV
    applications_path = "data/synthetic/output/applications.csv"
    generator.save_to_csv(applications, applications_path)
    logger.info(f"Saved {len(applications)} applications to {applications_path}")
    
    # Generate document text examples for the first 10 applications
    logger.info("Generating synthetic documents")
    document_types = ['income', 'id', 'address', 'family']
    
    for i in range(10):
        app_data = applications.iloc[i].to_dict()
        
        # Generate document texts for this application
        app_documents = {}
        for doc_type in document_types:
            text = generator.generate_document_text(app_data, doc_type)
            app_documents[doc_type] = text
            
            # Save individual document texts
            doc_path = f"data/synthetic/output/documents/app_{i+1}_{doc_type}.txt"
            with open(doc_path, 'w') as f:
                f.write(text)
        
        # Save all documents for this application as JSON
        app_docs_path = f"data/synthetic/output/documents/app_{i+1}_documents.json"
        generator.save_to_json(app_documents, app_docs_path)
    
    logger.info(f"Generated document texts for 10 applications")
    
    # Generate recommendations for all applications
    logger.info("Generating enablement recommendations")
    all_recommendations = []
    
    for i in range(len(applications)):
        app_data = applications.iloc[i].to_dict()
        recommendations = generator.generate_enablement_recommendations(app_data)
        
        all_recommendations.append({
            "application_id": i + 1,
            "recommendations": recommendations
        })
    
    # Save all recommendations
    recommendations_path = "data/synthetic/output/recommendations.json"
    generator.save_to_json(all_recommendations, recommendations_path)
    logger.info(f"Saved recommendations to {recommendations_path}")
    
    # Load the data into the database if specified
    load_to_db = os.environ.get('LOAD_TO_DB', 'false').lower() == 'true'
    
    if load_to_db:
        logger.info("Loading synthetic data into database")
        try:
            # Initialize database connector
            db = DatabaseConnector()
            
            # Store applications in database
            for i in range(len(applications)):
                app_data = applications.iloc[i].to_dict()
                
                # Add recommendations if available
                app_data['enablement_recommendations'] = all_recommendations[i]['recommendations'] if i < len(all_recommendations) else []
                
                # Store in database
                app_id = db.store_application(app_data)
                logger.info(f"Stored application {i+1} with ID {app_id}")
            
            logger.info("Database loading complete")
        except Exception as e:
            logger.error(f"Error loading data into database: {str(e)}")
    
    logger.info("Synthetic data generation complete")

if __name__ == "__main__":
    main()

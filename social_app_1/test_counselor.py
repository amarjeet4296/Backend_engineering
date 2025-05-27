from counselor import CounselorAgent
from assessor import AssessorAgent
import os
from dotenv import load_dotenv

def main():
    # Load environment variables
    load_dotenv()
    
    # Initialize the CounselorAgent
    counselor = CounselorAgent()
    
    # Test data
    test_data = {
        "income": 45000,
        "family_size": 6,
        "address": "123 Main St, Anytown, USA",
        "assessment_status": "rejected",
        "risk_level": "high"
    }
    
    # Test different queries
    queries = [
        "What are the income requirements?",
        "Why was my application rejected?",
        "What can I do to improve my application?",
        "What documents do I need to submit?"
    ]
    
    print("Testing CounselorAgent...\n")
    
    for query in queries:
        print(f"\nQuery: {query}")
        print("-" * 50)
        guidance = counselor.provide_guidance(test_data, query)
        print(f"Response:\n{guidance}")
        print("-" * 50)

if __name__ == "__main__":
    main() 
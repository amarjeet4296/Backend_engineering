import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get configuration from environment variables
PORT = int(os.getenv("PORT", 8000))
HOST = os.getenv("HOST", "127.0.0.1")

if __name__ == "__main__":
    print("Starting Product Image Gallery API...")
    print(f"Access the API at http://{HOST}:{PORT}")
    print(f"API documentation is available at http://{HOST}:{PORT}/docs")
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=True) 
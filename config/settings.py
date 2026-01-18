import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:123456@localhost:5432/quran_db"
)

# Server configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))

# Print configuration (for debugging)
if __name__ == "__main__":
    print(f"DATABASE_URL: {DATABASE_URL}")
    print(f"HOST: {HOST}")
    print(f"PORT: {PORT}")
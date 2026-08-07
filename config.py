import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask
    SECRET_KEY = os.getenv("SECRET_KEY", "default-secret-key")
    
    # Database - SQLite
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DATABASE_PATH = os.getenv("DATABASE_PATH", "database/scraper.db")
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, DATABASE_PATH)}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # API Keys
    SEMANTIC_SCHOLAR_API_KEY = os.getenv("SEMANTIC_SCHOLAR_API_KEY", "")
    
    # API Endpoints
    SEMANTIC_SCHOLAR_API_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
    ARXIV_API_URL = "http://export.arxiv.org/api/query"
    
    # Folder paths
    PDF_DOWNLOAD_DIR = os.getenv("PDF_DOWNLOAD_DIR", "downloads/pdf")
    EXPORT_DIR = os.getenv("EXPORT_DIR", "exports")
    
    # Scraping settings
    MAX_PAPERS_PER_REQUEST = 100
    REQUEST_DELAY = 1.0  # delay antar request (detik) untuk menghindari rate limit
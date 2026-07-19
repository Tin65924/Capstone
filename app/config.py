import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/library_db')
    GOOGLE_OAUTH_CLIENT_ID = os.getenv('GOOGLE_OAUTH_CLIENT_ID')
    GOOGLE_OAUTH_CLIENT_SECRET = os.getenv('GOOGLE_OAUTH_CLIENT_SECRET')
    MAX_BORROW_LIMIT_STUDENT = 3
    MAX_BORROW_LIMIT_FACULTY = 10
    OVERNIGHT_DUE_DAYS = 1
    DAILY_CIRCULATION_DUE_DAYS = 7
    FACULTY_LOAN_DAYS = 30
    OVERDUE_FINE_PER_DAY = 10.0

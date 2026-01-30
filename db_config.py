"""
Database Configuration for Smart Study Planner
Supports both PostgreSQL and SQLite for development
"""

import os
from dotenv import load_dotenv
from urllib.parse import urlparse

# Load environment variables
load_dotenv()

class DatabaseConfig:
    """Database configuration class"""
    
    # Database type (postgresql or sqlite)
    DB_TYPE = os.getenv('DB_TYPE', 'sqlite')  # Default to SQLite for easier local development
    
    # PostgreSQL Configuration
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_NAME = os.getenv('DB_NAME', 'Study_Planner')
    DB_USER = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'Bhushan9545104832')
    
    # SQLite Configuration
    DB_SQLITE_PATH = os.getenv('DB_SQLITE_PATH', os.path.join(os.path.dirname(__file__), '..', 'study_planner.db'))
    
    # Connection pool settings
    DB_POOL_SIZE = int(os.getenv('DB_POOL_SIZE', '5'))
    DB_MAX_OVERFLOW = int(os.getenv('DB_MAX_OVERFLOW', '10'))
    
    @classmethod
    def get_connection_string(cls):
        """Generate connection string based on database type"""
        if cls.DB_TYPE == 'sqlite':
            return f"sqlite:///{cls.DB_SQLITE_PATH}"
        else:
            return cls.DB_HOST
    
    @classmethod
    def get_psycopg2_connection_params(cls):
        """Get connection parameters for psycopg2"""
        if cls.DB_TYPE == 'sqlite':
            return {'database': cls.DB_SQLITE_PATH}
        else:
            if cls.DB_HOST.startswith('postgresql://'):
                parsed = urlparse(cls.DB_HOST)
                return {
                    'host': parsed.hostname,
                    'port': parsed.port,
                    'database': parsed.path.lstrip('/'),
                    'user': parsed.username,
                    'password': parsed.password
                }
            else:
                return {
                    'host': cls.DB_HOST,
                    'port': cls.DB_PORT,
                    'database': cls.DB_NAME,
                    'user': cls.DB_USER,
                    'password': cls.DB_PASSWORD
                }

# Application Configuration
class AppConfig:
    """Application configuration"""
    
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', '5000'))
    
    # CORS settings
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')
    
    # Session settings
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

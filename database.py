"""
Database connection and operations module
Handles both PostgreSQL and SQLite database connections
"""

import os
from contextlib import contextmanager
from db_config import DatabaseConfig
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import appropriate database driver
if DatabaseConfig.DB_TYPE == 'sqlite':
    import sqlite3
    # Enable foreign key support for SQLite
    def dict_factory(cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d
else:
    import psycopg2
    from psycopg2 import pool, extras

class Database:
    """Database connection manager for both PostgreSQL and SQLite"""
    
    _connection_pool = None
    _db_type = DatabaseConfig.DB_TYPE
    
    @classmethod
    def initialize_pool(cls):
        """Initialize the connection pool"""
        try:
            if cls._connection_pool is None:
                if cls._db_type == 'sqlite':
                    # SQLite doesn't need a connection pool
                    cls._connection_pool = True
                    logger.info("SQLite database initialized successfully")
                else:
                    cls._connection_pool = psycopg2.pool.ThreadedConnectionPool(
                        minconn=1,
                        maxconn=DatabaseConfig.DB_POOL_SIZE,
                        **DatabaseConfig.get_psycopg2_connection_params()
                    )
                    logger.info("PostgreSQL connection pool initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing database connection: {e}")
            raise
    
    @classmethod
    def close_pool(cls):
        """Close all connections"""
        if cls._db_type != 'sqlite' and cls._connection_pool:
            cls._connection_pool.closeall()
            logger.info("Database connection pool closed")
    
    @classmethod
    @contextmanager
    def get_connection(cls):
        """Get a database connection"""
        if cls._connection_pool is None:
            cls.initialize_pool()
        
        if cls._db_type == 'sqlite':
            conn = sqlite3.connect(DatabaseConfig.DB_SQLITE_PATH)
            conn.row_factory = dict_factory
            conn.execute("PRAGMA foreign_keys = ON")
            try:
                yield conn
            finally:
                conn.close()
        else:
            conn = cls._connection_pool.getconn()
            try:
                yield conn
            finally:
                cls._connection_pool.putconn(conn)
    
    @classmethod
    @contextmanager
    def get_cursor(cls, cursor_factory=None):
        """Get a cursor from a connection"""
        with cls.get_connection() as conn:
            if cls._db_type == 'sqlite':
                cursor = conn.cursor()
            else:
                cursor = conn.cursor(cursor_factory=cursor_factory or extras.RealDictCursor)
            try:
                yield cursor
                conn.commit()
            except Exception as e:
                conn.rollback()
                logger.error(f"Database operation error: {e}")
                raise
            finally:
                cursor.close()
    
    @classmethod
    def execute_query(cls, query, params=None, fetch=True):
        """Execute a query and optionally fetch results"""
        with cls.get_cursor() as cursor:
            cursor.execute(query, params or ())
            if fetch:
                if cls._db_type == 'sqlite':
                    # Convert rows to dict format for consistency
                    columns = [desc[0] for desc in cursor.description] if cursor.description else []
                    rows = cursor.fetchall()
                    return [dict(zip(columns, row)) for row in rows]
                else:
                    return cursor.fetchall()
            return cursor.rowcount
    
    @classmethod
    def fetch_one(cls, query, params=None):
        """Fetch a single row"""
        with cls.get_cursor() as cursor:
            cursor.execute(query, params or ())
            if cls._db_type == 'sqlite':
                row = cursor.fetchone()
                if row and cursor.description:
                    columns = [desc[0] for desc in cursor.description]
                    return dict(zip(columns, row))
                return row
            else:
                return cursor.fetchone()
    
    @classmethod
    def fetch_all(cls, query, params=None):
        """Fetch all rows"""
        with cls.get_cursor() as cursor:
            cursor.execute(query, params or ())
            if cls._db_type == 'sqlite':
                rows = cursor.fetchall()
                if rows and cursor.description:
                    columns = [desc[0] for desc in cursor.description]
                    return [dict(zip(columns, row)) for row in rows]
                return rows
            else:
                return cursor.fetchall()
    
    @classmethod
    def test_connection(cls):
        """Test database connection"""
        try:
            with cls.get_cursor() as cursor:
                if DatabaseConfig.DB_TYPE == 'sqlite':
                    cursor.execute("SELECT sqlite_version();")
                    version = cursor.fetchone()
                    logger.info(f"SQLite version: {version[0]}")
                else:
                    cursor.execute("SELECT version();")
                    version = cursor.fetchone()
                    logger.info(f"PostgreSQL version: {version['version']}")
                return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

# Initialize the connection pool when module is imported
Database.initialize_pool()

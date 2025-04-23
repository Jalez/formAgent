"""
Database Manager for FormAgent

This module handles database connections and schema management
using SQLite as the backend.
"""

import os
import sqlite3
import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages database connections and operations for FormAgent."""
    
    def __init__(self, db_path: str):
        """
        Initialize database manager.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self._ensure_directory_exists()
        
    def _ensure_directory_exists(self):
        """Ensure that the directory for the database file exists."""
        directory = os.path.dirname(self.db_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
            logger.info(f"Created directory for database: {directory}")
    
    def get_connection(self):
        """
        Get a connection to the SQLite database.
        
        Returns:
            sqlite3.Connection: Database connection object
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Allow access to rows by column name
        return conn
    
    def initialize_database(self):
        """Initialize the database schema if it doesn't exist."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Create user_data table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_data (
                    id TEXT PRIMARY KEY,
                    data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create form_mappings table for storing form field mappings
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS form_mappings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    domain TEXT NOT NULL,
                    form_id TEXT,
                    field_name TEXT NOT NULL,
                    field_type TEXT,
                    user_field TEXT NOT NULL,
                    confidence REAL DEFAULT 1.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(domain, form_id, field_name)
                )
            """)
            
            # Create form_interpretations table for AI interpretations
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS form_interpretations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    domain TEXT NOT NULL,
                    form_id TEXT,
                    interpretation_data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    confidence REAL DEFAULT 0.0,
                    UNIQUE(domain, form_id)
                )
            """)
            
            # Create schema version table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Insert or update schema version
            cursor.execute("""
                INSERT OR REPLACE INTO schema_version (version, applied_at)
                VALUES (1, CURRENT_TIMESTAMP)
            """)
            
            conn.commit()
            logger.info("Database schema initialized successfully")
            
        except sqlite3.Error as e:
            logger.error(f"Database initialization error: {e}")
        finally:
            conn.close()
    
    def get_user_data(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user data by user ID.
        
        Args:
            user_id: The user identifier
            
        Returns:
            Dict or None: User data as dictionary, or None if not found
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT data FROM user_data WHERE id = ?",
                (user_id,)
            )
            
            result = cursor.fetchone()
            
            if result:
                return json.loads(result['data'])
            else:
                logger.info(f"No data found for user_id: {user_id}")
                return {}
                
        except sqlite3.Error as e:
            logger.error(f"Error fetching user data: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for user data: {e}")
            return None
        finally:
            conn.close()
    
    def save_user_data(self, user_id: str, data: Dict[str, Any]) -> bool:
        """
        Save or update user data.
        
        Args:
            user_id: The user identifier
            data: User data to save
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            serialized_data = json.dumps(data)
            
            # Insert or replace data
            cursor.execute(
                """
                INSERT OR REPLACE INTO user_data (id, data, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                """,
                (user_id, serialized_data)
            )
            
            conn.commit()
            logger.info(f"User data saved for user_id: {user_id}")
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Error saving user data: {e}")
            return False
        finally:
            conn.close()
    
    def get_form_mappings(self, domain: str, form_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get form field mappings for a specific domain and optional form ID.
        
        Args:
            domain: The website domain
            form_id: Optional form identifier
            
        Returns:
            List[Dict]: List of form field mappings
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if form_id:
                cursor.execute(
                    """
                    SELECT field_name, field_type, user_field, confidence
                    FROM form_mappings
                    WHERE domain = ? AND form_id = ?
                    """,
                    (domain, form_id)
                )
            else:
                cursor.execute(
                    """
                    SELECT field_name, field_type, user_field, confidence
                    FROM form_mappings
                    WHERE domain = ?
                    """,
                    (domain,)
                )
            
            mappings = []
            for row in cursor.fetchall():
                mappings.append({
                    'field_name': row['field_name'],
                    'field_type': row['field_type'],
                    'user_field': row['user_field'],
                    'confidence': row['confidence']
                })
                
            return mappings
            
        except sqlite3.Error as e:
            logger.error(f"Error fetching form mappings: {e}")
            return []
        finally:
            conn.close()
    
    def save_form_mapping(self, 
                         domain: str, 
                         field_name: str, 
                         user_field: str, 
                         form_id: Optional[str] = None, 
                         field_type: Optional[str] = None,
                         confidence: float = 1.0) -> bool:
        """
        Save a form field mapping.
        
        Args:
            domain: The website domain
            field_name: The name of the form field
            user_field: The corresponding user data field
            form_id: Optional form identifier
            field_type: Optional field type (text, email, etc.)
            confidence: Confidence score for this mapping
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                """
                INSERT OR REPLACE INTO form_mappings 
                (domain, form_id, field_name, field_type, user_field, confidence)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (domain, form_id, field_name, field_type, user_field, confidence)
            )
            
            conn.commit()
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Error saving form mapping: {e}")
            return False
        finally:
            conn.close()
            
    def save_form_interpretation(self, 
                                domain: str, 
                                interpretation_data: Dict[str, Any], 
                                form_id: Optional[str] = None,
                                confidence: float = 0.0) -> bool:
        """
        Save an AI interpretation of a form.
        
        Args:
            domain: The website domain
            interpretation_data: The AI's interpretation data
            form_id: Optional form identifier
            confidence: Confidence score for this interpretation
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            serialized_data = json.dumps(interpretation_data)
            
            cursor.execute(
                """
                INSERT OR REPLACE INTO form_interpretations
                (domain, form_id, interpretation_data, confidence)
                VALUES (?, ?, ?, ?)
                """,
                (domain, form_id, serialized_data, confidence)
            )
            
            conn.commit()
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Error saving form interpretation: {e}")
            return False
        finally:
            conn.close()
            
    def get_form_interpretation(self, 
                               domain: str, 
                               form_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get the AI interpretation for a form.
        
        Args:
            domain: The website domain
            form_id: Optional form identifier
            
        Returns:
            Dict or None: The interpretation data or None if not found
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if form_id:
                cursor.execute(
                    """
                    SELECT interpretation_data, confidence 
                    FROM form_interpretations
                    WHERE domain = ? AND form_id = ?
                    """,
                    (domain, form_id)
                )
            else:
                cursor.execute(
                    """
                    SELECT interpretation_data, confidence
                    FROM form_interpretations
                    WHERE domain = ?
                    ORDER BY confidence DESC
                    LIMIT 1
                    """,
                    (domain,)
                )
                
            result = cursor.fetchone()
            
            if result:
                interpretation = json.loads(result['interpretation_data'])
                interpretation['confidence'] = result['confidence']
                return interpretation
            else:
                return None
                
        except sqlite3.Error as e:
            logger.error(f"Error fetching form interpretation: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for interpretation data: {e}")
            return None
        finally:
            conn.close()
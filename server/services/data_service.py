"""
Data Service for FormAgent

This module handles user data operations, providing a layer between
the API endpoints and the database.
"""

import logging
from typing import Dict, Any, Optional, List

from database.db_manager import DatabaseManager
from models.user_data import UserData

logger = logging.getLogger(__name__)

class DataService:
    """Service for managing user data operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize the data service.
        
        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager
    
    def get_user_data(self, user_id: str) -> Dict[str, Any]:
        """
        Get user data by user ID.
        
        Args:
            user_id: The user identifier
            
        Returns:
            Dict: User data as dictionary
        """
        try:
            # Fetch data from database
            data = self.db_manager.get_user_data(user_id)
            
            if not data:
                # Return empty object for new users
                return {}
            
            return data
            
        except Exception as e:
            logger.error(f"Error in get_user_data: {str(e)}")
            return {}
    
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
            # Create a UserData instance for validation
            user_data = UserData.from_dict(user_id, data)
            
            # Save to database
            success = self.db_manager.save_user_data(user_id, user_data.to_dict())
            
            return success
            
        except Exception as e:
            logger.error(f"Error in save_user_data: {str(e)}")
            return False
    
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
            return self.db_manager.get_form_mappings(domain, form_id)
        except Exception as e:
            logger.error(f"Error in get_form_mappings: {str(e)}")
            return []
    
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
            return self.db_manager.save_form_mapping(
                domain, field_name, user_field, form_id, field_type, confidence
            )
        except Exception as e:
            logger.error(f"Error in save_form_mapping: {str(e)}")
            return False
            
    def bulk_save_form_mappings(self, 
                                domain: str, 
                                mappings: List[Dict[str, Any]], 
                                form_id: Optional[str] = None) -> bool:
        """
        Save multiple form field mappings in bulk.
        
        Args:
            domain: The website domain
            mappings: List of mapping dictionaries
            form_id: Optional form identifier
            
        Returns:
            bool: True if all successful, False if any failed
        """
        try:
            success = True
            
            for mapping in mappings:
                field_name = mapping.get('field_name')
                user_field = mapping.get('user_field')
                field_type = mapping.get('field_type')
                confidence = mapping.get('confidence', 1.0)
                
                if not field_name or not user_field:
                    continue
                    
                result = self.db_manager.save_form_mapping(
                    domain, field_name, user_field, form_id, field_type, confidence
                )
                
                if not result:
                    success = False
            
            return success
        except Exception as e:
            logger.error(f"Error in bulk_save_form_mappings: {str(e)}")
            return False
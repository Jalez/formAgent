"""
Form Interpreter for FormAgent

This module provides AI-powered form field analysis and interpretation
to improve form filling accuracy by understanding the context and intent
of form fields.
"""

import logging
import re
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Common form field patterns
EMAIL_PATTERN = re.compile(r'email|e[-_]?mail|mail', re.I)
PHONE_PATTERN = re.compile(r'phone|telephone|mobile|cell|tel', re.I)
NAME_PATTERN = re.compile(r'name|full[-_]?name', re.I)
FIRST_NAME_PATTERN = re.compile(r'first[-_]?name|given[-_]?name|fname', re.I)
LAST_NAME_PATTERN = re.compile(r'last[-_]?name|surname|family[-_]?name|lname', re.I)
ADDRESS_PATTERN = re.compile(r'address|street|addr', re.I)
CITY_PATTERN = re.compile(r'city|town|locality', re.I)
STATE_PATTERN = re.compile(r'state|province|region|county', re.I)
ZIP_PATTERN = re.compile(r'zip|postal|post[-_]?code', re.I)
COUNTRY_PATTERN = re.compile(r'country|nation', re.I)

class FormInterpreter:
    """
    AI-powered form field interpreter for FormAgent.
    
    This class is responsible for analyzing form fields and suggesting
    mappings to user data fields. It uses a combination of pattern matching,
    field attribute analysis, and (in future versions) machine learning to 
    provide accurate field mappings.
    """
    
    def __init__(self):
        """Initialize the form interpreter."""
        # Could initialize ML models or external AI service clients here
        pass
        
    def interpret_form(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a form structure and suggest field mappings.
        
        Args:
            form_data: Dictionary containing form field information
            
        Returns:
            Dict: Interpretation results with suggested mappings
        """
        # Extract form fields
        fields = form_data.get('fields', [])
        if not fields:
            return {'mappings': [], 'confidence': 0}
        
        # Process each field to generate mappings
        mappings = []
        for field in fields:
            mapping = self._interpret_field(field)
            if mapping:
                mappings.append(mapping)
        
        # Calculate overall confidence
        confidence = self._calculate_confidence(mappings)
        
        return {
            'mappings': mappings,
            'confidence': confidence
        }
    
    def _interpret_field(self, field: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Interpret a single form field.
        
        Args:
            field: Dictionary with field properties (name, id, type, etc.)
            
        Returns:
            Dict or None: Mapping suggestion or None if no match found
        """
        field_name = field.get('name', '')
        field_id = field.get('id', '')
        field_type = field.get('type', '')
        field_label = field.get('label', '')
        field_placeholder = field.get('placeholder', '')
        
        # Combine all field attributes for better matching
        field_text = f"{field_name} {field_id} {field_label} {field_placeholder}"
        
        # Try to match using regex patterns
        user_field, confidence = self._match_field_patterns(field_text, field_type)
        
        if user_field:
            return {
                'field_name': field_name or field_id,
                'field_type': field_type,
                'user_field': user_field,
                'confidence': confidence
            }
        
        # In future versions, this could call a machine learning model
        # or external AI service for more advanced interpretation
        
        return None
    
    def _match_field_patterns(self, field_text: str, field_type: str) -> Tuple[Optional[str], float]:
        """
        Match field text against common patterns.
        
        Args:
            field_text: Combined text from field attributes
            field_type: HTML input type
            
        Returns:
            Tuple[str, float]: Suggested user field and confidence score
        """
        # Check for email fields
        if field_type == 'email' or EMAIL_PATTERN.search(field_text):
            return 'email', 0.9
        
        # Check for phone fields
        if field_type == 'tel' or PHONE_PATTERN.search(field_text):
            return 'phone', 0.9
        
        # Check for name fields
        if FIRST_NAME_PATTERN.search(field_text):
            return 'first_name', 0.9
        
        if LAST_NAME_PATTERN.search(field_text):
            return 'last_name', 0.9
        
        if NAME_PATTERN.search(field_text):
            return 'full_name', 0.8
        
        # Check for address fields
        if ADDRESS_PATTERN.search(field_text):
            return 'address_street', 0.8
        
        if CITY_PATTERN.search(field_text):
            return 'address_city', 0.8
        
        if STATE_PATTERN.search(field_text):
            return 'address_state', 0.8
        
        if ZIP_PATTERN.search(field_text):
            return 'address_zip', 0.9
        
        if COUNTRY_PATTERN.search(field_text):
            return 'address_country', 0.9
            
        # No match found
        return None, 0.0
    
    def _calculate_confidence(self, mappings: List[Dict[str, Any]]) -> float:
        """
        Calculate overall confidence for the form interpretation.
        
        Args:
            mappings: List of field mappings
            
        Returns:
            float: Overall confidence score between 0 and 1
        """
        if not mappings:
            return 0.0
        
        # Calculate average confidence of all mappings
        total_confidence = sum(m['confidence'] for m in mappings)
        return total_confidence / len(mappings)
        
    def enhance_with_ai(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use advanced AI/ML to enhance form interpretation.
        
        This method is a placeholder for future AI integration with
        large language models or specialized form understanding models.
        
        Args:
            form_data: Dictionary containing form field information
            
        Returns:
            Dict: Enhanced interpretation results
        """
        # Basic interpretation first
        interpretation = self.interpret_form(form_data)
        
        # TODO: Integrate with AI/ML service
        # This could involve sending the form data to an external API
        # or using a local machine learning model
        
        # For now, just return the basic interpretation
        return interpretation
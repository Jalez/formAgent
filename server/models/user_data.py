"""
UserData model for FormAgent

This module defines the data structure for user form data.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional


@dataclass
class UserData:
    """
    UserData class represents user information used for form filling.
    
    This structured representation helps organize and validate user data
    that will be used to fill forms.
    """
    
    # User identifier
    user_id: str
    
    # Personal information
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    
    # Contact information
    email: Optional[str] = None
    phone: Optional[str] = None
    
    # Address information
    address_street: Optional[str] = None
    address_city: Optional[str] = None
    address_state: Optional[str] = None
    address_zip: Optional[str] = None
    address_country: Optional[str] = None
    
    # Storage for additional custom fields
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, user_id: str, data: Dict[str, Any]) -> 'UserData':
        """
        Create a UserData instance from a dictionary.
        
        Args:
            user_id: The user identifier
            data: Dictionary containing user data
            
        Returns:
            UserData: A new UserData instance
        """
        # Extract known fields
        known_fields = {
            'first_name': data.get('first_name'),
            'last_name': data.get('last_name'),
            'full_name': data.get('full_name'),
            'email': data.get('email'),
            'phone': data.get('phone'),
            'address_street': data.get('address_street'),
            'address_city': data.get('address_city'),
            'address_state': data.get('address_state'),
            'address_zip': data.get('address_zip'),
            'address_country': data.get('address_country')
        }
        
        # Store all other fields as custom fields
        custom_fields = {k: v for k, v in data.items() 
                        if k not in known_fields and v is not None}
        
        return cls(user_id=user_id, custom_fields=custom_fields, **known_fields)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the UserData instance to a dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the user data
        """
        # Start with the standard fields
        result = {
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'email': self.email,
            'phone': self.phone,
            'address_street': self.address_street,
            'address_city': self.address_city,
            'address_state': self.address_state,
            'address_zip': self.address_zip,
            'address_country': self.address_country
        }
        
        # Remove None values
        result = {k: v for k, v in result.items() if v is not None}
        
        # Add custom fields
        result.update(self.custom_fields)
        
        return result
    
    def update(self, data: Dict[str, Any]) -> None:
        """
        Update user data with new values.
        
        Args:
            data: Dictionary containing updated user data
        """
        # Update known fields
        if 'first_name' in data:
            self.first_name = data['first_name']
        if 'last_name' in data:
            self.last_name = data['last_name']
        if 'full_name' in data:
            self.full_name = data['full_name']
        if 'email' in data:
            self.email = data['email']
        if 'phone' in data:
            self.phone = data['phone']
        if 'address_street' in data:
            self.address_street = data['address_street']
        if 'address_city' in data:
            self.address_city = data['address_city']
        if 'address_state' in data:
            self.address_state = data['address_state']
        if 'address_zip' in data:
            self.address_zip = data['address_zip']
        if 'address_country' in data:
            self.address_country = data['address_country']
            
        # Update custom fields
        for k, v in data.items():
            if k not in {
                'first_name', 'last_name', 'full_name', 
                'email', 'phone', 
                'address_street', 'address_city', 'address_state', 
                'address_zip', 'address_country'
            }:
                self.custom_fields[k] = v
/**
 * FormAgent Shared Constants
 * Centralized location for constants used across the extension
 */

// Server connection information
export const SERVER_URL = 'http://127.0.0.1:5000';

// Common form field mappings (field name variations to our data structure)
export const FIELD_MAPPINGS = {
  // Name fields
  'first_name': ['first_name', 'firstname', 'fname', 'given_name', 'givenname'],
  'last_name': ['last_name', 'lastname', 'lname', 'surname', 'family_name', 'familyname'],
  'full_name': ['full_name', 'fullname', 'name', 'your_name', 'yourname'],
  
  // Contact fields
  'email': ['email', 'email_address', 'emailaddress', 'e-mail', 'mail'],
  'phone': ['phone', 'phone_number', 'phonenumber', 'telephone', 'tel', 'mobile', 'cell'],
  
  // Address fields
  'address_street': ['address', 'street', 'street_address', 'streetaddress', 'addr', 'line1', 'address_line1'],
  'address_city': ['city', 'town', 'locality'],
  'address_state': ['state', 'province', 'region', 'county'],
  'address_zip': ['zip', 'zipcode', 'zip_code', 'postal', 'postal_code', 'postalcode'],
  'address_country': ['country', 'nation']
};

// Storage keys
export const STORAGE_KEYS = {
  USER_DATA: 'userData',
  DISABLED_SITES: 'disabledSites'
};

// Message actions
export const ACTIONS = {
  GET_DATA: 'getData',
  UPDATE_DATA: 'updateData',
  DATA_UPDATED: 'dataUpdated',
  FILL_FORMS: 'fillForms',
  UPDATE_DISABLE_STATUS: 'updateDisableStatus'
};
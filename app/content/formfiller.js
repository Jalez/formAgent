/**
 * FormAgent Content Script
 * Detects and fills form fields on web pages
 */

import { FIELD_MAPPINGS, ACTIONS } from '../shared/constants.js';

// Reversed mapping for looking up keys
let fieldLookup = {};
Object.entries(FIELD_MAPPINGS).forEach(([key, variations]) => {
  variations.forEach(variation => {
    fieldLookup[variation] = key;
  });
  // Also map the key to itself
  fieldLookup[key] = key;
});

/**
 * Helper to find the right data field to use for an input
 * @param {HTMLElement} input - The input element to examine
 * @param {Object} userData - The user data object
 * @returns {string|null} The value to fill, or null if no match
 */
function findMatchingUserData(input, userData) {
  if (!userData) return null;
  
  // Check various attributes that might contain field identifiers
  const identifiers = [
    input.name?.toLowerCase(),
    input.id?.toLowerCase(),
    input.getAttribute('placeholder')?.toLowerCase(),
    input.getAttribute('data-field')?.toLowerCase(),
    input.getAttribute('aria-label')?.toLowerCase()
  ].filter(Boolean); // Remove undefined/null values
  
  // Try to match each identifier with our mappings
  for (const identifier of identifiers) {
    // Direct match
    if (userData[identifier] !== undefined) {
      return userData[identifier];
    }
    
    // Match through field lookup mapping
    const mappedKey = fieldLookup[identifier];
    if (mappedKey && userData[mappedKey] !== undefined) {
      return userData[mappedKey];
    }
    
    // Try partial matches for longer identifiers
    for (const [key, value] of Object.entries(userData)) {
      if (identifier.includes(key)) {
        return value;
      }
    }
  }
  
  return null;
}

/**
 * Fill a single input field
 * @param {HTMLElement} input - The input to fill
 * @param {Object} userData - User data object
 * @returns {boolean} True if filled, false otherwise
 */
function fillInputField(input, userData) {
  // Skip fields that are already filled
  if (input.value) return false;
  
  // Skip hidden, disabled, or readonly fields
  if (input.type === 'hidden' || input.disabled || input.readOnly) return false;
  
  // Skip password fields (for security reasons)
  if (input.type === 'password') return false;
  
  // Find matching value for this field
  const valueToFill = findMatchingUserData(input, userData);
  if (!valueToFill) return false;
  
  // Set the value
  input.value = valueToFill;
  
  // Dispatch events to trigger any listeners on the page
  input.dispatchEvent(new Event('input', { bubbles: true }));
  input.dispatchEvent(new Event('change', { bubbles: true }));
  
  return true;
}

/**
 * Fill all form fields on the page
 */
async function fillFormFields() {
  // Request user data from background script
  const response = await browser.runtime.sendMessage({ action: ACTIONS.GET_DATA });
  const userData = response?.userData;
  
  if (!userData) {
    console.log('FormAgent: No user data available to fill forms');
    return;
  }
  
  // Find all input, textarea, and select elements
  const inputFields = document.querySelectorAll('input, textarea, select');
  let fillCount = 0;
  
  inputFields.forEach(input => {
    if (fillInputField(input, userData)) {
      fillCount++;
    }
  });
  
  if (fillCount > 0) {
    console.log(`FormAgent: Filled ${fillCount} form fields`);
  }
}

// Set up a MutationObserver to handle dynamically added form fields
function setupFormObserver() {
  const observer = new MutationObserver(mutations => {
    let shouldFill = false;
    
    // Check if any new input elements were added
    for (const mutation of mutations) {
      if (mutation.type === 'childList') {
        for (const node of mutation.addedNodes) {
          if (node.nodeName === 'INPUT' || node.nodeName === 'TEXTAREA' || node.nodeName === 'SELECT') {
            shouldFill = true;
            break;
          } else if (node.querySelectorAll) {
            const inputs = node.querySelectorAll('input, textarea, select');
            if (inputs.length > 0) {
              shouldFill = true;
              break;
            }
          }
        }
      }
      
      if (shouldFill) break;
    }
    
    if (shouldFill) {
      // Debounce to avoid filling multiple times for complex DOM changes
      clearTimeout(window.formAgentDebounce);
      window.formAgentDebounce = setTimeout(() => {
        fillFormFields();
      }, 500);
    }
  });
  
  // Start observing the document
  observer.observe(document.body, {
    childList: true,
    subtree: true
  });
}

// Listen for messages from popup
browser.runtime.onMessage.addListener((message) => {
  if (message.action === ACTIONS.FILL_FORMS) {
    fillFormFields();
    return Promise.resolve({ success: true });
  }
  
  if (message.action === ACTIONS.UPDATE_DISABLE_STATUS) {
    // Handle enable/disable status update for this site
    // This could store the status locally or simply refresh the page
    return Promise.resolve({ success: true });
  }
});

// Run when content script is loaded
(function() {
  // Wait a short moment to let the page's own JavaScript run first
  setTimeout(() => {
    fillFormFields();
    setupFormObserver();
  }, 500);
})();
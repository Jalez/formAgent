/**
 * FormAgent Options Page Script
 * Handles loading, editing, and saving user data
 */

import { SERVER_URL, STORAGE_KEYS, ACTIONS } from '../shared/constants.js';

const form = document.getElementById('userData');
const statusMessage = document.getElementById('statusMessage');

// Load user data when options page opens
async function loadUserData() {
  try {
    // First try to get data from the background script
    const response = await browser.runtime.sendMessage({ action: ACTIONS.GET_DATA });
    
    if (response && response.userData) {
      populateForm(response.userData);
      return;
    }
    
    // If that fails, try fetching directly from server
    const serverResponse = await fetch(`${SERVER_URL}/data`);
    
    if (serverResponse.ok) {
      const data = await serverResponse.json();
      populateForm(data);
    } else {
      showStatus('Could not load your data. Is FormAgent running?', 'error');
    }
  } catch (error) {
    console.error('Error loading user data:', error);
    showStatus('Error loading your data. Please check that FormAgent is running.', 'error');
  }
}

// Populate form with user data
function populateForm(userData) {
  if (!userData) return;
  
  // Get all input fields
  const inputs = form.querySelectorAll('input');
  
  // Fill each input with corresponding data if available
  inputs.forEach(input => {
    const fieldName = input.name;
    if (userData[fieldName]) {
      input.value = userData[fieldName];
    }
  });
  
  // Special handling for full name if only first and last are provided
  if (!userData.full_name && userData.first_name && userData.last_name) {
    const fullNameInput = document.getElementById('full_name');
    if (fullNameInput && !fullNameInput.value) {
      fullNameInput.value = `${userData.first_name} ${userData.last_name}`;
    }
  }
}

// Save user data
async function saveUserData(event) {
  event.preventDefault();
  
  const formData = new FormData(form);
  const userData = {};
  
  // Convert form data to object
  for (const [key, value] of formData.entries()) {
    if (value.trim()) {
      userData[key] = value.trim();
    }
  }
  
  try {
    // Send data to background script to update server and cache
    const response = await browser.runtime.sendMessage({
      action: ACTIONS.UPDATE_DATA,
      data: userData
    });
    
    if (response && response.success) {
      showStatus('Settings saved successfully!', 'success');
    } else {
      showStatus('Failed to save settings. Please try again.', 'error');
    }
  } catch (error) {
    console.error('Error saving data:', error);
    
    // Try saving directly to server as fallback
    try {
      const serverResponse = await fetch(`${SERVER_URL}/data`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(userData)
      });
      
      if (serverResponse.ok) {
        showStatus('Settings saved successfully!', 'success');
        // Update the background script cache
        await browser.runtime.sendMessage({
          action: ACTIONS.DATA_UPDATED,
          newData: userData
        });
      } else {
        showStatus('Failed to save settings. Is FormAgent running?', 'error');
      }
    } catch (serverError) {
      console.error('Error saving to server:', serverError);
      showStatus('Failed to connect to FormAgent server. Please check that it\'s running.', 'error');
    }
  }
}

// Display status message
function showStatus(message, type) {
  statusMessage.textContent = message;
  statusMessage.className = `status ${type}`;
  
  // Hide status after a few seconds
  setTimeout(() => {
    statusMessage.className = 'status hidden';
  }, 5000);
}

// Initialize the options page
document.addEventListener('DOMContentLoaded', loadUserData);
form.addEventListener('submit', saveUserData);

// Add helper to auto-populate full name from first and last name
const firstNameInput = document.getElementById('first_name');
const lastNameInput = document.getElementById('last_name');
const fullNameInput = document.getElementById('full_name');

function updateFullName() {
  const firstName = firstNameInput.value.trim();
  const lastName = lastNameInput.value.trim();
  
  if (firstName || lastName) {
    fullNameInput.value = `${firstName} ${lastName}`.trim();
  }
}

firstNameInput.addEventListener('blur', updateFullName);
lastNameInput.addEventListener('blur', updateFullName);
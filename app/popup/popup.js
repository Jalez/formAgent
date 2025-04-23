/**
 * FormAgent Popup Script
 * Handles popup UI interactions and server status checks
 */

import { SERVER_URL, STORAGE_KEYS, ACTIONS } from '../shared/constants.js';

const serverStatus = document.getElementById('serverStatus');
const serverStatusText = document.getElementById('serverStatusText');
const optionsButton = document.getElementById('optionsButton');
const fillFormsButton = document.getElementById('fillFormsButton');
const disableButton = document.getElementById('disableButton');

// Check server status when popup opens
async function checkServerStatus() {
  try {
    const response = await fetch(`${SERVER_URL}/data`, { 
      method: 'GET',
      headers: { 'Accept': 'application/json' }
    });
    
    if (response.ok) {
      serverStatus.classList.add('active');
      serverStatus.classList.remove('inactive');
      serverStatusText.textContent = 'Server is running';
      return true;
    } else {
      serverStatus.classList.add('inactive');
      serverStatus.classList.remove('active');
      serverStatusText.textContent = 'Server error';
      return false;
    }
  } catch (error) {
    console.error('Error checking server status:', error);
    serverStatus.classList.add('inactive');
    serverStatus.classList.remove('active');
    serverStatusText.textContent = 'Server not running';
    return false;
  }
}

// Open options page
function openOptions() {
  browser.runtime.openOptionsPage();
}

// Fill forms on the current page
async function fillForms() {
  try {
    // Get the current active tab
    const tabs = await browser.tabs.query({ active: true, currentWindow: true });
    
    if (tabs && tabs.length > 0) {
      // Send message to content script to fill forms
      await browser.tabs.sendMessage(tabs[0].id, { action: ACTIONS.FILL_FORMS });
      
      // Close popup after command is sent
      window.close();
    }
  } catch (error) {
    console.error('Error triggering form fill:', error);
  }
}

// Toggle form filling for the current site
async function toggleDisable() {
  try {
    const tabs = await browser.tabs.query({ active: true, currentWindow: true });
    
    if (tabs && tabs.length > 0) {
      const url = new URL(tabs[0].url);
      const hostname = url.hostname;
      
      // Get current disabled sites
      const result = await browser.storage.local.get(STORAGE_KEYS.DISABLED_SITES);
      let disabledSites = result[STORAGE_KEYS.DISABLED_SITES] || [];
      
      if (disableButton.textContent === 'Disable for This Site') {
        // Add site to disabled list
        if (!disabledSites.includes(hostname)) {
          disabledSites.push(hostname);
        }
        disableButton.textContent = 'Enable for This Site';
      } else {
        // Remove site from disabled list
        disabledSites = disabledSites.filter(site => site !== hostname);
        disableButton.textContent = 'Disable for This Site';
      }
      
      // Save updated disabled sites
      await browser.storage.local.set({ [STORAGE_KEYS.DISABLED_SITES]: disabledSites });
      
      // Inform the content script about the change
      await browser.tabs.sendMessage(tabs[0].id, { 
        action: ACTIONS.UPDATE_DISABLE_STATUS, 
        isDisabled: disableButton.textContent === 'Enable for This Site'
      });
    }
  } catch (error) {
    console.error('Error toggling disable status:', error);
  }
}

// Check if the current site is disabled
async function checkSiteDisabled() {
  try {
    const tabs = await browser.tabs.query({ active: true, currentWindow: true });
    
    if (tabs && tabs.length > 0) {
      const url = new URL(tabs[0].url);
      const hostname = url.hostname;
      
      // Get current disabled sites
      const result = await browser.storage.local.get(STORAGE_KEYS.DISABLED_SITES);
      const disabledSites = result[STORAGE_KEYS.DISABLED_SITES] || [];
      
      // Update button text based on disabled status
      if (disabledSites.includes(hostname)) {
        disableButton.textContent = 'Enable for This Site';
      } else {
        disableButton.textContent = 'Disable for This Site';
      }
    }
  } catch (error) {
    console.error('Error checking site disabled status:', error);
  }
}

// Initialize the popup
document.addEventListener('DOMContentLoaded', async () => {
  // Check server status
  await checkServerStatus();
  
  // Check if current site is disabled
  await checkSiteDisabled();
  
  // Set up event listeners
  optionsButton.addEventListener('click', openOptions);
  fillFormsButton.addEventListener('click', fillForms);
  disableButton.addEventListener('click', toggleDisable);
});
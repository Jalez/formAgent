/**
 * FormAgent Background Script
 * Handles data synchronization with the local server and manages cached form data
 */

import { SERVER_URL, STORAGE_KEYS, ACTIONS } from './shared/constants.js';

let userData = null;

// Fetch user data from server on startup or extension installation
async function fetchUserData() {
  try {
    const response = await fetch(`${SERVER_URL}/data`);
    if (response.ok) {
      userData = await response.json();
      // Store in local storage as backup in case service worker gets terminated
      browser.storage.local.set({ [STORAGE_KEYS.USER_DATA]: userData });
      console.log('FormAgent: User data successfully loaded from server');
      return userData;
    } else {
      console.error('FormAgent: Failed to fetch user data', response.status);
      return null;
    }
  } catch (error) {
    console.error('FormAgent: Error connecting to local server', error);
    
    // Try to load from cache if server connection fails
    try {
      const result = await browser.storage.local.get(STORAGE_KEYS.USER_DATA);
      if (result[STORAGE_KEYS.USER_DATA]) {
        userData = result[STORAGE_KEYS.USER_DATA];
        console.log('FormAgent: Loaded user data from cache');
        return userData;
      }
    } catch (storageError) {
      console.error('FormAgent: Error loading from cache', storageError);
    }
    
    return null;
  }
}

// Listen for messages from content scripts or popup
browser.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === ACTIONS.GET_DATA) {
    // If we have data in memory, return it immediately
    if (userData) {
      return Promise.resolve({ userData });
    }
    
    // Otherwise fetch it first
    return fetchUserData().then(data => {
      return { userData: data };
    });
  }
  
  if (message.action === ACTIONS.UPDATE_DATA) {
    return updateUserData(message.data).then(success => {
      return { success };
    });
  }
  
  if (message.action === ACTIONS.DATA_UPDATED) {
    userData = message.newData;
    browser.storage.local.set({ [STORAGE_KEYS.USER_DATA]: userData });
    return Promise.resolve({ success: true });
  }
});

// Update user data on the server
async function updateUserData(newData) {
  try {
    const response = await fetch(`${SERVER_URL}/data`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(newData)
    });
    
    if (response.ok) {
      userData = newData;
      browser.storage.local.set({ [STORAGE_KEYS.USER_DATA]: userData });
      console.log('FormAgent: User data successfully updated on server');
      return true;
    } else {
      console.error('FormAgent: Failed to update user data', response.status);
      return false;
    }
  } catch (error) {
    console.error('FormAgent: Error connecting to local server for update', error);
    return false;
  }
}

// Initialize on install or startup
browser.runtime.onInstalled.addListener(() => {
  fetchUserData();
});

browser.runtime.onStartup.addListener(() => {
  fetchUserData();
});
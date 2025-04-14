// auto-filler.js
// Script that automatically fills form inputs with random data

// Configuration
const config = {
    // How frequently to check for new inputs (in milliseconds)
    scanInterval: 1000,
    // Whether to automatically fill inputs when found
    autoFill: true,
    // Types of inputs to target
    targetInputTypes: ['text', 'email', 'password', 'number', 'tel', 'url', 'textarea', 'select'],
    // Whether to fill hidden inputs
    fillHiddenInputs: false
};

// Data generators for different types of inputs
const dataGenerators = {
    text: () => `Random_Text_${Math.floor(Math.random() * 10000)}`,
    email: () => `user${Math.floor(Math.random() * 10000)}@example.com`,
    password: () => `Password${Math.floor(Math.random() * 10000)}!`,
    number: () => Math.floor(Math.random() * 100).toString(),
    tel: () => `555${Math.floor(Math.random() * 10000000).toString().padStart(7, '0')}`,
    url: () => `https://example${Math.floor(Math.random() * 1000)}.com`,
    textarea: () => `This is some random text content.\nLine ${Math.floor(Math.random() * 100)}`,
    select: (selectElement) => {
        const options = selectElement.querySelectorAll('option');
        if (options.length > 1) {
            // Choose a random non-placeholder option (skip the first one if it appears to be a placeholder)
            const startIndex = options[0].value === '' || options[0].text.includes('Select') ? 1 : 0;
            const randomIndex = startIndex + Math.floor(Math.random() * (options.length - startIndex));
            return options[randomIndex].value;
        }
        return '';
    },
    checkbox: () => Math.random() > 0.5, // 50% chance of checking
    radio: (radioElement) => {
        // Find all radio buttons in the same group
        const name = radioElement.name;
        if (!name) return false;
        
        const radioGroup = document.querySelectorAll(`input[type="radio"][name="${name}"]`);
        if (radioGroup.length === 0) return false;
        
        // Select a random radio button from the group
        const randomIndex = Math.floor(Math.random() * radioGroup.length);
        return radioGroup[randomIndex] === radioElement;
    }
};

// Keep track of inputs we've already filled
const filledInputs = new Set();

// Function to fill an input with appropriate random data
function fillInput(input) {
    if (filledInputs.has(input)) return;
    
    // Check if the input is visible (unless configured to fill hidden inputs)
    if (!config.fillHiddenInputs) {
        const isVisible = input.offsetParent !== null;
        if (!isVisible) return;
    }

    try {
        let value;
        const tagName = input.tagName.toLowerCase();
        const inputType = input.type ? input.type.toLowerCase() : '';
        
        // Handle different input types
        if (tagName === 'textarea') {
            value = dataGenerators.textarea();
            input.value = value;
        } else if (tagName === 'select') {
            value = dataGenerators.select(input);
            if (value) input.value = value;
        } else if (inputType === 'checkbox') {
            const shouldCheck = dataGenerators.checkbox();
            input.checked = shouldCheck;
        } else if (inputType === 'radio') {
            const shouldCheck = dataGenerators.radio(input);
            if (shouldCheck) input.checked = true;
        } else if (config.targetInputTypes.includes(inputType)) {
            // Use specific generator for known types, or fall back to text
            value = dataGenerators[inputType] ? dataGenerators[inputType]() : dataGenerators.text();
            input.value = value;
        }
        
        // Mark this input as filled
        filledInputs.add(input);
        
        // Dispatch input event to trigger any event listeners
        input.dispatchEvent(new Event('input', { bubbles: true }));
        input.dispatchEvent(new Event('change', { bubbles: true }));
        
        console.log(`Filled input: ${input.name || input.id || 'unnamed'} with ${value || 'a value'}`);
    } catch (error) {
        console.error(`Error filling input:`, error);
    }
}

// Function to scan the page for inputs
function scanForInputs() {
    // Get all inputs, textareas, and selects
    const inputElements = document.querySelectorAll('input, textarea, select');
    
    inputElements.forEach(input => {
        if (config.autoFill) {
            fillInput(input);
        }
    });
}

// Observer to detect new inputs added to the DOM
function setupMutationObserver() {
    const observer = new MutationObserver(mutations => {
        let shouldScan = false;
        
        mutations.forEach(mutation => {
            if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                shouldScan = true;
            }
        });
        
        if (shouldScan) {
            scanForInputs();
        }
    });
    
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
    
    return observer;
}

// Main initialization function
function initialize() {
    console.log('Auto-filler script initialized');
    
    // Initial scan
    scanForInputs();
    
    // Set up periodic scanning
    const scanInterval = setInterval(scanForInputs, config.scanInterval);
    
    // Set up mutation observer to catch dynamically added inputs
    const observer = setupMutationObserver();
    
    // Add control hotkeys
    document.addEventListener('keydown', e => {
        // Ctrl+Alt+F to force fill all inputs
        if (e.ctrlKey && e.altKey && e.key === 'f') {
            config.autoFill = true;
            scanForInputs();
            e.preventDefault();
        }
        
        // Ctrl+Alt+S to toggle auto-fill
        if (e.ctrlKey && e.altKey && e.key === 's') {
            config.autoFill = !config.autoFill;
            console.log(`Auto-fill ${config.autoFill ? 'enabled' : 'disabled'}`);
            e.preventDefault();
        }
    });
    
    return {
        stop: () => {
            clearInterval(scanInterval);
            observer.disconnect();
            console.log('Auto-filler stopped');
        },
        forceRefill: () => {
            filledInputs.clear();
            scanForInputs();
            console.log('Forced refill of all inputs');
        }
    };
}

// Start the auto-filler when the page is fully loaded
if (document.readyState === 'complete') {
    window.autoFiller = initialize();
} else {
    window.addEventListener('load', () => {
        window.autoFiller = initialize();
    });
}

// Export controller for direct script inclusion
window.autoFiller = window.autoFiller || {
    start: initialize,
    isRunning: false
};
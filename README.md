# FormAgent - Intelligent Web Form Auto-Filling Agent

An advanced, multi-browser agent for automatically filling out web forms with contextually appropriate data.

## Features

- Automatic form input detection and filling with randomized but realistic data
- Support for multiple browsers (Chrome, Firefox, Safari)
- Browser extension mode for persistent use
- Standalone mode that attaches to existing browser sessions
- Customizable input types and patterns
- Support for dynamic form elements

## Future Development Plans

We're planning to enhance FormAgent with these advanced capabilities:

- **MCP Integration**: Leveraging the Model Context Protocol for:
  - Agent orchestration and multi-step reasoning
  - Tool integration with databases and external systems
  - Memory management across form filling sessions
  - Planning capabilities for complex forms
- **RAG Implementation**: Retrieval-Augmented Generation for context-aware form filling
- **Local LLM Integration**: Support for locally installed language models
- **Intelligent Form Analysis**: Advanced form field recognition and contextual value generation

These features will enable FormAgent to generate more realistic, contextually appropriate data based on the form's domain and purpose.

## Getting Started

### Prerequisites

- Python 3.6+
- One or more of the following browsers:
  - Google Chrome
  - Mozilla Firefox
  - Safari (macOS only)
- Required Python packages (see `requirements.txt`)

### Installation

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

### Usage

#### Command Line Interface

Run the main script to choose a browser and start filling forms:

```bash
python formagent.py --browser chrome
```

#### Browser-Specific Auto-Fillers

Attach to an existing browser session with remote debugging enabled:

```bash
# For Firefox
python src/browsers/firefox_auto_filler.py --attach

# For Chrome
python src/browsers/chrome_auto_filler.py --attach

# For Safari
python src/browsers/safari_auto_filler.py --attach
```

#### Additional Options

- `--debug`: Enable debug mode (non-headless)
- `--interval 1.5`: Set scanning interval to 1.5 seconds
- `--fill-hidden`: Include hidden form fields
- `--url "https://example.com/form"`: Open a specific URL

## Project Structure

- `formagent.py` - Main entry point
- `src/` - Source code
  - `core/` - Core functionality
    - `auto-filler.js` - Main JavaScript form filling logic
  - `browsers/` - Browser-specific implementations
- `docs/` - Documentation
- `test/` - Test files and forms
- `test-form.html` - Sample form for testing

## License

MIT

## Contributors

- Jaakko Rajala
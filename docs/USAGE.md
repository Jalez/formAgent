# FormAgent Usage Guide

This document provides examples and instructions for using FormAgent in various scenarios.

## Basic Usage

FormAgent can be run in multiple ways depending on your needs.

### Command Line Interface

The simplest way to use FormAgent is through the main CLI:

```bash
# Run with default browser (Firefox)
python formagent.py

# Run with a specific browser
python formagent.py --browser chrome
python formagent.py --browser firefox
python formagent.py --browser safari

# Enable debug mode (non-headless)
python formagent.py --debug

# Set custom scanning interval (default is 2 seconds)
python formagent.py --interval 1.5

# Fill hidden form fields
python formagent.py --fill-hidden
```

### Using the Shell Script

The `start_formagent.sh` script provides a convenient way to start FormAgent:

```bash
# Run with default options
./start_formagent.sh

# Choose a browser
./start_formagent.sh --chrome
./start_formagent.sh --firefox
./start_formagent.sh --safari

# Enable debug mode
./start_formagent.sh --debug

# Custom scanning interval
./start_formagent.sh --interval 1.5
```

### Using Make

The project includes a Makefile for common operations:

```bash
# Install dependencies
make install

# Run with default browser
make run

# Run with specific browser
make run-chrome
make run-firefox
make run-safari

# Run tests
make test

# Clean temporary files
make clean
```

## Browser-Specific Usage

### Firefox

```bash
# Run Firefox auto-filler directly
python src/browsers/firefox_auto_filler.py

# Attach to an existing Firefox instance with remote debugging enabled
python src/browsers/firefox_auto_filler.py --attach
```

### Chrome

```bash
# Run Chrome auto-filler directly
python src/browsers/chrome_auto_filler.py

# Attach to an existing Chrome instance with remote debugging enabled (needs to be started with --remote-debugging-port=9222)
python src/browsers/chrome_auto_filler.py --attach
```

### Safari (macOS only)

```bash
# Run Safari auto-filler directly
python src/browsers/safari_auto_filler.py

# Attach to an existing Safari session
python src/browsers/safari_auto_filler.py --attach
```

## Customizing Form Filling Behavior

The form filling behavior is controlled by the JavaScript code in `src/core/auto-filler.js`. 

When using FormAgent in a browser:

- Use `Ctrl+Alt+F` to force fill all form fields
- Use `Ctrl+Alt+S` to toggle auto-fill on/off

## Roadmap: Advanced Features

We're planning to enhance FormAgent with advanced AI capabilities that will make form filling smarter and more context-aware. Here's our roadmap for future development:

### 1. RAG (Retrieval-Augmented Generation) Integration

RAG will allow FormAgent to generate contextually appropriate form data by:

- Analyzing the form's structure and purpose
- Retrieving relevant information from a knowledge base
- Generating realistic, domain-specific values

Implementation plan:
- Create a database of common form field types and appropriate values
- Implement a retrieval mechanism based on field analysis
- Connect with language models to generate contextual values

### 2. MCP (Model Context Protocol) Integration

FormAgent will leverage the Model Context Protocol for advanced capabilities:

- **Agent Orchestration**: Coordinate multiple LLM steps for complex form filling tasks
- **Tool Integration**: Allow the agent to interact with databases, APIs, and other systems
- **Memory Management**: Remember previously seen forms and user preferences
- **Planning & Reasoning**: Understand relationships between form fields to generate coherent data

This comprehensive MCP integration will transform FormAgent from a simple form filler into a true intelligent agent capable of understanding form context and generating appropriate responses.

### 3. Local LLM Integration

For privacy-conscious users, we'll support locally installed language models:

- Lightweight models that can run on typical development machines
- No data sent to external APIs
- Customizable for specific domains or industries

Planned LLM options:
- Llama 2 (smaller variants)
- Mistral 7B
- Phi-2

### 4. Architectural Additions

The project structure will expand to include:

```
FormAgent
├── src/
│   ├── browsers/  (existing)
│   ├── core/      (existing)
│   ├── rag/       (new)
│   │   ├── retriever.py      (database queries)
│   │   ├── generator.py      (LLM integration)
│   │   ├── knowledge_base.py (database management)
│   │   └── form_analyzer.py  (field classification)
│   └── mcp/       (new)
│       ├── agent.py          (agent implementation)
│       ├── client.py         (MCP communication)
│       ├── memory.py         (context storage)
│       ├── planning.py       (task planning)
│       ├── tools/            (external tool integrations)
│       ├── adapters/         (model-specific adapters)
│       └── config.py         (model configuration)
```

## Troubleshooting

If you encounter issues:

1. Check the logs in the `logs/` directory
2. Try running in debug mode with the `--debug` flag
3. If a browser is failing to launch, ensure you have the correct driver installed for your browser version

## For Developers

To extend FormAgent with support for additional browsers or input types:

1. Study the existing browser implementations in `src/browsers/`
2. Create a new browser-specific file following the same pattern
3. Add the appropriate input data generators in `src/core/auto-filler.js`
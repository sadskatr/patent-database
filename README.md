# Patent Search Tool

A structured, debug-friendly, and interactive GUI that allows users to efficiently query the USPTO patent database via the ODP API.

## Features

- **Dynamic Search Interface**: Adjusts input fields based on the selected search type
- **Multiple Search Types**:
  - Simple keyword search
  - Boolean search with AND, OR, NOT operators
  - Wildcard search with *
  - Field-specific search
  - Range search
  - Filtered search
  - Faceted search
- **Debug Tools**:
  - Console logging
  - Query preview
  - API response inspection
- **Export Functionality**: Export search results to CSV
- **Pagination**: Navigate through large result sets

## Project Structure

```
patent_database/  
├── run.py              # Standalone development server  
├── config.py           # Tool configuration (API key, constants, etc.)  
└── patent_database/    # Main tool directory  
    ├── __init__.py     # Flask Blueprint setup  
    ├── routes.py       # Route handlers  
    ├── operations.py   # Core business logic (query construction & API calls)  
    ├── utils.py        # Helper functions (validation, CSV formatting)
    ├── constants.py    # Field mappings, API endpoints
    ├── templates/      # HTML templates  
    │   ├── base.html   # Base template  
    │   └── patent_database/  
    │       └── index.html  # Main UI for the search tool  
    └── static/         # Static assets
        └── patent_database/
            ├── css/    # CSS files
            └── js/     # JavaScript files
```

## Setup

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Configure your USPTO ODP API key in `config.py`
4. Run the development server:
   ```
   python run.py
   ```
5. Open http://127.0.0.1:5000/patent_database in your browser

## API Key

You need a USPTO ODP API key to use this tool. You can obtain one from the [USPTO Developer Portal](https://developer.uspto.gov/).

Once you have your API key, update the `ODP_API_KEY` value in `config.py`:

```python
class DevConfig:
    # ...
    ODP_API_KEY = 'your_api_key_here'
    # ...
```

## Search Types

### Simple Search
Basic keyword search across patent data.

### Boolean Search
Combine multiple search terms with AND, OR, NOT operators.

### Wildcard Search
Use * as a wildcard in your search (e.g., "auto*" matches "automatic").

### Field-Specific Search
Search in a specific field of the patent data.

### Range Search
Search for patents within a date range.

### Filtered Search
Filter patents by specific criteria.

### Faceted Search
Group search results by selected facets.

## Debug Mode

Enable debug mode to see:
- API request payloads
- API response data
- Error messages
- Query construction details

## Query Preview

Enable query preview to see the constructed API request before submitting it.

## Requirements

- Python 3.8+
- Flask 3.0.0
- Requests 2.31.0
- Other dependencies listed in requirements.txt
class DevConfig:
    SECRET_KEY = 'dev'
    DEBUG = True
    # USPTO ODP API Key - Replace with your actual API key
    ODP_API_KEY = 'YOUR_API_KEY_HERE'
    # Tool name for display
    TOOL_NAME = 'Patent Search Tool'
    # Default number of results per page
    DEFAULT_RESULTS_PER_PAGE = 50
    # Maximum number of results per page
    MAX_RESULTS_PER_PAGE = 100
    # Logging level
    LOG_LEVEL = 'INFO'
    # Add other tool-specific configuration here
import json
import logging
import time
import requests
from flask import current_app

from .constants import SEARCH_TYPES, MAX_RESULTS_PER_PAGE, DEFAULT_SORT_FIELD
from .utils import validate_search_params, format_results_for_csv

# Configure logging
logger = logging.getLogger(__name__)

def run_operation(operation_type, params=None):
    """
    Process an operation request
    
    Args:
        operation_type (str): Type of operation to perform
        params (dict): Parameters for the operation
    
    Returns:
        dict: Operation result
    """
    if params is None:
        params = {}
    
    logger.info(f"Running operation: {operation_type}")
    logger.info(f"Operation params: {json.dumps(params, default=str)}")
    
    # Map operation types to functions
    operations = {
        'search': search_patents,
        'export_csv': export_to_csv,
        'test_connection': test_api_connection
    }
    
    if operation_type not in operations:
        return {
            'success': False,
            'error': f'Unknown operation type: {operation_type}'
        }
    
    # Call the appropriate function
    try:
        result = operations[operation_type](params)
        return result
    except Exception as e:
        logger.error(f"Error in operation {operation_type}: {str(e)}")
        return {
            'success': False,
            'error': f'Operation error: {str(e)}'
        }

def search_patents(params):
    """
    Search patents using the USPTO API
    
    Args:
        params (dict): Search parameters
    
    Returns:
        dict: Search results
    """
    # Validate search parameters
    validation = validate_search_params(params)
    if not validation['valid']:
        return {
            'success': False,
            'error': validation['error']
        }
    
    # Get search type
    search_type = params.get('search_type', 'simple')
    if search_type not in SEARCH_TYPES:
        return {
            'success': False,
            'error': f'Invalid search type: {search_type}'
        }
    
    # Get query parameters
    query_params = params.get('query_params', {})
    
    # Build API request payload
    try:
        payload = build_search_payload(search_type, query_params, params)
    except Exception as e:
        logger.error(f"Error building search payload: {str(e)}")
        return {
            'success': False,
            'error': f'Error building search payload: {str(e)}'
        }
    
    # Make API request
    api_url = 'https://api.uspto.gov/api/v1/patent/applications/search'
    
    try:
        api_key = get_api_key()
        if not api_key:
            return {
                'success': False,
                'error': 'API key is not set in config.py'
            }
        
        headers = {
            'X-API-KEY': api_key,
            'Content-Type': 'application/json'
        }
        
        # Make the API request with retry logic for rate limiting
        response_data = make_api_request(api_url, headers, payload)
        
        if not response_data['success']:
            return response_data
        
        # Process the response
        data = response_data['data']
        
        # Extract results from patentFileWrapperDataBag
        results = data.get('patentFileWrapperDataBag', [])
        
        # Add a more accessible results field for compatibility
        data['results'] = results
        
        # Return the processed results
        return {
            'success': True,
            'data': data
        }
        
    except Exception as e:
        logger.error(f"Error in search_patents: {str(e)}")
        return {
            'success': False,
            'error': f'Search error: {str(e)}'
        }

def make_api_request(url, headers, payload, max_retries=3, retry_delay=2):
    """
    Make an API request with retry logic for rate limiting
    
    Args:
        url (str): API endpoint URL
        headers (dict): Request headers
        payload (dict): Request payload
        max_retries (int): Maximum number of retry attempts
        retry_delay (int): Delay between retries in seconds
    
    Returns:
        dict: API response data
    """
    for attempt in range(max_retries):
        try:
            logger.info(f"Making API request to {url} (attempt {attempt+1}/{max_retries})")
            
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            status = response.status_code
            logger.info(f"API response status: {status}")
            
            # Check for rate limiting (429)
            if status == 429 and attempt < max_retries - 1:
                retry_after = int(response.headers.get('Retry-After', retry_delay))
                logger.warning(f"Rate limited. Retrying after {retry_after} seconds")
                time.sleep(retry_after)
                continue
                
            # Process successful response
            if status == 200:
                try:
                    data = response.json()
                    return {
                        'success': True,
                        'data': data
                    }
                except Exception as e:
                    logger.error(f"Error parsing API response: {str(e)}")
                    return {
                        'success': False,
                        'error': f'Error parsing API response: {str(e)}'
                    }
            else:
                error_message = f"API error: {status}"
                if hasattr(response, 'text'):
                    error_message += f" - {response.text[:200]}"
                logger.error(error_message)
                return {
                    'success': False,
                    'error': error_message
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request exception: {str(e)}")
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds")
                time.sleep(retry_delay)
            else:
                return {
                    'success': False,
                    'error': f'API request failed: {str(e)}'
                }
    
    # Should not reach here, but just in case
    return {
        'success': False,
        'error': 'Maximum retries exceeded'
    }

def build_search_payload(search_type, query_params, params):
    """
    Build the search payload for the USPTO API
    
    Args:
        search_type (str): Type of search
        query_params (dict): Query parameters
        params (dict): Additional parameters
    
    Returns:
        dict: Formatted payload for the API
    """
    # Get pagination parameters
    page = int(params.get('page', 1))
    limit = int(params.get('limit', MAX_RESULTS_PER_PAGE))
    
    # Calculate offset
    offset = (page - 1) * limit
    
    # Create pagination object
    pagination = {
        "offset": offset,
        "limit": limit
    }
    
    # Get sort parameters
    sort_field = params.get('sort_field', DEFAULT_SORT_FIELD)
    sort_order = params.get('sort_order', 'desc')
    
    # Create sort object
    sort = [
        {
            "field": sort_field,
            "direction": sort_order
        }
    ]
    
    payload = {}
    
    # 1. fields (first in test.py)
    payload["fields"] = params.get('fields', [
        "inventionTitle",
        "applicationNumberText",
        "applicationMetaData",
        "inventorNameText"
    ])
    
    # 2. filters (second in test.py)
    payload["filters"] = [
        {
            "name": "applicationMetaData.applicationTypeLabelName",
            "value": ["Utility"]
        }
    ]
    
    # 3. pagination (third in test.py)
    payload["pagination"] = pagination
    
    # 4. q (query term - fourth in test.py)
    if search_type == 'simple':
        payload["q"] = query_params.get('term', '')
    else:
        # Default to wildcard for other search types
        payload["q"] = '*'
    
    # 5. rangeFilters (fifth in test.py)
    # Add date range if provided (applies to all search types)
    date_from = query_params.get('dateFrom', '')
    date_to = query_params.get('dateTo', '')
    
    if date_from and date_to:
        payload["rangeFilters"] = [
            {
                "field": "applicationMetaData.filingDate",
                "valueFrom": date_from,
                "valueTo": date_to
            }
        ]
    
    # 6. sort (sixth in test.py)
    payload["sort"] = sort
    
    # Now handle specific search types
    if search_type == 'boolean':
        # For boolean search, format in the style of "field1:term1 AND field2:term2"
        query_terms = []
        for i, term in enumerate(query_params.get('terms', [])):
            if term.get('field') and term.get('value'):
                # First term has no operator
                if i == 0 or term.get('operator') is None:
                    query_terms.append(f"{term['field']}:{term['value']}")
                else:
                    # Subsequent terms have operators
                    operator = term.get('operator', 'AND').upper()
                    if operator == 'NOT':
                        query_terms.append(f"NOT {term['field']}:{term['value']}")
                    else:
                        query_terms.append(f"{operator} {term['field']}:{term['value']}")
        
        payload["q"] = ' '.join(query_terms) or '*'  # Use * as fallback if no terms
    
    elif search_type == 'wildcard':
        # Format as field:term* for wildcard searches
        field = query_params.get('field', 'inventionTitle')
        value = query_params.get('value', '')
        payload["q"] = f"{field}:{value}"
    
    elif search_type == 'field_specific':
        # Format as field:value for field-specific searches
        field = query_params.get('field', '')
        value = query_params.get('value', '')
        payload["q"] = f"{field}:{value}"
    
    elif search_type == 'range':
        # For range searches, add to rangeFilters
        field = query_params.get('field', 'applicationMetaData.filingDate')
        value_from = query_params.get('valueFrom', '')
        value_to = query_params.get('valueTo', '')
        
        if value_from and value_to:
            # Create or update rangeFilters
            if "rangeFilters" not in payload:
                payload["rangeFilters"] = []
            
            # Add our range filter
            range_filter = {
                "field": field,
                "valueFrom": value_from,
                "valueTo": value_to
            }
            
            # Check if we need to replace an existing one
            found = False
            for i, existing in enumerate(payload["rangeFilters"]):
                if existing.get("field") == field:
                    payload["rangeFilters"][i] = range_filter
                    found = True
                    break
            
            if not found:
                payload["rangeFilters"].append(range_filter)
    
    elif search_type == 'filtered':
        # For filtered searches, add to filters
        field = query_params.get('field', '')
        value = query_params.get('value', '')
        
        if field and value:
            payload["filters"].append({
                "name": field,
                "value": [value]
            })
    
    elif search_type == 'faceted':
        # For faceted searches, add facets
        facets = query_params.get('facets', [])
        if facets:
            payload["facets"] = facets
    
    # Final validation - ensure query term exists
    if not payload.get("q"):
        payload["q"] = '*'
    
    logger.info(f"Final payload: {json.dumps(payload, indent=2)}")
    return payload

def export_to_csv(params):
    """
    Export search results to CSV format
    
    Args:
        params (dict): Parameters including search results to export
    
    Returns:
        dict: Success flag and CSV data
    """
    # If results are provided directly, format them
    if 'results' in params:
        results = params.get('results', [])
        csv_data = format_results_for_csv(results)
        
        return {
            'success': True,
            'csv_data': csv_data
        }
    
    # Otherwise, perform a search and then format results
    elif 'search_params' in params:
        search_params = params.get('search_params', {})
        
        # Set limit to maximum to get more results for export
        if 'pagination' in search_params:
            search_params['pagination']['limit'] = 100
        
        # Run the search
        search_result = search_patents(search_params)
        
        if search_result.get('success'):
            # Get results from the patentFileWrapperDataBag field
            data = search_result.get('data', {})
            
            # Use the results field we added in search_patents for compatibility
            results = data.get('results', [])
            
            # If no results field (older version), try patentFileWrapperDataBag directly
            if not results and 'patentFileWrapperDataBag' in data:
                results = data.get('patentFileWrapperDataBag', [])
                
            csv_data = format_results_for_csv(results)
            
            return {
                'success': True,
                'csv_data': csv_data
            }
        else:
            return {
                'success': False,
                'error': search_result.get('error', 'Failed to retrieve results for export')
            }
    else:
        return {
            'success': False,
            'error': 'No results or search parameters provided for export'
        }

def get_api_key():
    """Get API key from config"""
    from config import DevConfig
    return getattr(DevConfig, 'ODP_API_KEY', '')

def test_api_connection():
    """
    Test function to check if the USPTO API is reachable
    
    Returns:
        dict: Status of the API connection
    """
    try:
        api_key = get_api_key()
        
        if not api_key:
            return {
                'success': False,
                'error': 'API key is not set in config.py'
            }
        
        # Use the exact same URL and test payload from the working test script
        test_url = 'https://api.uspto.gov/api/v1/patent/applications/search'
        
        # Use a simple, known-working test payload
        test_payload = {
            "q": "applicationMetaData.applicationTypeLabelName:Utility",
            "filters": [
                {
                    "name": "applicationMetaData.applicationStatusDescriptionText",
                    "value": ["Patented Case"]
                }
            ],
            "pagination": {
                "offset": 0,
                "limit": 1
            },
            "fields": [
                "applicationNumberText",
                "applicationMetaData.filingDate"
            ]
        }
        
        headers = {
            'X-API-KEY': api_key,
            'Content-Type': 'application/json'
        }
        
        logger.info(f"Testing API connection to: {test_url}")
        logger.info(f"Test payload: {json.dumps(test_payload)}")
        
        # Make a POST request to match how the working example does it
        response = requests.post(
            test_url,
            headers=headers,
            json=test_payload,
            allow_redirects=True,
            timeout=30
        )
        
        status = response.status_code
        logger.info(f"Test connection status: {status}")
        logger.info(f"Response headers: {dict(response.headers)}")
        
        if status == 200:
            # Try to parse the response
            try:
                result = response.json()
                
                # Handle the actual API response structure
                results = result.get('patentFileWrapperDataBag', [])
                result_count = len(results)
                total_count = result.get('count', 0)
                
                logger.info(f"API test successful: {total_count} total results, {result_count} returned")
                
                return {
                    'success': True,
                    'message': f'API connection successful. Found {total_count} matching patents.'
                }
            except Exception as e:
                logger.error(f"Error parsing API response: {str(e)}")
                return {
                    'success': True,
                    'message': 'API connection successful, but error parsing response'
                }
        elif status == 403:
            logger.error(f"API Key is invalid or unauthorized: {response.text}")
            return {
                'success': False,
                'error': 'API Key is invalid or unauthorized'
            }
        elif status == 404:
            logger.error(f"No matching records found or invalid endpoint: {response.text}")
            return {
                'success': False,
                'error': 'No matching records found or invalid endpoint'
            }
        else:
            error_message = f"API error: {status}"
            if hasattr(response, 'text'):
                error_message += f" - {response.text[:200]}"
            logger.error(error_message)
            return {
                'success': False,
                'error': error_message
            }
    
    except Exception as e:
        logger.error(f"Error testing API connection: {str(e)}")
        return {
            'success': False,
            'error': f"Connection error: {str(e)}"
        }
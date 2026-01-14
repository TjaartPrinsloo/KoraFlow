#!/usr/bin/env python3
"""
API Handler
Handles API endpoint creation tasks with template-based generation.
"""

import re
from .base_handler import BaseHandler


class APIHandler(BaseHandler):
    """Handler for API endpoint tasks"""
    
    @property
    def task_type(self) -> str:
        return 'api'
    
    def _load_template(self):
        """Load API template"""
        return self._load_template_file('api_template.py.j2')
    
    def _get_filters(self, query: str, params: dict) -> dict:
        """Get filters for API-related chunks"""
        filters = {}
        
        # Filter by API files
        filters['file_pattern'] = '**/api/**/*.py'
        
        # Add keywords
        filters['keywords'] = ['@frappe.whitelist', 'api', 'endpoint', 'whitelisted']
        
        return filters
    
    def _prepare_template_vars(self, query: str, chunks: list, params: dict) -> dict:
        """Prepare template variables"""
        # Extract endpoint name
        endpoint_match = re.search(r'endpoint\s+(?:named|called)?\s*([a-z_]+)', query, re.IGNORECASE)
        endpoint_name = endpoint_match.group(1).strip() if endpoint_match else 'custom_endpoint'
        
        # Extract method
        method = params.get('method', 'GET')
        if 'post' in query.lower():
            method = 'POST'
        elif 'get' in query.lower():
            method = 'GET'
        
        # Extract function name
        function_name = endpoint_name.replace(' ', '_')
        
        # Extract DocType if mentioned
        doctype_match = re.search(r'for\s+([A-Z][A-Za-z0-9\s]+)', query, re.IGNORECASE)
        doctype = doctype_match.group(1).strip() if doctype_match else ''
        
        return {
            'endpoint_name': endpoint_name,
            'function_name': function_name,
            'description': query,
            'method': method,
            'doctype': doctype,
            'params': [],
            'fields': []
        }


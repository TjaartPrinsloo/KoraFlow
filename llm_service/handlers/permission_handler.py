#!/usr/bin/env python3
"""
Permission Handler
Handles permission logic tasks with template-based generation.
"""

import re
from .base_handler import BaseHandler


class PermissionHandler(BaseHandler):
    """Handler for permission logic tasks"""
    
    @property
    def task_type(self) -> str:
        return 'permission'
    
    def _load_template(self):
        """Load permission template"""
        return self._load_template_file('permission_template.py.j2')
    
    def _get_filters(self, query: str, params: dict) -> dict:
        """Get filters for permission-related chunks"""
        filters = {}
        
        # Filter by permission-related files
        filters['keywords'] = ['permission', 'has_permission', 'permission_query_conditions', 'role']
        
        return filters
    
    def _prepare_template_vars(self, query: str, chunks: list, params: dict) -> dict:
        """Prepare template variables"""
        # Extract DocType
        doctype_match = re.search(r'for\s+([A-Z][A-Za-z0-9\s]+)', query, re.IGNORECASE)
        doctype = doctype_match.group(1).strip() if doctype_match else 'DocType'
        
        # Extract role if mentioned
        role = ''
        role_match = re.search(r'role\s+([A-Z][A-Za-z0-9\s]+)', query, re.IGNORECASE)
        if role_match:
            role = role_match.group(1).strip()
        
        # Extract user field if mentioned
        user_field = ''
        user_field_match = re.search(r'user\s+field\s+([a-z_]+)', query, re.IGNORECASE)
        if user_field_match:
            user_field = user_field_match.group(1).strip()
        
        return {
            'doctype': doctype,
            'app_name': 'koraflow_core',
            'role': role,
            'role_based': bool(role),
            'user_field': user_field
        }


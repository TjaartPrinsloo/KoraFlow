#!/usr/bin/env python3
"""
Patch Handler
Handles patch script creation tasks with template-based generation.
"""

import re
from .base_handler import BaseHandler


class PatchHandler(BaseHandler):
    """Handler for patch script creation tasks"""
    
    @property
    def task_type(self) -> str:
        return 'patch'
    
    def _load_template(self):
        """Load patch template"""
        return self._load_template_file('patch_template.py.j2')
    
    def _get_filters(self, query: str, params: dict) -> dict:
        """Get filters for patch-related chunks"""
        filters = {}
        
        # Filter by patch files
        filters['file_pattern'] = '**/patches/**/*.py'
        
        # Add keywords
        filters['keywords'] = ['patch', 'execute', 'migrate', 'custom field']
        
        return filters
    
    def _prepare_template_vars(self, query: str, chunks: list, params: dict) -> dict:
        """Prepare template variables"""
        # Extract patch action
        action = params.get('action', 'update')
        if 'add field' in query.lower():
            action = 'add_field'
        elif 'migrate' in query.lower():
            action = 'migrate'
        
        # Extract DocType
        doctype_match = re.search(r'to\s+([A-Z][A-Za-z0-9\s]+)', query, re.IGNORECASE)
        doctype = doctype_match.group(1).strip() if doctype_match else 'DocType'
        
        # Extract field info if adding field
        fieldname = ''
        fieldtype = 'Data'
        label = ''
        
        if action == 'add_field':
            field_match = re.search(r'field\s+(?:named|called)?\s*([a-z_]+)', query, re.IGNORECASE)
            if field_match:
                fieldname = field_match.group(1).strip()
                label = fieldname.replace('_', ' ').title()
            
            # Infer field type
            if 'date' in fieldname:
                fieldtype = 'Date'
            elif 'amount' in fieldname or 'price' in fieldname:
                fieldtype = 'Currency'
            elif 'link' in fieldname:
                fieldtype = 'Link'
        
        # Generate patch name
        patch_name = f"add_{fieldname}_to_{doctype.lower().replace(' ', '_')}" if fieldname else "update_patch"
        
        return {
            'patch_name': patch_name,
            'description': query,
            'action': action,
            'doctype': doctype,
            'fieldname': fieldname,
            'fieldtype': fieldtype,
            'label': label
        }


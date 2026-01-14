#!/usr/bin/env python3
"""
UX Handler
Handles Desk UX component creation tasks with template-based generation.
"""

import re
from .base_handler import BaseHandler


class UXHandler(BaseHandler):
    """Handler for UX/UI tasks"""
    
    @property
    def task_type(self) -> str:
        return 'ux'
    
    def _load_template(self):
        """Load UX template"""
        return self._load_template_file('ux_template.js.j2')
    
    def _get_filters(self, query: str, params: dict) -> dict:
        """Get filters for UX-related chunks"""
        filters = {}
        
        # Filter by JS/Vue files
        filters['file_pattern'] = '**/*.js'
        filters['keywords'] = ['frappe.ui.form', 'refresh', 'onload', 'custom_button']
        
        return filters
    
    def _prepare_template_vars(self, query: str, chunks: list, params: dict) -> dict:
        """Prepare template variables"""
        # Extract DocType
        doctype_match = re.search(r'for\s+([A-Z][A-Za-z0-9\s]+)', query, re.IGNORECASE)
        doctype = doctype_match.group(1).strip() if doctype_match else 'DocType'
        
        # Extract component name
        component_match = re.search(r'component\s+(?:named|called)?\s*([a-z_]+)', query, re.IGNORECASE)
        component_name = component_match.group(1).strip() if component_match else f'{doctype.lower()}_component'
        
        # Determine event type
        event = 'refresh'  # Default
        if 'onload' in query.lower() or 'load' in query.lower():
            event = 'onload'
        elif 'field' in query.lower():
            event = 'field'
        
        # Extract field name if field event
        field_name = ''
        if event == 'field':
            field_match = re.search(r'field\s+([a-z_]+)', query, re.IGNORECASE)
            if field_match:
                field_name = field_match.group(1).strip()
        
        return {
            'component_name': component_name,
            'doctype': doctype,
            'description': query,
            'event': event,
            'field_name': field_name,
            'button': 'button' in query.lower(),
            'button_label': 'Custom Action',
            'button_action': '// Add button action',
            'init_logic': '// Initialize form',
            'field_logic': '// Handle field change'
        }


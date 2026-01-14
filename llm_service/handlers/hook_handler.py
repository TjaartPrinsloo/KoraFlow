#!/usr/bin/env python3
"""
Hook Handler
Handles hook wiring tasks with template-based generation.
"""

import re
from .base_handler import BaseHandler


class HookHandler(BaseHandler):
    """Handler for hook wiring tasks"""
    
    @property
    def task_type(self) -> str:
        return 'hook'
    
    def _load_template(self):
        """Load hook template"""
        return self._load_template_file('hook_template.py.j2')
    
    def _get_filters(self, query: str, params: dict) -> dict:
        """Get filters for hook-related chunks"""
        filters = {}
        
        # Filter by hooks.py files
        filters['file_pattern'] = '**/hooks.py'
        
        # Add keywords
        filters['keywords'] = ['doc_events', 'scheduler_events', 'hook', 'on_submit', 'on_insert']
        
        return filters
    
    def _prepare_template_vars(self, query: str, chunks: list, params: dict) -> dict:
        """Prepare template variables"""
        # Extract DocType from query or params
        doctype = params.get('doctype', '')
        if not doctype:
            # Try to extract from query
            match = re.search(r'(?:for|on|when)\s+([A-Z][A-Za-z0-9\s]+)', query, re.IGNORECASE)
            if match:
                doctype = match.group(1).strip()
        
        # Extract event from query or params
        event = params.get('event', 'on_submit')
        if not event:
            # Try to extract from query
            event_match = re.search(r'(on_submit|on_insert|on_update|on_cancel|after_insert|before_submit)', query, re.IGNORECASE)
            if event_match:
                event = event_match.group(1)
        
        # Extract automation description from query
        description = query
        if 'automate' in query.lower():
            description = query.split('automate')[-1].strip()
        
        # Generate function name
        function_name = f"handle_{doctype.lower().replace(' ', '_')}_{event}"
        
        # Extract automation logic from query
        automation_logic = ""
        if 'quote' in query.lower() and 'sales order' in query.lower():
            automation_logic = "Create Quote → Sales Order → Delivery Note → Sales Invoice workflow"
        elif 'create' in query.lower():
            automation_logic = "Create related documents"
        
        return {
            'doctype': doctype or 'Document',
            'event': event,
            'app_name': 'koraflow_core',
            'function_name': function_name,
            'description': description,
            'automation_logic': automation_logic
        }


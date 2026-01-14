#!/usr/bin/env python3
"""
DocType Handler
Handles DocType creation tasks with template-based generation.
"""

import re
from .base_handler import BaseHandler


class DocTypeHandler(BaseHandler):
    """Handler for DocType creation tasks"""
    
    @property
    def task_type(self) -> str:
        return 'doctype'
    
    def _load_template(self):
        """Load DocType template"""
        return self._load_template_file('doctype_template.json.j2')
    
    def _get_filters(self, query: str, params: dict) -> dict:
        """Get filters for DocType-related chunks"""
        filters = {}
        
        # Filter by doctype-related files
        filters['file_pattern'] = '**/*doctype*.py'
        
        # Add keywords
        filters['keywords'] = ['doctype', 'docfield', 'field']
        
        return filters
    
    def _prepare_template_vars(self, query: str, chunks: list, params: dict) -> dict:
        """Prepare template variables"""
        # Extract DocType name
        doctype_name = params.get('doctype_name', 'Custom DocType')
        if not doctype_name:
            # Try to extract from query
            match = re.search(r'doctype\s+(?:for|named|called)\s+([A-Z][A-Za-z0-9\s-]+)', query, re.IGNORECASE)
            if match:
                doctype_name = match.group(1).strip()
        
        # Extract fields from query or params
        fields = params.get('fields', [])
        if not fields:
            # Try to extract fields from query
            fields_match = re.search(r'fields?[:\s]+([^.]+)', query, re.IGNORECASE)
            if fields_match:
                fields = [f.strip() for f in fields_match.group(1).split(',')]
        
        # Parse fields into structured format
        parsed_fields = []
        for i, field in enumerate(fields, 1):
            field_parts = field.split()
            fieldname = field_parts[0].lower().replace(' ', '_')
            fieldtype = 'Data'  # Default
            
            # Infer field type from field name
            if 'email' in fieldname:
                fieldtype = 'Data'
            elif 'date' in fieldname:
                fieldtype = 'Date'
            elif 'amount' in fieldname or 'price' in fieldname or 'cost' in fieldname:
                fieldtype = 'Currency'
            elif 'phone' in fieldname or 'mobile' in fieldname:
                fieldtype = 'Data'
            elif 'link' in fieldname or 'reference' in fieldname:
                fieldtype = 'Link'
            
            parsed_fields.append({
                'fieldname': fieldname,
                'fieldtype': fieldtype,
                'label': field.title(),
                'idx': i
            })
        
        # Add standard fields if none provided
        if not parsed_fields:
            parsed_fields = [
                {'fieldname': 'title', 'fieldtype': 'Data', 'label': 'Title', 'idx': 1, 'reqd': True}
            ]
        
        return {
            'doctype_name': doctype_name,
            'module_name': 'koraflow_core',  # Default, can be extracted from query
            'fields': parsed_fields,
            'title_field': parsed_fields[0]['fieldname'] if parsed_fields else 'name'
        }


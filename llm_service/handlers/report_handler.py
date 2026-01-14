#!/usr/bin/env python3
"""
Report Handler
Handles report query creation tasks with template-based generation.
"""

import re
from .base_handler import BaseHandler


class ReportHandler(BaseHandler):
    """Handler for report query tasks"""
    
    @property
    def task_type(self) -> str:
        return 'report'
    
    def _load_template(self):
        """Load report template"""
        return self._load_template_file('report_template.py.j2')
    
    def _get_filters(self, query: str, params: dict) -> dict:
        """Get filters for report-related chunks"""
        filters = {}
        
        # Filter by report files
        filters['file_pattern'] = '**/report/**/*.py'
        
        # Add keywords
        filters['keywords'] = ['report', 'query', 'execute', 'columns', 'data']
        
        return filters
    
    def _prepare_template_vars(self, query: str, chunks: list, params: dict) -> dict:
        """Prepare template variables"""
        # Extract report name
        report_match = re.search(r'report\s+(?:named|called)?\s*([A-Z][A-Za-z0-9\s]+)', query, re.IGNORECASE)
        report_name = report_match.group(1).strip() if report_match else 'Custom Report'
        
        # Extract DocType
        doctype_match = re.search(r'for\s+([A-Z][A-Za-z0-9\s]+)', query, re.IGNORECASE)
        doctype = doctype_match.group(1).strip() if doctype_match else 'DocType'
        
        # Default columns
        columns = [
            {'fieldname': 'name', 'label': 'Name', 'fieldtype': 'Link', 'width': 200},
            {'fieldname': 'modified', 'label': 'Modified', 'fieldtype': 'Datetime', 'width': 150}
        ]
        
        return {
            'report_name': report_name,
            'description': query,
            'doctype': doctype,
            'columns': columns,
            'filters': []
        }


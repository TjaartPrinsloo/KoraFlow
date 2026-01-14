#!/usr/bin/env python3
"""
Job Handler
Handles background job creation tasks with template-based generation.
"""

import re
from .base_handler import BaseHandler


class JobHandler(BaseHandler):
    """Handler for background job tasks"""
    
    @property
    def task_type(self) -> str:
        return 'job'
    
    def _load_template(self):
        """Load job template"""
        return self._load_template_file('job_template.py.j2')
    
    def _get_filters(self, query: str, params: dict) -> dict:
        """Get filters for job-related chunks"""
        filters = {}
        
        # Filter by job-related files
        filters['keywords'] = ['frappe.enqueue', 'background', 'job', 'async']
        
        return filters
    
    def _prepare_template_vars(self, query: str, chunks: list, params: dict) -> dict:
        """Prepare template variables"""
        # Extract job name
        job_match = re.search(r'job\s+(?:named|called)?\s*([a-z_]+)', query, re.IGNORECASE)
        job_name = job_match.group(1).strip() if job_match else 'background_job'
        
        # Extract function name
        function_name = job_name.replace(' ', '_')
        
        # Extract job logic from query
        job_logic = query
        
        return {
            'job_name': job_name,
            'function_name': function_name,
            'description': query,
            'app_name': 'koraflow_core',
            'params': [],
            'job_logic': job_logic
        }


#!/usr/bin/env python3
"""
Scheduler Handler
Handles scheduler task creation with template-based generation.
"""

import re
from .base_handler import BaseHandler


class SchedulerHandler(BaseHandler):
    """Handler for scheduler task creation"""
    
    @property
    def task_type(self) -> str:
        return 'scheduler'
    
    def _load_template(self):
        """Load scheduler template"""
        return self._load_template_file('scheduler_template.py.j2')
    
    def _get_filters(self, query: str, params: dict) -> dict:
        """Get filters for scheduler-related chunks"""
        filters = {}
        
        # Filter by scheduler-related files
        filters['file_pattern'] = '**/hooks.py'
        filters['keywords'] = ['scheduler_events', 'daily', 'hourly', 'weekly', 'monthly']
        
        return filters
    
    def _prepare_template_vars(self, query: str, chunks: list, params: dict) -> dict:
        """Prepare template variables"""
        # Extract frequency
        frequency = 'daily'  # Default
        if 'hourly' in query.lower():
            frequency = 'hourly'
        elif 'daily' in query.lower():
            frequency = 'daily'
        elif 'weekly' in query.lower():
            frequency = 'weekly'
        elif 'monthly' in query.lower():
            frequency = 'monthly'
        elif 'all' in query.lower():
            frequency = 'all'
        
        # Extract function name
        function_match = re.search(r'task\s+(?:named|called)?\s*([a-z_]+)', query, re.IGNORECASE)
        function_name = function_match.group(1).strip() if function_match else f'scheduled_task_{frequency}'
        
        # Extract task logic
        task_logic = query
        
        return {
            'function_name': function_name,
            'description': query,
            'frequency': frequency,
            'app_name': 'koraflow_core',
            'task_logic': task_logic
        }


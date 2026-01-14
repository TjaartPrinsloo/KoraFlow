#!/usr/bin/env python3
"""
Task Router
Detects task type from user queries and routes to appropriate handlers.
"""

import re
from typing import Dict, Optional, Tuple


class TaskRouter:
    """Routes queries to task-specific handlers based on query content"""
    
    # Task detection patterns
    TASK_PATTERNS = {
        'doctype': [
            r'\b(create|make|build|generate|new)\s+(a\s+)?doctype',
            r'\bdoctype\s+(for|with|named)',
            r'\b(custom\s+)?doctype\s+(creation|setup|definition)',
            r'\bdefine\s+(a\s+)?doctype',
        ],
        'hook': [
            r'\b(create|add|setup|wire|configure)\s+(a\s+)?hook',
            r'\bhook\s+(for|on|when|after|before)',
            r'\b(automate|trigger|on_submit|on_insert|on_update)',
            r'\bdoc_events|scheduler_events|app_include',
            r'\bwhen\s+\w+\s+(is\s+)?(submitted|inserted|updated|cancelled)',
        ],
        'patch': [
            r'\b(create|write|make|generate)\s+(a\s+)?patch',
            r'\bpatch\s+(script|file|to)',
            r'\bmigrate|migration|data\s+update',
            r'\badd\s+(field|column|doctype)\s+via\s+patch',
        ],
        'permission': [
            r'\b(create|setup|configure|add)\s+(a\s+)?permission',
            r'\bpermission\s+(query|logic|rule|check)',
            r'\bhas_permission|permission_query_conditions',
            r'\b(role|user)\s+(access|permission)',
        ],
        'report': [
            r'\b(create|make|build|generate)\s+(a\s+)?report',
            r'\breport\s+(query|for|with)',
            r'\bquery\s+(report|builder)',
            r'\bsql\s+query\s+for\s+report',
        ],
        'api': [
            r'\b(create|make|build|add)\s+(an\s+)?api\s+(endpoint|method)',
            r'\bapi\s+(endpoint|route|method|function)',
            r'\b@frappe\.whitelist|whitelisted\s+method',
            r'\b(rest|http)\s+endpoint',
        ],
        'job': [
            r'\b(create|make|setup)\s+(a\s+)?(background\s+)?job',
            r'\bbackground\s+(job|task|process)',
            r'\benqueue|frappe\.enqueue',
            r'\b(async|asynchronous)\s+task',
        ],
        'scheduler': [
            r'\b(create|setup|add)\s+(a\s+)?scheduler',
            r'\bscheduler\s+(task|event|job)',
            r'\bscheduler_events|(daily|hourly|weekly|monthly)\s+task',
            r'\b(cron|scheduled)\s+job',
        ],
        'ux': [
            r'\b(create|modify|update|tweak)\s+(desk|ui|ux|frontend)',
            r'\b(desk|ui|ux)\s+(component|form|view|tweak)',
            r'\b(vue|javascript|js)\s+(component|form)',
            r'\bfrontend\s+(change|modification)',
        ],
    }
    
    def __init__(self):
        self.compiled_patterns = {
            task: [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
            for task, patterns in self.TASK_PATTERNS.items()
        }
    
    def detect_task(self, query: str) -> Tuple[str, Dict]:
        """
        Detect task type from query
        
        Returns:
            Tuple of (task_type, extracted_params)
        """
        query_lower = query.lower()
        
        # Check each task type
        for task_type, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                if pattern.search(query):
                    params = self._extract_params(query, task_type)
                    return task_type, params
        
        # Default to generic
        return 'generic', {}
    
    def _extract_params(self, query: str, task_type: str) -> Dict:
        """Extract task-specific parameters from query"""
        params = {}
        query_lower = query.lower()
        
        if task_type == 'doctype':
            # Extract DocType name
            doctype_match = re.search(r'doctype\s+(?:for|named|called)\s+([A-Z][A-Za-z0-9\s-]+)', query, re.IGNORECASE)
            if doctype_match:
                params['doctype_name'] = doctype_match.group(1).strip()
            
            # Extract fields
            fields_match = re.search(r'fields?[:\s]+([^.]+)', query, re.IGNORECASE)
            if fields_match:
                params['fields'] = [f.strip() for f in fields_match.group(1).split(',')]
        
        elif task_type == 'hook':
            # Extract DocType and event
            doctype_match = re.search(r'(?:for|on)\s+([A-Z][A-Za-z0-9\s]+)', query, re.IGNORECASE)
            if doctype_match:
                params['doctype'] = doctype_match.group(1).strip()
            
            event_match = re.search(r'(on_submit|on_insert|on_update|on_cancel|after_insert|before_submit)', query, re.IGNORECASE)
            if event_match:
                params['event'] = event_match.group(1)
        
        elif task_type == 'patch':
            # Extract patch purpose
            if 'add field' in query_lower:
                params['action'] = 'add_field'
            elif 'migrate' in query_lower:
                params['action'] = 'migrate'
            elif 'update' in query_lower:
                params['action'] = 'update'
        
        elif task_type == 'api':
            # Extract endpoint purpose
            if 'get' in query_lower:
                params['method'] = 'GET'
            elif 'post' in query_lower:
                params['method'] = 'POST'
        
        return params


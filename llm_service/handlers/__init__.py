"""
Task Handlers
Handlers for different task types with template-based generation.
"""

from .base_handler import BaseHandler
from .doctype_handler import DocTypeHandler
from .hook_handler import HookHandler
from .patch_handler import PatchHandler
from .permission_handler import PermissionHandler
from .report_handler import ReportHandler
from .api_handler import APIHandler
from .job_handler import JobHandler
from .scheduler_handler import SchedulerHandler
from .ux_handler import UXHandler
from .code_review_handler import CodeReviewHandler

__all__ = [
    'BaseHandler',
    'DocTypeHandler',
    'HookHandler',
    'PatchHandler',
    'PermissionHandler',
    'ReportHandler',
    'APIHandler',
    'JobHandler',
    'SchedulerHandler',
    'UXHandler',
    'CodeReviewHandler',
]


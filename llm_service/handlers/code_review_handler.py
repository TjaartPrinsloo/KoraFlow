#!/usr/bin/env python3
"""
Code Review Handler
Handler for reviewing code against Frappe standards using RAG.
"""

from typing import Dict, List, Optional
from pathlib import Path
import jinja2
from .base_handler import BaseHandler


class CodeReviewHandler(BaseHandler):
    """Handler for code review tasks"""
    
    @property
    def task_type(self) -> str:
        return 'code_review'
    
    def _load_template(self) -> jinja2.Template:
        """Load code review template"""
        template_path = Path(__file__).parent.parent / "templates" / "code_review_template.py.j2"
        if template_path.exists():
            with open(template_path, 'r') as f:
                return jinja2.Template(f.read())
        return None
    
    def _get_filters(self, query: str, params: Dict) -> Dict:
        """Get FAISS filters for code review"""
        # Filter for Frappe standards, coding conventions, and examples
        filters = {}
        
        # Add language-specific keywords if detected
        file_path = params.get('file_path', '')
        keywords = ['frappe', 'standard', 'convention', 'best practice', 'pattern']
        
        if file_path.endswith('.py'):
            keywords.extend(['python', 'pep8', 'docstring', 'frappe api'])
        elif file_path.endswith(('.js', '.vue')):
            keywords.extend(['javascript', 'eslint', 'prettier', 'vue', 'frappe ui'])
        elif file_path.endswith('.scss'):
            keywords.extend(['scss', 'css', 'prettier', 'design system'])
        
        filters['keywords'] = keywords
        
        # Prefer Frappe/ERPNext repos
        # Note: FAISS filters use single repo value, so we'll filter in post-processing
        # or search without repo filter and rely on keywords
        
        return filters
    
    def _prepare_template_vars(self, query: str, chunks: List[Dict], params: Dict) -> Dict:
        """Prepare template variables for code review"""
        code = params.get('code', '')
        file_path = params.get('file_path', '')
        file_type = params.get('file_type', 'python')
        
        # Extract standards from chunks
        standards = []
        examples = []
        
        for chunk in chunks:
            content = chunk.get('content', '')
            if 'standard' in content.lower() or 'convention' in content.lower():
                standards.append(content[:500])
            else:
                examples.append(content[:500])
        
        return {
            'code': code,
            'file_path': file_path,
            'file_type': file_type,
            'standards': standards[:3],  # Top 3 standards
            'examples': examples[:2],  # Top 2 examples
            'query': query
        }
    
    def review_code(self, code: str, file_path: str, file_type: Optional[str] = None) -> Dict:
        """
        Review code against Frappe standards
        
        Args:
            code: Code to review
            file_path: Path to the file being reviewed
            file_type: Type of file (python, javascript, vue, scss)
            
        Returns:
            Review results with issues and suggestions
        """
        # Detect file type if not provided
        if not file_type:
            if file_path.endswith('.py'):
                file_type = 'python'
            elif file_path.endswith('.js'):
                file_type = 'javascript'
            elif file_path.endswith('.vue'):
                file_type = 'vue'
            elif file_path.endswith('.scss'):
                file_type = 'scss'
            else:
                file_type = 'unknown'
        
        # Build review query
        query = f"Review this {file_type} code for Frappe Framework standards and best practices: {file_path}"
        
        params = {
            'code': code,
            'file_path': file_path,
            'file_type': file_type
        }
        
        # Get task config
        task_config = self.config.get('task_routing', {}).get('tasks', {}).get(self.task_type, {})
        self.top_k = task_config.get('top_k', 5)  # More context for reviews
        self.max_context_chars = task_config.get('max_context_chars', 1000)  # More context
        
        # Retrieve relevant standards and examples
        chunks = self.retrieve_context(query, params)
        
        if not chunks:
            # Fallback: try without filters
            chunks = self.faiss_manager.search(query, top_k=self.top_k)
        
        # Build review prompt
        prompt = self._build_review_prompt(code, file_path, file_type, chunks)
        
        # Generate review
        temperature = task_config.get('temperature', 0.3)
        review_text = self.ollama_client.generate(
            prompt,
            temperature=temperature,
            max_tokens=self.config.get('ollama', {}).get('max_tokens', 4096)
        )
        
        # Parse review (structured format)
        review = self._parse_review(review_text, chunks)
        
        return review
    
    def _build_review_prompt(self, code: str, file_path: str, file_type: str, chunks: List[Dict]) -> str:
        """Build comprehensive review prompt"""
        # Build context from chunks
        context_parts = []
        citations = []
        
        for i, chunk in enumerate(chunks, 1):
            citation = self._format_citation(chunk)
            citations.append(citation)
            
            context_parts.append(f"[Standard/Example {i} - {citation}]:")
            content = chunk.get('content', '')[:self.max_context_chars]
            context_parts.append(content)
            context_parts.append("")
        
        context = "\n".join(context_parts)
        
        # Build comprehensive prompt
        prompt = f"""You are a senior Frappe Framework code reviewer. Review the following code against Frappe standards and best practices.

FRAppe Framework Standards and Examples:
{context}

CODE TO REVIEW:
File: {file_path}
Type: {file_type}

```{file_type}
{code}
```

REVIEW REQUIREMENTS:
1. Check adherence to Frappe coding standards (PEP 8 for Python, ESLint/Prettier for JS/Vue)
2. Verify Frappe-specific patterns and conventions
3. Check for security issues
4. Verify proper error handling
5. Check documentation and docstrings
6. Verify proper use of Frappe APIs and utilities
7. Check for performance issues
8. Verify proper use of imports and dependencies

OUTPUT FORMAT (JSON-like structure):
{{
  "summary": "Overall assessment",
  "score": 0-100,
  "issues": [
    {{
      "severity": "error|warning|info",
      "line": <line_number>,
      "rule": "standard/convention name",
      "message": "Issue description",
      "suggestion": "How to fix"
    }}
  ],
  "suggestions": [
    "General improvement suggestions"
  ],
  "positive_feedback": [
    "What was done well"
  ]
}}

Provide a thorough review focusing on Frappe Framework standards."""
        
        return prompt
    
    def _parse_review(self, review_text: str, chunks: List[Dict]) -> Dict:
        """Parse review text into structured format"""
        # Try to extract JSON from review
        import json
        import re
        
        # Look for JSON block
        json_match = re.search(r'\{[\s\S]*\}', review_text)
        if json_match:
            try:
                parsed = json.loads(json_match.group())
                parsed['citations'] = [self._format_citation(chunk) for chunk in chunks]
                parsed['raw_review'] = review_text
                return parsed
            except:
                pass
        
        # Fallback: parse unstructured review
        return {
            'summary': review_text[:500],
            'score': None,
            'issues': [],
            'suggestions': [],
            'positive_feedback': [],
            'citations': [self._format_citation(chunk) for chunk in chunks],
            'raw_review': review_text
        }
    
    def generate(self, query: str, params: Dict) -> Dict:
        """Generate code review (override base method)"""
        code = params.get('code', '')
        file_path = params.get('file_path', '')
        file_type = params.get('file_type')
        
        if not code:
            raise ValueError("Code is required for review")
        
        review = self.review_code(code, file_path, file_type)
        
        return {
            'answer': review.get('raw_review', ''),
            'task_type': self.task_type,
            'review': review,
            'retrieved_chunks': len(review.get('citations', [])),
            'citations': review.get('citations', [])
        }


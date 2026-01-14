#!/usr/bin/env python3
"""
Base Handler
Base class for all task handlers.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from pathlib import Path
import jinja2


class BaseHandler(ABC):
    """Base class for task-specific handlers"""
    
    def __init__(self, config: Dict, faiss_manager, ollama_client, cache=None):
        """
        Initialize handler
        
        Args:
            config: Configuration dict
            faiss_manager: FAISSManager instance
            ollama_client: OllamaClient instance
            cache: QueryCache instance (optional)
        """
        self.config = config
        self.faiss_manager = faiss_manager
        self.ollama_client = ollama_client
        self.cache = cache
        
        # Load template
        self.template = self._load_template()
        
        # Get task-specific config
        task_config = config.get('task_routing', {}).get('tasks', {}).get(self.task_type, {})
        self.top_k = task_config.get('top_k', 2)
        self.max_context_chars = task_config.get('max_context_chars', 300)
        self.use_template = task_config.get('use_template', True)
    
    @property
    @abstractmethod
    def task_type(self) -> str:
        """Task type identifier"""
        pass
    
    @abstractmethod
    def _load_template(self) -> jinja2.Template:
        """Load Jinja2 template for this task type"""
        pass
    
    @abstractmethod
    def _get_filters(self, query: str, params: Dict) -> Dict:
        """Get FAISS filters for this task type"""
        pass
    
    def retrieve_context(self, query: str, params: Dict) -> List[Dict]:
        """
        Retrieve relevant context chunks
        
        Args:
            query: User query
            params: Extracted parameters
            
        Returns:
            List of relevant chunks
        """
        filters = self._get_filters(query, params)
        chunks = self.faiss_manager.search(query, top_k=self.top_k, filters=filters)
        
        # Truncate content to max_context_chars
        for chunk in chunks:
            content = chunk.get('content', '')
            if len(content) > self.max_context_chars:
                chunk['content'] = content[:self.max_context_chars] + "..."
        
        return chunks
    
    def build_prompt(self, query: str, chunks: List[Dict], params: Dict) -> str:
        """
        Build optimized prompt for this task type
        
        Args:
            query: User query
            chunks: Retrieved context chunks
            params: Extracted parameters
            
        Returns:
            Optimized prompt string
        """
        if not chunks:
            raise ValueError(f"No relevant context found for {self.task_type} task")
        
        # Build context from chunks
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            context_parts.append(f"[Example {i}]:")
            context_parts.append(chunk.get('content', '')[:self.max_context_chars])
            context_parts.append("")
        
        context = "\n".join(context_parts)
        
        # Build task-specific prompt
        if self.use_template and self.template:
            # Use template-based prompt
            template_vars = self._prepare_template_vars(query, chunks, params)
            try:
                template_str = self.template.render(**template_vars)
                prompt = f"""Fill {self.task_type} template based on examples:

Examples:
{context}

Template:
{template_str}

Requirements: {query}

Output: Complete, valid code only. No explanations."""
            except Exception as e:
                # Fallback to simple prompt if template rendering fails
                prompt = self._build_simple_prompt(query, chunks)
        else:
            prompt = self._build_simple_prompt(query, chunks)
        
        return prompt
    
    def _build_simple_prompt(self, query: str, chunks: List[Dict]) -> str:
        """Build simple prompt without template"""
        context = "\n".join([chunk.get('content', '')[:self.max_context_chars] for chunk in chunks])
        
        return f"""You are a Frappe Framework expert. Generate {self.task_type} code.

Examples:
{context}

Task: {query}

Output: Complete, valid code only."""
    
    @abstractmethod
    def _prepare_template_vars(self, query: str, chunks: List[Dict], params: Dict) -> Dict:
        """Prepare template variables from query and chunks"""
        pass
    
    def generate(self, query: str, params: Dict) -> Dict:
        """
        Generate response for this task type
        
        Args:
            query: User query
            params: Extracted parameters
            
        Returns:
            Response dict with answer and metadata
        """
        # Check cache first
        if self.cache:
            cached = self.cache.get(self.task_type, query, self.top_k)
            if cached:
                return cached
        
        # Retrieve context
        chunks = self.retrieve_context(query, params)
        
        if not chunks:
            raise ValueError(f"No relevant context found for {self.task_type} task")
        
        # Build prompt
        prompt = self.build_prompt(query, chunks, params)
        
        # Generate answer
        task_config = self.config.get('task_routing', {}).get('tasks', {}).get(self.task_type, {})
        temperature = task_config.get('temperature', 0.3)  # Lower temp for code generation
        
        answer = self.ollama_client.generate(
            prompt,
            temperature=temperature,
            max_tokens=self.config.get('ollama', {}).get('max_tokens', 2048)
        )
        
        # Format response
        response = {
            'answer': answer,
            'task_type': self.task_type,
            'retrieved_chunks': len(chunks),
            'citations': [self._format_citation(chunk) for chunk in chunks],
            'used_template': self.use_template
        }
        
        # Cache result
        if self.cache:
            ttl = self.config.get('task_routing', {}).get('cache_ttl', 3600)
            self.cache.set(self.task_type, query, response, ttl=ttl, top_k=self.top_k)
        
        return response
    
    def _format_citation(self, chunk: Dict) -> str:
        """Format citation from chunk metadata"""
        repo = chunk.get('repo', 'unknown')
        path = chunk.get('path', 'unknown')
        return f"{repo}/{path}"
    
    def _load_template_file(self, template_name: str) -> jinja2.Template:
        """Load template from file"""
        template_path = Path(__file__).parent.parent / "templates" / template_name
        if not template_path.exists():
            return None
        
        with open(template_path, 'r') as f:
            template_str = f.read()
        
        return jinja2.Template(template_str)


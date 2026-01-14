#!/usr/bin/env python3
"""
RAG Pipeline Service
Retrieval-Augmented Generation pipeline with safety prompting and citations.
"""

import os
import json
import yaml
import faiss
import requests
from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

from ollama_client import OllamaClient
from faiss_manager import FAISSManager
from task_router import TaskRouter
from cache import QueryCache
from handlers import (
    DocTypeHandler, HookHandler, PatchHandler, PermissionHandler,
    ReportHandler, APIHandler, JobHandler, SchedulerHandler, UXHandler,
    CodeReviewHandler
)


def load_config():
    """Load configuration from config.yml"""
    # Try local path first, then Docker path
    local_config = Path(__file__).parent.parent / "config.yml"
    docker_config = Path("/app/config.yml")
    
    if local_config.exists():
        config_path = local_config
    elif docker_config.exists():
        config_path = docker_config
    else:
        raise FileNotFoundError(f"config.yml not found at {local_config} or {docker_config}")
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


class QueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5
    include_citations: Optional[bool] = True


class Citation(BaseModel):
    source: str
    repo: str
    path: str
    commit: str
    line_ranges: dict
    score: float
    content_preview: str


class RAGResponse(BaseModel):
    answer: str
    citations: List[Citation]
    retrieved_chunks: int


class RAGPipeline:
    def __init__(self, config):
        self.config = config
        
        # Auto-detect Ollama connection
        self._auto_detect_ollama()
        
        self.ollama = OllamaClient(config)
        self.faiss_manager = FAISSManager(config)
        
        # Initialize task router
        self.task_router = TaskRouter()
        
        # Initialize cache if enabled
        cache_enabled = config.get('task_routing', {}).get('cache_enabled', True)
        self.cache = QueryCache() if cache_enabled else None
        
        # Initialize handlers
        self.handlers = {
            'doctype': DocTypeHandler(config, self.faiss_manager, self.ollama, self.cache),
            'hook': HookHandler(config, self.faiss_manager, self.ollama, self.cache),
            'patch': PatchHandler(config, self.faiss_manager, self.ollama, self.cache),
            'permission': PermissionHandler(config, self.faiss_manager, self.ollama, self.cache),
            'report': ReportHandler(config, self.faiss_manager, self.ollama, self.cache),
            'api': APIHandler(config, self.faiss_manager, self.ollama, self.cache),
            'job': JobHandler(config, self.faiss_manager, self.ollama, self.cache),
            'scheduler': SchedulerHandler(config, self.faiss_manager, self.ollama, self.cache),
            'ux': UXHandler(config, self.faiss_manager, self.ollama, self.cache),
            'code_review': CodeReviewHandler(config, self.faiss_manager, self.ollama, self.cache),
        }
    
    def _auto_detect_ollama(self):
        """Auto-detect and configure Ollama connection"""
        import requests
        
        # Try localhost first
        ollama_hosts = ['localhost', '127.0.0.1']
        ollama_port = self.config.get('ollama', {}).get('port', 11434)
        
        # Check if host is already set to docker internal
        current_host = self.config.get('ollama', {}).get('host', 'localhost')
        if current_host == 'host.docker.internal':
            # Try localhost when running locally
            for host in ollama_hosts:
                try:
                    url = f"http://{host}:{ollama_port}/api/tags"
                    response = requests.get(url, timeout=2)
                    if response.status_code == 200:
                        self.config['ollama']['host'] = host
                        return
                except:
                    continue
        else:
            # Check if current host is accessible
            try:
                url = f"http://{current_host}:{ollama_port}/api/tags"
                response = requests.get(url, timeout=2)
                if response.status_code == 200:
                    return
            except:
                pass
        
        # If we get here, Ollama might not be running - keep original config
    
    def format_citation(self, chunk_metadata):
        """Format citation according to specification"""
        if chunk_metadata['type'] == 'documentation':
            # Doc citation: docs.frappe.io/path#Heading
            url = chunk_metadata['path']
            headings = chunk_metadata.get('headings', [])
            heading_text = headings[0]['text'] if headings else ''
            return f"{url}#{heading_text}" if heading_text else url
        else:
            # Code citation: repo/path/file.py#L10-L40@commitSHA
            repo = chunk_metadata['repo']
            path = chunk_metadata['path']
            line_ranges = chunk_metadata.get('line_ranges', {})
            commit = chunk_metadata.get('commit', 'unknown')
            
            line_start = line_ranges.get('start', 0)
            line_end = line_ranges.get('end', 0)
            
            if line_start and line_end:
                return f"{repo}/{path}#L{line_start}-L{line_end}@{commit}"
            else:
                return f"{repo}/{path}@{commit}"
    
    def retrieve_context(self, query, top_k=None):
        """Retrieve relevant context from FAISS index"""
        if top_k is None:
            top_k = self.config['retrieval']['top_k']
        
        results = self.faiss_manager.search(query, top_k=top_k)
        
        # Filter by similarity threshold
        threshold = self.config['retrieval']['similarity_threshold']
        filtered_results = [r for r in results if r['score'] >= threshold]
        
        return filtered_results
    
    def build_prompt(self, query, retrieved_chunks):
        """Build prompt with retrieved context and safety checks"""
        # Safety check: abort if no relevant context
        if not retrieved_chunks:
            raise ValueError("No relevant context found for query. Cannot provide answer without documentation.")
        
        # Build context from retrieved chunks
        context_parts = []
        citations = []
        
        for i, chunk in enumerate(retrieved_chunks):
            citation = self.format_citation(chunk)
            citations.append(citation)
            
            # Add citation marker
            context_parts.append(f"[Citation {i+1}: {citation}]")
            context_parts.append(chunk.get('metadata', {}).get('content', chunk.get('content', ''))[:500])
            context_parts.append("")
        
        context = "\n".join(context_parts)
        
        # Build prompt with safety instructions
        prompt = f"""You are a KoraFlow AI assistant helping with Frappe Framework and ERPNext development.

IMPORTANT SAFETY RULES:
1. Only answer based on the provided context below
2. Always cite your sources using the citation format provided
3. If the context doesn't contain enough information, say so explicitly
4. Never make assumptions not supported by the documentation

CONTEXT (with citations):
{context}

USER QUERY: {query}

Please provide a helpful answer based on the context above. Include citations in your response using the format [Citation N]."""

        return prompt, citations
    
    def generate_answer(self, query, top_k=None):
        """Generate answer using RAG pipeline with task routing"""
        # Check if task routing is enabled
        routing_enabled = self.config.get('task_routing', {}).get('enabled', True)
        
        if routing_enabled:
            # Detect task type
            task_type, params = self.task_router.detect_task(query)
            
            # Use task-specific handler if available
            if task_type != 'generic' and task_type in self.handlers:
                try:
                    handler_response = self.handlers[task_type].generate(query, params)
                    
                    # Convert handler response to RAGResponse format
                    formatted_citations = [
                        Citation(
                            source=cit,
                            repo=cit.split('/')[0] if '/' in cit else 'unknown',
                            path=cit.split('/', 1)[1] if '/' in cit else cit,
                            commit='unknown',
                            line_ranges={},
                            score=0.8,
                            content_preview=''
                        )
                        for cit in handler_response.get('citations', [])
                    ]
                    
                    return RAGResponse(
                        answer=handler_response['answer'],
                        citations=formatted_citations,
                        retrieved_chunks=handler_response.get('retrieved_chunks', 0)
                    )
                except Exception as e:
                    # Fallback to generic if handler fails
                    import traceback
                    print(f"Handler {task_type} failed, falling back to generic: {e}")
                    traceback.print_exc()
        
        # Fallback to generic RAG
        return self._generate_generic_answer(query, top_k)
    
    def _generate_generic_answer(self, query, top_k=None):
        """Generate answer using generic RAG pipeline"""
        # Step 1: Retrieve context
        retrieved_chunks = self.retrieve_context(query, top_k)
        
        if not retrieved_chunks:
            raise ValueError("No relevant documentation found for this query.")
        
        # Step 2: Build prompt with context
        prompt, citations = self.build_prompt(query, retrieved_chunks)
        
        # Step 3: Generate answer
        answer = self.ollama.generate(
            prompt,
            temperature=self.config['ollama']['temperature'],
            max_tokens=self.config['ollama']['max_tokens']
        )
        
        # Step 4: Format response with citations
        formatted_citations = [
            Citation(
                source=chunk['source'],
                repo=chunk['repo'],
                path=chunk['path'],
                commit=chunk.get('commit', 'unknown'),
                line_ranges=chunk.get('line_ranges', {}),
                score=chunk['score'],
                content_preview=chunk.get('content', '')[:200]
            )
            for chunk in retrieved_chunks
        ]
        
        return RAGResponse(
            answer=answer,
            citations=formatted_citations,
            retrieved_chunks=len(retrieved_chunks)
        )


# FastAPI app
app = FastAPI(title="KoraFlow RAG Pipeline", version="1.0.0")

# Initialize pipeline
config = load_config()
pipeline = RAGPipeline(config)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    ollama_available = pipeline.ollama.is_available()
    cache_stats = pipeline.cache.stats() if pipeline.cache else None
    
    return {
        "status": "healthy" if ollama_available else "degraded",
        "ollama_available": ollama_available,
        "index_size": pipeline.faiss_manager.index.ntotal,
        "task_routing_enabled": pipeline.config.get('task_routing', {}).get('enabled', True),
        "cache_stats": cache_stats
    }


@app.post("/query", response_model=RAGResponse)
async def query(request: QueryRequest):
    """Query the RAG pipeline"""
    try:
        response = pipeline.generate_answer(request.query, request.top_k)
        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


if __name__ == "__main__":
    import os
    port = int(os.getenv("RAG_PORT", "8001"))  # Use 8001 to avoid conflict with Frappe
    uvicorn.run(app, host="0.0.0.0", port=port)


#!/usr/bin/env python3
"""
RAG Pipeline Service
Retrieval-Augmented Generation pipeline with safety prompting and citations.
"""

import os
import json
import yaml
import faiss
from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

from ollama_client import OllamaClient
from faiss_manager import FAISSManager


def load_config():
    """Load configuration from config.yml"""
    config_path = Path("/app/config.yml")
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
        self.ollama = OllamaClient(config)
        self.faiss_manager = FAISSManager(config)
    
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
        """Generate answer using RAG pipeline"""
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
    return {
        "status": "healthy" if ollama_available else "degraded",
        "ollama_available": ollama_available,
        "index_size": pipeline.faiss_manager.index.ntotal
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
    uvicorn.run(app, host="0.0.0.0", port=8000)


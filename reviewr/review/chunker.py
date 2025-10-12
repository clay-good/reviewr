from abc import ABC, abstractmethod
from typing import List
from pathlib import Path

from ..providers.base import CodeChunk


class ChunkStrategy(ABC):
    """Abstract base class for chunking strategies."""
    
    @abstractmethod
    def chunk_file(self, file_path: str, content: str, language: str, 
                   max_tokens: int) -> List[CodeChunk]:
        """
        Chunk a file into reviewable pieces.
        
        Args:
            file_path: Path to the file
            content: File content
            language: Programming language
            max_tokens: Maximum tokens per chunk
            
        Returns:
            List of code chunks
        """
        pass


class SimpleChunker(ChunkStrategy):
    """Simple line-based chunking strategy."""
    
    def __init__(self, overlap_lines: int = 10):
        """
        Initialize simple chunker.
        
        Args:
            overlap_lines: Number of lines to overlap between chunks
        """
        self.overlap_lines = overlap_lines
    
    def chunk_file(self, file_path: str, content: str, language: str, 
                   max_tokens: int) -> List[CodeChunk]:
        """Chunk file by lines with overlap."""
        lines = content.split('\n')
        total_lines = len(lines)
        
        # Estimate lines per chunk (roughly 4 chars per token, 50 chars per line avg)
        chars_per_chunk = max_tokens * 4
        lines_per_chunk = max(chars_per_chunk // 50, 50)  # At least 50 lines
        
        # If file is small enough, return as single chunk
        if total_lines <= lines_per_chunk:
            return [CodeChunk(
                content=content,
                file_path=file_path,
                start_line=1,
                end_line=total_lines,
                language=language,
                context=None
            )]
        
        chunks = []
        start = 0
        
        while start < total_lines:
            end = min(start + lines_per_chunk, total_lines)
            
            chunk_lines = lines[start:end]
            chunk_content = '\n'.join(chunk_lines)
            
            # Add context from previous chunk if not first chunk
            context = None
            if start > 0 and self.overlap_lines > 0:
                context_start = max(0, start - self.overlap_lines)
                context_lines = lines[context_start:start]
                context = '\n'.join(context_lines)
            
            chunk = CodeChunk(
                content=chunk_content,
                file_path=file_path,
                start_line=start + 1,
                end_line=end,
                language=language,
                context=context
            )
            chunks.append(chunk)
            
            # Move to next chunk with overlap
            start = end - self.overlap_lines if end < total_lines else end
        
        return chunks


class FileBasedChunker(ChunkStrategy):
    """Chunk entire files as single units."""
    
    def chunk_file(self, file_path: str, content: str, language: str, 
                   max_tokens: int) -> List[CodeChunk]:
        """Return entire file as a single chunk."""
        lines = content.split('\n')
        
        return [CodeChunk(
            content=content,
            file_path=file_path,
            start_line=1,
            end_line=len(lines),
            language=language,
            context=None
        )]


def get_chunker(strategy: str, **kwargs) -> ChunkStrategy:
    """
    Get a chunker instance by strategy name.
    
    Args:
        strategy: Strategy name (simple, file_based, ast_aware)
        **kwargs: Additional arguments for the chunker
        
    Returns:
        ChunkStrategy instance
    """
    strategies = {
        'simple': SimpleChunker,
        'sliding_window': SimpleChunker,
        'file_based': FileBasedChunker,
        'ast_aware': SimpleChunker,  # Fallback to simple for now
    }
    
    chunker_class = strategies.get(strategy, SimpleChunker)
    return chunker_class(**kwargs)


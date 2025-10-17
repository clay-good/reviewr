import hashlib
import json
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from diskcache import Cache
import os


@dataclass
class CacheEntry:
    """A cache entry for a code review."""
    file_hash: str
    file_path: str
    review_types: List[str]
    findings: List[Dict[str, Any]]
    timestamp: float
    provider: str
    model: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CacheEntry':
        """Create from dictionary."""
        return cls(**data)


class IntelligentCache:
    """Intelligent caching system with hash-based invalidation."""
    
    def __init__(self, cache_dir: Optional[Path] = None, ttl: int = 86400 * 7):
        """
        Initialize the cache.
        
        Args:
            cache_dir: Directory for cache storage (default: ~/.cache/reviewr)
            ttl: Time-to-live in seconds (default: 7 days)
        """
        if cache_dir is None:
            cache_dir = Path.home() / '.cache' / 'reviewr'
        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.cache = Cache(str(self.cache_dir))
        self.ttl = ttl
        self.stats = {
            'hits': 0,
            'misses': 0,
            'invalidations': 0
        }
    
    def _compute_file_hash(self, file_path: Path) -> str:
        """
        Compute SHA-256 hash of file content.
        
        Args:
            file_path: Path to file
            
        Returns:
            Hex digest of file hash
        """
        sha256 = hashlib.sha256()
        
        try:
            with open(file_path, 'rb') as f:
                # Read in chunks for large files
                for chunk in iter(lambda: f.read(8192), b''):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except Exception:
            # If we can't read the file, return a timestamp-based hash
            return hashlib.sha256(str(time.time()).encode()).hexdigest()
    
    def _compute_cache_key(
        self,
        file_hash: str,
        review_types: List[str],
        provider: str,
        model: str
    ) -> str:
        """
        Compute cache key from file hash and review parameters.
        
        Args:
            file_hash: Hash of file content
            review_types: List of review types
            provider: LLM provider name
            model: Model name
            
        Returns:
            Cache key string
        """
        # Sort review types for consistent keys
        sorted_types = sorted(review_types)
        key_data = f"{file_hash}:{':'.join(sorted_types)}:{provider}:{model}"
        return hashlib.sha256(key_data.encode()).hexdigest()
    
    def get(
        self,
        file_path: Path,
        review_types: List[str],
        provider: str,
        model: str
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get cached review results if available and valid.
        
        Args:
            file_path: Path to file
            review_types: List of review types
            provider: LLM provider name
            model: Model name
            
        Returns:
            Cached findings or None if not found/invalid
        """
        # Compute current file hash
        current_hash = self._compute_file_hash(file_path)
        
        # Compute cache key
        cache_key = self._compute_cache_key(current_hash, review_types, provider, model)
        
        # Try to get from cache
        try:
            cached_data = self.cache.get(cache_key)
            
            if cached_data is None:
                self.stats['misses'] += 1
                return None
            
            # Deserialize
            entry = CacheEntry.from_dict(cached_data)
            
            # Verify file hash matches (content hasn't changed)
            if entry.file_hash != current_hash:
                self.stats['invalidations'] += 1
                self.cache.delete(cache_key)
                return None
            
            # Check if expired
            age = time.time() - entry.timestamp
            if age > self.ttl:
                self.stats['invalidations'] += 1
                self.cache.delete(cache_key)
                return None
            
            self.stats['hits'] += 1
            return entry.findings
            
        except Exception:
            self.stats['misses'] += 1
            return None
    
    def set(
        self,
        file_path: Path,
        review_types: List[str],
        provider: str,
        model: str,
        findings: List[Dict[str, Any]]
    ) -> None:
        """
        Store review results in cache.
        
        Args:
            file_path: Path to file
            review_types: List of review types
            provider: LLM provider name
            model: Model name
            findings: Review findings to cache
        """
        # Compute file hash
        file_hash = self._compute_file_hash(file_path)
        
        # Compute cache key
        cache_key = self._compute_cache_key(file_hash, review_types, provider, model)
        
        # Create cache entry
        entry = CacheEntry(
            file_hash=file_hash,
            file_path=str(file_path),
            review_types=review_types,
            findings=findings,
            timestamp=time.time(),
            provider=provider,
            model=model
        )
        
        # Store in cache
        try:
            self.cache.set(cache_key, entry.to_dict(), expire=self.ttl)
        except Exception:
            # Silently fail if cache write fails
            pass
    
    def invalidate_file(self, file_path: Path) -> int:
        """
        Invalidate all cache entries for a specific file.
        
        Args:
            file_path: Path to file
            
        Returns:
            Number of entries invalidated
        """
        count = 0
        file_path_str = str(file_path)
        
        try:
            # Iterate through cache and remove entries for this file
            for key in list(self.cache.iterkeys()):
                try:
                    entry_data = self.cache.get(key)
                    if entry_data and entry_data.get('file_path') == file_path_str:
                        self.cache.delete(key)
                        count += 1
                except Exception:
                    continue
        except Exception:
            pass
        
        self.stats['invalidations'] += count
        return count
    
    def clear(self) -> None:
        """Clear all cache entries."""
        try:
            self.cache.clear()
            self.stats['invalidations'] += len(self.cache)
        except Exception:
            pass
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache stats
        """
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'invalidations': self.stats['invalidations'],
            'total_requests': total_requests,
            'hit_rate': f"{hit_rate:.1f}%",
            'cache_size': len(self.cache),
            'cache_dir': str(self.cache_dir)
        }
    
    def get_size(self) -> int:
        """Get number of entries in cache."""
        try:
            return len(self.cache)
        except Exception:
            return 0
    
    def close(self) -> None:
        """Close the cache."""
        try:
            self.cache.close()
        except Exception:
            pass


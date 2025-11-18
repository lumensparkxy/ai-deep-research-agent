"""
Simple file-based cache manager for API responses.
"""

import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Optional, Any

class CacheManager:
    """Simple file-based cache manager."""
    
    def __init__(self, cache_dir: str, enabled: bool = True):
        self.cache_dir = Path(cache_dir)
        self.enabled = enabled
        self.logger = logging.getLogger(__name__)
        
        if self.enabled:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            
    def get(self, key: str) -> Optional[Any]:
        """Retrieve value from cache."""
        if not self.enabled:
            return None
            
        cache_file = self._get_cache_file(key)
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.logger.debug(f"Cache hit for key: {key}")
                    return data
            except Exception as e:
                self.logger.warning(f"Failed to read cache for key {key}: {e}")
        return None
        
    def set(self, key: str, value: Any) -> None:
        """Set value in cache."""
        if not self.enabled:
            return
            
        cache_file = self._get_cache_file(key)
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(value, f, ensure_ascii=False)
                self.logger.debug(f"Cache set for key: {key}")
        except Exception as e:
            self.logger.warning(f"Failed to write cache for key {key}: {e}")
            
    def _get_cache_file(self, key: str) -> Path:
        """Generate cache file path from key."""
        hashed_key = hashlib.sha256(key.encode('utf-8')).hexdigest()
        return self.cache_dir / f"{hashed_key}.json"

import os
import json
import pickle
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict

from .models import ContentDNA, PlatformContent, PublishResult


@dataclass
class CacheEntry:
    """Represents a cached item with metadata"""
    key: str
    data: Any
    created_at: datetime
    expires_at: Optional[datetime] = None
    access_count: int = 0
    last_accessed: Optional[datetime] = None


@dataclass
class FailedPost:
    """Represents a failed posting attempt that can be retried"""
    platform: str
    content: PlatformContent
    error: str
    attempt_count: int
    created_at: datetime
    last_attempt: datetime
    next_retry: datetime
    max_retries: int = 3


class CacheManager:
    """Intelligent caching and recovery system for content publishing"""
    
    def __init__(self, cache_dir: Path = None):
        self.cache_dir = cache_dir or Path("cache")
        self.cache_dir.mkdir(exist_ok=True)
        
        # Cache subdirectories
        self.content_cache_dir = self.cache_dir / "content"
        self.dna_cache_dir = self.cache_dir / "dna"
        self.failed_posts_dir = self.cache_dir / "failed_posts"
        self.results_dir = self.cache_dir / "results"
        
        for dir_path in [self.content_cache_dir, self.dna_cache_dir, 
                        self.failed_posts_dir, self.results_dir]:
            dir_path.mkdir(exist_ok=True)
        
        # In-memory cache for quick access
        self._memory_cache: Dict[str, CacheEntry] = {}
        
        # Load existing failed posts
        self._load_failed_posts()
    
    def _get_cache_key(self, content: str, platform: str = None) -> str:
        """Generate cache key from content"""
        import hashlib
        content_hash = hashlib.md5(content.encode()).hexdigest()[:12]
        if platform:
            return f"{platform}_{content_hash}"
        return content_hash
    
    def cache_content_dna(self, content: str, dna: ContentDNA, ttl_hours: int = 24) -> str:
        """Cache extracted content DNA"""
        cache_key = self._get_cache_key(content)
        expires_at = datetime.now() + timedelta(hours=ttl_hours)
        
        # Save to file
        cache_file = self.dna_cache_dir / f"{cache_key}.json"
        cache_data = {
            "content_hash": cache_key,
            "dna": asdict(dna),
            "created_at": datetime.now().isoformat(),
            "expires_at": expires_at.isoformat(),
            "original_content_length": len(content)
        }
        
        with open(cache_file, 'w') as f:
            json.dump(cache_data, f, indent=2)
        
        # Add to memory cache
        entry = CacheEntry(
            key=cache_key,
            data=dna,
            created_at=datetime.now(),
            expires_at=expires_at
        )
        self._memory_cache[f"dna_{cache_key}"] = entry
        
        print(f"💾 Cached content DNA: {cache_key}")
        return cache_key
    
    def get_cached_dna(self, content: str) -> Optional[ContentDNA]:
        """Retrieve cached content DNA"""
        cache_key = self._get_cache_key(content)
        memory_key = f"dna_{cache_key}"
        
        # Check memory cache first
        if memory_key in self._memory_cache:
            entry = self._memory_cache[memory_key]
            if not entry.expires_at or datetime.now() < entry.expires_at:
                entry.access_count += 1
                entry.last_accessed = datetime.now()
                print(f"🎯 Retrieved DNA from memory cache: {cache_key}")
                return entry.data
            else:
                # Expired
                del self._memory_cache[memory_key]
        
        # Check file cache
        cache_file = self.dna_cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    cache_data = json.load(f)
                
                expires_at = datetime.fromisoformat(cache_data['expires_at'])
                if datetime.now() < expires_at:
                    # Reconstruct ContentDNA
                    dna_data = cache_data['dna']
                    dna = ContentDNA(**dna_data)
                    
                    # Add back to memory cache
                    entry = CacheEntry(
                        key=cache_key,
                        data=dna,
                        created_at=datetime.fromisoformat(cache_data['created_at']),
                        expires_at=expires_at,
                        access_count=1,
                        last_accessed=datetime.now()
                    )
                    self._memory_cache[memory_key] = entry
                    
                    print(f"📁 Retrieved DNA from file cache: {cache_key}")
                    return dna
                else:
                    # Expired, remove file
                    cache_file.unlink()
                    
            except Exception as e:
                print(f"⚠️  Error reading cache file {cache_file}: {e}")
                cache_file.unlink(missing_ok=True)
        
        return None
    
    def cache_platform_content(self, content_dna_key: str, platform: str, 
                             content: PlatformContent, ttl_hours: int = 6) -> str:
        """Cache generated platform content"""
        cache_key = f"{platform}_{content_dna_key}"
        expires_at = datetime.now() + timedelta(hours=ttl_hours)
        
        # Save to file
        cache_file = self.content_cache_dir / f"{cache_key}.json"
        cache_data = {
            "platform": platform,
            "content_dna_key": content_dna_key,
            "content": {
                "platform": content.platform,
                "title": content.title,
                "body": content.body,
                "metadata": content.metadata,
                "validation": asdict(content.validation) if content.validation else None
            },
            "created_at": datetime.now().isoformat(),
            "expires_at": expires_at.isoformat()
        }
        
        with open(cache_file, 'w') as f:
            json.dump(cache_data, f, indent=2)
        
        print(f"💾 Cached {platform} content: {cache_key}")
        return cache_key
    
    def get_cached_platform_content(self, content_dna_key: str, platform: str) -> Optional[PlatformContent]:
        """Retrieve cached platform content"""
        cache_key = f"{platform}_{content_dna_key}"
        cache_file = self.content_cache_dir / f"{cache_key}.json"
        
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    cache_data = json.load(f)
                
                expires_at = datetime.fromisoformat(cache_data['expires_at'])
                if datetime.now() < expires_at:
                    # Reconstruct PlatformContent
                    content_data = cache_data['content']
                    from .models import ValidationResult
                    
                    validation = None
                    if content_data['validation']:
                        validation = ValidationResult(**content_data['validation'])
                    
                    content = PlatformContent(
                        platform=content_data['platform'],
                        title=content_data['title'],
                        body=content_data['body'],
                        metadata=content_data['metadata'],
                        validation=validation
                    )
                    
                    print(f"📁 Retrieved {platform} content from cache: {cache_key}")
                    return content
                else:
                    # Expired, remove file
                    cache_file.unlink()
                    
            except Exception as e:
                print(f"⚠️  Error reading cache file {cache_file}: {e}")
                cache_file.unlink(missing_ok=True)
        
        return None
    
    def save_failed_post(self, platform: str, content: PlatformContent, error: str):
        """Save failed post for retry"""
        failed_post = FailedPost(
            platform=platform,
            content=content,
            error=error,
            attempt_count=1,
            created_at=datetime.now(),
            last_attempt=datetime.now(),
            next_retry=self._calculate_next_retry(1)
        )
        
        # Generate unique ID for failed post
        failed_id = f"{platform}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Save to file
        failed_file = self.failed_posts_dir / f"{failed_id}.json"
        failed_data = {
            "id": failed_id,
            "platform": failed_post.platform,
            "content": {
                "platform": content.platform,
                "title": content.title,
                "body": content.body,
                "metadata": content.metadata
            },
            "error": failed_post.error,
            "attempt_count": failed_post.attempt_count,
            "created_at": failed_post.created_at.isoformat(),
            "last_attempt": failed_post.last_attempt.isoformat(),
            "next_retry": failed_post.next_retry.isoformat(),
            "max_retries": failed_post.max_retries
        }
        
        with open(failed_file, 'w') as f:
            json.dump(failed_data, f, indent=2)
        
        print(f"💾 Saved failed post for retry: {failed_id}")
        return failed_id
    
    def _load_failed_posts(self) -> List[FailedPost]:
        """Load existing failed posts from disk"""
        failed_posts = []
        
        for failed_file in self.failed_posts_dir.glob("*.json"):
            try:
                with open(failed_file, 'r') as f:
                    data = json.load(f)
                
                from .models import ValidationResult
                
                # Reconstruct PlatformContent
                content_data = data['content']
                content = PlatformContent(
                    platform=content_data['platform'],
                    title=content_data['title'],
                    body=content_data['body'],
                    metadata=content_data['metadata'],
                    validation=ValidationResult(is_valid=True, warnings=[], errors=[], suggestions=[])
                )
                
                failed_post = FailedPost(
                    platform=data['platform'],
                    content=content,
                    error=data['error'],
                    attempt_count=data['attempt_count'],
                    created_at=datetime.fromisoformat(data['created_at']),
                    last_attempt=datetime.fromisoformat(data['last_attempt']),
                    next_retry=datetime.fromisoformat(data['next_retry']),
                    max_retries=data.get('max_retries', 3)
                )
                
                failed_posts.append(failed_post)
                
            except Exception as e:
                print(f"⚠️  Error loading failed post {failed_file}: {e}")
                # Remove corrupted file
                failed_file.unlink(missing_ok=True)
        
        return failed_posts
    
    def get_retry_ready_posts(self) -> List[FailedPost]:
        """Get failed posts that are ready for retry"""
        failed_posts = self._load_failed_posts()
        now = datetime.now()
        
        retry_ready = []
        for post in failed_posts:
            if (post.attempt_count < post.max_retries and 
                now >= post.next_retry):
                retry_ready.append(post)
        
        return retry_ready
    
    def update_failed_post_attempt(self, failed_id: str, new_error: str = None) -> bool:
        """Update failed post with new attempt"""
        failed_file = self.failed_posts_dir / f"{failed_id}.json"
        
        if not failed_file.exists():
            return False
        
        try:
            with open(failed_file, 'r') as f:
                data = json.load(f)
            
            data['attempt_count'] += 1
            data['last_attempt'] = datetime.now().isoformat()
            
            if new_error:
                data['error'] = new_error
            
            # Calculate next retry time
            data['next_retry'] = self._calculate_next_retry(data['attempt_count']).isoformat()
            
            with open(failed_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"⚠️  Error updating failed post {failed_id}: {e}")
            return False
    
    def remove_failed_post(self, failed_id: str) -> bool:
        """Remove failed post (after successful retry or giving up)"""
        failed_file = self.failed_posts_dir / f"{failed_id}.json"
        
        if failed_file.exists():
            failed_file.unlink()
            print(f"🗑️  Removed failed post: {failed_id}")
            return True
        
        return False
    
    def _calculate_next_retry(self, attempt_count: int) -> datetime:
        """Calculate next retry time with exponential backoff"""
        # Exponential backoff: 1min, 5min, 30min
        delays = [1, 5, 30]  # minutes
        delay_index = min(attempt_count - 1, len(delays) - 1)
        delay_minutes = delays[delay_index]
        
        return datetime.now() + timedelta(minutes=delay_minutes)
    
    def save_publish_results(self, results: Dict[str, PublishResult]) -> str:
        """Save publishing results for audit trail"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = self.results_dir / f"publish_results_{timestamp}.json"
        
        results_data = {
            "timestamp": datetime.now().isoformat(),
            "results": {}
        }
        
        for platform, result in results.items():
            results_data["results"][platform] = {
                "platform": result.platform,
                "success": result.success,
                "url": result.url,
                "error": result.error,
                "metadata": result.metadata
            }
        
        with open(results_file, 'w') as f:
            json.dump(results_data, f, indent=2)
        
        print(f"💾 Saved publish results: {results_file.name}")
        return str(results_file)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        stats = {
            "memory_cache_size": len(self._memory_cache),
            "dna_cache_files": len(list(self.dna_cache_dir.glob("*.json"))),
            "content_cache_files": len(list(self.content_cache_dir.glob("*.json"))),
            "failed_posts": len(list(self.failed_posts_dir.glob("*.json"))),
            "results_files": len(list(self.results_dir.glob("*.json"))),
            "total_cache_size_mb": self._get_directory_size(self.cache_dir) / (1024 * 1024)
        }
        
        # Memory cache access stats
        total_access = sum(entry.access_count for entry in self._memory_cache.values())
        stats["memory_cache_total_access"] = total_access
        
        return stats
    
    def _get_directory_size(self, directory: Path) -> int:
        """Get total size of directory in bytes"""
        total_size = 0
        for file_path in directory.rglob("*"):
            if file_path.is_file():
                total_size += file_path.stat().st_size
        return total_size
    
    def cleanup_expired_cache(self):
        """Remove expired cache entries"""
        now = datetime.now()
        removed_count = 0
        
        # Clean memory cache
        expired_keys = []
        for key, entry in self._memory_cache.items():
            if entry.expires_at and now >= entry.expires_at:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._memory_cache[key]
            removed_count += 1
        
        # Clean file caches
        for cache_dir in [self.dna_cache_dir, self.content_cache_dir]:
            for cache_file in cache_dir.glob("*.json"):
                try:
                    with open(cache_file, 'r') as f:
                        data = json.load(f)
                    
                    if 'expires_at' in data:
                        expires_at = datetime.fromisoformat(data['expires_at'])
                        if now >= expires_at:
                            cache_file.unlink()
                            removed_count += 1
                            
                except Exception:
                    # Remove corrupted files
                    cache_file.unlink()
                    removed_count += 1
        
        if removed_count > 0:
            print(f"🧹 Cleaned up {removed_count} expired cache entries")
        
        return removed_count
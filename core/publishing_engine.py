import os
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from .content_analyzer import ContentAnalyzer
from .models import ContentDNA, PlatformContent, PublishResult


class PublishingEngine:
    """Main orchestrator for the two-phase publishing system"""
    
    def __init__(self, config_dir: Path = None):
        self.config_dir = config_dir or Path("config")
        self.platforms_dir = Path("platforms")
        self.cache_dir = Path("cache")
        self.content_analyzer = ContentAnalyzer()
        self.platform_adapters = {}
        
        # Ensure cache directory exists
        self.cache_dir.mkdir(exist_ok=True)
        
        # Load available platforms
        self._load_platform_adapters()
    
    def _load_platform_adapters(self):
        """Dynamically load platform adapters"""
        platform_modules = {
            'hackernews': 'platforms.hackernews.adapter',
            'reddit': 'platforms.reddit.adapter', 
            'twitter': 'platforms.twitter.adapter',
            'medium': 'platforms.medium.adapter',
            'devto': 'platforms.devto.adapter',
            'peerlist': 'platforms.peerlist.adapter'
        }
        
        for platform_name, module_path in platform_modules.items():
            try:
                module = __import__(module_path, fromlist=[''])
                adapter_class = getattr(module, f'{platform_name.title()}Adapter')
                config_dir = self.platforms_dir / platform_name
                self.platform_adapters[platform_name] = adapter_class(config_dir)
            except (ImportError, AttributeError) as e:
                print(f"⚠️  Platform {platform_name} not available: {e}")
    
    def analyze_content(self, markdown_content: str) -> ContentDNA:
        """Phase 1: Extract content DNA"""
        print("🔍 Analyzing content...")
        content_dna = self.content_analyzer.analyze(markdown_content)
        print("🧬 Content DNA extracted")
        return content_dna
    
    def generate_platform_content(self, content_dna: ContentDNA, platforms: List[str] = None) -> Dict[str, PlatformContent]:
        """Phase 2: Generate platform-specific content"""
        if platforms is None:
            platforms = list(self.platform_adapters.keys())
        
        print("🎯 Generating platform-specific content...")
        results = {}
        api_key = os.environ.get("OPENAI_API_KEY")
        
        for platform_name in platforms:
            if platform_name not in self.platform_adapters:
                print(f"❌ Platform {platform_name} not available")
                continue
                
            try:
                adapter = self.platform_adapters[platform_name]
                content = adapter.generate_content(content_dna, api_key)
                validation = adapter.validate_content(content)
                content.validation = validation
                
                results[platform_name] = content
                
                status = "✅" if validation.is_valid else "⚠️"
                print(f"  {status} {platform_name.title()}")
                
                if validation.warnings:
                    for warning in validation.warnings:
                        print(f"    ⚠️  {warning}")
                        
            except Exception as e:
                print(f"  ❌ {platform_name.title()}: {str(e)}")
        
        return results
    
    def preview_content(self, platform_content: Dict[str, PlatformContent]) -> str:
        """Generate a preview of all platform content"""
        preview = []
        preview.append("=" * 60)
        preview.append("CONTENT PREVIEW")
        preview.append("=" * 60)
        
        for platform_name, content in platform_content.items():
            preview.append(f"\n📱 {platform_name.upper()}")
            preview.append("-" * 40)
            preview.append(f"Title: {content.title}")
            preview.append(f"Body: {content.body[:200]}...")
            
            if content.metadata:
                preview.append(f"Metadata: {json.dumps(content.metadata, indent=2)}")
            
            if not content.validation.is_valid:
                preview.append("❌ VALIDATION ISSUES:")
                for error in content.validation.errors:
                    preview.append(f"  • {error}")
            
            if content.validation.warnings:
                preview.append("⚠️  WARNINGS:")
                for warning in content.validation.warnings:
                    preview.append(f"  • {warning}")
            
            preview.append("")
        
        return "\n".join(preview)
    
    def cache_content(self, content_dna: ContentDNA, platform_content: Dict[str, PlatformContent]) -> Path:
        """Cache generated content for recovery"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        cache_file = self.cache_dir / f"session_{timestamp}.json"
        
        cache_data = {
            "timestamp": timestamp,
            "content_dna": content_dna.__dict__,
            "platform_content": {
                name: {
                    "title": content.title,
                    "body": content.body,
                    "metadata": content.metadata,
                    "validation": {
                        "is_valid": content.validation.is_valid,
                        "warnings": content.validation.warnings,
                        "errors": content.validation.errors,
                        "suggestions": content.validation.suggestions
                    }
                }
                for name, content in platform_content.items()
            }
        }
        
        with open(cache_file, 'w') as f:
            json.dump(cache_data, f, indent=2)
        
        print(f"💾 Content cached to {cache_file}")
        return cache_file
    
    def publish_content(self, platform_content: Dict[str, PlatformContent], platforms: List[str] = None) -> Dict[str, PublishResult]:
        """Publish content to specified platforms"""
        if platforms is None:
            platforms = list(platform_content.keys())
        
        results = {}
        
        for platform_name in platforms:
            if platform_name not in platform_content:
                continue
                
            if platform_name not in self.platform_adapters:
                results[platform_name] = PublishResult(
                    platform=platform_name,
                    success=False,
                    error="Platform adapter not available"
                )
                continue
            
            content = platform_content[platform_name]
            
            # Skip if validation failed
            if not content.validation.is_valid:
                results[platform_name] = PublishResult(
                    platform=platform_name,
                    success=False,
                    error="Content validation failed"
                )
                print(f"❌ Skipping {platform_name}: validation failed")
                continue
            
            try:
                adapter = self.platform_adapters[platform_name]
                result = adapter.post_content(content)
                results[platform_name] = result
                
                if result.success:
                    print(f"✅ {platform_name.title()}: {result.url}")
                else:
                    print(f"❌ {platform_name.title()}: {result.error}")
                    
            except Exception as e:
                results[platform_name] = PublishResult(
                    platform=platform_name,
                    success=False,
                    error=str(e)
                )
                print(f"❌ {platform_name.title()}: {str(e)}")
        
        return results
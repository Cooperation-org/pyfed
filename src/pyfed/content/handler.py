"""
Unified content handling implementation.
"""

from typing import Dict, Any, List, Optional, Tuple
import re
from urllib.parse import urlparse
import markdown
from bs4 import BeautifulSoup
import html

from ..utils.exceptions import ContentError
from ..utils.logging import get_logger
from ..federation.discovery import InstanceDiscovery

logger = get_logger(__name__)

class ContentHandler:
    """Handle content processing."""

    def __init__(self,
                 instance_discovery: InstanceDiscovery,
                 allowed_tags: Optional[List[str]] = None,
                 allowed_attributes: Optional[Dict[str, List[str]]] = None):
        self.instance_discovery = instance_discovery
        self.allowed_tags = allowed_tags or [
            'p', 'br', 'span', 'a', 'em', 'strong',
            'ul', 'ol', 'li', 'blockquote', 'code',
            'pre', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'
        ]
        self.allowed_attributes = allowed_attributes or {
            'a': ['href', 'rel', 'class'],
            'span': ['class'],
            'code': ['class'],
            'pre': ['class']
        }
        self.markdown = markdown.Markdown(
            extensions=['extra', 'smarty', 'codehilite']
        )
        self.mention_pattern = re.compile(r'@([^@\s]+)@([^\s]+)')

    async def process_content(self,
                            content: str,
                            content_type: str = "text/markdown",
                            local_domain: Optional[str] = None) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Process content including formatting and mentions.
        
        Args:
            content: Raw content
            content_type: Content type (text/markdown or text/html)
            local_domain: Local domain for resolving mentions
            
        Returns:
            Tuple of (processed content, mention objects)
        """
        try:
            # Process mentions first
            processed_content, mentions = await self._process_mentions(
                content, local_domain
            )
            
            # Format content
            formatted_content = await self._format_content(
                processed_content,
                content_type
            )
            
            return formatted_content, mentions
            
        except Exception as e:
            logger.error(f"Content processing failed: {e}")
            raise ContentError(f"Content processing failed: {e}")

    async def _process_mentions(self,
                              content: str,
                              local_domain: Optional[str]) -> Tuple[str, List[Dict[str, Any]]]:
        """Process mentions in content."""
        mentions = []
        processed = content
        
        # Find all mentions
        for match in self.mention_pattern.finditer(content):
            username, domain = match.groups()
            mention = await self._resolve_mention(username, domain, local_domain)
            if mention:
                mentions.append(mention)
                # Replace mention with link
                processed = processed.replace(
                    f"@{username}@{domain}",
                    f"<span class='h-card'><a href='{mention['href']}' class='u-url mention'>@{username}</a></span>"
                )
        
        return processed, mentions

    async def _resolve_mention(self,
                             username: str,
                             domain: str,
                             local_domain: Optional[str]) -> Optional[Dict[str, Any]]:
        """Resolve mention to actor."""
        try:
            # Local mention
            if domain == local_domain:
                return {
                    "type": "Mention",
                    "href": f"https://{domain}/users/{username}",
                    "name": f"@{username}@{domain}"
                }
            
            # Remote mention
            webfinger = await self.instance_discovery.webfinger(
                f"acct:{username}@{domain}"
            )
            
            if not webfinger:
                return None
                
            # Find actor URL
            actor_url = None
            for link in webfinger.get('links', []):
                if link.get('rel') == 'self' and link.get('type') == 'application/activity+json':
                    actor_url = link.get('href')
                    break
            
            if not actor_url:
                return None
                
            return {
                "type": "Mention",
                "href": actor_url,
                "name": f"@{username}@{domain}"
            }
            
        except Exception as e:
            logger.error(f"Failed to resolve mention: {e}")
            return None

    async def _format_content(self,
                            content: str,
                            content_type: str) -> str:
        """Format content."""
        try:
            # Convert to HTML
            if content_type == "text/markdown":
                html_content = self.markdown.convert(content)
            else:
                html_content = content
            
            # Sanitize HTML
            clean_html = self._sanitize_html(html_content)
            
            # Add microformats
            formatted = self._add_microformats(clean_html)
            
            return formatted
            
        except Exception as e:
            logger.error(f"Failed to format content: {e}")
            raise ContentError(f"Failed to format content: {e}")

    def _sanitize_html(self, content: str) -> str:
        """Sanitize HTML content."""
        try:
            soup = BeautifulSoup(content, 'html.parser')
            
            for tag in soup.find_all(True):
                if tag.name not in self.allowed_tags:
                    tag.unwrap()
                else:
                    # Remove disallowed attributes
                    allowed = self.allowed_attributes.get(tag.name, [])
                    for attr in list(tag.attrs):
                        if attr not in allowed:
                            del tag[attr]
                            
                    # Clean URLs in links
                    if tag.name == 'a' and tag.get('href'):
                        tag['href'] = self._clean_url(tag['href'])
                        tag['rel'] = 'nofollow noopener noreferrer'
            
            return str(soup)
            
        except Exception as e:
            logger.error(f"Failed to sanitize HTML: {e}")
            raise ContentError(f"Failed to sanitize HTML: {e}")

    def _clean_url(self, url: str) -> str:
        """Clean and validate URL."""
        url = url.strip()
        
        # Only allow http(s) URLs
        if not url.startswith(('http://', 'https://')):
            return '#'
            
        return url

    def _add_microformats(self, content: str) -> str:
        """Add microformat classes."""
        try:
            soup = BeautifulSoup(content, 'html.parser')
            
            # Add e-content class to content wrapper
            if soup.find(['p', 'div']):
                wrapper = soup.find(['p', 'div'])
                wrapper['class'] = wrapper.get('class', []) + ['e-content']
            
            # Add u-url class to links
            for link in soup.find_all('a'):
                link['class'] = link.get('class', []) + ['u-url']
            
            return str(soup)
            
        except Exception as e:
            logger.error(f"Failed to add microformats: {e}")
            return content 
"""
Tests for Activity Delivery implementation.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
import aiohttp
from datetime import datetime
from typing import Dict, Any
import asyncio
from aiohttp import ClientResponse, StreamReader

from pyfed.federation.delivery import ActivityDelivery, DeliveryResult
from pyfed.federation.discovery import InstanceDiscovery
from pyfed.security.key_management import KeyManager
from pyfed.security.http_signatures import HTTPSignatureVerifier
from pyfed.utils.exceptions import DeliveryError

class MockResponse:
    """Mock aiohttp response."""
    def __init__(self, status: int, text: str = "", headers: Dict[str, str] = None):
        self.status = status
        self._text = text
        self.headers = headers or {}

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    async def text(self):
        return self._text

@pytest.fixture
def key_manager():
    key_manager = KeyManager(
        domain="b055-197-211-61-144.ngrok-free.app",
        keys_path="/Users/kene/Desktop/funkwhale-pyfed/main-lib/lastest-lib/pres_mode/pyfed/example_keys",
        rotation_config=False
    )
    key_manager.initialize()
    return key_manager

@pytest.fixture
def delivery_service(key_manager):
    """Create test delivery service."""
    discovery = InstanceDiscovery()
    discovery.initialize()
    
    # delivery = ActivityDelivery(key_manager=key_manager, discovery=discovery)
    service = ActivityDelivery(
        key_manager=key_manager,
        discovery=discovery
    )
    return service

@pytest.fixture
def test_activity():
    """Create test activity."""
    return {
        "id": "test_id",
        "type": "Create",
        "actor": "https://example.com/users/test",
        "object": {
            "type": "Note",
            "content": "Test note"
        }
    }

@pytest.mark.asyncio
async def test_successful_delivery(delivery_service, test_activity):
    """Test successful activity delivery."""
    recipients = "https://remote.com/users/bob/inbox"
    
    async def mock_post(*args, **kwargs):
        return MockResponse(status=202)
    
    with patch('aiohttp.ClientSession.post', new_callable=AsyncMock, side_effect=mock_post):
        result = await delivery_service.deliver_to_inbox(
            activity=test_activity,
            inbox_url=recipients,
            username="test_user"
        )
        
        print(result)
        assert sorted(result.success) == sorted(recipients)
        assert not result.failed
        assert result.status_code == 202

# @pytest.mark.asyncio
# async def test_failed_delivery(delivery_service, test_activity):
#     """Test failed activity delivery."""
#     recipients = ["https://remote.com/users/bob/inbox"]
    
#     async def mock_post(*args, **kwargs):
#         return MockResponse(status=500, text="Internal Server Error")
    
#     with patch('aiohttp.ClientSession.post', new_callable=AsyncMock, side_effect=mock_post):
#         result = await delivery_service.deliver_activity(
#             activity=test_activity,
#             recipients=recipients
#         )
        
#         assert not result.success
#         assert sorted(result.failed) == sorted(recipients)
#         assert result.status_code == 500
#         assert "Internal Server Error" in str(result.error_message)

# @pytest.mark.asyncio
# async def test_rate_limited_delivery(delivery_service, test_activity):
#     """Test rate-limited delivery with retry."""
#     recipients = ["https://remote.com/users/bob/inbox"]
    
#     responses = [
#         MockResponse(status=429, headers={"Retry-After": "1"}),
#         MockResponse(status=202)
#     ]
#     response_iter = iter(responses)
    
#     async def mock_post(*args, **kwargs):
#         return next(response_iter)
    
#     with patch('aiohttp.ClientSession.post', new_callable=AsyncMock, side_effect=mock_post):
#         result = await delivery_service.deliver_activity(
#             activity=test_activity,
#             recipients=recipients
#         )
        
#         assert sorted(result.success) == sorted(recipients)
#         assert not result.failed
#         assert result.status_code == 202

# @pytest.mark.asyncio
# async def test_shared_inbox_delivery(delivery_service, test_activity):
#     """Test delivery to shared inbox."""
#     recipients = [
#         "https://remote.com/users/bob/inbox",
#         "https://remote.com/users/alice/inbox"
#     ]
    
#     async def mock_post(*args, **kwargs):
#         return MockResponse(status=202)
    
#     with patch('aiohttp.ClientSession.post', new_callable=AsyncMock, side_effect=mock_post):
#         result = await delivery_service.deliver_activity(
#             activity=test_activity,
#             recipients=recipients
#         )
        
#         assert sorted(result.success) == sorted(recipients)
#         assert not result.failed
#         assert result.status_code == 202

# @pytest.mark.asyncio
# async def test_delivery_timeout(delivery_service, test_activity):
#     """Test delivery timeout handling."""
#     recipients = ["https://remote.com/users/bob/inbox"]
    
#     async def mock_post(*args, **kwargs):
#         raise asyncio.TimeoutError()
    
#     with patch('aiohttp.ClientSession.post', new_callable=AsyncMock, side_effect=mock_post):
#         result = await delivery_service.deliver_activity(
#             activity=test_activity,
#             recipients=recipients
#         )
        
#         assert not result.success
#         assert sorted(result.failed) == sorted(recipients)
#         assert "timeout" in str(result.error_message).lower()

# @pytest.mark.asyncio
# async def test_multiple_domains(delivery_service, test_activity):
#     """Test delivery to multiple domains."""
#     recipients = [
#         "https://remote1.com/users/bob/inbox",
#         "https://remote2.com/users/alice/inbox"
#     ]
    
#     async def mock_post(url, *args, **kwargs):
#         if "remote1.com" in url:
#             return MockResponse(status=202)
#         return MockResponse(status=500, text="Error")
    
#     with patch('aiohttp.ClientSession.post', new_callable=AsyncMock, side_effect=mock_post):
#         result = await delivery_service.deliver_activity(
#             activity=test_activity,
#             recipients=recipients
#         )
        
#         assert len([r for r in result.success if "remote1.com" in r]) == 1
#         assert len([r for r in result.failed if "remote2.com" in r]) == 1

# @pytest.mark.asyncio
# async def test_signature_error(delivery_service, test_activity):
#     """Test handling of signature errors."""
#     recipients = ["https://remote.com/users/bob/inbox"]
    
#     delivery_service.signature_verifier.sign_request.side_effect = Exception("Signature error")
    
#     result = await delivery_service.deliver_activity(
#         activity=test_activity,
#         recipients=recipients
#     )
    
#     assert not result.success
#     assert sorted(result.failed) == sorted(recipients)
#     assert "Signature error" in str(result.error_message)
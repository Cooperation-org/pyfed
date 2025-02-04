import pytest
from unittest.mock import AsyncMock, patch
from pyfed.federation.resolver import ActivityPubResolver

@pytest.mark.asyncio
async def test_resolve_actor_success():
    resolver = ActivityPubResolver()
    actor_id = "https://example.com/actor"
    
    # Mock the HTTP response
    with patch('aiohttp.ClientSession.get', new_callable=AsyncMock) as mock_get:
        mock_get.return_value.__aenter__.return_value.status = 200
        mock_get.return_value.__aenter__.return_value.json.return_value = {
            "id": actor_id,
            "type": "Person",
            "name": "Test Actor"
        }
        
        actor_data = await resolver.resolve_actor(actor_id)
        print(actor_data)
        assert actor_data['id'] == actor_id
        assert actor_data['type'] == "Person"

@pytest.mark.asyncio
async def test_resolve_actor_not_found():
    resolver = ActivityPubResolver()
    actor_id = "https://example.com/unknown_actor"
    
    with patch('aiohttp.ClientSession.get', new_callable=AsyncMock) as mock_get:
        mock_get.return_value.__aenter__.return_value.status = 404
        
        actor_data = await resolver.resolve_actor(actor_id)
        assert actor_data is None
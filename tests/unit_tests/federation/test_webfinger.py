@pytest.mark.asyncio
async def test_webfinger_client_success():
    client = WebFingerClient()
    account = "user@example.com"
    
    with patch('aiohttp.ClientSession.get', new_callable=AsyncMock) as mock_get:
        mock_get.return_value.__aenter__.return_value.status = 200
        mock_get.return_value.__aenter__.return_value.json.return_value = {
            "subject": f"acct:{account}",
            "aliases": ["https://example.com/user"],
            "links": [{"rel": "self", "href": "https://example.com/user"}]
        }
        
        result = await client.get_actor_url(account)
        assert result == "https://example.com/user"
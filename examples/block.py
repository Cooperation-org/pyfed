"""
Example of blocking a Mastodon user using ActivityPub.
"""

import asyncio
import logging
from pathlib import Path
import sys
from config import CONFIG
from datetime import datetime

# Add src directory to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from pyfed.models import APPerson, APBlock
from pyfed.federation.delivery import ActivityDelivery
from pyfed.federation.discovery import InstanceDiscovery
from pyfed.security.key_management import KeyManager

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def block_user(resource="acct:kene29@mastodon.social"):
    # Initialize components with config
    key_manager = KeyManager(
        domain=CONFIG["domain"],
        keys_path=CONFIG["keys_path"],
        rotation_config=False
    )
    await key_manager.initialize()
    
    discovery = InstanceDiscovery()
    await discovery.initialize()
    
    delivery = ActivityDelivery(key_manager=key_manager, discovery=discovery)
    
    try:
        # 1. First, perform WebFinger lookup to get the actor's URL
        logger.info("Performing WebFinger lookup...")
        webfinger_result = await discovery.webfinger(
            resource=resource  # Replace with target username
        )
        logger.info(f"WebFinger result: {webfinger_result}")
        
        if not webfinger_result:
            raise Exception("Could not find user through WebFinger")
            
        # Find ActivityPub actor URL from WebFinger result
        actor_url = None
        for link in webfinger_result.get('links', []):
            if link.get('rel') == 'self' and link.get('type') == 'application/activity+json':
                actor_url = link.get('href')
                break
                
        if not actor_url:
            raise Exception("Could not find ActivityPub actor URL")
            
        # 2. Fetch the actor's profile to get their inbox URL
        logger.info(f"Fetching actor profile from {actor_url}")
        async with discovery.session.get(actor_url) as response:
            if response.status != 200:
                raise Exception(f"Failed to fetch actor profile: {response.status}")
            actor_data = await response.json()
            
        # Get the inbox URL from the actor's profile
        inbox_url = actor_data.get('inbox')
        if not inbox_url:
            raise Exception("Could not find actor's inbox URL")
        
        logger.info(f"Found actor's inbox: {inbox_url}")
            
        # 3. Create our actor
        actor = APPerson(
            id=f"https://12f8-197-211-61-33.ngrok-free.app/users/testuser",
            name="Alice",
            preferred_username="alice",
            inbox=f"https://12f8-197-211-61-33.ngrok-free.app/users/testuser/inbox",
            outbox=f"https://12f8-197-211-61-33.ngrok-free.app/users/testuser/outbox",
            followers=f"https://12f8-197-211-61-33.ngrok-free.app/users/testuser/followers"
        )

        # 4. Create Block activity
        block = APBlock(
            id=f"https://{CONFIG['domain']}/activities/{int(asyncio.get_event_loop().time() * 1000)}",
            actor=str(actor.id),
            object=actor_url,  # The user we want to block
            published=datetime.utcnow().isoformat() + "Z",
            to=[actor_url]  # Send only to the blocked user
        )
        
        # 5. Deliver the Block activity
        logger.info("Sending Block activity...")
        result = await delivery.deliver_to_inbox(
            activity=block.serialize(),
            inbox_url=inbox_url,
            username=CONFIG["user"]
        )
        logger.info(f"Delivery result: {result}")
        
        if result.success:
            logger.info("Block activity sent successfully!")
            logger.info(f"Successfully delivered to: {result.success}")
        else:
            logger.error("Block activity failed!")
            if result.failed:
                logger.error(f"Failed recipients: {result.failed}")
            if result.error_message:
                logger.error(f"Error: {result.error_message}")
            
    except Exception as e:
        logger.error(f"Error: {e}")
        raise
        
    finally:
        # Clean up
        await discovery.close()
        await delivery.close()

if __name__ == "__main__":
    asyncio.run(block_user())

"""
Example of sending a message to Mastodon following ActivityPub spec.
"""

import asyncio
import logging
from pathlib import Path
import sys
from config import CONFIG
from datetime import datetime, timezone

# Add src directory to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from pyfed.models import APPerson, APNote, APCreate
from pyfed.federation.delivery import ActivityDelivery
from pyfed.federation.discovery import InstanceDiscovery
from pyfed.security.key_management import KeyManager

logging.basicConfig(level=logging.DEBUG)  # Set to DEBUG for more detailed logs
logger = logging.getLogger(__name__)

async def send_activity_to_mastodon(
    resource="acct:kene29@mastodon.social",
    message="Hello @gvelez17@mas.to! This is a test note to test mention to Golda"
    ):
    # Initialize components with config
    key_manager = KeyManager(
        domain=CONFIG["domain"],
        keys_path=CONFIG["keys_path"],
        rotation_config=False
    )
    await key_manager.initialize()
    
    # Force generate a new key with proper format
    # await key_manager.rotate_keys() 
    
    active_key = await key_manager.get_active_key()
    logger.debug(f"Using active key ID: {active_key.key_id}")
    logger.debug(f"Key document URL: https://{CONFIG['domain']}/keys/{active_key.key_id.split('/')[-1]}")
    
    discovery = InstanceDiscovery()
    await discovery.initialize()
    
    delivery = ActivityDelivery(key_manager=key_manager, discovery=discovery)
   
    try:
        # 1. First, perform WebFinger lookup to get the actor's URL
        logger.info("Performing WebFinger lookup...")
        webfinger_result = await discovery.webfinger(
            resource=resource
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
            
        # 3. Create the Activity with ngrok domain
        note_id = f"https://{CONFIG['domain']}/notes/{int(asyncio.get_event_loop().time() * 1000)}"

        # Create actor
        actor = APPerson(
            id=f"https://{CONFIG['domain']}/users/{CONFIG['user']}",
            name="Alice",
            preferred_username="alice",
            inbox="https://example.com/users/alice/inbox",
            outbox="https://example.com/users/alice/outbox",
            followers="https://example.com/users/alice/followers"
        )

        # Create note with string attributed_to
        note = APNote(
            id=note_id,
            content=message,
            attributed_to=str(actor.id),  # Convert URL to string
            to=[inbox_url],
            cc=["https://www.w3.org/ns/activitystreams#Public"],
            published=datetime.utcnow().isoformat() + "Z",
            url=str(note_id),
            tag=[{
                    "type": "Mention",
                    "href": actor_url,
                    "name": "@gvelez17@mas.to"
                }]
        )

        # Create activity
        create_activity = APCreate(
            id=f"https://example.com/activities/{datetime.now(timezone.utc).timestamp()}",
            actor=str(actor.id),  # Convert URL to string
            object=note,
            to=note.to,
            cc=note.cc,
            published=datetime.utcnow().isoformat() + "Z",
        )
        
        # 4. Deliver the activity
        logger.info("Delivering activity...")
        result = await delivery.deliver_to_inbox(
            activity=create_activity.serialize(),
            inbox_url=inbox_url,
            username=CONFIG["user"]
        )
        logger.info(f"Delivery result: {result}")
        
        if result.success:
            logger.info("Activity delivered successfully!")
            logger.info(f"Successfully delivered to: {result.success}")
        else:
            logger.error("Activity delivery failed!")
            if result.failed:
                logger.error(f"Failed recipients: {result.failed}")
            if result.error_message:
                logger.error(f"Error: {result.error_message}")
            
    except Exception as e:
        logger.error(f"Error: {e}")
        
    finally:
        # Clean up
        await discovery.close()
        await delivery.close()

if __name__ == "__main__":
    asyncio.run(send_activity_to_mastodon())
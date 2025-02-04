"""
Minimal ActivityPub server example using PyFed.
"""

import asyncio
import logging
import json
from aiohttp import web
from datetime import datetime
from cryptography.hazmat.primitives import serialization
from pathlib import Path
import sys

from config import CONFIG

# Add src directory to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from pyfed.security.key_management import KeyManager, KeyRotation
from pyfed.security.http_signatures import HTTPSignatureVerifier
from pyfed.models import APPerson, APAccept, APReject
from pyfed.federation.delivery import ActivityDelivery
from pyfed.federation.discovery import InstanceDiscovery
from pyfed.serializers import ActivityPubSerializer

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize components
key_manager = None
delivery = None
discovery = None
signature_verifier = None

async def verify_signature(request):
    """Verify HTTP signature of incoming request."""
    try:
        signature_header = request.headers.get('Signature')
        if not signature_header:
            raise web.HTTPUnauthorized(reason="No signature header found")
            
        # Get the raw body for signature verification
        body = await request.read()
        
        # Verify the signature
        result = await signature_verifier.verify_request(
            method=request.method,
            path=str(request.url),
            headers=dict(request.headers),
            # body=body
        )
        
        if not result.is_valid:
            raise web.HTTPUnauthorized(reason=f"Invalid signature: {result.error}")
            
        return result
            
    except Exception as e:
        logger.error(f"Signature verification failed: {e}")
        raise web.HTTPUnauthorized(reason=str(e))

async def handle_activity(activity_data):
    """Process incoming ActivityPub activity."""
    try:
        activity_type = activity_data.get('type')
        actor = activity_data.get('actor')
        
        logger.info(f"Received {activity_type} activity from {actor}")
        
        if activity_type == 'Follow':
            # Auto-accept all follow requests in this example
            accept = APAccept(
                id=f"https://{CONFIG['domain']}/activities/{int(asyncio.get_event_loop().time() * 1000)}",
                actor=f"https://{CONFIG['domain']}/users/{CONFIG['user']}",
                object=activity_data,
                to=[actor]
            )
            
            # Get actor's inbox
            actor_data = await discovery.get_actor(actor)
            inbox_url = actor_data.get('inbox')
            
            if not inbox_url:
                raise Exception("Could not find actor's inbox")
                
            # Send Accept activity
            result = await delivery.deliver_to_inbox(
                activity=accept.serialize(),
                inbox_url=inbox_url,
                username="testuser"
            )
            
            if not result.success:
                logger.error(f"Failed to deliver Accept: {result.error_message}")
                
        elif activity_type == 'Like':
            # Process Like activity
            logger.info(f"Received Like on object: {activity_data.get('object')}")
            
        elif activity_type == 'Announce':
            # Process Announce (boost) activity
            logger.info(f"Received Announce of object: {activity_data.get('object')}")
            
        elif activity_type == 'Block':
            # Process Block activity
            logger.info(f"Received Block from actor: {actor}")
            
        else:
            logger.warning(f"Unhandled activity type: {activity_type}")
            
    except Exception as e:
        logger.error(f"Error handling activity: {e}")
        raise

async def inbox_handler(request):
    """Handle incoming ActivityPub activities."""
    try:
        username = request.match_info['username']
        body = await request.json()
        
        # Convert headers to dict and make case-insensitive
        headers = {k.lower(): v for k, v in request.headers.items()}
        
        # Verify HTTP signature
        verifier = HTTPSignatureVerifier(key_manager=key_manager)
        if not await verifier.verify_request(
            headers=headers,
            method=request.method,
            path=request.path,
            body=body
        ):
            return web.Response(
                status=401,
                text=json.dumps({"error": "Invalid signature"}),
                content_type='application/json'
            )

        logger.info(f"Received activity: {body}")
        
        # Process the activity
        await handle_activity(body)
        
        return web.Response(status=202)  # Accepted
        
    except web.HTTPException as e:
        raise
    except Exception as e:
        logger.error(f"Error in inbox handler: {e}")
        return web.Response(
            status=500,
            text=json.dumps({"error": str(e)}),
            content_type='application/json'
        )

async def actor_handler(request):
    """Return actor information."""
    try:
        username = request.match_info['username']
        if username != CONFIG['user']:
            raise web.HTTPNotFound(reason=f"User {username} not found")
            
        # Get active key for public key info
        active_key = await key_manager.get_active_key()
        
        response = {
            "@context": ["https://www.w3.org/ns/activitystreams", "https://w3id.org/security/v1"],
            "type": "Person",
            "id": f"https://{CONFIG['domain']}/users/{username}",
            "preferredUsername": username,
            "inbox": f"https://{CONFIG['domain']}/users/{username}/inbox",
            "outbox": f"https://{CONFIG['domain']}/users/{username}/outbox",
            "followers": f"https://{CONFIG['domain']}/users/{username}/followers",
            "publicKey": {
                "id": active_key.key_id,
                "owner": f"https://{CONFIG['domain']}/users/{username}",
                "publicKeyPem": await key_manager.get_public_key_pem(username)
            }
        }
        
        return web.Response(
            text=json.dumps(response),
            content_type='application/activity+json'
        )
        
    except Exception as e:
        logger.error(f"Error in actor handler: {e}")
        raise web.HTTPInternalServerError(reason=str(e))

async def key_handler(request):
    """Handle requests for public keys."""
    try:
        key_id = request.match_info['key_id']
        logger.info(f"\n=== Received request for key: {key_id} ===")
        
        # Find the requested key from all active keys
        requested_key_url = f"https://{CONFIG['domain']}/keys/{key_id}"
        if requested_key_url not in key_manager.active_keys:
            logger.error(f"ERROR: No key found with ID {key_id}")
            raise web.HTTPNotFound(reason=f"Key {key_id} not found")
            
        key_pair = key_manager.active_keys[requested_key_url]
        public_key_pem = key_pair.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')
        
        # Return key document with proper JSON-LD context
        response = {
            "@context": [
                "https://www.w3.org/ns/activitystreams",
                "https://w3id.org/security/v1"
            ],
            "id": requested_key_url,
            "owner": f"https://{CONFIG['domain']}/users/{CONFIG['user']}",
            "publicKeyPem": public_key_pem
        }
        
        logger.info(f"Sending response: {response}")
        return web.Response(
            text=json.dumps(response),
            content_type='application/activity+json'
        )
        
    except Exception as e:
        logger.error(f"Error serving key: {str(e)}")
        raise

async def webfinger_handler(request):
    """Handle WebFinger requests."""
    resource = request.query.get('resource')
    if not resource or not resource.startswith('acct:'):
        raise web.HTTPBadRequest(reason="Invalid resource parameter")
        
    username = resource.split('@')[0].replace('acct:', '')
    if username != CONFIG['user']:
        raise web.HTTPNotFound(reason="User not found")
        
    response = {
        "subject": f"acct:{username}@{CONFIG['domain']}",
        "links": [
            {
                "rel": "self",
                "type": "application/activity+json",
                "href": f"https://{CONFIG['domain']}/users/{CONFIG['user']}"
            }
        ]
    }
    
    return web.Response(
        text=json.dumps(response),
        content_type='application/jrd+json'
    )

async def init_app():
    """Initialize the application and its dependencies."""
    global key_manager, delivery, discovery, signature_verifier
    
    try:
        # Initialize components with proper configuration
        key_manager = KeyManager(
            domain=CONFIG["domain"],
            keys_path=CONFIG["keys_path"],
            rotation_config=KeyRotation(
                rotation_interval=30,  # 30 days
                key_overlap=2,   # 2 days overlap
                key_size=2048    # RSA key size
            )
        )
        await key_manager.initialize()
        
        discovery = InstanceDiscovery()
        await discovery.initialize()
        
        delivery = ActivityDelivery(key_manager=key_manager, discovery=discovery)
        
        signature_verifier = HTTPSignatureVerifier(key_manager=key_manager)
        
        # Create application
        app = web.Application()
        
        # Add routes
        app.router.add_get('/.well-known/webfinger', webfinger_handler)
        app.router.add_get('/users/{username}', actor_handler)
        app.router.add_post('/users/{username}/inbox', inbox_handler)
        app.router.add_get('/keys/{key_id}', key_handler)
        
        return app
        
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        raise

if __name__ == '__main__':
    app = asyncio.get_event_loop().run_until_complete(init_app())
    web.run_app(app, host='0.0.0.0', port=8880)

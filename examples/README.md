# PyFed Mastodon Integration Demo

This guide demonstrates how to use PyFed to interact with Mastodon using the ActivityPub protocol. The example shows how to send a message (Note) to a Mastodon user using federation.

## Prerequisites

1. Python 3.9 or higher
2. Virtual environment (recommended)
3. ngrok installed (for local testing)
4. A Mastodon account to send messages to

## Installation

1. Clone the repository and set up the environment:

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

2. Set up ngrok for local testing:
```bash
# Start ngrok on port 8880
ngrok http 8880
```
Save the ngrok URL (e.g., "12f8-197-211-61-33.ngrok-free.app") for configuration.

## Configuration

1. Create a `config.py` file in the examples directory with your settings:

```python
CONFIG = {
    "domain": "12f8-197-211-61-33.ngrok-free.app",  # Your ngrok URL (without https://)
    "user": "testuser",
    "keys_path": "example_keys",
    "port": 8880
}
```

2. Create the keys directory:
```bash
mkdir example_keys
```

3. Start the key server:
```bash
python examples/minimal_server.py
```
The key server will handle key management and HTTP signatures automatically.

## Running the Example

1. Ensure both ngrok and the key server are running

2. Run the examples:
```bash
python examples/send_message.py
```
or
```bash
python examples/follow.py
```
or
```bash
python examples/like.py
```
or
```bash
python examples/announce.py
```
or 
```bash
python examples/block.py
```

3. Check the logs for the federation process:
   - WebFinger lookup
   - Actor discovery
   - Message delivery
   - HTTP signatures

## Troubleshooting

Common issues and solutions:

1. **Connection Issues**
   - Verify ngrok is running and URL is correct
   - Check if key server is running on port 8880
   - Ensure ngrok URL is properly set in config

2. **WebFinger Lookup Fails**
   - Verify the Mastodon username is correct
   - Check if the instance is online
   - Ensure proper network connectivity

3. **Delivery Errors**
   - Verify your ngrok URL is current (they expire)
   - Check key server logs for signature issues
   - Ensure Mastodon instance is reachable

## Understanding the Code

The example demonstrates several key PyFed features:

1. **Key Management**
   - Automatic key generation and management via key server
   - Handles HTTP signatures for federation

2. **Federation**
   - WebFinger protocol for user discovery
   - ActivityPub protocol for message delivery

3. **Activity Creation**
   - Creates ActivityPub Note objects
   - Wraps them in Create activities

## Next Steps

1. Try sending different types of activities
2. Implement inbox handling for responses
3. Add error handling and retries
4. Explore other ActivityPub interactions
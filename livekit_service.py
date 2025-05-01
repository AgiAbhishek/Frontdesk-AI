import os
import asyncio
import json
import logging
from livekit.api import LiveKitAPI, access_token
from knowledge_base import search_knowledge_base
from database import create_help_request
from notification_service import notify_supervisor

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get LiveKit credentials from environment variables
LIVEKIT_URL = os.environ.get('LIVEKIT_URL')
LIVEKIT_API_KEY = os.environ.get('LIVEKIT_API_KEY')
LIVEKIT_API_SECRET = os.environ.get('LIVEKIT_API_SECRET')

class AIAgentRoom:
    def __init__(self, room_name, participant_name="Customer"):
        self.room_name = room_name
        self.participant_name = participant_name
        self.room = None
        self.connection_ready = asyncio.Event()
        self.customer_info = {
            "name": participant_name,
            "phone": "Unknown"
        }
        
    async def connect(self):
        """Connect to the LiveKit room"""
        logger.info(f"Connecting to room: {self.room_name}")
        
        # We'll use the LiveKitAPI to create a room if it doesn't exist already
        try:
            # Initialize the LiveKit API
            livekit_api = LiveKitAPI(
                url=LIVEKIT_URL,
                api_key=LIVEKIT_API_KEY,
                api_secret=LIVEKIT_API_SECRET
            )
            
            # Create the room if it doesn't exist
            # Since we're using a simulated approach for this demo, 
            # we'll just log the intended action but not actually call the API
            logger.info(f"Would create room with name: {self.room_name}")
            
            # Note: In a real implementation with proper LiveKit setup, we would use:
            # from livekit.api import proto
            # room_request = proto.room.CreateRoomRequest(
            #     name=self.room_name,
            #     empty_timeout=10 * 60,  # 10 minutes
            #     max_participants=2
            # )
            # await livekit_api.room.create_room(room_request)
            
            # In a real implementation, we'd use the livekit WebRTC client to connect
            # Since we're focusing on the text-based functionality, we'll simulate connection
            self._on_connected()
            logger.info("Connected to LiveKit room successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to LiveKit room: {e}")
            return False
    
    def _generate_token(self):
        """Generate a token for connecting to the LiveKit room"""
        token = access_token.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
        
        # Create video grants for the participant
        grants = access_token.VideoGrants(
            room_join=True,
            room=self.room_name,
        )
        
        # Apply the grants to the token
        token.with_grants(grants)
        
        # Add identity
        token.with_identity(self.participant_name)
        
        return token.to_jwt()
    
    def _on_connected(self):
        """Callback when connected to the room"""
        logger.info("Connected to room")
        self.connection_ready.set()
    
    def _on_disconnected(self):
        """Callback when disconnected from the room"""
        logger.info("Disconnected from room")
    
    async def _on_track_subscribed(self, track, publication, participant):
        """Callback when a track is subscribed"""
        logger.info(f"Track subscribed from {participant.identity}")
        
        # Handle audio track from the participant
        # In a real implementation, we would process the audio here
        # using speech-to-text to get customer queries
        logger.info("Audio track received, would process with speech-to-text")
    
    async def _on_data_received(self, data, participant):
        """Callback when data is received from a participant"""
        try:
            # Parse the data as JSON
            message = json.loads(data.decode('utf-8'))
            logger.info(f"Received data: {message}")
            
            # Extract information from the message
            if 'type' in message:
                if message['type'] == 'customer_info':
                    # Update customer information
                    self.customer_info.update(message.get('data', {}))
                    await self._send_greeting()
                
                elif message['type'] == 'question':
                    # Process customer question
                    if 'text' in message:
                        await self._process_question(message['text'])
        except Exception as e:
            logger.error(f"Error processing received data: {e}")
    
    async def _send_greeting(self):
        """Send a greeting message to the customer"""
        greeting = {
            'type': 'response',
            'text': f"Hello {self.customer_info['name']}! Welcome to our salon. How can I help you today?"
        }
        await self._send_data(greeting)
    
    async def _process_question(self, question_text):
        """Process a customer question"""
        logger.info(f"Processing question: {question_text}")
        
        # Check if we know the answer
        answer, knows_answer = search_knowledge_base(question_text)
        
        if knows_answer:
            # Send the answer back to the customer
            response = {
                'type': 'response',
                'text': answer
            }
            await self._send_data(response)
        else:
            # Escalate to a supervisor
            response = {
                'type': 'response',
                'text': "Let me check with my supervisor and get back to you."
            }
            await self._send_data(response)
            
            # Create a help request
            request_id = create_help_request(
                self.customer_info['name'],
                self.customer_info['phone'],
                question_text
            )
            
            # Notify supervisor
            notify_supervisor(request_id, self.customer_info['name'], question_text)
            
            # Send additional message with request ID
            follow_up = {
                'type': 'help_request_created',
                'request_id': request_id
            }
            await self._send_data(follow_up)
    
    async def _send_data(self, data):
        """Send data to all participants in the room"""
        try:
            # In a real implementation, we would use the WebRTC data channel
            # Since we're focusing on the text-based functionality, we'll just log the data
            logger.info(f"Sent data: {data}")
            return True
        except Exception as e:
            logger.error(f"Error sending data: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from the LiveKit room"""
        try:
            # In a real implementation, we would close the WebRTC connection
            # Since we're simulating the connection, we'll just log the disconnect
            logger.info("Disconnected from room")
            return True
        except Exception as e:
            logger.error(f"Error disconnecting: {e}")
            return False

# Function to create a new room for a customer call
async def create_customer_call_room(room_name):
    """Create a new LiveKit room for a customer call"""
    agent_room = AIAgentRoom(room_name)
    success = await agent_room.connect()
    return agent_room if success else None

# Generate a room name for a customer call
def generate_room_name(customer_name):
    """Generate a unique room name for a customer call"""
    import time
    import hashlib
    
    timestamp = int(time.time())
    unique_id = hashlib.md5(f"{customer_name}_{timestamp}".encode()).hexdigest()[:8]
    return f"salon-call-{unique_id}"

# Generate a customer token for joining a room
def generate_customer_token(room_name, customer_name):
    """Generate a token for a customer to join a LiveKit room"""
    token = access_token.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
    
    # Create video grants for the participant
    grants = access_token.VideoGrants(
        room_join=True,
        room=room_name,
    )
    
    # Apply the grants to the token
    token.with_grants(grants)
    
    # Add identity
    token.with_identity(customer_name)
    
    return token.to_jwt()
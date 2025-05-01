import os
import asyncio
import json
import logging
from livekit import rtc, room, agents
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
        
        room_options = room.RoomOptions()
        self.room = room.Room(options=room_options)
        
        # Set up event listeners
        self.room.on("connected", self._on_connected)
        self.room.on("disconnected", self._on_disconnected)
        self.room.on("track_subscribed", self._on_track_subscribed)
        self.room.on("data_received", self._on_data_received)
        
        # Connect to the room
        try:
            await self.room.connect(LIVEKIT_URL, self._generate_token())
            await self.connection_ready.wait()
            logger.info("Connected to LiveKit room successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to LiveKit room: {e}")
            return False
    
    def _generate_token(self):
        """Generate a token for connecting to the LiveKit room"""
        from livekit.auth import AccessToken
        
        token = AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
        token.add_grant(room=self.room_name, room_join=True, room_admin=False)
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
        logger.info(f"Track subscribed: {track.kind} from {participant.identity}")
        
        # Handle audio track from the participant
        if track.kind == rtc.TrackKind.AUDIO:
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
        if self.room:
            try:
                json_data = json.dumps(data).encode('utf-8')
                await self.room.local_participant.publish_data(json_data, rtc.DataPacket.Kind.RELIABLE)
                logger.info(f"Sent data: {data}")
            except Exception as e:
                logger.error(f"Error sending data: {e}")
    
    async def disconnect(self):
        """Disconnect from the LiveKit room"""
        if self.room:
            await self.room.disconnect()
            logger.info("Disconnected from room")

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
    from livekit.auth import AccessToken
    
    token = AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
    token.add_grant(
        room=room_name,
        room_join=True,
        room_admin=False,
        identity=customer_name
    )
    return token.to_jwt()
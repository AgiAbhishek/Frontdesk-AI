import time
import datetime
from knowledge_base import search_knowledge_base
from database import create_help_request, get_db_connection
from notification_service import notify_supervisor

def simulate_call(question, customer_name, customer_phone):
    """
    Simulate a call from a customer to the AI agent
    
    Args:
        question: The customer's question
        customer_name: The customer's name
        customer_phone: The customer's phone number
        
    Returns:
        tuple: (response, request_id, knows_answer)
            - response: The AI's response
            - request_id: ID of help request if created, otherwise None
            - knows_answer: Boolean indicating if AI knew the answer
    """
    print(f"Call from {customer_name} ({customer_phone}): {question}")
    
    # Check if the AI knows the answer
    answer, knows_answer = search_knowledge_base(question)
    
    if knows_answer:
        # AI knows the answer
        response = f"Thank you for your question. {answer}"
        return response, None, True
    else:
        # AI doesn't know - escalate to human supervisor
        response = "Let me check with my supervisor and get back to you."
        
        # Create help request
        request_id = create_help_request(customer_name, customer_phone, question)
        
        # Notify supervisor (simulated)
        notify_supervisor(request_id, customer_name, question)
        
        return response, request_id, False

def handle_livekit_call():
    """
    LiveKit call handling implementation
    
    This function delegates to the livekit_service module which implements:
    1. Set up a WebRTC connection
    2. Handle audio/video streams
    3. Process audio through speech-to-text
    4. Generate AI responses
    5. Convert responses to speech
    
    For demonstration purposes, the implementation focuses on text-based messaging
    as a simpler way to show the help request flow.
    """
    import asyncio
    from livekit_service import create_customer_call_room, generate_room_name
    
    # Create a new call room
    async def start_call(customer_name="Customer"):
        room_name = generate_room_name(customer_name)
        room = await create_customer_call_room(room_name)
        if room:
            print(f"Started LiveKit call in room: {room_name}")
            return room, room_name
        else:
            print("Failed to create LiveKit call room")
            return None, None
    
    # This would be called when a call is received
    # For test purposes, we return values that could be used to join the room
    loop = asyncio.get_event_loop()
    if not loop.is_running():
        room, room_name = loop.run_until_complete(start_call())
        return room, room_name
    else:
        print("Event loop already running, cannot start call synchronously")
        return None, None

def follow_up_with_customer(request_id, response):
    """
    Follow up with the customer after receiving a supervisor response
    
    In a real implementation, this would send an SMS or make a call to the customer.
    For this simulation, we just log the follow-up.
    
    Args:
        request_id: The ID of the help request
        response: The supervisor's response
    """
    # Get customer info
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT customer_name, customer_phone, question FROM help_requests WHERE id = ?", (request_id,))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        customer_name = result['customer_name']
        customer_phone = result['customer_phone']
        question = result['question']
        
        # In a real system, this would send an SMS via Twilio or similar
        print(f"Sending SMS to {customer_phone}:")
        print(f"Hello {customer_name}, regarding your question about '{question}', {response}")
        
        return True
    else:
        print(f"Error: Could not find request with ID {request_id}")
        return False

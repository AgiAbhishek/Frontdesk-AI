def notify_supervisor(request_id, customer_name, question):
    """
    Simulate notifying a supervisor about a help request
    
    In a real implementation, this would send an SMS, email, or push notification
    to the supervisor. For this simulation, we just log the notification.
    
    Args:
        request_id: The ID of the help request
        customer_name: The customer's name
        question: The customer's question
    """
    # In a real system, this would use Twilio, email API, etc.
    print(f"[NOTIFICATION] Request #{request_id} from {customer_name}:")
    print(f"Hey, I need help answering '{question}'.")

def notify_customer(customer_phone, customer_name, response):
    """
    Simulate notifying a customer with a response
    
    In a real implementation, this would send an SMS or make a call to the customer.
    For this simulation, we just log the notification.
    
    Args:
        customer_phone: The customer's phone number
        customer_name: The customer's name
        response: The response to send to the customer
    """
    # In a real system, this would use Twilio or similar
    print(f"[SMS to {customer_phone}] Hello {customer_name}, {response}")

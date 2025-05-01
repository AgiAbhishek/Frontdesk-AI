import streamlit as st
import sqlite3
import datetime
import time
import os
from database import init_db, get_db_connection
from knowledge_base import get_knowledge_base
from ai_agent import simulate_call

# Set page config
st.set_page_config(
    page_title="Frontdesk AI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database if it doesn't exist
init_db()

# Main app title
st.title("Frontdesk AI Assistant")

# Sidebar with app navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Select a page:",
    ["Home", "Make a Call", "LiveKit Call", "View Requests", "Knowledge Base"]
)

# Knowledge base information for our fake salon
salon_info = get_knowledge_base()

if page == "Home":
    st.header("Welcome to Frontdesk AI Assistant")
    st.subheader("Human-in-the-Loop AI System")
    
    st.write("""
    This system simulates an AI receptionist for a salon business.
    When the AI doesn't know the answer, it escalates to a human supervisor,
    follows up with the customer, and updates its knowledge base automatically.
    
    **Features:**
    - AI Agent handles incoming calls
    - Escalates unknown queries to human supervisors
    - Tracks help requests and resolutions
    - Updates knowledge base with new information
    - Follows up with customers automatically
    - Real-time calls via LiveKit WebRTC integration
    
    **Try it out:**
    - Use the 'Make a Call' page to simulate a simple customer call
    - Try the 'LiveKit Call' page for real-time communication (WebRTC)
    - Check 'View Requests' to see and respond to pending help requests
    - Browse the 'Knowledge Base' to see what the AI has learned
    """)
    
    # Display some stats
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get count of pending requests
    cursor.execute("SELECT COUNT(*) FROM help_requests WHERE status = 'pending'")
    pending_count = cursor.fetchone()[0]
    
    # Get count of resolved requests
    cursor.execute("SELECT COUNT(*) FROM help_requests WHERE status = 'resolved'")
    resolved_count = cursor.fetchone()[0]
    
    # Get count of knowledge base items
    cursor.execute("SELECT COUNT(*) FROM knowledge_base")
    kb_count = cursor.fetchone()[0]
    
    conn.close()
    
    # Display metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Pending Requests", pending_count)
    with col2:
        st.metric("Resolved Requests", resolved_count)
    with col3:
        st.metric("Knowledge Base Items", kb_count)

elif page == "Make a Call":
    st.header("Simulate a Customer Call")
    
    st.write("""
    This page simulates a customer calling the AI receptionist.
    Enter your question, and the AI will either answer based on its knowledge base
    or create a help request if it doesn't know the answer.
    """)
    
    # Customer information
    customer_name = st.text_input("Your Name", "John Doe")
    customer_phone = st.text_input("Your Phone Number", "+1234567890")
    
    # Customer question
    question = st.text_input("Ask a question about the salon:", 
                          "What are your opening hours?")
    
    if st.button("Simulate Call"):
        with st.spinner("Processing call..."):
            # Simulate call processing time
            time.sleep(1)
            
            # Process the call
            response, request_id, knows_answer = simulate_call(question, customer_name, customer_phone)
            
            # Display the AI's response
            st.subheader("AI Response:")
            st.info(response)
            
            if not knows_answer:
                st.success("A help request has been created. The supervisor will respond soon.")
                st.write(f"Request ID: {request_id}")
                
                # Simulate the supervisor notification (in real-world, this would be a text/email)
                st.subheader("Behind the scenes:")
                st.code(f"Supervisor Notification: Hey, I need help answering '{question}' from {customer_name}.")

elif page == "View Requests":
    st.header("Help Requests")
    
    # Get help requests from database
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT id, customer_name, customer_phone, question, status, created_at, resolved_at
    FROM help_requests
    ORDER BY 
        CASE 
            WHEN status = 'pending' THEN 1
            WHEN status = 'resolved' THEN 2
            ELSE 3
        END,
        created_at DESC
    """)
    requests = cursor.fetchall()
    conn.close()
    
    # Filter options
    status_filter = st.selectbox("Filter by status:", ["All", "Pending", "Resolved", "Unresolved"])
    
    # Display requests
    if not requests:
        st.info("No help requests found in the system.")
    else:
        # Filter based on selection
        filtered_requests = []
        for req in requests:
            req_id, cust_name, cust_phone, question, status, created, resolved = req
            if status_filter == "All" or status_filter.lower() == status:
                filtered_requests.append(req)
        
        if not filtered_requests:
            st.info(f"No {status_filter.lower()} requests found.")
        else:
            for req in filtered_requests:
                req_id, cust_name, cust_phone, question, status, created, resolved = req
                
                # Create an expander for each request
                with st.expander(f"Request #{req_id} - {status.title()} - {created}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Customer:** {cust_name}")
                        st.write(f"**Phone:** {cust_phone}")
                        st.write(f"**Question:** {question}")
                        st.write(f"**Status:** {status.title()}")
                        st.write(f"**Created:** {created}")
                        if resolved:
                            st.write(f"**Resolved:** {resolved}")
                    
                    with col2:
                        if status == "pending":
                            # Show response form
                            st.write("**Provide Answer:**")
                            answer = st.text_area(f"Answer for request #{req_id}", key=f"answer_{req_id}")
                            if st.button("Submit Response", key=f"submit_{req_id}"):
                                if answer.strip():
                                    # Update the request status
                                    conn = get_db_connection()
                                    cursor = conn.cursor()
                                    
                                    # Update help_request
                                    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                    cursor.execute("""
                                    UPDATE help_requests
                                    SET status = 'resolved', response = ?, resolved_at = ?
                                    WHERE id = ?
                                    """, (answer, now, req_id))
                                    
                                    # Add to knowledge base
                                    cursor.execute("""
                                    INSERT INTO knowledge_base (question, answer, source, created_at)
                                    VALUES (?, ?, ?, ?)
                                    """, (question, answer, f"Help Request #{req_id}", now))
                                    
                                    conn.commit()
                                    conn.close()
                                    
                                    # Simulate sending a notification to the customer
                                    st.success(f"Response submitted! Customer will be notified.")
                                    st.code(f"SMS to {cust_phone}: Hello {cust_name}, regarding your question about '{question}', {answer}")
                                    
                                    # Refresh the page
                                    st.rerun()
                                else:
                                    st.error("Please provide an answer before submitting.")
                        
                        elif status == "resolved":
                            # Show the response
                            conn = get_db_connection()
                            cursor = conn.cursor()
                            cursor.execute("SELECT response FROM help_requests WHERE id = ?", (req_id,))
                            response = cursor.fetchone()[0]
                            conn.close()
                            
                            st.write("**Response:**")
                            st.info(response)

elif page == "LiveKit Call":
    st.header("Real-Time LiveKit Call")
    
    st.write("""
    This page demonstrates how to start a LiveKit call. In a production environment,
    this would connect to LiveKit's WebRTC service to provide real-time audio/video communication.
    
    The AI can then listen to the customer's questions in real-time, provide answers from its 
    knowledge base, or escalate to a human supervisor when needed.
    """)
    
    # Customer information
    customer_name = st.text_input("Your Name", "John Doe", key="lk_name")
    customer_phone = st.text_input("Your Phone Number", "+1234567890", key="lk_phone")
    
    # Start call button
    if st.button("Start LiveKit Call"):
        with st.spinner("Connecting to LiveKit..."):
            # Import here to avoid loading issues
            from ai_agent import handle_livekit_call
            
            # Start a LiveKit call
            try:
                room, room_name = handle_livekit_call()
                
                if room and room_name:
                    st.success("LiveKit call started successfully!")
                    
                    # Display room information
                    st.subheader("Call Information")
                    st.write(f"Room Name: {room_name}")
                    
                    # In a real app, we would display connection details or embed an iframe
                    # for the WebRTC interface. For this demo, we'll show a simulation.
                    
                    st.subheader("Simulated LiveKit Call Interface")
                    
                    # Create tabs for the interface
                    call_tab1, call_tab2 = st.tabs(["Customer View", "Behind the Scenes"])
                    
                    with call_tab1:
                        st.write("**Customer Call Interface**")
                        
                        # Simulate message exchange
                        st.chat_message("assistant").write("Hello! Welcome to our salon. How can I help you today?")
                        
                        # Customer question
                        question = st.text_input("Ask a question:", key="lk_question")
                        
                        if st.button("Send", key="lk_send"):
                            if question:
                                # Show customer message
                                st.chat_message("user").write(question)
                                
                                # Process with AI agent
                                from knowledge_base import search_knowledge_base
                                answer, knows_answer = search_knowledge_base(question)
                                
                                if knows_answer:
                                    # AI knows answer
                                    st.chat_message("assistant").write(answer)
                                else:
                                    # AI doesn't know
                                    st.chat_message("assistant").write("Let me check with my supervisor and get back to you.")
                                    
                                    # Create help request
                                    from database import create_help_request
                                    from notification_service import notify_supervisor
                                    
                                    request_id = create_help_request(customer_name, customer_phone, question)
                                    notify_supervisor(request_id, customer_name, question)
                                    
                                    st.success(f"Help request created (ID: {request_id})")
                    
                    with call_tab2:
                        st.write("**Behind the Scenes**")
                        st.write("In a real implementation, this would show:")
                        st.write("- WebRTC connection statistics")
                        st.write("- Audio processing (speech-to-text)")
                        st.write("- AI agent thought process")
                        st.write("- Knowledge base lookup results")
                        
                        # Show example logs
                        with st.expander("Connection Logs"):
                            st.code(f"""
[INFO] Connected to LiveKit room: {room_name}
[INFO] Using LiveKit server: {os.environ.get('LIVEKIT_URL', '[URL HIDDEN]')}
[INFO] Participant joined: {customer_name}
[INFO] Audio track received, processing with speech-to-text
[INFO] Real-time transcription active
                            """)
                else:
                    st.error("Failed to start LiveKit call. Please check the LiveKit credentials and try again.")
            except Exception as e:
                st.error(f"Error starting LiveKit call: {str(e)}")
                st.info("This could be due to missing or incorrect LiveKit credentials, or network connectivity issues.")

elif page == "Knowledge Base":
    st.header("AI Knowledge Base")
    
    # Get knowledge base items
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT question, answer, source, created_at FROM knowledge_base ORDER BY created_at DESC")
    kb_items = cursor.fetchall()
    conn.close()
    
    # Display items
    if not kb_items:
        st.info("No items in the knowledge base yet.")
    else:
        # Add search functionality
        search_term = st.text_input("Search the knowledge base:", "")
        
        displayed_items = []
        if search_term:
            for item in kb_items:
                question, answer, source, created = item
                if search_term.lower() in question.lower() or search_term.lower() in answer.lower():
                    displayed_items.append(item)
            
            if not displayed_items:
                st.info(f"No results found for '{search_term}'")
        else:
            displayed_items = kb_items
        
        # Display items
        for item in displayed_items:
            question, answer, source, created = item
            with st.expander(f"Q: {question}"):
                st.write(f"**Answer:** {answer}")
                st.write(f"**Source:** {source}")
                st.write(f"**Added:** {created}")

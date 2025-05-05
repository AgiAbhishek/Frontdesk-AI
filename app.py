import streamlit as st
import sqlite3
import datetime
import time
import os
from database import init_db, get_db_connection
from knowledge_base import get_knowledge_base, add_to_knowledge_base
from ai_agent import simulate_call

# Set page config - must be the first Streamlit command
st.set_page_config(
    page_title="Frontdesk AI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
custom_css = """
<style>
    /* Main container styling */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Card styling */
    .stcard {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    .stcard:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 15px rgba(0, 0, 0, 0.1);
    }
    
    /* Dashboard metrics styling */
    .metric-container {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #007BFF;
    }
    .metric-label {
        font-size: 1rem;
        color: #4b5563;
    }
    
    /* Navigation styling */
    .css-1d391kg {
        background-color: #1a2238;
    }
    .css-1lcbmhc {
        background-color: #1a2238;
    }
    
    /* Status badges */
    .status-badge {
        display: inline-block;
        padding: 5px 10px;
        border-radius: 15px;
        font-size: 0.8rem;
        font-weight: 500;
    }
    .status-pending {
        background-color: #FEF3C7;
        color: #92400E;
    }
    .status-resolved {
        background-color: #D1FAE5;
        color: #065F46;
    }
    .status-unresolved {
        background-color: #FEE2E2;
        color: #991B1B;
    }
    
    /* Header styling */
    h1 {
        color: #1a2238;
        font-weight: 700;
        margin-bottom: 1.5rem;
    }
    h2 {
        color: #1a2238;
        font-weight: 600;
        margin-top: 1.5rem;
    }
    h3 {
        color: #344054;
        font-weight: 600;
    }
    
    /* Button styling */
    .stButton button {
        border-radius: 6px;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    /* Input field styling */
    .stTextInput input, .stTextArea textarea {
        border-radius: 6px;
        border: 1px solid #e2e8f0;
    }
    
    /* Divider styling */
    hr {
        margin: 2rem 0;
        border-color: #e2e8f0;
    }
    
    /* Footer styling */
    .footer {
        margin-top: 40px;
        text-align: center;
        color: #6B7280;
        font-size: 0.875rem;
    }
    
    /* Chat bubble styling */
    .chat-bubble {
        display: flex;
        margin-bottom: 15px;
    }
    .chat-avatar {
        border-radius: 50%;
        width: 40px;
        height: 40px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 10px;
        flex-shrink: 0;
    }
    .chat-message {
        padding: 10px;
        border-radius: 10px;
        flex: 1;
    }
    .user-avatar {
        background-color: #e2e8f0;
    }
    .ai-avatar {
        background-color: #dbeafe;
    }
    .user-message {
        background-color: #f1f5f9;
    }
    .ai-message {
        background-color: #eff6ff;
    }
</style>
"""

# Inject custom CSS
st.markdown(custom_css, unsafe_allow_html=True)

# Initialize database if it doesn't exist
init_db()

# Sidebar with app navigation and branding
with st.sidebar:
    # Logo and app name
    st.markdown("""
    <div style="display: flex; align-items: center; margin-bottom: 20px;">
        <div style="background-color: #007BFF; width: 40px; height: 40px; border-radius: 10px; display: flex; justify-content: center; align-items: center; margin-right: 10px;">
            <span style="color: white; font-size: 24px;">🤖</span>
        </div>
        <div>
            <h2 style="margin: 0; color: #007BFF; font-size: 1.5rem;">Frontdesk AI</h2>
            <p style="margin: 0; color: #a0aec0; font-size: 0.8rem;">Human-in-the-Loop Assistant</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<hr style='margin: 0 0 20px 0; border-color: #2d3748;'>", unsafe_allow_html=True)
    
    # Navigation menu with icons
    st.sidebar.markdown("### Main Navigation")
    
    # Fix the radio button by adding a proper label and using key for uniqueness
    page_icons = {
        "Dashboard": "🏠",
        "Simulate Call": "📞",
        "LiveKit Call": "🔊",
        "Help Requests": "🔔",
        "Knowledge Base": "📚"
    }
    
    # Create proper navigation with better labeling
    selected_page = st.sidebar.radio(
        "Select Navigation",  # Added a proper label here
        list(page_icons.keys()),
        format_func=lambda x: f"{page_icons[x]} {x}",
        label_visibility="collapsed",  # Hide the label but keep it accessible
        key="main_navigation"  # Add a key for state management
    )
    
    # Map the navigation options to our original page names
    page_mapping = {
        "Dashboard": "Home",
        "Simulate Call": "Make a Call",
        "LiveKit Call": "LiveKit Call",
        "Help Requests": "View Requests",
        "Knowledge Base": "Knowledge Base"
    }
    
    # Convert the selected option to our original page name
    page = page_mapping[selected_page]
    
    # Add some space to ensure footer doesn't overlap
    st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True)
    
    # Footer in sidebar - now with position fixed at the bottom with padding
    st.sidebar.markdown("""
    <div style="position: fixed; bottom: 0; left: 0; right: 0; background-color: #1a2238; padding: 10px; text-align: center;">
        <p style="margin: 0; color: #a0aec0; font-size: 0.8rem;">Frontdesk AI Assistant v1.0</p>
        <p style="margin: 0; padding-bottom: 5px; color: #a0aec0; font-size: 0.7rem;">© 2025 Frontdesk Engineering</p>
    </div>
    """, unsafe_allow_html=True)

# Knowledge base information for our fake salon
salon_info = get_knowledge_base()

if page == "Home":
    # Main title with animation
    st.markdown("""
    <h1 style="text-align: center; animation: fadeIn 1s ease-out;">
        <span style="color: #007BFF;">Frontdesk AI</span> Dashboard
    </h1>
    <p style="text-align: center; font-size: 1.2rem; color: #4b5563; margin-bottom: 40px;">
        Human-in-the-Loop AI System for Salon Business
    </p>
    <style>
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(-10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        @keyframes slideIn {
            from { opacity: 0; transform: translateX(-20px); }
            to { opacity: 1; transform: translateX(0); }
        }
        .animated {
            animation: slideIn 0.6s ease-out;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Display stats in nice metric cards
    from database import execute_db_operation
    
    @execute_db_operation
    def get_dashboard_metrics():
        conn = get_db_connection()
        try:
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
            
            # Get today's requests
            cursor.execute("SELECT COUNT(*) FROM help_requests WHERE date(created_at) = date('now')")
            today_count = cursor.fetchone()[0]
            
            return {
                'pending': pending_count,
                'resolved': resolved_count,
                'kb_items': kb_count,
                'today': today_count
            }
        except Exception as e:
            print(f"Error fetching dashboard metrics: {e}")
            return {'pending': 0, 'resolved': 0, 'kb_items': 0, 'today': 0}
        finally:
            conn.close()
    
    metrics = get_dashboard_metrics()
    
    # Display metrics in stylish cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-container" style="border-left: 5px solid #007BFF;">
            <div class="metric-value">{metrics['pending']}</div>
            <div class="metric-label">Pending Requests</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-container" style="border-left: 5px solid #2cb67d;">
            <div class="metric-value">{metrics['resolved']}</div>
            <div class="metric-label">Resolved Requests</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-container" style="border-left: 5px solid #ff6b6b;">
            <div class="metric-value">{metrics['today']}</div>
            <div class="metric-label">Today's Requests</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col4:
        st.markdown(f"""
        <div class="metric-container" style="border-left: 5px solid #f9c74f;">
            <div class="metric-value">{metrics['kb_items']}</div>
            <div class="metric-label">Knowledge Base Items</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Main feature cards
    st.markdown("<h2 class='animated' style='margin-top: 40px;'>Main Features</h2>", unsafe_allow_html=True)
    
    # First row of cards
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="stcard">
            <h3 style="color: #007BFF; margin-top: 0;">🎯 AI-Powered Reception</h3>
            <p>Our AI agent handles customer inquiries automatically, responding to known questions instantly from its knowledge base.</p>
            <p>When the AI doesn't know an answer, it creates a help request and gracefully escalates to a human supervisor.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="stcard">
            <h3 style="color: #2cb67d; margin-top: 0;">🔄 Human-in-the-Loop</h3>
            <p>Supervisors review and respond to questions the AI couldn't answer, ensuring every customer gets accurate information.</p>
            <p>All supervisor responses are automatically added to the knowledge base, making the AI smarter over time.</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Second row of cards
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="stcard">
            <h3 style="color: #ff6b6b; margin-top: 0;">📱 Real-Time Communication</h3>
            <p>Customers can interact with the AI through phone calls, LiveKit WebRTC integration, or text messaging.</p>
            <p>The system processes questions in real-time and provides immediate responses or escalation as needed.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="stcard">
            <h3 style="color: #f9c74f; margin-top: 0;">📊 Knowledge Management</h3>
            <p>The system maintains an expanding knowledge base that grows with each customer interaction.</p>
            <p>Supervisors can manually add or edit knowledge entries to proactively prepare for common questions.</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Quick actions section
    st.markdown("<h2 class='animated' style='margin-top: 30px;'>Quick Actions</h2>", unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📞 Simulate Call", use_container_width=True):
            st.switch_page("app.py")  # This will refresh with the new page selection
            page = "Make a Call"
    
    with col2:
        if st.button("📱 Start LiveKit Call", use_container_width=True):
            st.switch_page("app.py")
            page = "LiveKit Call"
    
    with col3:
        if st.button("🔔 View Pending Requests", use_container_width=True):
            st.switch_page("app.py")
            page = "View Requests"
    
    with col4:
        if st.button("📚 Browse Knowledge Base", use_container_width=True):
            st.switch_page("app.py")
            page = "Knowledge Base"
    
    # Recent activity 
    st.markdown("<h2 class='animated' style='margin-top: 30px;'>Recent Activity</h2>", unsafe_allow_html=True)
    
    @execute_db_operation
    def get_recent_activity(limit=5):
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT 'request' as type, id, customer_name, question, status, created_at 
            FROM help_requests
            UNION ALL
            SELECT 'knowledge' as type, id, 'System' as customer_name, question, 'added' as status, created_at
            FROM knowledge_base
            ORDER BY created_at DESC
            LIMIT ?
            """, (limit,))
            return cursor.fetchall()
        except Exception as e:
            print(f"Error fetching recent activity: {e}")
            return []
        finally:
            conn.close()
    
    activity = get_recent_activity(5)
    
    if activity:
        # Create an activity timeline
        st.markdown("""
        <div style="border-left: 2px solid #e2e8f0; margin-left: 10px; padding-left: 20px;">
        """, unsafe_allow_html=True)
        
        for item in activity:
            item_type, item_id, name, question, status, created_at = item
            
            if item_type == 'request':
                icon = "🔔" if status == "pending" else "✅"
                status_class = "status-pending" if status == "pending" else "status-resolved"
                action = "created" if status == "pending" else "resolved"
                
                st.markdown(f"""
                <div style="margin-bottom: 15px; position: relative;">
                    <div style="position: absolute; left: -31px; background-color: white; border-radius: 50%; width: 20px; height: 20px; text-align: center; border: 2px solid #e2e8f0;">
                        {icon}
                    </div>
                    <p style="margin: 0; color: #4b5563; font-size: 0.8rem;">{created_at}</p>
                    <p style="margin: 0; font-weight: 500;">Help request {action}</p>
                    <p style="margin: 0;">"{question}" from {name}</p>
                    <span class="status-badge {status_class}">{status}</span>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="margin-bottom: 15px; position: relative;">
                    <div style="position: absolute; left: -31px; background-color: white; border-radius: 50%; width: 20px; height: 20px; text-align: center; border: 2px solid #e2e8f0;">
                        📚
                    </div>
                    <p style="margin: 0; color: #4b5563; font-size: 0.8rem;">{created_at}</p>
                    <p style="margin: 0; font-weight: 500;">Knowledge base updated</p>
                    <p style="margin: 0;">Added: "{question}"</p>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("No recent activity found.")
    
    # Footer with helpful information
    st.markdown("""
    <div class="footer">
        <hr style="margin: 30px 0 20px 0;">
        <p>This AI system continuously learns from supervisor responses to improve customer service.</p>
        <p>For assistance with the dashboard, contact system administrator.</p>
    </div>
    """, unsafe_allow_html=True)

elif page == "Make a Call":
    # Page header with animation
    st.markdown("""
    <h1 style="animation: fadeIn 1s ease-out;">
        <span style="color: #007BFF;">Simulate</span> Customer Call
    </h1>
    <p style="font-size: 1.1rem; color: #4b5563; margin-bottom: 30px;">
        Test the AI receptionist by simulating a customer phone call
    </p>
    """, unsafe_allow_html=True)
    
    # Layout with two columns
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # How it works card
        st.markdown("""
        <div class="stcard">
            <h3 style="color: #007BFF; margin-top: 0;">📞 How It Works</h3>
            <ol>
                <li><strong>Enter your information</strong> and question in the form</li>
                <li><strong>Click "Make Call"</strong> to simulate a phone call to the AI receptionist</li>
                <li>The AI will <strong>check its knowledge base</strong> for an answer</li>
                <li>If the answer is known, it will <strong>respond immediately</strong></li>
                <li>If unknown, it will <strong>create a help request</strong> for a human supervisor</li>
                <li>When a supervisor responds, you'll receive a <strong>follow-up notification</strong></li>
            </ol>
            <p>The AI system gets smarter with each question as supervisors add new knowledge.</p>
        </div>
        
        <div class="stcard">
            <h3 style="color: #2cb67d; margin-top: 0;">📚 Sample Questions</h3>
            <p>Try asking these questions to test the system:</p>
            <ul>
                <li>What are your business hours?</li>
                <li>Do you offer hair coloring services?</li>
                <li>How much does a haircut cost?</li>
                <li>Is Jane working tomorrow?</li>
                <li>Do I need an appointment?</li>
            </ul>
            <p><em>Tip: Ask some questions not in the knowledge base to test the escalation process.</em></p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # Call simulator card
        st.markdown("""
        <div class="stcard">
            <h3 style="color: #007BFF; text-align: center; margin-top: 0;">📱 Call Simulator</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Form for call simulation
        with st.form("call_form"):
            # Customer information
            customer_name = st.text_input("Your Name", "John Doe")
            customer_phone = st.text_input("Your Phone Number", "+1234567890")
            
            # Customer question with larger input
            question = st.text_area("Your Question", 
                                  "What are your opening hours?",
                                  height=100)
            
            # Submit button styled as call button
            call_button = st.form_submit_button("📞 Make Call")
        
        if call_button:
            # Progress animation
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Simulate call progress
            status_text.text("Connecting call...")
            for i in range(101):
                progress_bar.progress(i)
                time.sleep(0.01)
                if i == 30:
                    status_text.text("Processing your question...")
                elif i == 70:
                    status_text.text("Generating response...")
            status_text.empty()
            
            # Process the call
            response, request_id, knows_answer = simulate_call(question, customer_name, customer_phone)
            
            # Display the response in a styled card
            st.markdown("""
            <div class="stcard" style="border-left: 4px solid #007BFF; margin-top: 20px;">
                <h3 style="color: #007BFF; margin-top: 0;">AI Response:</h3>
            """, unsafe_allow_html=True)
            
            st.info(response)
            
            if not knows_answer:
                st.markdown("""
                <div style="background-color: #d1fae5; padding: 10px; border-radius: 5px; margin-top: 10px;">
                    <p style="margin: 0; color: #065f46; font-weight: 500;">
                        ✅ A help request has been created and sent to a supervisor
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                st.write(f"**Request ID:** {request_id}")
                
                # Simulate the supervisor notification with better styling
                st.markdown(f"""
                <div style="background-color: #f8fafc; padding: 15px; border-radius: 5px; margin-top: 15px; border-left: 3px solid #94a3b8;">
                    <p style="margin: 0; color: #475569; font-size: 0.9rem; font-weight: 500;">Behind the scenes:</p>
                    <p style="margin: 0; font-family: monospace; color: #334155; background-color: #f1f5f9; padding: 8px; border-radius: 4px; margin-top: 5px;">
                        Supervisor Notification: Hey, I need help answering '{question}' from {customer_name}.
                    </p>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Show a "Make another call" button
            if st.button("📞 Make Another Call"):
                st.rerun()

elif page == "LiveKit Call":
    # Page header with animation
    st.markdown("""
    <h1 style="animation: fadeIn 1s ease-out;">
        <span style="color: #007BFF;">LiveKit</span> WebRTC Call
    </h1>
    <p style="font-size: 1.1rem; color: #4b5563; margin-bottom: 30px;">
        Start a real-time call with the AI receptionist using LiveKit WebRTC
    </p>
    """, unsafe_allow_html=True)
    
    # Check if we have LiveKit credentials
    # Explicitly set to True to force the app into LiveKit mode
    has_livekit_creds = True
    
    if not has_livekit_creds:
        # No credentials, show setup instructions
        st.warning("LiveKit credentials not found. This is demo mode.")
        
        st.markdown("""
        <div class="stcard">
            <h3 style="color: #007BFF; margin-top: 0;">🔧 Setup Instructions</h3>
            <p>To enable real LiveKit functionality, you need to set up LiveKit credentials in your environment:</p>
            <ol>
                <li>Create a LiveKit account at <a href="https://livekit.io" target="_blank">livekit.io</a></li>
                <li>Create a new project and generate API keys</li>
                <li>Add the following environment variables to your .env file:
                    <ul>
                        <li>LIVEKIT_URL - Your LiveKit server URL</li>
                        <li>LIVEKIT_API_KEY - Your API key</li>
                        <li>LIVEKIT_API_SECRET - Your API secret</li>
                    </ul>
                </li>
                <li>Restart the application</li>
            </ol>
            <p>In demo mode, the system will simulate LiveKit functionality.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Demo mode with simulated call
        st.markdown("""
        <div class="stcard">
            <h3 style="color: #007BFF; margin-top: 0;">📱 Demo Mode Call</h3>
            <p>Start a simulated LiveKit call in demo mode:</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            customer_name = st.text_input("Your Name", "John Doe")
        
        # Store conversation state
        if 'demo_call_active' not in st.session_state:
            st.session_state.demo_call_active = False
            
        if 'conversation' not in st.session_state:
            st.session_state.conversation = []
        
        # Start/End call buttons
        if not st.session_state.demo_call_active:
            if st.button("📞 Start Demo Call", use_container_width=True):
                st.session_state.demo_call_active = True
                st.session_state.room_id = f"demo-{int(time.time())}"
                
                # Start with a greeting
                st.session_state.conversation = [
                    {"role": "ai", "content": f"Hello {customer_name}, welcome to our salon! How can I help you today?"}
                ]
                st.rerun()
        else:
            # Generate a simulated room
            room_id = st.session_state.room_id
            
            # Show call interface
            st.markdown(f"""
            <div class="stcard" style="text-align: center;">
                <h3 style="color: #007BFF; margin-top: 0;">Simulated Call Active</h3>
                <p style="color: #4b5563;">Room ID: {room_id}</p>
                <div style="background-color: #f0f9ff; border-radius: 10px; padding: 20px; margin-top: 20px;">
                    <p style="font-weight: 500; color: #0369a1;">Demo Mode - No actual WebRTC connection</p>
                    <p>In a real implementation, this would show:</p>
                    <ul style="text-align: left; margin: 10px 0; list-style-type: none; padding-left: 0;">
                        <li>✅ Video feed</li>
                        <li>✅ Audio controls</li>
                        <li>✅ Real-time transcription</li>
                        <li>✅ AI responses</li>
                    </ul>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Conversation area
            st.markdown("""
            <div class="stcard">
                <h3 style="color: #007BFF; margin-top: 0;">Conversation</h3>
            </div>
            """, unsafe_allow_html=True)
            
            # Display conversation using Streamlit components instead of raw HTML
            for message in st.session_state.conversation:
                role = message["role"]
                content = message["content"]
                
                if role == "user":
                    with st.container():
                        cols = st.columns([1, 12])
                        with cols[0]:
                            st.markdown("👤")
                        with cols[1]:
                            st.info(content)
                else:
                    with st.container():
                        cols = st.columns([1, 12])
                        with cols[0]:
                            st.markdown("🤖")
                        with cols[1]:
                            st.success(content)
            
            # User input for conversation
            user_question = st.text_input("Type your question here:", key="demo_question")
            
            if st.button("Send", key="demo_send"):
                if user_question.strip():
                    # Add user message to conversation
                    st.session_state.conversation.append({"role": "user", "content": user_question})
                    
                    # Generate AI response based on predefined knowledge
                    # Simple response logic for demo
                    response = ""
                    question_lower = user_question.lower()
                    
                    if "hour" in question_lower or "open" in question_lower or "time" in question_lower:
                        response = "Our salon is open Monday to Friday from 9am to 7pm, and Saturdays from 10am to 6pm. We're closed on Sundays."
                    elif "price" in question_lower or "cost" in question_lower or "haircut" in question_lower:
                        response = "Our haircuts start at $45 for a basic cut, and go up to $75 for a cut and style with our senior stylists. Would you like to schedule an appointment?"
                    elif "color" in question_lower or "dye" in question_lower:
                        response = "Yes, we offer a full range of hair coloring services! Basic color starts at $85, while balayage or ombre treatments start at $150."
                    elif "appointment" in question_lower or "book" in question_lower or "schedule" in question_lower:
                        response = "Yes, appointments are recommended. Would you like me to help you book one now?"
                    elif "name" in question_lower:
                        response = "My name is Frontdesk AI Assistant. I'm here to help with any questions about our salon services."
                    else:
                        response = "I'm not sure I understand your question. Could you please rephrase it or ask about our salon services, hours, or pricing?"
                    
                    # Add AI response to conversation
                    st.session_state.conversation.append({"role": "ai", "content": response})
                    
                    # Clear the input field by rerunning
                    st.rerun()
                else:
                    st.warning("Please enter a question first.")
            
            # End call button
            if st.button("📞 End Call", use_container_width=True):
                st.session_state.demo_call_active = False
                st.rerun()
    else:
        # We have credentials, offer real LiveKit call
        from livekit_service import generate_room_name, generate_customer_token
        
        st.markdown("""
        <div class="stcard">
            <h3 style="color: #007BFF; margin-top: 0;">📱 Start a LiveKit Call</h3>
            <p>Connect to the AI receptionist using LiveKit's WebRTC capabilities:</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Store conversation state for real LiveKit calls as well
        if 'livekit_call_active' not in st.session_state:
            st.session_state.livekit_call_active = False
            
        if 'livekit_conversation' not in st.session_state:
            st.session_state.livekit_conversation = []
        
        if not st.session_state.livekit_call_active:
            col1, col2 = st.columns([1, 1])
            
            with col1:
                customer_name = st.text_input("Your Name", "John Doe")
            
            # Start call button
            if st.button("📞 Start LiveKit Call", use_container_width=True):
                # Create an actual LiveKit room
                room_name = generate_room_name(customer_name)
                customer_token = generate_customer_token(room_name, customer_name)
                
                # Store in session state
                st.session_state.livekit_call_active = True
                st.session_state.room_name = room_name
                st.session_state.customer_token = customer_token
                st.session_state.customer_name = customer_name
                
                # Start with a greeting
                st.session_state.livekit_conversation = [
                    {"role": "ai", "content": f"Hello {customer_name}, welcome to our salon! How can I help you today?"}
                ]
                
                # Call the LiveKit handler (asynchronous)
                try:
                    from ai_agent import handle_livekit_call
                    handle_livekit_call()
                    st.rerun()
                except Exception as e:
                    st.error(f"Error connecting to LiveKit: {str(e)}")
                    st.session_state.livekit_call_active = False
        else:
            # Show calling interface - the call is active
            room_name = st.session_state.room_name
            
            st.markdown(f"""
            <div class="stcard" style="text-align: center;">
                <h3 style="color: #007BFF; margin-top: 0;">LiveKit Call Active</h3>
                <p style="color: #4b5563;">Room: {room_name}</p>
                <p>WebRTC connection established with LiveKit servers.</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.success("Call connected successfully!")
            
            # Conversation area
            st.markdown("""
            <div class="stcard">
                <h3 style="color: #007BFF; margin-top: 0;">Conversation</h3>
            </div>
            """, unsafe_allow_html=True)
            
            # Display conversation using Streamlit components
            for message in st.session_state.livekit_conversation:
                role = message["role"]
                content = message["content"]
                
                if role == "user":
                    with st.container():
                        cols = st.columns([1, 12])
                        with cols[0]:
                            st.markdown("👤")
                        with cols[1]:
                            st.info(content)
                else:
                    with st.container():
                        cols = st.columns([1, 12])
                        with cols[0]:
                            st.markdown("🤖")
                        with cols[1]:
                            st.success(content)
            
            # User input for conversation
            user_question = st.text_input("Type your question here:", key="livekit_question")
            
            if st.button("Send", key="livekit_send"):
                if user_question.strip():
                    # Add user message to conversation
                    st.session_state.livekit_conversation.append({"role": "user", "content": user_question})
                    
                    # Process with AI agent
                    from knowledge_base import search_knowledge_base
                    answer, knows_answer = search_knowledge_base(user_question)
                    
                    if knows_answer:
                        # AI knows answer
                        response = answer
                    else:
                        # AI doesn't know
                        response = "I don't have that information in my knowledge base yet. Let me create a help request for a human supervisor to answer your question. We'll follow up with you soon."
                        
                        # Create help request
                        from database import create_help_request
                        from notification_service import notify_supervisor
                        
                        request_id = create_help_request(
                            st.session_state.customer_name, 
                            "LiveKit Call",  # Use a placeholder for phone in LiveKit calls
                            user_question
                        )
                        notify_supervisor(request_id, st.session_state.customer_name, user_question)
                        
                        # Add note about help request
                        st.session_state.livekit_conversation.append(
                            {"role": "system", "content": f"Help request created (ID: {request_id})"}
                        )
                    
                    # Add AI response to conversation
                    st.session_state.livekit_conversation.append({"role": "ai", "content": response})
                    
                    # Clear the input field by rerunning
                    st.rerun()
                else:
                    st.warning("Please enter a question first.")
            
            # End call button
            if st.button("📞 End Call", use_container_width=True):
                st.session_state.livekit_call_active = False
                st.session_state.livekit_conversation = []
                st.rerun()

elif page == "View Requests":
    # Page header with animation
    st.markdown("""
    <h1 style="animation: fadeIn 1s ease-out;">
        <span style="color: #007BFF;">Help</span> Requests Dashboard
    </h1>
    <p style="font-size: 1.1rem; color: #4b5563; margin-bottom: 30px;">
        Manage customer inquiries that the AI escalated to human supervisors
    </p>
    """, unsafe_allow_html=True)
    
    # Get help requests from database using our wrapper
    from database import execute_db_operation
    
    @execute_db_operation
    def get_help_requests():
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT id, customer_name, customer_phone, question, status, created_at, resolved_at,
                   ROUND((julianday('now') - julianday(created_at)) * 24, 1) as hours_waiting
            FROM help_requests
            ORDER BY 
                CASE 
                    WHEN status = 'pending' THEN 1
                    WHEN status = 'resolved' THEN 2
                    ELSE 3
                END,
                created_at DESC
            """)
            return cursor.fetchall()
        except Exception as e:
            print(f"Error fetching help requests: {e}")
            return []
        finally:
            conn.close()
    
    requests = get_help_requests()
    
    # Count the different types of requests
    pending_count = sum(1 for req in requests if req['status'] == 'pending')
    resolved_count = sum(1 for req in requests if req['status'] == 'resolved')
    unresolved_count = sum(1 for req in requests if req['status'] == 'unresolved')
    
    # Dashboard metrics
    st.markdown("<h2 class='animated' style='margin-top: 0;'>Request Overview</h2>", unsafe_allow_html=True)
    
    # Show metrics in a row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-container" style="border-left: 5px solid #007BFF;">
            <div class="metric-value">{len(requests)}</div>
            <div class="metric-label">Total Requests</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-container" style="border-left: 5px solid #f97316;">
            <div class="metric-value">{pending_count}</div>
            <div class="metric-label">Pending</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-container" style="border-left: 5px solid #10b981;">
            <div class="metric-value">{resolved_count}</div>
            <div class="metric-label">Resolved</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-container" style="border-left: 5px solid #ef4444;">
            <div class="metric-value">{unresolved_count}</div>
            <div class="metric-label">Unresolved</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Filter options in a cleaner UI
    st.markdown("<h2 class='animated' style='margin-top: 20px;'>Request Management</h2>", unsafe_allow_html=True)
    
    # Filter bar
    st.markdown("""
    <div style="background-color: #f8fafc; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
        <p style="margin: 0 0 10px 0; font-weight: 500;">Filter requests:</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        status_filter = st.selectbox("Status", ["All", "Pending", "Resolved", "Unresolved"])
    
    with col2:
        search_term = st.text_input("Search by customer name or question", placeholder="Type to search...")
    
    # Display requests
    if not requests:
        st.info("No help requests found in the system.")
    else:
        # Filter based on selection
        filtered_requests = []
        for req in requests:
            req_id = req['id']
            cust_name = req['customer_name']
            cust_phone = req['customer_phone']
            question = req['question']
            status = req['status']
            created = req['created_at']
            resolved = req['resolved_at']
            hours_waiting = req['hours_waiting']
            
            # Apply status filter
            status_match = status_filter == "All" or status_filter.lower() == status
            
            # Apply search filter if provided
            search_match = True
            if search_term:
                search_term_lower = search_term.lower()
                search_match = (search_term_lower in cust_name.lower() or 
                               search_term_lower in question.lower())
            
            if status_match and search_match:
                filtered_requests.append(req)
        
        if not filtered_requests:
            st.info(f"No matching requests found with the current filters.")
        else:
            # Add a count of filtered results
            st.markdown(f"<p style='color: #64748b;'>{len(filtered_requests)} requests found</p>", unsafe_allow_html=True)
            
            # Display requests in card format
            for req in filtered_requests:
                req_id = req['id']
                cust_name = req['customer_name']
                cust_phone = req['customer_phone']
                question = req['question']
                status = req['status']
                created = req['created_at']
                resolved = req['resolved_at']
                hours_waiting = req['hours_waiting']
                
                # Create a card container for each request
                with st.container():
                    # Create card with proper styling
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.markdown(f"### Request #{req_id}")
                        st.markdown(f"From {cust_name} • {created}")
                        if status == 'pending':
                            st.markdown(f"• {hours_waiting:.1f} hours ago")
                    
                    with col2:
                        if status == 'pending':
                            st.markdown(f"<div style='background-color: #fff7ed; padding: 5px 10px; border-radius: 20px; display: inline-block; text-align: center;'><span>🔔 Pending</span></div>", unsafe_allow_html=True)
                        elif status == 'resolved':
                            st.markdown(f"<div style='background-color: #ecfdf5; padding: 5px 10px; border-radius: 20px; display: inline-block; text-align: center;'><span>✅ Resolved</span></div>", unsafe_allow_html=True)
                        else:
                            st.markdown(f"<div style='background-color: #fef2f2; padding: 5px 10px; border-radius: 20px; display: inline-block; text-align: center;'><span>⚠️ Unresolved</span></div>", unsafe_allow_html=True)
                    
                    # Display the question
                    st.markdown("**Question:**")
                    st.markdown(f"<div style='padding: 10px; background-color: #f8fafc; border-radius: 6px;'>{question}</div>", unsafe_allow_html=True)
                    
                    # Action part based on status
                    if status == 'pending':
                        with st.expander("Respond to this request"):
                            st.markdown(f"**Customer Details:**")
                            st.markdown(f"📱 {cust_phone}")
                            st.markdown(f"⏰ Waiting for {hours_waiting:.1f} hours")
                            
                            # Response form
                            answer = st.text_area(
                                "Your Response", 
                                key=f"answer_{req_id}", 
                                height=100,
                                placeholder="Provide an answer that will be sent to the customer and added to the knowledge base..."
                            )
                            
                            # Options and submit
                            add_to_kb = st.checkbox("Add to knowledge base", key=f"kb_{req_id}", value=True)
                            
                            col1, col2 = st.columns([1, 3])
                            with col1:
                                if st.button("Send Response", key=f"submit_{req_id}", use_container_width=True):
                                    if answer.strip():
                                        # Use our database wrapper
                                        @execute_db_operation
                                        def resolve_request_and_update_kb(req_id, question, answer, cust_name, cust_phone, add_to_kb):
                                            conn = get_db_connection()
                                            try:
                                                cursor = conn.cursor()
                                                
                                                # Update help_request
                                                now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                                cursor.execute("""
                                                UPDATE help_requests
                                                SET status = 'resolved', response = ?, resolved_at = ?
                                                WHERE id = ?
                                                """, (answer, now, req_id))
                                                
                                                # Add to knowledge base if requested
                                                if add_to_kb:
                                                    # We'll use our standalone function to handle this properly
                                                    add_to_knowledge_base(question, answer, f"Supervisor response to {cust_name}")
                                                
                                                # Commit the transaction
                                                conn.commit()
                                                
                                                # Return success
                                                return True
                                            except Exception as e:
                                                print(f"Error resolving request: {e}")
                                                conn.rollback()
                                                return False
                                            finally:
                                                conn.close()
                                        
                                        # Process the response
                                        success = resolve_request_and_update_kb(req_id, question, answer, cust_name, cust_phone, add_to_kb)
                                        
                                        if success:
                                            st.success("Response sent to customer and request marked as resolved!")
                                            
                                            if add_to_kb:
                                                st.info("Answer added to knowledge base.")
                                            
                                            # Notify customer
                                            try:
                                                from ai_agent import follow_up_with_customer
                                                follow_up_with_customer(req_id, answer)
                                                st.success("Customer has been notified with the answer.")
                                            except Exception as e:
                                                st.warning(f"Customer notification failed: {e}")
                                            
                                            # Refresh the page to show the updated state
                                            time.sleep(1.5)
                                            st.rerun()
                                        else:
                                            st.error("Failed to resolve the request. Please try again.")
                                    else:
                                        st.warning("Please provide a response before submitting.")
                    # If already resolved, show the resolution details
                    elif status == 'resolved':
                        # Get the response for this request
                        @execute_db_operation
                        def get_response(req_id):
                            conn = get_db_connection()
                            try:
                                cursor = conn.cursor()
                                cursor.execute("SELECT response FROM help_requests WHERE id = ?", (req_id,))
                                result = cursor.fetchone()
                                return result['response'] if result else "No response recorded"
                            except Exception as e:
                                print(f"Error fetching response: {e}")
                                return "Error retrieving response"
                            finally:
                                conn.close()
                        
                        response = get_response(req_id)
                        
                        with st.expander("View resolution details"):
                            st.markdown(f"**✅ Resolved on {resolved}**")
                            st.markdown("**Supervisor Response:**")
                            st.markdown(f"<div style='padding: 10px; background-color: #f8fafc; border-radius: 6px;'>{response}</div>", unsafe_allow_html=True)
                    
                    # Add a divider between requests
                    st.markdown("<hr>", unsafe_allow_html=True)

elif page == "Knowledge Base":
    # Page header with animation and styling
    st.markdown("""
    <h1 style="animation: fadeIn 1s ease-out;">
        <span style="color: #007BFF;">Knowledge</span> Base Management
    </h1>
    <p style="font-size: 1.1rem; color: #4b5563; margin-bottom: 30px;">
        View and manage the AI assistant's knowledge repository
    </p>
    """, unsafe_allow_html=True)
    
    # Determine if we're in add mode
    add_mode = st.toggle("Add New Knowledge", value=False)
    
    if add_mode:
        # Show form to add new knowledge
        st.markdown("""
        <div class="stcard">
            <h3 style="color: #007BFF; margin-top: 0;">Add New Knowledge</h3>
            <p>Add a new question and answer to the knowledge base to enhance the AI's capabilities.</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("add_knowledge_form"):
            question = st.text_input("Question", placeholder="E.g., What are your business hours?")
            answer = st.text_area("Answer", placeholder="E.g., Our salon is open Monday-Friday from 9am to 7pm, Saturday from 10am to 6pm, and closed on Sundays.")
            source = st.text_input("Source", "Manual addition", help="Where this knowledge comes from (e.g., website, manual addition, etc.)")
            
            submit = st.form_submit_button("Add to Knowledge Base")
            
        if submit:
            if question and answer:
                try:
                    # Use our knowledge base function to add the entry
                    add_to_knowledge_base(question, answer, source)
                    st.success("Successfully added to knowledge base!")
                    
                    # Show the newly added entry in a styled card
                    st.markdown(f"""
                    <div class="stcard" style="border-left: 4px solid #10b981; margin-top: 15px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                            <h3 style="margin: 0; color: #10b981;">New Knowledge Added</h3>
                            <div style="background-color: #ecfdf5; padding: 5px 10px; border-radius: 20px;">
                                <span style="color: #10b981; font-weight: 500;">✅ Added</span>
                            </div>
                        </div>
                        <p style="font-weight: 500; margin-bottom: 5px;">Question:</p>
                        <p style="background-color: #f8fafc; padding: 10px; border-radius: 6px; margin-bottom: 15px;">{question}</p>
                        <p style="font-weight: 500; margin-bottom: 5px;">Answer:</p>
                        <p style="background-color: #f8fafc; padding: 10px; border-radius: 6px;">{answer}</p>
                        <p style="color: #64748b; font-size: 0.9rem; margin-top: 10px;">Source: {source}</p>
                    </div>
                    """, unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Error adding to knowledge base: {str(e)}")
            else:
                st.warning("Both question and answer are required.")
    else:
        # Show knowledge base browser
        st.markdown("""
        <div class="stcard">
            <h3 style="color: #007BFF; margin-top: 0;">Browse Knowledge Base</h3>
            <p>View all the questions and answers in the AI's knowledge base.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Search and filter
        search_term = st.text_input("Search Knowledge Base", placeholder="Type to search questions or answers...")
        
        # Get the knowledge base
        knowledge_items = get_knowledge_base()
        
        # Filter if search term provided
        if search_term:
            search_term_lower = search_term.lower()
            filtered_items = []
            
            for item in knowledge_items:
                if isinstance(item, dict):
                    question = item.get('question', '').lower()
                    answer = item.get('answer', '').lower()
                    
                    if search_term_lower in question or search_term_lower in answer:
                        filtered_items.append(item)
            
            display_items = filtered_items
        else:
            display_items = knowledge_items
        
        # Display knowledge base
        if not display_items:
            if search_term:
                st.info(f"No knowledge found matching '{search_term}'.")
            else:
                st.info("Knowledge base is empty. Add some knowledge to get started.")
        else:
            # Add a count of items
            st.markdown(f"<p style='color: #64748b;'>{len(display_items)} items found</p>", unsafe_allow_html=True)
            
            # Display items in an expander
            for i, item in enumerate(display_items):
                if isinstance(item, dict):
                    item_id = item.get('id', i)
                    question = item.get('question', 'No question')
                    answer = item.get('answer', 'No answer')
                    source = item.get('source', 'Unknown')
                    created = item.get('created_at', 'Unknown date')
                    
                    # Create a card for the knowledge item
                    with st.expander(f"Q: {question}"):
                        st.markdown(f"""
                        <div style="margin-bottom: 10px;">
                            <p style="font-weight: 500; margin-bottom: 5px;">Answer:</p>
                            <p style="background-color: #f8fafc; padding: 10px; border-radius: 6px;">{answer}</p>
                        </div>
                        
                        <div style="display: flex; justify-content: space-between; font-size: 0.9rem; color: #64748b;">
                            <p style="margin: 0;">Source: {source}</p>
                            <p style="margin: 0;">Added: {created}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Add delete button - this would actually remove from DB in a real app
                        if st.button("Delete This Item", key=f"delete_{item_id}"):
                            st.warning("⚠️ Delete functionality is disabled for this demo.")
# Frontdesk AI Assistant

A human-in-the-loop AI system that enables salon businesses to handle customer inquiries with AI assistance and human supervision.


## Overview

Frontdesk AI Assistant is a sophisticated application built to demonstrate an AI-powered customer service system with human supervision capabilities. The application uses an AI agent to handle customer inquiries, automatically responding to known questions, and escalating unknown questions to human supervisors.

## Key Features

- 🤖 **AI-Powered Reception**: Responds to customer inquiries automatically using a knowledge base
- 🔄 **Human-in-the-Loop**: Escalates unknown questions to human supervisors
- 📚 **Growing Knowledge Base**: Learns from supervisor responses to get smarter over time
- 📱 **Multi-Channel Communication**: Simulates phone calls and LiveKit WebRTC integration
- 📊 **Supervisor Dashboard**: Manage help requests and view metrics
- 🔒 **Database Management**: Secure storage of customer interactions

## Technology Stack

**Frontend**: Streamlit for the web interface  
**Backend**: Python  
**Database**: SQLite with thread-safe operations  
**Real-time Communication**: LiveKit WebRTC integration  
**Authentication**: JWT-based token generation  

**External Services**:
- LiveKit for WebRTC connections (optional)
- Twilio integration for SMS notifications (optional)

## Installation

### Prerequisites
- Python 3.10 or higher
- pip (Python package installer)

### Setup Instructions

1. Clone the repository
```bash
git clone https://github.com/yourusername/frontdesk-ai-assistant.git
cd frontdesk-ai-assistant
```
2. Create a virtual environment (optional but recommended)
 ```bash
 python -m venv venv
 source venv/bin/activate  # On Windows: venv\Scripts\activate
 ```
3. Install dependencies
```bash
 pip install -r installation_requirements.txt
```
4. Environment variables (optional)
Create a .env file in the root directory for optional external services:
```bash
# LiveKit credentials (optional)
LIVEKIT_URL=your_livekit_url
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret

# Twilio credentials (optional)
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=your_phone_number
```
Running the Application

Start the Streamlit server:
```bash
streamlit run app.py
```
The application will be available at http://localhost:5000

## Project Structure

**app.py:** Main application with Streamlit UI

**database.py:** Database operations and management

**knowledge_base.py:** Knowledge base management for AI responses

**ai_agent.py:** AI agent implementation for customer interactions

**livekit_service.py:** LiveKit WebRTC integration

**notification_service.py:** Service for sending notifications

**pages/:** Additional Streamlit pages

**supervisor_dashboard.py:** Dashboard for supervisors to view and respond to help requests

**knowledge_base_view.py:** UI for viewing and managing the knowledge base

## Usage Workflow

**Customer Interaction:** Customer asks a question through the simulated call or LiveKit interface

**AI Response:** AI agent checks the knowledge base for a known answer

**Escalation:** If no answer is found, a help request is created for human supervisors

**Supervisor Review:** Supervisors view pending requests on the dashboard and respond

**Knowledge Update:** Responses are added to the knowledge base for future use

**Customer Follow-up:** The system notifies the customer of the response

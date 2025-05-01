import sqlite3
import os
import datetime

# Database path
DB_PATH = "frontdesk_ai.db"

def init_db():
    """Initialize the database with necessary tables if they don't exist"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create help_requests table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS help_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_name TEXT NOT NULL,
        customer_phone TEXT NOT NULL,
        question TEXT NOT NULL,
        response TEXT,
        status TEXT DEFAULT 'pending',
        created_at TEXT NOT NULL,
        resolved_at TEXT
    )
    ''')
    
    # Create knowledge_base table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS knowledge_base (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT NOT NULL,
        answer TEXT NOT NULL,
        source TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    ''')
    
    # Pre-populate knowledge base with salon information if it's empty
    cursor.execute("SELECT COUNT(*) FROM knowledge_base")
    count = cursor.fetchone()[0]
    
    if count == 0:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        initial_knowledge = [
            ("What are your opening hours?", "We're open Monday to Friday from 9 AM to 7 PM, and Saturday from 10 AM to 5 PM. We're closed on Sundays.", "Initial Setup", now),
            ("What services do you offer?", "We offer haircuts, styling, coloring, highlights, perms, and facial waxing. We also have manicure and pedicure services.", "Initial Setup", now),
            ("Do I need an appointment?", "Yes, we recommend booking an appointment. Walk-ins are accepted based on availability.", "Initial Setup", now),
            ("Where are you located?", "We're located at 123 Beauty Lane, Downtown, CA 90210.", "Initial Setup", now),
            ("What's your cancellation policy?", "Please give us at least 24 hours notice for cancellations to avoid a cancellation fee of 50% of the service cost.", "Initial Setup", now)
        ]
        
        cursor.executemany(
            "INSERT INTO knowledge_base (question, answer, source, created_at) VALUES (?, ?, ?, ?)",
            initial_knowledge
        )
    
    conn.commit()
    conn.close()

def get_db_connection():
    """Get a connection to the SQLite database"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def create_help_request(customer_name, customer_phone, question):
    """Create a new help request in the database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute('''
    INSERT INTO help_requests 
    (customer_name, customer_phone, question, status, created_at)
    VALUES (?, ?, ?, ?, ?)
    ''', (customer_name, customer_phone, question, 'pending', now))
    
    request_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return request_id

def check_for_timeouts():
    """Check for help requests that have been pending for too long and mark them as unresolved"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Define timeout period (24 hours in this example)
    timeout_hours = 24
    
    # Calculate the cutoff time
    now = datetime.datetime.now()
    cutoff = (now - datetime.timedelta(hours=timeout_hours)).strftime("%Y-%m-%d %H:%M:%S")
    
    # Update requests that have timed out
    cursor.execute('''
    UPDATE help_requests
    SET status = 'unresolved'
    WHERE status = 'pending' AND created_at < ?
    ''', (cutoff,))
    
    updated_count = cursor.rowcount
    conn.commit()
    conn.close()
    
    return updated_count

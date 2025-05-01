import sqlite3
from database import get_db_connection

def get_knowledge_base():
    """Get the entire knowledge base"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT question, answer FROM knowledge_base")
    kb_items = cursor.fetchall()
    
    conn.close()
    
    # Convert to dictionary for easier lookup
    knowledge = {}
    for item in kb_items:
        knowledge[item['question'].lower()] = item['answer']
    
    return knowledge

def search_knowledge_base(query):
    """Search the knowledge base for an answer to the query"""
    # Get knowledge base
    knowledge = get_knowledge_base()
    
    # Normalize query
    query = query.lower().strip()
    
    # Direct match
    if query in knowledge:
        return knowledge[query], True
    
    # Partial match (simple implementation - in production would use better NLP techniques)
    for question, answer in knowledge.items():
        # Check if all words in the query are in the question
        query_words = set(query.split())
        question_words = set(question.split())
        
        # If 75% of the query words are in the question, consider it a match
        if len(query_words.intersection(question_words)) >= len(query_words) * 0.75:
            return answer, True
    
    # No match found
    return None, False

def add_to_knowledge_base(question, answer, source):
    """Add a new item to the knowledge base"""
    import datetime
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute('''
    INSERT INTO knowledge_base 
    (question, answer, source, created_at)
    VALUES (?, ?, ?, ?)
    ''', (question, answer, source, now))
    
    kb_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return kb_id

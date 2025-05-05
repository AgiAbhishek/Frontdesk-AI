import streamlit as st
import pandas as pd
from database import get_db_connection

st.set_page_config(
    page_title="Knowledge Base", 
    page_icon="📚",
    layout="wide"
)

st.title("AI Knowledge Base")
st.write("This page shows all the information that the AI agent knows.")

# Create tabs
tab1, tab2 = st.tabs(["Browse Knowledge", "Add Knowledge"])

with tab1:
    st.header("Browse Knowledge Base")
    
    # Search functionality
    search = st.text_input("Search knowledge base:", "")
    
    # Get knowledge base entries from the database using our wrapper
    from database import execute_db_operation
    
    @execute_db_operation
    def get_kb_entries(search_term):
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            
            # Build query based on search term
            if search_term:
                cursor.execute("""
                SELECT id, question, answer, source, created_at 
                FROM knowledge_base
                WHERE question LIKE ? OR answer LIKE ?
                ORDER BY created_at DESC
                """, (f"%{search_term}%", f"%{search_term}%"))
            else:
                cursor.execute("""
                SELECT id, question, answer, source, created_at 
                FROM knowledge_base
                ORDER BY created_at DESC
                """)
            
            return cursor.fetchall()
        except Exception as e:
            print(f"Error fetching knowledge base entries: {e}")
            return []
        finally:
            conn.close()
    
    kb_entries = get_kb_entries(search)
    
    if not kb_entries:
        if search:
            st.info(f"No entries found matching '{search}'.")
        else:
            st.info("No entries in the knowledge base yet.")
    else:
        # Display count
        st.subheader(f"{len(kb_entries)} entries found")
        
        # Display as a table for overview
        kb_data = []
        for entry in kb_entries:
            # Truncate long texts for table view
            question = entry['question']
            if len(question) > 50:
                question = question[:47] + "..."
                
            kb_data.append({
                "ID": entry['id'],
                "Question": question,
                "Source": entry['source'],
                "Date Added": entry['created_at']
            })
        
        df = pd.DataFrame(kb_data)
        st.dataframe(df, use_container_width=True)
        
        # Allow user to select an entry to view details
        selected_id = st.selectbox("Select an entry to view full details:", 
                                 ["None"] + [str(entry['id']) for entry in kb_entries])
        
        if selected_id != "None":
            # Find the selected entry
            selected_entry = next((entry for entry in kb_entries if str(entry['id']) == selected_id), None)
            
            if selected_entry:
                st.subheader("Knowledge Entry Details")
                
                st.write("**Question:**")
                st.info(selected_entry['question'])
                
                st.write("**Answer:**")
                st.success(selected_entry['answer'])
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Source:** {selected_entry['source']}")
                with col2:
                    st.write(f"**Added:** {selected_entry['created_at']}")

with tab2:
    st.header("Add New Knowledge")
    st.write("Use this form to manually add new information to the AI's knowledge base.")
    
    # Input form
    with st.form("add_knowledge_form"):
        question = st.text_area("Question:", 
                             placeholder="Enter a question that customers might ask")
        
        answer = st.text_area("Answer:", 
                           placeholder="Enter the information that answers this question")
        
        source = st.text_input("Source:", "Manual Entry", 
                            help="Where did this information come from?")
        
        submit = st.form_submit_button("Add to Knowledge Base")
        
        if submit:
            if question.strip() and answer.strip():
                # Add to database using knowledge_base module's function
                from knowledge_base import add_to_knowledge_base
                
                # This function already has the execute_db_operation decorator
                add_to_knowledge_base(question, answer, source)
                
                st.success("Knowledge added successfully!")
                
                # Clear form (by rerunning the page)
                st.rerun()
            else:
                st.error("Please enter both a question and an answer.")
    
    # Knowledge categories
    st.subheader("Common Knowledge Categories")
    st.write("""
    Consider adding knowledge in these common categories:
    - Services and pricing
    - Booking and scheduling policies
    - Location and hours
    - Cancellation policies
    - Special promotions or discounts
    - Staff information
    - Product recommendations
    """)
import streamlit as st
import sqlite3
import datetime
import pandas as pd
from database import get_db_connection
from knowledge_base import add_to_knowledge_base
from ai_agent import follow_up_with_customer

st.set_page_config(
    page_title="Supervisor Dashboard", 
    page_icon="🧠",
    layout="wide"
)

st.title("Supervisor Dashboard")

# Create tabs for different views
tab1, tab2, tab3 = st.tabs(["Pending Requests", "Request History", "Stats"])

with tab1:
    st.header("Pending Help Requests")
    
    # Get pending help requests
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT id, customer_name, customer_phone, question, created_at,
           ROUND((julianday('now') - julianday(created_at)) * 24, 1) as hours_waiting
    FROM help_requests 
    WHERE status = 'pending'
    ORDER BY created_at ASC
    """)
    pending_requests = cursor.fetchall()
    conn.close()
    
    if not pending_requests:
        st.info("No pending help requests at the moment.")
    else:
        # Show count
        st.subheader(f"{len(pending_requests)} pending requests")
        
        # Display each pending request in a card-like format
        for request in pending_requests:
            req_id = request['id']
            customer_name = request['customer_name']
            customer_phone = request['customer_phone']
            question = request['question']
            created_at = request['created_at']
            hours_waiting = request['hours_waiting']
            
            # Create a container for the request
            with st.container():
                # Two columns: request details and response form
                col1, col2 = st.columns([3, 2])
                
                with col1:
                    st.subheader(f"Request #{req_id}")
                    st.write(f"**From:** {customer_name} ({customer_phone})")
                    st.write(f"**Question:** {question}")
                    st.write(f"**Received:** {created_at} ({hours_waiting} hours ago)")
                    
                    # Add warning for old requests
                    if hours_waiting > 12:
                        st.warning(f"⚠️ This request has been waiting for over {int(hours_waiting)} hours!")
                
                with col2:
                    # Response form
                    st.write("**Submit Response:**")
                    response = st.text_area("Your answer", key=f"resp_{req_id}", height=100)
                    
                    # Add to knowledge base option
                    add_to_kb = st.checkbox("Add to knowledge base", key=f"kb_{req_id}", value=True)
                    
                    # Submit button
                    if st.button("Send Response", key=f"send_{req_id}"):
                        if response.strip():
                            # Update the database
                            conn = get_db_connection()
                            cursor = conn.cursor()
                            
                            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            
                            # Update help request
                            cursor.execute("""
                            UPDATE help_requests
                            SET status = 'resolved', response = ?, resolved_at = ?
                            WHERE id = ?
                            """, (response, now, req_id))
                            
                            # Add to knowledge base if checked
                            if add_to_kb:
                                add_to_knowledge_base(question, response, f"Help Request #{req_id}")
                            
                            conn.commit()
                            conn.close()
                            
                            # Follow up with customer
                            follow_up_with_customer(req_id, response)
                            
                            st.success("Response sent and request resolved!")
                            
                            # Refresh the page
                            st.rerun()
                        else:
                            st.error("Please enter a response before submitting.")
                
                # Add a separator
                st.markdown("---")

with tab2:
    st.header("Request History")
    
    # Filter options
    status_filter = st.selectbox(
        "Filter by status:",
        ["All", "Resolved", "Unresolved", "Pending"],
        key="history_filter"
    )
    
    # Date range filter
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("From date:", 
                                datetime.date.today() - datetime.timedelta(days=30))
    with col2:
        end_date = st.date_input("To date:", datetime.date.today())
    
    # Convert dates to strings for SQL
    start_date_str = start_date.strftime("%Y-%m-%d")
    end_date_str = (end_date + datetime.timedelta(days=1)).strftime("%Y-%m-%d")  # Add a day to include end date
    
    # Get requests with filters
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Build query based on filters
    query = """
    SELECT id, customer_name, customer_phone, question, status, created_at, resolved_at, response,
           ROUND((julianday(IFNULL(resolved_at, 'now')) - julianday(created_at)) * 24, 1) as resolution_hours
    FROM help_requests 
    WHERE created_at BETWEEN ? AND ?
    """
    params = [start_date_str, end_date_str]
    
    if status_filter != "All":
        query += " AND status = ?"
        params.append(status_filter.lower())
    
    query += " ORDER BY created_at DESC"
    
    cursor.execute(query, params)
    history_requests = cursor.fetchall()
    conn.close()
    
    if not history_requests:
        st.info(f"No requests found matching your filters.")
    else:
        # Create a DataFrame for display
        requests_data = []
        for req in history_requests:
            requests_data.append({
                "ID": req['id'],
                "Customer": req['customer_name'],
                "Phone": req['customer_phone'],
                "Question": req['question'],
                "Status": req['status'].title(),
                "Created": req['created_at'],
                "Resolved": req['resolved_at'] if req['resolved_at'] else "-",
                "Hours": req['resolution_hours']
            })
        
        df = pd.DataFrame(requests_data)
        
        # Display as a table
        st.dataframe(df, use_container_width=True)
        
        # Allow user to select a request to view details
        selected_req_id = st.selectbox("Select a request to view details:", 
                                     ["None"] + [str(req['id']) for req in history_requests])
        
        if selected_req_id != "None":
            # Find the selected request
            selected_req = next((req for req in history_requests if str(req['id']) == selected_req_id), None)
            
            if selected_req:
                st.subheader(f"Request #{selected_req['id']} Details")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Customer:** {selected_req['customer_name']}")
                    st.write(f"**Phone:** {selected_req['customer_phone']}")
                    st.write(f"**Status:** {selected_req['status'].title()}")
                    st.write(f"**Created:** {selected_req['created_at']}")
                    if selected_req['resolved_at']:
                        st.write(f"**Resolved:** {selected_req['resolved_at']}")
                        st.write(f"**Resolution Time:** {selected_req['resolution_hours']} hours")
                
                with col2:
                    st.write("**Question:**")
                    st.info(selected_req['question'])
                    
                    if selected_req['response']:
                        st.write("**Response:**")
                        st.success(selected_req['response'])

with tab3:
    st.header("System Statistics")
    
    # Get statistics from database
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get counts by status
    cursor.execute("""
    SELECT status, COUNT(*) as count
    FROM help_requests
    GROUP BY status
    """)
    status_counts = cursor.fetchall()
    
    # Get average resolution time
    cursor.execute("""
    SELECT AVG((julianday(resolved_at) - julianday(created_at)) * 24) as avg_hours
    FROM help_requests
    WHERE status = 'resolved'
    """)
    avg_resolution = cursor.fetchone()
    
    # Get requests per day for the last 30 days
    cursor.execute("""
    SELECT date(created_at) as date, COUNT(*) as count
    FROM help_requests
    WHERE created_at >= date('now', '-30 days')
    GROUP BY date(created_at)
    ORDER BY date(created_at)
    """)
    daily_counts = cursor.fetchall()
    
    # Get knowledge base growth
    cursor.execute("""
    SELECT date(created_at) as date, COUNT(*) as count
    FROM knowledge_base
    GROUP BY date(created_at)
    ORDER BY date(created_at)
    """)
    kb_growth = cursor.fetchall()
    
    conn.close()
    
    # Display status counts
    st.subheader("Request Status")
    
    # Create status counts dictionary
    status_dict = {s['status']: s['count'] for s in status_counts}
    total = sum(status_dict.values())
    
    # Display metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Requests", total)
    with col2:
        st.metric("Pending", status_dict.get('pending', 0))
    with col3:
        st.metric("Resolved", status_dict.get('resolved', 0))
    
    # Average resolution time
    if avg_resolution and avg_resolution['avg_hours']:
        st.subheader("Resolution Performance")
        avg_hours = round(avg_resolution['avg_hours'], 1)
        st.metric("Average Resolution Time", f"{avg_hours} hours")
    
    # Daily requests chart
    if daily_counts:
        st.subheader("Requests per Day (Last 30 Days)")
        
        # Convert to DataFrame for charting
        daily_data = pd.DataFrame(daily_counts, columns=['date', 'count'])
        daily_data['date'] = pd.to_datetime(daily_data['date'])
        
        # Create chart
        st.line_chart(daily_data.set_index('date'))
    
    # Knowledge base growth
    if kb_growth:
        st.subheader("Knowledge Base Growth")
        
        # Convert to DataFrame for charting
        kb_data = pd.DataFrame(kb_growth, columns=['date', 'count'])
        kb_data['date'] = pd.to_datetime(kb_data['date'])
        
        # Calculate cumulative sum
        kb_data['cumulative'] = kb_data['count'].cumsum()
        
        # Create chart
        st.line_chart(kb_data.set_index('date')['cumulative'])

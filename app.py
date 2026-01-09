import streamlit as st
import asyncio
from agent import process_receipt
import os
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(
    page_title="My Tax Agent | Secure Dashboard",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB_FILE = "tax_records.csv"

def check_password():
    """Returns True if the user had the correct password."""
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == st.secrets["APP_PASSWORD"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password
        st.markdown("## 🔒 Private Access")
        st.write("This Tax Agent is secured. Please enter your credentials.")
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        st.caption("Protected by Streamlit Secrets")
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error
        st.markdown("## 🔒 Private Access")
        st.write("This Tax Agent is secured. Please enter your credentials.")
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        st.error("😕 Password incorrect. Please try again.")
        return False
    else:
        # Password correct
        return True

# Password protection - check before showing the app
if not check_password():
    st.stop()  # Stop execution if password is incorrect

st.title("📂 Smart Tax Filer Agent")

def save_to_csv(data):
    record = data.model_dump()
    record['processed_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    df = pd.DataFrame([record])
    if not os.path.isfile(DB_FILE):
        df.to_csv(DB_FILE, index=False)
    else:
        df.to_csv(DB_FILE, mode='a', header=False, index=False)

def load_csv_safe():
    """Safely load CSV file, handling schema changes and parsing errors."""
    if not os.path.isfile(DB_FILE):
        return pd.DataFrame()
    
    try:
        # Try reading with error handling
        df = pd.read_csv(DB_FILE, on_bad_lines='skip', engine='python')
        
        # Ensure all expected columns exist, fill missing ones with None
        expected_columns = ['amount', 'category', 'merchant', 'date', 'description', 'audit_reasoning', 'processed_at']
        for col in expected_columns:
            if col not in df.columns:
                df[col] = None
        
        # Return only expected columns in the right order
        return df[expected_columns]
    except Exception as e:
        st.error(f"Error reading CSV file: {str(e)}")
        # Try to recover by reading with minimal settings
        try:
            return pd.read_csv(DB_FILE, sep=',', error_bad_lines=False, warn_bad_lines=False)
        except:
            return pd.DataFrame()

# --- Sidebar Logic ---
with st.sidebar:
    # --- DISCLAIMER ---
    st.warning("⚠️ **DISCLAIMER:** This is an AI tool. I am NOT a CPA. Verify all results with a professional.")
    
    st.header("📊 Tax Insights")
    if os.path.isfile(DB_FILE):
        df_history = load_csv_safe()
        
        # Monthly Summary Chart
        st.subheader("Spending by Category")
        fig = px.pie(df_history, values='amount', names='category', hole=0.4)
        fig.update_layout(showlegend=False, height=250, margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig, use_container_width=True)
        
        total_spent = df_history['amount'].sum()
        st.metric("Total Tracked Expenses", f"${total_spent:,.2f}")
        
        st.divider()
        st.download_button("Download CSV", data=open(DB_FILE, 'rb'), file_name="tax_records.csv")
    
    # Logout button - always visible at the bottom of the sidebar
    st.divider()  # Optional: Adds a visual separator
    if st.button("🔒 Log Out"):
        # Clear password-related session state to return to login screen
        if "password_correct" in st.session_state:
            del st.session_state["password_correct"]
        if "password" in st.session_state:
            del st.session_state["password"]
        st.rerun()

# --- Main Interface ---
col_upload, col_view = st.columns([1, 1])

with col_upload:
    st.subheader("Step 1: Process Receipt")
    uploaded_file = st.file_uploader("Upload receipt image", type=["jpg", "png", "jpeg"])
    
    if uploaded_file:
        st.image(uploaded_file, width=250)
        if st.button("Analyze & Save Record"):
            temp_path = f"temp_{uploaded_file.name}"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            with st.spinner("AI classifying expense..."):
                result = asyncio.run(process_receipt(file_path=temp_path))
                save_to_csv(result)
                os.remove(temp_path)
                
                # SAVE RESULT TO SESSION STATE (The "Sticky" Fix)
                st.session_state['last_result'] = result
                st.rerun()

    # DISPLAY RESULT (Outside the button so it shows after rerun)
    if 'last_result' in st.session_state:
        res = st.session_state['last_result']
        st.success(f"Recorded ${res.amount} under {res.category}!")
        
        # --- NEW COLLAPSIBLE BOX ---
        with st.expander("ℹ️ See AI Reasoning"):
            st.write(res.audit_reasoning)
            st.caption("This reasoning is generated by AI and should be reviewed.")

with col_view:
    st.subheader("Step 2: Recent History")
    if os.path.isfile(DB_FILE):
        search_query = st.text_input("🔍 Search vendors or categories")
        full_history = load_csv_safe()
        
        # Rename audit_reasoning to AI_reasoning for display
        if 'audit_reasoning' in full_history.columns:
            full_history = full_history.rename(columns={'audit_reasoning': 'AI_reasoning'})
        
        if search_query:
            filtered_df = full_history[
                full_history['merchant'].astype(str).str.contains(search_query, case=False, na=False) | 
                full_history['category'].astype(str).str.contains(search_query, case=False, na=False)
            ]
            st.dataframe(filtered_df, use_container_width=True)
        else:
            st.dataframe(full_history.tail(10), use_container_width=True)
    else:
        st.info("No records found yet. Upload your first receipt!")

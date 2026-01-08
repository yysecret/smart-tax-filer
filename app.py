import streamlit as st
import asyncio
from agent import process_receipt
import os
import pandas as pd
import plotly.express as px
from datetime import datetime

import streamlit as st

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
        st.text_input("Please enter the access password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error
        st.text_input("Please enter the access password", type="password", on_change=password_entered, key="password")
        st.error("😕 Password incorrect")
        return False
    else:
        # Password correct
        return True

if not check_password():
    st.stop()  # Do not run the rest of the app if not authenticated

st.set_page_config(page_title="Smart Tax Filer", page_icon="💰", layout="wide")
st.title("📂 Smart Tax Filer Agent")

DB_FILE = "tax_records.csv"

def save_to_csv(data):
    record = data.model_dump()
    record['processed_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    df = pd.DataFrame([record])
    if not os.path.isfile(DB_FILE):
        df.to_csv(DB_FILE, index=False)
    else:
        df.to_csv(DB_FILE, mode='a', header=False, index=False)

# --- Sidebar Logic ---
with st.sidebar:
    st.header("📊 Tax Insights")
    if os.path.isfile(DB_FILE):
        df_history = pd.read_csv(DB_FILE)
        
        # Monthly Summary Chart
        st.subheader("Spending by Category")
        fig = px.pie(df_history, values='amount', names='category', hole=0.4)
        fig.update_layout(showlegend=False, height=250, margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig, use_container_width=True)
        
        total_spent = df_history['amount'].sum()
        st.metric("Total Tracked Expenses", f"${total_spent:,.2f}")
        
        st.divider()
        st.download_button("Download CSV", data=open(DB_FILE, 'rb'), file_name="tax_records.csv")

# --- Main Interface ---
col_upload, col_view = st.columns([1, 1])

with col_upload:
    st.subheader("Step 1: Upload")
    uploaded_file = st.file_uploader("Upload receipt image", type=["jpg", "png", "jpeg"])
    
    if uploaded_file:
        st.image(uploaded_file, width=250)
        if st.button("Analyze & Save"):
            temp_path = f"temp_{uploaded_file.name}"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            with st.spinner("Classifying..."):
                result = asyncio.run(process_receipt(file_path=temp_path))
                save_to_csv(result)
                os.remove(temp_path)
                st.success(f"Saved ${result.amount} to {result.category}!")
                
                # Display Audit Reasoning
                if result.audit_reasoning:
                    st.info(f"**IRS Justification:** {result.audit_reasoning}")
                
                st.rerun() # Refresh to update the chart

with col_view:
    st.subheader("Step 2: Recent History")
    if os.path.isfile(DB_FILE):
        search_query = st.text_input("🔍 Search vendors or categories")
        full_history = pd.read_csv(DB_FILE)
        
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

"""
Minimal version of the enhanced app for troubleshooting loading issues
"""

import streamlit as st
import pandas as pd
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set page config
st.set_page_config(
    page_title="Minimal Social Security App",
    page_icon="🤖",
    layout="wide"
)

# Initialize session state variables
if 'initialized' not in st.session_state:
    st.session_state.initialized = False

# Title and application description
st.title("🤖 AI-Powered Social Security Application System (Minimal Version)")

# Create sidebar for navigation
with st.sidebar:
    st.header("Navigation")
    
    # Create tabs
    tabs = ["Home", "System Info"]
    
    selected_tab = st.radio("Select a page", tabs)
    
    # Show system status
    st.sidebar.markdown("---")
    st.sidebar.subheader("System Status")
    st.sidebar.success("✅ System Ready")

# Home Tab
if selected_tab == "Home":
    st.header("🏠 Welcome to the Social Security Application System")
    
    st.markdown("""
    This is a minimal version of the application for troubleshooting purposes.
    
    ### Features:
    
    1. **Automated Document Processing**: Extracts information from various document types
    2. **Advanced Data Validation**: Ensures data quality and consistency
    3. **ML-Based Eligibility Assessment**: Fair and consistent assessment of applications
    4. **Economic Enablement Recommendations**: Personalized guidance for applicants
    
    ### System Configuration:
    """)
    
    # Display system info
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Python Version", "3.9")
        st.metric("Streamlit Version", "1.31.1")
    
    with col2:
        st.metric("Database", "PostgreSQL")
        st.metric("Status", "Connected")

# System Info Tab
elif selected_tab == "System Info":
    st.header("ℹ️ System Information")
    
    st.subheader("Environment Variables")
    
    # Display environment variables (only non-sensitive ones)
    env_vars = {
        "HOME": os.environ.get("HOME", "Not set"),
        "PYTHONPATH": os.environ.get("PYTHONPATH", "Not set"),
        "SHELL": os.environ.get("SHELL", "Not set"),
        "TERM": os.environ.get("TERM", "Not set"),
        "USER": os.environ.get("USER", "Not set")
    }
    
    st.json(env_vars)
    
    st.subheader("Application Structure")
    
    # Display application structure
    st.markdown("""
    ```
    social_app_1/
    ├── agents/
    ├── data/
    ├── models/
    ├── utils/
    ├── app.py
    ├── enhanced_app.py
    ├── requirements.txt
    └── README.md
    ```
    """)
    
    st.subheader("Current Time")
    st.write(f"The current time is: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Add test button
    if st.button("Test Button"):
        st.success("Button clicked successfully!")
        st.balloons()

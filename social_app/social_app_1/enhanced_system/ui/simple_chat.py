"""
Simple standalone chat application for the Social Security Support System.
This is a fallback implementation that doesn't rely on the backend API.
"""

import streamlit as st
import requests
import json
import os
from datetime import datetime

def run_simple_chat():
    """Run a simple chat interface that works without complex backend dependencies."""
    st.title("AI Support Assistant (Simple Mode)")
    
    # Option to disable Ollama attempts
    use_ollama = not st.checkbox("Skip Ollama connection (faster responses)", value=True)
    
    # Initialize chat history
    if "simple_chat_history" not in st.session_state:
        st.session_state.simple_chat_history = []
    
    # Display chat messages
    for message in st.session_state.simple_chat_history:
        if message["role"] == "user":
            st.markdown(f"**You:** {message['content']}")
        else:
            st.markdown(f"**AI Assistant:** {message['content']}")
    
    # Input for new message
    user_input = st.text_input("Type your message here:", key="simple_chat_input")
    
    # When user submits a message
    if st.button("Send", key="simple_chat_send"):
        if user_input:
            # Add user message to chat history
            st.session_state.simple_chat_history.append({
                "role": "user",
                "content": user_input
            })
            
            # Generate AI response (without depending on backend)
            ai_response = get_simple_response(user_input, use_ollama)
            
            # Add AI response to chat history
            st.session_state.simple_chat_history.append({
                "role": "assistant",
                "content": ai_response
            })
            
            # Store the input to clear it on the next rerun
            st.session_state["last_message"] = user_input
            
            # Rerun to update the UI
            st.rerun()
    
    # Option to clear chat history
    if st.button("Clear Chat History", key="simple_clear_chat"):
        st.session_state.simple_chat_history = []
        st.rerun()

def get_simple_response(user_query, use_ollama=False):
    """Generate a simple response based on the user query without backend API."""
    try:
        # Try direct Ollama connection only if enabled
        if use_ollama:
            try:
                with st.spinner("Connecting to Ollama..."):
                    response = requests.post(
                        "http://localhost:11434/api/generate",
                        json={
                            "model": "mistral",
                            "prompt": f"""You are a helpful AI assistant for the Social Security Support System.
                            The user has a question about their social security application: {user_query}
                            Provide a helpful, concise response:""",
                            "stream": False
                        },
                        timeout=15  # 15-second timeout (increased from 5)
                    )
                
                if response.status_code == 200:
                    return response.json().get("response", "No response received from AI system.")
            except Exception as e:
                # If Ollama fails, continue to fallback responses
                st.error(f"Could not connect to Ollama: {str(e)}")
        else:
            st.info("Using pre-programmed responses (Ollama connection disabled).")
        
        # Fallback to simple rule-based responses
        user_query = user_query.lower()
        
        if "income" in user_query or "financial" in user_query or "money" in user_query:
            return "Based on your income and financial situation, you may be eligible for additional support. I recommend submitting your latest income statements and employment records to strengthen your application."
        
        elif "document" in user_query or "upload" in user_query:
            return "To complete your application, please upload the following documents: proof of identity (Emirates ID or passport), proof of income (salary slips or bank statements), and proof of residence (utility bills or rental agreement)."
        
        elif "status" in user_query or "progress" in user_query:
            return "Your application is currently being processed. The typical processing time is 5-7 business days. You'll receive notifications as your application progresses through validation and assessment."
        
        elif "eligible" in user_query or "qualify" in user_query:
            return "Eligibility for social security benefits depends on several factors including income level, family size, employment status, and residency status. Based on the information in your application, our system will determine your eligibility and provide recommendations."
        
        elif "help" in user_query or "assistance" in user_query:
            return "I'm here to help with your social security application. I can provide information on eligibility criteria, required documents, application status, and recommendations based on your specific situation."
        
        else:
            return "Thank you for your query. I'm your AI assistant for the Social Security Support System. I can help with application submissions, document requirements, eligibility criteria, and checking application status. Please let me know how I can assist you further."
    
    except Exception as e:
        return f"I apologize, but I encountered an error while processing your request. Please try again or contact support if the issue persists. Error details: {str(e)}"

if __name__ == "__main__":
    run_simple_chat()

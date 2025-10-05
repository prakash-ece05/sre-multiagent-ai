"""
SRE Multi-Agent Conversational AI System
Main Streamlit Application
"""

import streamlit as st
import os
from dotenv import load_dotenv
from datetime import datetime
from agents.root_agent import create_root_agent
from google.adk.sessions import InMemorySessionsService
from google.adk.runners import Runner

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="SRE Conversational AI",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .user-message {
        background-color: #e3f2fd;
    }
    .agent-message {
        background-color: #f5f5f5;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'session_service' not in st.session_state:
    st.session_state.session_service = InMemorySessionsService()
if 'runner' not in st.session_state:
    root_agent = create_root_agent()
    st.session_state.runner = Runner(
        agent=root_agent,
        sessions_service=st.session_state.session_service
    )
if 'session_id' not in st.session_state:
    st.session_state.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

# Main content
def main():
  #Initialize ADK components at app level
  if "adk_initialized" not in st.session_state:
    try:
      #Pull API key
      use_vertex_ai = os.environ.get("GOOGLE_GENAI_USE_VERTEXAI")
      api_key = os.environ.get("GOOGLE_API_KEY")
      if not use_vertex_ai and (not api_key or "YOUR_GOOGLE_API_KEY" in api_key):
        st.error("API is Required")
        st.stop()
      
      #Initialize ADK components once at app level
      adk_runner, session_service = get_cached_adk()
      st.session_state.adk_runner = adk_runner
      st.session_state.session_service = session_service
      st.session_state.adk_initialized = true
      print(" ADK Initialized")
except Exception as e:
    st.error(f" Fatal Error: Could not initialize ADK: {e}")
    st.stop

if __name__ == "__main__":
  main()
  

  
fe_allow_html=True)

import streamlit as st
import os
import time

DEFAULT_API_URL = "http://localhost:8000"

def get_api_url(debug: bool = True):
    # Step 1: ENV
    env_url = os.getenv("API_URL")
    if env_url:
        if debug:
            st.info(f"🌍 API_URL from environment: `{env_url}`")
        return env_url

    # Step 2: JS-injected query param
    for _ in range(3):  # Retry for a short time
        api_url = st.query_params.get("api_url")
        if api_url:
            if debug:
                st.info(f"🧠 API_URL from query param: `{api_url}`")
            return api_url
        time.sleep(0.5)

    # Step 3: Fallback
    if debug:
        st.warning(f"❌ Fallback to default: `{DEFAULT_API_URL}`")
    return DEFAULT_API_URL

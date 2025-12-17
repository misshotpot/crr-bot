import streamlit as st
from openai import OpenAI
import json

st.title("🔍 Diagnostic Test")

# Test 1: Check if secrets exist
st.subheader("Test 1: Secrets Configuration")

try:
    api_key = st.secrets.get("OPENAI_API_KEY")
    if api_key:
        st.success(f"✅ OPENAI_API_KEY found (starts with: {api_key[:10]}...)")
    else:
        st.error("❌ OPENAI_API_KEY not found")
except Exception as e:
    st.error(f"❌ Error reading OPENAI_API_KEY: {str(e)}")

try:
    google_creds = st.secrets.get("GOOGLE_CREDENTIALS")
    if google_creds:
        st.success("✅ GOOGLE_CREDENTIALS found")
        creds_dict = json.loads(google_creds)
        st.info(f"Project ID: {creds_dict.get('project_id', 'Not found')}")
    else:
        st.error("❌ GOOGLE_CREDENTIALS not found")
except Exception as e:
    st.error(f"❌ Error reading GOOGLE_CREDENTIALS: {str(e)}")

# Test 2: Test OpenAI API
st.subheader("Test 2: OpenAI API Connection")

if st.button("Test OpenAI API"):
    try:
        api_key = st.secrets["OPENAI_API_KEY"]
        client = OpenAI(api_key=api_key)
        
        # Simple test call
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say 'test successful'"}],
            max_tokens=10
        )
        
        st.success("✅ OpenAI API works!")
        st.write(f"Response: {response.choices[0].message.content}")
        
    except Exception as e:
        st.error(f"❌ OpenAI API Error: {str(e)}")

# Test 3: Test Google Sheets
st.subheader("Test 3: Google Sheets Connection")

if st.button("Test Google Sheets"):
    try:
        import gspread
        from oauth2client.service_account import ServiceAccountCredentials
        
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        
        creds_dict = json.loads(st.secrets["GOOGLE_CREDENTIALS"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        gclient = gspread.authorize(creds)
        
        st.success("✅ Google Sheets connection works!")
        
        # Try to access or create spreadsheet
        try:
            spreadsheet = gclient.open("CRA_Training_Data")
            st.success(f"✅ Found existing spreadsheet: CRA_Training_Data")
        except:
            st.info("⚠️ Spreadsheet not found, but connection works")
        
    except Exception as e:
        st.error(f"❌ Google Sheets Error: {str(e)}")

st.markdown("---")
st.caption("Run these tests to diagnose configuration issues")

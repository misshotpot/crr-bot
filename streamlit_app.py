import streamlit as st
from openai import OpenAI
import json
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Page configuration
st.set_page_config(
    page_title="Community Risk Assessment",
    page_icon="🚒",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""
<style>
    [data-testid="collapsedControl"] {display: block !important; opacity: 0.5;}
    [data-testid="collapsedControl"]:hover {opacity: 1;}
    .main {max-width: 800px; margin: 0 auto; padding: 2rem 1rem;}
    h1 {font-size: 1.5rem !important; font-weight: 600 !important; margin-bottom: 0.5rem !important;}
    .stChatMessage {padding: 1rem !important; margin-bottom: 0.5rem !important; border-radius: 8px !important;}
    .stButton button {border-radius: 6px !important; font-weight: 500 !important;}
    .stDeployButton {display: none}
    footer {visibility: hidden}
    hr {margin: 1.5rem 0; border: none; border-top: 1px solid #e5e5e5;}
</style>
""", unsafe_allow_html=True)

# API & Google Sheets
try:
    openai_api_key = st.secrets["OPENAI_API_KEY"]
    client = OpenAI(api_key=openai_api_key)
except Exception as e:
    st.error("⚠️ OpenAI API key not configured.")
    st.stop()

@st.cache_resource
def init_google_sheets():
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds_dict = json.loads(st.secrets.get("GOOGLE_CREDENTIALS", "{}"))
        if not creds_dict:
            return None, "Credentials not found"
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        gclient = gspread.authorize(creds)
        sheet_name = "CRA_Training_Data"
        try:
            spreadsheet = gclient.open(sheet_name)
            sheet = spreadsheet.sheet1
        except gspread.SpreadsheetNotFound:
            spreadsheet = gclient.create(sheet_name)
            sheet = spreadsheet.sheet1
            sheet.append_row(["Timestamp", "Session ID", "User Name", "Department", "Message Count", "Full Conversation (JSON)", "Generated Report", "Risks Identified"])
        return sheet, None
    except Exception as e:
        return None, str(e)

google_sheet, sheets_error = init_google_sheets()

def save_conversation_to_sheets(sheet, session_data):
    if sheet is None:
        return False, "Sheet not initialized"
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        row = [
            timestamp,
            session_data.get("session_id", ""),
            session_data.get("user_info", {}).get("name", "Unknown"),
            session_data.get("user_info", {}).get("department", "Unknown"),
            len(session_data.get("messages", [])),
            json.dumps(session_data.get("messages", []), ensure_ascii=False),
            session_data.get("report", "")[:500],
            ", ".join(session_data.get("risks", []))
        ]
        sheet.append_row(row)
        return True, "Saved"
    except Exception as e:
        return False, str(e)

# Default System Prompt
DEFAULT_PROMPT = """You are an AI consultant specializing in Community Risk Assessment (CRA) for fire departments.

Your role is three-fold:

1. ASSESSMENT CONDUCTOR: Guide fire chiefs through systematic risk identification.
2. DATA EDUCATOR: Help users understand data sources (OFIRMS, SVI, GIS, etc.).
3. EDUCATIONAL CONSULTANT: Explain risk interconnections and best practices.

CRITICAL RULES:
- Ask ONE QUESTION AT A TIME only
- Always EXPLAIN WHY you need information before asking
- EDUCATE throughout the conversation

TONE: Professional, educational, consultative."""

# Sidebar
with st.sidebar:
    st.title("⚙️ Settings")
    st.divider()
    
    st.subheader("🤖 System Prompt")
    
    if "custom_system_prompt" not in st.session_state:
        st.session_state.custom_system_prompt = DEFAULT_PROMPT
    
    prompt_text = st.text_area("Edit:", st.session_state.custom_system_prompt, height=250)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Save", use_container_width=True):
            st.session_state.custom_system_prompt = prompt_text
            st.success("✅ Saved!")
    with col2:
        if st.button("↺ Reset", use_container_width=True):
            st.session_state.custom_system_prompt = DEFAULT_PROMPT
            st.success("✅ Reset!")
    
    st.divider()
    st.subheader("📝 Presets")
    
    presets = {
        "🔥 Standard": DEFAULT_PROMPT,
        "🌟 Friendly": "You are a friendly AI assistant for fire risk assessment.\n\nBe warm and supportive. Make it easy.\n\nTONE: Friendly, casual.",
        "📊 Data": "You are a data analyst for fire risk assessment.\n\nFocus on numbers and statistics.\n\nTONE: Analytical, precise.",
        "🎓 Teacher": "You are a patient teacher about risk assessment.\n\nExplain thoroughly with examples.\n\nTONE: Patient, educational.",
        "🇨🇳 中文": "你是消防风险评估AI顾问。\n\n引导识别风险、教育数据、提供建议。\n\n一次一问题，先解释原因。\n\n语气：专业、教育。"
    }
    
    for name, content in presets.items():
        if st.button(name, use_container_width=True):
            st.session_state.custom_system_prompt = content
            st.rerun()
    
    st.divider()
    st.subheader("🎛️ Model")
    
    if "model_name" not in st.session_state:
        st.session_state.model_name = "gpt-4"
    
    st.session_state.model_name = st.selectbox("Model:", ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"])
    
    if "temperature" not in st.session_state:
        st.session_state.temperature = 0.7
    
    st.session_state.temperature = st.slider("Temperature:", 0.0, 1.0, 0.7, 0.1)

# Report Generation
def generate_report(history):
    text = "\n\n".join([f"{m['role'].upper()}: {m['content']}" for m in history])
    prompt = f"""Create a CRA report from this conversation:

{text}

Format:

# Community Risk Assessment Report

## Department & Community Overview
## Identified Risks & Concerns  
## Key Findings & Recommendations
## Data & Resources Discussed

---
**Report Generated:** {datetime.now().strftime("%B %d, %Y at %I:%M %p")}
**Session ID:** {st.session_state.conversation_id}"""

    try:
        response = client.chat.completions.create(
            model=st.session_state.model_name,
            messages=[
                {"role": "system", "content": "You are an expert fire service consultant."},
                {"role": "user", "content": prompt}
            ],
            temperature=st.session_state.temperature,
            max_tokens=1500
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

# Session State
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": """Hello! I'm your AI consultant for Community Risk Assessment.

**To get started, could you tell me your name and role with the fire department?**

For example: "I'm Chief Smith from the Springfield Fire Department" """}]

if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = datetime.now().strftime("%Y%m%d_%H%M%S")

for key in ["user_info", "report_generated", "current_report", "auto_saved", "identified_risks"]:
    if key not in st.session_state:
        st.session_state[key] = [] if key == "identified_risks" else ({} if key == "user_info" else (False if "generated" in key or "saved" in key else None))

# Header
col1, col2, col3 = st.columns([3, 1, 1])

with col1:
    st.title("Community Risk Assessment")

with col2:
    if len(st.session_state.messages) >= 5 and st.button("📝 Report", use_container_width=True, type="primary"):
        with st.spinner("Generating..."):
            report = generate_report(st.session_state.messages)
            st.session_state.current_report = report
            st.session_state.report_generated = True
            if google_sheet and not st.session_state.auto_saved:
                save_conversation_to_sheets(google_sheet, {"session_id": st.session_state.conversation_id, "user_info": st.session_state.user_info, "messages": st.session_state.messages, "report": report, "risks": st.session_state.identified_risks})
                st.session_state.auto_saved = True
            st.rerun()

with col3:
    if st.button("🔄 New", use_container_width=True):
        if google_sheet and len(st.session_state.messages) > 2 and not st.session_state.auto_saved:
            save_conversation_to_sheets(google_sheet, {"session_id": st.session_state.conversation_id, "user_info": st.session_state.user_info, "messages": st.session_state.messages, "report": st.session_state.current_report, "risks": st.session_state.identified_risks})
        for key in list(st.session_state.keys()):
            if key not in ["custom_system_prompt", "model_name", "temperature"]:
                del st.session_state[key]
        st.rerun()

st.divider()

# Chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if st.session_state.report_generated and st.session_state.current_report:
    with st.expander("📊 Generated Report", expanded=True):
        st.markdown(st.session_state.current_report)
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            st.download_button("📥 Download", st.session_state.current_report, f"CRA_{st.session_state.conversation_id}.md", use_container_width=True)
        with col2:
            if st.button("🔄 Regenerate", use_container_width=True):
                st.session_state.current_report = generate_report(st.session_state.messages)
                st.rerun()

if prompt := st.chat_input("Message Community Risk Assessment..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        try:
            messages = [{"role": "system", "content": st.session_state.custom_system_prompt}] + st.session_state.messages[-20:]
            stream = client.chat.completions.create(model=st.session_state.model_name, messages=messages, stream=True, temperature=st.session_state.temperature, max_tokens=1000)
            response = st.write_stream(stream)
        except Exception as e:
            response = f"❌ Error: {str(e)}"
            st.error(response)
    
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()

st.divider()
col1, col2 = st.columns([3, 1])
with col1:
    st.caption(f"Session: {st.session_state.conversation_id}")
with col2:
    st.caption(f"Model: {st.session_state.model_name}")

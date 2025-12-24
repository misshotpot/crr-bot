import streamlit as st
from openai import OpenAI
import json
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Page configuration
st.set_page_config(
    page_title="🚒 Community Risk Assessment Bot",
    page_icon="🚒",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Hide sidebar completely with CSS
st.markdown("""
<style>
    [data-testid="collapsedControl"] {
        display: none
    }
    section[data-testid="stSidebar"] {
        display: none;
    }
    .main {
        padding-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# API Configuration
# ============================================

try:
    openai_api_key = st.secrets["OPENAI_API_KEY"]
    client = OpenAI(api_key=openai_api_key)
except Exception as e:
    st.error("⚠️ OpenAI API key not configured.")
    st.stop()

# ============================================
# Google Sheets Integration
# ============================================

@st.cache_resource
def init_google_sheets():
    """Initialize Google Sheets connection"""
    try:
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        
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
            
            # Add headers
            sheet.append_row([
                "Timestamp",
                "Session ID",
                "User Name",
                "Department",
                "Message Count",
                "Full Conversation (JSON)",
                "Generated Report",
                "Risks Identified"
            ])
        
        return sheet, None
        
    except Exception as e:
        return None, str(e)

# Initialize Google Sheets
google_sheet, sheets_error = init_google_sheets()

def save_conversation_to_sheets(sheet, session_data):
    """Save conversation data to Google Sheets"""
    if sheet is None:
        return False, "Sheet not initialized"
    
    try:
        session_id = session_data.get("session_id", "")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        user_name = session_data.get("user_info", {}).get("name", "Unknown")
        department = session_data.get("user_info", {}).get("department", "Unknown")
        messages = session_data.get("messages", [])
        message_count = len(messages)
        report = session_data.get("report", "Not generated")
        risks = ", ".join(session_data.get("risks", []))
        
        conversation_json = json.dumps(messages, ensure_ascii=False)
        
        row = [
            timestamp,
            session_id,
            user_name,
            department,
            message_count,
            conversation_json,
            report[:500] if report else "",
            risks
        ]
        
        sheet.append_row(row)
        
        return True, "Saved successfully"
        
    except Exception as e:
        return False, str(e)

# ============================================
# System Prompt
# ============================================

SYSTEM_PROMPT = """You are an AI consultant specializing in Community Risk Assessment (CRA) for fire departments.

Your role is three-fold:

1. ASSESSMENT CONDUCTOR: Guide fire chiefs through systematic risk identification.

2. DATA EDUCATOR: Help users understand data sources (OFIRMS, SVI, GIS, etc.).

3. EDUCATIONAL CONSULTANT: Explain risk interconnections and best practices.

CRITICAL RULES:
- Ask ONE QUESTION AT A TIME only
- Always EXPLAIN WHY you need information before asking
- EDUCATE throughout the conversation

TONE: Professional, educational, consultative."""

# ============================================
# Report Generation
# ============================================

def generate_cra_report(conversation_history):
    """Generate CRA report"""
    
    conversation_text = "\n\n".join([
        f"{msg['role'].upper()}: {msg['content']}" 
        for msg in conversation_history
    ])
    
    report_prompt = f"""Based on this conversation, create a concise CRA report.

CONVERSATION:
{conversation_text}

Create a professional report in markdown format:

# Community Risk Assessment Report

## Department & Community Overview
## Identified Risks & Concerns  
## Key Findings & Recommendations
## Data & Resources Discussed

---
**Report Generated:** {datetime.now().strftime("%B %d, %Y at %I:%M %p")}
**Session ID:** {st.session_state.conversation_id}

Be specific and actionable."""

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert fire service consultant."},
                {"role": "user", "content": report_prompt}
            ],
            temperature=0.7,
            max_tokens=1500
        )
        
        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating report: {str(e)}"

# ============================================
# Initialize Session State
# ============================================

if "messages" not in st.session_state:
    st.session_state.messages = []
    welcome = """Hello! I'm your AI consultant for Community Risk Assessment.

**To get started, could you tell me your name and role with the fire department?**

For example: "I'm Chief Smith from the Springfield Fire Department" """
    st.session_state.messages.append({"role": "assistant", "content": welcome})

if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = datetime.now().strftime("%Y%m%d_%H%M%S")

if "user_info" not in st.session_state:
    st.session_state.user_info = {}

if "report_generated" not in st.session_state:
    st.session_state.report_generated = False

if "current_report" not in st.session_state:
    st.session_state.current_report = None

if "auto_saved" not in st.session_state:
    st.session_state.auto_saved = False

if "identified_risks" not in st.session_state:
    st.session_state.identified_risks = []

# ============================================
# Header with Controls
# ============================================

st.title("🚒 Community Risk Assessment AI Consultant")

# Control buttons in header
col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

with col2:
    if len(st.session_state.messages) >= 5 and not st.session_state.report_generated:
        if st.button("📝 Generate Report", use_container_width=True):
            with st.spinner("Generating report..."):
                report = generate_cra_report(st.session_state.messages)
                st.session_state.current_report = report
                st.session_state.report_generated = True
                
                # Auto-save to Google Sheets
                if google_sheet and not st.session_state.auto_saved:
                    session_data = {
                        "session_id": st.session_state.conversation_id,
                        "user_info": st.session_state.user_info,
                        "messages": st.session_state.messages,
                        "report": report,
                        "risks": st.session_state.identified_risks
                    }
                    success, msg = save_conversation_to_sheets(google_sheet, session_data)
                    if success:
                        st.session_state.auto_saved = True
                
                st.rerun()

with col3:
    if st.session_state.report_generated and st.session_state.current_report:
        st.download_button(
            label="📥 Download",
            data=st.session_state.current_report,
            file_name=f"CRA_{st.session_state.conversation_id}.md",
            mime="text/markdown",
            use_container_width=True
        )

with col4:
    if st.button("🔄 New Chat", use_container_width=True):
        # Save before clearing
        if google_sheet and len(st.session_state.messages) > 2 and not st.session_state.auto_saved:
            session_data = {
                "session_id": st.session_state.conversation_id,
                "user_info": st.session_state.user_info,
                "messages": st.session_state.messages,
                "report": st.session_state.current_report,
                "risks": st.session_state.identified_risks
            }
            save_conversation_to_sheets(google_sheet, session_data)
        
        # Reset
        st.session_state.messages = []
        st.session_state.conversation_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.session_state.user_info = {}
        st.session_state.report_generated = False
        st.session_state.current_report = None
        st.session_state.auto_saved = False
        st.session_state.identified_risks = []
        st.rerun()

st.markdown("---")

# ============================================
# Chat Interface
# ============================================

# Display conversation
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Display generated report if available
if st.session_state.report_generated and st.session_state.current_report:
    with st.expander("📊 Generated Report", expanded=False):
        st.markdown(st.session_state.current_report)
        
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="📥 Download as Markdown",
                data=st.session_state.current_report,
                file_name=f"CRA_{st.session_state.conversation_id}.md",
                mime="text/markdown",
                key="download_md"
            )
        with col2:
            st.download_button(
                label="📄 Download as Text",
                data=st.session_state.current_report,
                file_name=f"CRA_{st.session_state.conversation_id}.txt",
                mime="text/plain",
                key="download_txt"
            )

# Chat input
if prompt := st.chat_input("Type your message..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                messages = [{"role": "system", "content": SYSTEM_PROMPT}]
                for msg in st.session_state.messages[-20:]:
                    messages.append({"role": msg["role"], "content": msg["content"]})
                
                stream = client.chat.completions.create(
                    model="gpt-4",
                    messages=messages,
                    stream=True,
                    temperature=0.7,
                    max_tokens=1000
                )
                
                response = st.write_stream(stream)
                
            except Exception as e:
                response = f"❌ Error: {str(e)}"
                st.error(response)
    
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()

# Footer
st.markdown("---")
col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    st.caption("🚒 AI-Enhanced Community Risk Assessment | For Fire Service Professionals")
with col2:
    if google_sheet and st.session_state.auto_saved:
        st.caption("✅ Data saved")
with col3:
    st.caption(f"Session: {st.session_state.conversation_id[:8]}...")

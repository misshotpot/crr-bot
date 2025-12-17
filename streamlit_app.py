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
    layout="wide"
)

# ============================================
# API Configuration
# ============================================

# OpenAI API
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
# Main Application
# ============================================

st.title("🚒 Community Risk Assessment AI Consultant")
st.markdown("""
**AI-Enhanced Community Risk Reduction with Automatic Data Collection**

- 🎯 Systematic risk identification
- 📊 Professional CRA reports
- 💾 Automatic conversation saving for research
""")

st.markdown("---")

# Initialize session state
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
# Sidebar
# ============================================

with st.sidebar:
    st.header("📋 Session Info")
    
    st.caption(f"Session: {st.session_state.conversation_id}")
    
    # Google Sheets status
    if google_sheet:
        st.success("✅ Auto-save: Enabled")
        st.caption("Data saved to Google Sheets")
    else:
        st.warning("⚠️ Auto-save: Disabled")
        if sheets_error:
            with st.expander("Error details"):
                st.text(sheets_error)
    
    st.markdown("---")
    
    # Stats
    st.subheader("💬 Stats")
    message_count = len(st.session_state.messages)
    st.metric("Messages", message_count)
    
    if st.session_state.identified_risks:
        st.metric("Risks", len(st.session_state.identified_risks))
    
    st.markdown("---")
    
    # Actions
    st.subheader("⚙️ Actions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 New", use_container_width=True):
            # Save before clearing
            if google_sheet and len(st.session_state.messages) > 2 and not st.session_state.auto_saved:
                session_data = {
                    "session_id": st.session_state.conversation_id,
                    "user_info": st.session_state.user_info,
                    "messages": st.session_state.messages,
                    "report": st.session_state.current_report,
                    "risks": st.session_state.identified_risks
                }
                success, msg = save_conversation_to_sheets(google_sheet, session_data)
                if success:
                    st.success("✅ Auto-saved to database")
                else:
                    st.warning(f"⚠️ Save failed: {msg}")
                    st.info("💾 Please use manual download backup")
            
            # Reset
            st.session_state.messages = []
            st.session_state.conversation_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            st.session_state.user_info = {}
            st.session_state.report_generated = False
            st.session_state.current_report = None
            st.session_state.auto_saved = False
            st.session_state.identified_risks = []
            st.rerun()
    
    with col2:
        if len(st.session_state.messages) > 2:
            download_data = {
                "session_id": st.session_state.conversation_id,
                "timestamp": datetime.now().isoformat(),
                "user_info": st.session_state.user_info,
                "messages": st.session_state.messages,
                "report": st.session_state.current_report
            }
            
            st.download_button(
                label="💾 Save",
                data=json.dumps(download_data, indent=2, ensure_ascii=False),
                file_name=f"CRA_{st.session_state.conversation_id}.json",
                mime="application/json",
                use_container_width=True
            )
    
    st.markdown("---")
    
    # Generate Report
    st.subheader("📋 Report")
    
    if len(st.session_state.messages) < 5:
        remaining = 5 - len(st.session_state.messages)
        st.info(f"💬 {remaining} more message(s)")
    else:
        st.success("✅ Ready!")
        
        if st.button("📝 Generate", type="primary", use_container_width=True):
            with st.spinner("Generating report..."):
                report = generate_cra_report(st.session_state.messages)
                st.session_state.current_report = report
                st.session_state.report_generated = True
                
                # Auto-save to Google Sheets when report generated
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
                        st.success("✅ Auto-saved to database")
                        st.success("✅ Report generated!")
                    else:
                        st.warning(f"⚠️ Save failed: {msg}")
                        st.info("💾 Please use manual download backup")
                        st.success("✅ Report generated!")
                else:
                    st.success("✅ Report generated!")
                
                st.rerun()
        
        if st.session_state.report_generated and st.session_state.current_report:
            st.download_button(
                label="📥 Download",
                data=st.session_state.current_report,
                file_name=f"CRA_{st.session_state.conversation_id}.md",
                mime="text/markdown",
                use_container_width=True
            )
    
    st.markdown("---")
    
    with st.expander("ℹ️ How to Use"):
        st.markdown("""
        **Quick Start:**
        1. Introduce yourself
        2. Answer 2-3 questions
        3. Generate report
        
        **Features:**
        - ✅ Auto-save to database
        - ✅ Download chat & report
        - ✅ Quick reports (3+ messages)
        
        **Data Collection:**
        All conversations automatically
        saved to Google Sheets for
        research and model training.
        """)
    
    if google_sheet:
        with st.expander("📊 View Data"):
            st.markdown("""
            **To view saved data:**
            1. Go to Google Sheets
            2. Find "CRA_Training_Data"
            3. View all conversations
            
            **Spreadsheet includes:**
            - Timestamp
            - User info
            - Full conversations
            - Generated reports
            - Identified risks
            """)

# ============================================
# Main Conversation Area
# ============================================

st.subheader("💬 Consultation")

# Display conversation
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

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

# Display generated report
if st.session_state.report_generated and st.session_state.current_report:
    st.markdown("---")
    st.subheader("📊 Generated Report")
    
    with st.expander("📄 View Report", expanded=True):
        st.markdown(st.session_state.current_report)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.download_button(
            label="📥 Download MD",
            data=st.session_state.current_report,
            file_name=f"CRA_{st.session_state.conversation_id}.md",
            mime="text/markdown"
        )
    
    with col2:
        st.download_button(
            label="📄 Download TXT",
            data=st.session_state.current_report,
            file_name=f"CRA_{st.session_state.conversation_id}.txt",
            mime="text/plain"
        )
    
    with col3:
        if st.button("🔄 Regenerate"):
            with st.spinner("Regenerating..."):
                report = generate_cra_report(st.session_state.messages)
                st.session_state.current_report = report
                st.rerun()

# Footer
st.markdown("---")
st.caption("🚒 AI-Enhanced Community Risk Assessment | For Fire Service Professionals")
if google_sheet:
    st.caption("💾 Conversations automatically saved to Google Sheets for research")
if st.session_state.auto_saved:
    st.caption("✅ This session has been saved to the database")

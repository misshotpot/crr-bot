import streamlit as st
from openai import OpenAI
import json
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="🚒 Community Risk Assessment Bot",
    page_icon="🚒",
    layout="wide"
)

# Read OpenAI API key from Streamlit Secrets
try:
    openai_api_key = st.secrets["OPENAI_API_KEY"]
    client = OpenAI(api_key=openai_api_key)
    api_configured = True
except Exception as e:
    api_configured = False
    st.error("⚠️ API key not configured. Please contact administrator.")
    st.stop()

# Fire service professional system prompt
SYSTEM_PROMPT = """You are an AI consultant specializing in Community Risk Assessment (CRA) for fire departments.

Your role is three-fold:

1. ASSESSMENT CONDUCTOR: Guide fire chiefs and officers through systematic risk identification using conversational interviews.

2. DATA EDUCATOR: Help users access and understand various data sources including:
   - OFIRMS (Ohio Fire Information Reporting Management System)
   - Social Vulnerability Index (SVI)
   - GIS community information
   - Local inspection reports and strategic plans
   - EMS incident data
   - Building and fire codes
   - Pre-incident plans
   - Weather, crime, and demographic data

3. EDUCATIONAL CONSULTANT: Explain why different data matters, how risk factors interconnect, and what various indicators mean for community safety.

CRITICAL INTERACTION RULES:
- Ask ONE QUESTION AT A TIME only - never ask multiple questions in one response
- Always EXPLAIN WHY you need information before asking the question
- When you find or discuss data, ASK if they have newer/better data before proceeding
- EDUCATE throughout - explain connections, why things matter, how factors relate
- After each response, explain why the next piece of information matters before asking for it

ADAPTIVE QUESTIONING:
Tailor your approach based on department type:
- Rural/Wildland Interface: Focus on vegetation management, evacuation routes, seasonal risks
- Urban Core: Emphasize high-rise buildings, population density, infrastructure age
- Suburban: Balance residential risks with commercial and industrial considerations
- Volunteer Departments: Consider resource limitations, response time challenges, training needs

CONVERSATION FLOW:
1. Start by learning about the user (name, role, department type, location, community characteristics)
2. Progressively build understanding through targeted questions
3. Share relevant examples from similar communities when appropriate
4. Explain how risk factors compound and interconnect
5. Validate findings with the user throughout the process

TONE: Professional, educational, consultative - like an experienced peer mentor who's helping them think through complex problems.

Remember: This is NOT just data collection - you're teaching systematic risk analysis while conducting the assessment. Users should leave with enhanced analytical skills they can apply ongoing."""

# Function to generate simplified CRA report
def generate_cra_report(conversation_history):
    """Generate a concise Community Risk Assessment report"""
    
    # Build conversation summary
    conversation_text = "\n\n".join([
        f"{msg['role'].upper()}: {msg['content']}" 
        for msg in conversation_history
    ])
    
    # Create simplified prompt for report generation
    report_prompt = f"""Based on the following conversation with a fire department officer, create a concise Community Risk Assessment (CRA) report.

CONVERSATION:
{conversation_text}

Create a professional but concise CRA report in markdown format with these sections:

# Community Risk Assessment Report

## Department & Community Overview
- Department name, location, and type
- Community characteristics
- Key demographics or geographic features mentioned

## Identified Risks & Concerns
- List all risks discussed (with priority if mentioned)
- Include any specific concerns raised
- Note any vulnerable populations or areas

## Key Findings & Recommendations
- Main takeaways from the assessment
- Immediate priorities (if identified)
- Suggested next steps or actions

## Data & Resources Discussed
- Any data sources mentioned (SVI, OFIRMS, etc.)
- Resources or information gaps identified

---
**Report Generated:** {datetime.now().strftime("%B %d, %Y at %I:%M %p")}
**Session ID:** {st.session_state.conversation_id}

Be concise but specific. If the conversation is brief, work with what was discussed. If information is missing, note it as a gap to address."""

    try:
        # Call OpenAI to generate report
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert fire service consultant. Create concise, actionable Community Risk Assessment reports based on conversations. Keep reports focused and practical."},
                {"role": "user", "content": report_prompt}
            ],
            temperature=0.7,
            max_tokens=1500
        )
        
        return response.choices[0].message.content
    
    except Exception as e:
        return f"Error generating report: {str(e)}"

# Title and introduction
st.title("🚒 Community Risk Assessment AI Consultant")
st.markdown("""
**Transforming Community Risk Reduction Through Intelligent Consultation**

This AI consultant helps fire departments conduct comprehensive Community Risk Assessments by:
- 🎯 Guiding systematic risk identification
- 📊 Explaining data sources and their relevance  
- 🧠 Teaching risk analysis methodologies
- 💡 Providing insights from similar communities
- 📋 Generating CRA reports
""")

st.markdown("---")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
    welcome = """Hello! I'm your AI consultant for Community Risk Assessment. Before we begin, I'd like to understand who I'm working with.

**Could you tell me your name and your role with the fire department?**

For example: "I'm Chief Smith from the Springfield Fire Department" or "I'm Lt. Johnson, we're a volunteer department in rural Ohio"."""
    st.session_state.messages.append({"role": "assistant", "content": welcome})

if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = datetime.now().strftime("%Y%m%d_%H%M%S")

if "user_info" not in st.session_state:
    st.session_state.user_info = {}

if "report_generated" not in st.session_state:
    st.session_state.report_generated = False

if "current_report" not in st.session_state:
    st.session_state.current_report = None

# Sidebar
with st.sidebar:
    st.header("📋 Session Information")
    
    st.caption(f"Session: {st.session_state.conversation_id}")
    
    # Display user information
    if st.session_state.user_info:
        st.subheader("👤 User Profile")
        for key, value in st.session_state.user_info.items():
            st.text(f"{key}: {value}")
    
    st.markdown("---")
    
    # Conversation statistics
    st.subheader("💬 Conversation Stats")
    message_count = len(st.session_state.messages)
    st.metric("Messages", message_count)
    
    st.markdown("---")
    
    # Action buttons
    st.subheader("⚙️ Actions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 New Session", use_container_width=True):
            st.session_state.messages = []
            st.session_state.conversation_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            st.session_state.user_info = {}
            st.session_state.report_generated = False
            st.session_state.current_report = None
            welcome = """Hello! I'm your AI consultant for Community Risk Assessment.

**Could you tell me your name and your role with the fire department?**"""
            st.session_state.messages.append({"role": "assistant", "content": welcome})
            st.rerun()
    
    with col2:
        if len(st.session_state.messages) > 2:
            download_data = {
                "session_id": st.session_state.conversation_id,
                "timestamp": datetime.now().isoformat(),
                "user_info": st.session_state.user_info,
                "messages": st.session_state.messages,
                "message_count": len(st.session_state.messages)
            }
            
            st.download_button(
                label="💾 Save Chat",
                data=json.dumps(download_data, indent=2),
                file_name=f"CRA_Chat_{st.session_state.conversation_id}.json",
                mime="application/json",
                use_container_width=True
            )
    
    st.markdown("---")
    
    # Generate CRA Report Section
    st.subheader("📋 Generate Report")
    
    # Can generate after 3+ messages (at least 2 exchanges)
    if len(st.session_state.messages) < 5:  # Welcome + user + bot + user + bot = 5
        remaining = 5 - len(st.session_state.messages)
        st.info(f"💬 {remaining} more message(s) to generate report")
    else:
        st.success("✅ Ready to generate report!")
        
        # Generate Report Button
        if st.button("📝 Generate Report", type="primary", use_container_width=True):
            with st.spinner("Generating CRA report..."):
                report = generate_cra_report(st.session_state.messages)
                st.session_state.current_report = report
                st.session_state.report_generated = True
                st.success("✅ Report generated!")
                st.rerun()
        
        # Download buttons (if report exists)
        if st.session_state.report_generated and st.session_state.current_report:
            st.download_button(
                label="📥 Download Report (MD)",
                data=st.session_state.current_report,
                file_name=f"CRA_Report_{st.session_state.conversation_id}.md",
                mime="text/markdown",
                use_container_width=True
            )
            
            st.download_button(
                label="📄 Download Report (TXT)",
                data=st.session_state.current_report,
                file_name=f"CRA_Report_{st.session_state.conversation_id}.txt",
                mime="text/plain",
                use_container_width=True
            )
    
    st.markdown("---")
    
    # Help information
    with st.expander("ℹ️ How to Use"):
        st.markdown("""
        **Getting Started:**
        1. Introduce yourself and department
        2. Answer 2-3 questions
        3. Generate your CRA report
        
        **Tips:**
        - Be specific about your community
        - Share key challenges
        - More detail = better report
        
        **Report:**
        - Available after 3+ messages
        - Can regenerate anytime
        - Download as MD or TXT
        """)

# Main conversation area
st.subheader("💬 Consultation")

# Display conversation history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Type your message here...", key="chat_input"):
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Generate AI response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # Build messages
                messages = [{"role": "system", "content": SYSTEM_PROMPT}]
                
                # Add conversation history (last 20 messages)
                for msg in st.session_state.messages[-20:]:
                    messages.append({"role": msg["role"], "content": msg["content"]})
                
                # Call OpenAI API
                stream = client.chat.completions.create(
                    model="gpt-4",
                    messages=messages,
                    stream=True,
                    temperature=0.7,
                    max_tokens=1000
                )
                
                # Stream response
                response = st.write_stream(stream)
                
            except Exception as e:
                response = f"❌ Error: {str(e)}\n\nPlease contact administrator."
                st.error(response)
    
    # Save response to history
    st.session_state.messages.append({"role": "assistant", "content": response})

# Display Generated Report (if exists)
if st.session_state.report_generated and st.session_state.current_report:
    st.markdown("---")
    st.subheader("📊 Generated CRA Report")
    
    with st.expander("📄 View Report", expanded=True):
        st.markdown(st.session_state.current_report)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.download_button(
            label="📥 Download Markdown",
            data=st.session_state.current_report,
            file_name=f"CRA_Report_{st.session_state.conversation_id}.md",
            mime="text/markdown"
        )
    
    with col2:
        st.download_button(
            label="📄 Download Text",
            data=st.session_state.current_report,
            file_name=f"CRA_Report_{st.session_state.conversation_id}.txt",
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
st.caption("🚒 AI-Enhanced Community Risk Assessment | Developed for Fire Service Professionals")
st.caption("💡 This bot educates while assessing - generates reports from your conversations")

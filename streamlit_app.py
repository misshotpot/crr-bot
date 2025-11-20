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

# ============================================
# KEY CHANGE: Read OpenAI API key from Streamlit Secrets
# Users don't need to input any API key
# ============================================

try:
    # Read OpenAI API key from Secrets
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

# Title and introduction
st.title("🚒 Community Risk Assessment AI Consultant")
st.markdown("""
**Transforming Community Risk Reduction Through Intelligent Consultation**

This AI consultant helps fire departments conduct comprehensive Community Risk Assessments by:
- 🎯 Guiding systematic risk identification
- 📊 Explaining data sources and their relevance  
- 🧠 Teaching risk analysis methodologies
- 💡 Providing insights from similar communities
""")

st.markdown("---")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
    # Add welcome message
    welcome = """Hello! I'm your AI consultant for Community Risk Assessment. Before we begin, I'd like to understand who I'm working with.

**Could you tell me your name and your role with the fire department?**

For example: "I'm Chief Smith from the Springfield Fire Department" or "I'm Lt. Johnson, we're a volunteer department in rural Ohio"."""
    st.session_state.messages.append({"role": "assistant", "content": welcome})

if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = datetime.now().strftime("%Y%m%d_%H%M%S")

if "user_info" not in st.session_state:
    st.session_state.user_info = {}

# Sidebar
with st.sidebar:
    st.header("📋 Session Information")
    
    # Display conversation ID
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
            welcome = """Hello! I'm your AI consultant for Community Risk Assessment. Before we begin, I'd like to understand who I'm working with.

**Could you tell me your name and your role with the fire department?**"""
            st.session_state.messages.append({"role": "assistant", "content": welcome})
            st.rerun()
    
    with col2:
        if len(st.session_state.messages) > 2:
            # Prepare download data
            download_data = {
                "session_id": st.session_state.conversation_id,
                "timestamp": datetime.now().isoformat(),
                "user_info": st.session_state.user_info,
                "messages": st.session_state.messages,
                "message_count": len(st.session_state.messages)
            }
            
            st.download_button(
                label="💾 Save",
                data=json.dumps(download_data, indent=2),
                file_name=f"CRA_{st.session_state.conversation_id}.json",
                mime="application/json",
                use_container_width=True
            )
    
    # Generate report button (when there's enough conversation)
    if len(st.session_state.messages) > 10:
        st.markdown("---")
        if st.button("📋 Generate CRA Report", type="primary", use_container_width=True):
            with st.spinner("Generating comprehensive CRA report..."):
                try:
                    # Build conversation summary
                    conversation_summary = "\n\n".join([
                        f"{msg['role'].upper()}: {msg['content']}" 
                        for msg in st.session_state.messages
                    ])
                    
                    report_prompt = f"""Based on the following conversation with a fire department officer, create a comprehensive Community Risk Assessment (CRA) report.

{conversation_summary}

Create a professional CRA report in markdown format with these sections:
1. Executive Summary
2. Department Information  
3. Community Profile
4. Identified Risks (categorized and prioritized)
5. Risk Analysis & Interconnections
6. Data Sources Used
7. Key Recommendations
8. Next Steps

Make it actionable and professional."""

                    response = client.chat.completions.create(
                        model="gpt-4",
                        messages=[
                            {"role": "system", "content": "You are an expert in creating Community Risk Assessment reports for fire departments."},
                            {"role": "user", "content": report_prompt}
                        ],
                        temperature=0.7
                    )
                    
                    report = response.choices[0].message.content
                    
                    # Display report
                    st.success("✅ Report generated!")
                    with st.expander("📄 View CRA Report", expanded=True):
                        st.markdown(report)
                    
                    # Download report
                    st.download_button(
                        label="📥 Download Report",
                        data=report,
                        file_name=f"CRA_Report_{st.session_state.conversation_id}.md",
                        mime="text/markdown",
                        use_container_width=True
                    )
                    
                except Exception as e:
                    st.error(f"Error generating report: {str(e)}")
    
    st.markdown("---")
    
    # Help information
    with st.expander("ℹ️ How to Use"):
        st.markdown("""
        **Getting Started:**
        1. Introduce yourself and your department
        2. Answer questions one at a time
        3. Learn about risk factors as you go
        
        **Tips:**
        - Be specific about your community
        - Share local challenges
        - Ask for explanations anytime
        
        **Features:**
        - Auto-saves conversation
        - Generates final CRA report
        - Educational throughout
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
                
                # Add conversation history (last 20 messages to control tokens)
                for msg in st.session_state.messages[-20:]:
                    messages.append({"role": msg["role"], "content": msg["content"]})
                
                # Call OpenAI API (streaming output)
                stream = client.chat.completions.create(
                    model="gpt-4",  # or "gpt-3.5-turbo" for faster and cheaper
                    messages=messages,
                    stream=True,
                    temperature=0.7,
                    max_tokens=1000
                )
                
                # Stream display response
                response = st.write_stream(stream)
                
            except Exception as e:
                response = f"❌ Error: {str(e)}\n\nPlease contact administrator."
                st.error(response)
    
    # Save response to history
    st.session_state.messages.append({"role": "assistant", "content": response})

# Footer
st.markdown("---")
st.caption("🚒 AI-Enhanced Community Risk Assessment | Developed for Fire Service Professionals")
st.caption("💡 This bot educates while assessing - each conversation helps you learn systematic risk analysis methods")

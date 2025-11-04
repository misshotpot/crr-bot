import streamlit as st
from openai import OpenAI
import json
from datetime import datetime

# 页面配置
st.set_page_config(
    page_title="🚒 Community Risk Assessment Bot",
    page_icon="🚒",
    layout="wide"
)

# 消防专业系统提示词
SYSTEM_PROMPT = """You are an AI consultant specializing in Community Risk Assessment (CRA) for fire departments. Your role is three-fold:

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
   - Public health and environmental indicators

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

# 标题和介绍
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

# API Key 输入
openai_api_key = st.text_input("OpenAI API Key", type="password", help="Enter your OpenAI API key to begin")

if not openai_api_key:
    st.info("🔑 Please add your OpenAI API key to continue.", icon="🗝️")
    st.markdown("Get your API key from: [OpenAI Platform](https://platform.openai.com/api-keys)")
    st.stop()

# 创建 OpenAI 客户端
try:
    client = OpenAI(api_key=openai_api_key)
except Exception as e:
    st.error(f"Error initializing OpenAI client: {str(e)}")
    st.stop()

# 初始化 session state
if "messages" not in st.session_state:
    st.session_state.messages = []
    # 添加欢迎消息
    welcome = """Hello! I'm your AI consultant for Community Risk Assessment. Before we begin, I'd like to understand who I'm working with.

**Could you tell me your name and your role with the fire department?**

For example: "I'm Chief Smith from the Springfield Fire Department" or "I'm Lt. Johnson, we're a volunteer department in rural Ohio"."""
    st.session_state.messages.append({"role": "assistant", "content": welcome})

if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = datetime.now().strftime("%Y%m%d_%H%M%S")

if "user_info" not in st.session_state:
    st.session_state.user_info = {}

# 侧边栏
with st.sidebar:
    st.header("📋 Session Information")
    
    # 显示对话 ID
    st.caption(f"Session: {st.session_state.conversation_id}")
    
    # 显示用户信息
    if st.session_state.user_info:
        st.subheader("👤 User Profile")
        for key, value in st.session_state.user_info.items():
            st.text(f"{key}: {value}")
    
    st.markdown("---")
    
    # 对话统计
    st.subheader("💬 Conversation Stats")
    message_count = len(st.session_state.messages)
    st.metric("Messages", message_count)
    
    st.markdown("---")
    
    # 操作按钮
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
            # 准备下载数据
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
    
    # 生成报告按钮（当有足够对话时）
    if len(st.session_state.messages) > 10:
        st.markdown("---")
        if st.button("📋 Generate CRA Report", type="primary", use_container_width=True):
            with st.spinner("Generating comprehensive CRA report..."):
                try:
                    # 构建对话摘要
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
                    
                    # 显示报告
                    st.success("✅ Report generated!")
                    with st.expander("📄 View CRA Report", expanded=True):
                        st.markdown(report)
                    
                    # 下载报告
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
    
    # 帮助信息
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

# 主对话区域
st.subheader("💬 Consultation")

# 显示对话历史
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 聊天输入
if prompt := st.chat_input("Type your message here...", key="chat_input"):
    # 显示用户消息
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # 生成 AI 响应
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # 构建消息
                messages = [{"role": "system", "content": SYSTEM_PROMPT}]
                
                # 添加对话历史（最近20条以控制 token）
                for msg in st.session_state.messages[-20:]:
                    messages.append({"role": msg["role"], "content": msg["content"]})
                
                # 调用 OpenAI API（流式输出）
                stream = client.chat.completions.create(
                    model="gpt-4",
                    messages=messages,
                    stream=True,
                    temperature=0.7,
                    max_tokens=1000
                )
                
                # 流式显示响应
                response = st.write_stream(stream)
                
            except Exception as e:
                response = f"❌ Error: {str(e)}\n\nPlease check your API key and try again."
                st.error(response)
    
    # 保存响应到历史
    st.session_state.messages.append({"role": "assistant", "content": response})

# 页脚
st.markdown("---")
st.caption("🚒 AI-Enhanced Community Risk Assessment | Developed for Fire Service Professionals")
st.caption("💡 This bot educates while assessing - each conversation helps you learn systematic risk analysis methods")








import streamlit as st
from openai import OpenAI
import json
from datetime import datetime
import os

# 页面配置
st.set_page_config(
    page_title="🚒 Community Risk Assessment Bot",
    page_icon="🚒",
    layout="wide"
)

# 读取知识库文件
@st.cache_data
def load_knowledge_base():
    """加载消防知识库"""
    try:
        # 尝试从同目录读取
        if os.path.exists("fire_knowledge_base.md"):
            with open("fire_knowledge_base.md", "r", encoding="utf-8") as f:
                return f.read()
        else:
            return """
## Knowledge Base Not Found

Using built-in knowledge. For enhanced capabilities, upload fire_knowledge_base.md to the repository.

### Basic Knowledge:
- OFIRMS: Ohio Fire Information Reporting Management System
- SVI: Social Vulnerability Index from CDC
- NFIRS: National Fire Incident Reporting System
- Always consider: population demographics, housing age, response times, mutual aid capabilities
"""
    except Exception as e:
        st.sidebar.warning(f"Knowledge base loading issue: {str(e)}")
        return "Using built-in knowledge only."

# 加载知识库
KNOWLEDGE_BASE = load_knowledge_base()

# 消防专业系统提示词（集成知识库）
SYSTEM_PROMPT = f"""You are an AI consultant specializing in Community Risk Assessment (CRA) for fire departments. Your role is three-fold:

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

---

REFERENCE KNOWLEDGE BASE:

{KNOWLEDGE_BASE}

---

Use the knowledge base above to:
- Reference specific incidents and lessons learned
- Explain data sources and how to access them
- Highlight risk factor interconnections
- Suggest relevant questions based on community type
- Mention emerging trends when appropriate
- Cite recent research when relevant

CONVERSATION FLOW:
1. Start by learning about the user (name, role, department type, location, community characteristics)
2. Progressively build understanding through targeted questions
3. Share relevant examples from the knowledge base when appropriate
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
- 📚 Leveraging up-to-date fire service knowledge
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
    
    # 知识库状态
    if "fire_knowledge_base.md" in KNOWLEDGE_BASE or len(KNOWLEDGE_BASE) > 500:
        st.success("✅ Knowledge Base: Loaded")
        with st.expander("📚 View Knowledge Base Summary"):
            # 显示知识库摘要
            lines = KNOWLEDGE_BASE.split('\n')
            headers = [line for line in lines if line.startswith('##')]
            st.markdown("**Available Topics:**")
            for header in headers[:15]:  # 显示前15个主题
                st.caption(header)
    else:
        st.warning("⚠️ Knowledge Base: Basic mode")
        st.caption("Upload fire_knowledge_base.md for enhanced features")
    
    st.markdown("---")
    
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
                "message_count": len(st.session_state.messages),
                "knowledge_base_used": "Yes" if len(KNOWLEDGE_BASE) > 500 else "Basic"
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

Reference relevant information from the knowledge base when applicable. Make it actionable and professional."""

                    response = client.chat.completions.create(
                        model="gpt-4",
                        messages=[
                            {"role": "system", "content": f"You are an expert in creating Community Risk Assessment reports for fire departments. Use this knowledge base for context:\n\n{KNOWLEDGE_BASE[:3000]}"},
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
        - Bot uses knowledge base for insights
        
        **Features:**
        - Auto-saves conversation
        - Generates final CRA report
        - References recent incidents & research
        - Educational throughout
        """)
    
    # 知识库更新提示
    with st.expander("🔄 Update Knowledge Base"):
        st.markdown("""
        **To add new resources:**
        
        1. Edit `fire_knowledge_base.md` in GitHub
        2. Add new incidents, research, or data sources
        3. Commit changes
        4. App will auto-reload with new knowledge
        
        **What to include:**
        - Recent incident lessons learned
        - New research findings
        - Updated data sources
        - Emerging trends
        - Best practices from similar departments
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
st.caption("🚒 AI-Enhanced Community Risk Assessment | Powered by Knowledge Base")
st.caption("💡 This bot uses curated fire service knowledge to provide relevant, up-to-date guidance")

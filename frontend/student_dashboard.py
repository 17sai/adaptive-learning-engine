"""
Student Learning Dashboard
Streamlit frontend for students to view their personalized learning path
and real-time recommendations.
"""

import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import os

# Page config
st.set_page_config(
    page_title="My Learning Path",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api")

# Check API connectivity
@st.cache_resource
def check_api_health():
    try:
        response = requests.get(f"{API_BASE_URL.replace('/api', '')}/health", timeout=2)
        return response.status_code == 200
    except:
        return False

st.title("📚 My Adaptive Learning Path")
st.markdown("Your personalized journey to mastery")

# Check API health
if not check_api_health():
    st.error("⚠️ Cannot connect to the backend API!")
    st.info(
        f"\n**Troubleshooting:**\n"
        f"1. Ensure backend is running: `python -m uvicorn app.main:app --reload`\n"
        f"2. Expected API URL: {API_BASE_URL}\n"
        f"3. If backend runs on different host, set: `API_BASE_URL=http://your-host:8000/api`\n"
        f"4. Check firewall/network settings"
    )
    st.stop()

# Sidebar - Student Selection
with st.sidebar:
    st.header("👤 Profile")
    student_id = st.number_input("Student ID", min_value=1, value=1)
    
    if st.button("🔄 Refresh Data"):
        st.rerun()


# Main layout - 3 columns
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    st.header("Current Recommendation")
    try:
        response = requests.get(f"{API_BASE_URL}/students/{student_id}/recommendation")
        if response.status_code == 200:
            rec = response.json()
            
            # Display recommendation
            st.success(f"**Next Topic:** {rec.get('recommended_topic_id', 'N/A')}")
            st.info(f"**Difficulty:** {'⭐' * rec.get('recommended_difficulty', 1)}")
            st.metric("Confidence", f"{rec.get('confidence', 0):.1%}")
            
            # Explanation (Why am I learning this?)
            with st.expander("Why am I learning this?"):
                st.write(rec.get('explanation', 'Loading explanation...'))
            
            # Alternative topics
            if rec.get('alternative_topics'):
                st.write("**Alternative Topics:**")
                for alt in rec['alternative_topics']:
                    st.write(f"- {alt.get('name', 'Unknown')} (score: {alt.get('score', 0):.2f})")
        else:
            st.error("Could not fetch recommendation")
    except Exception as e:
        st.error(f"Error: {str(e)}")

with col2:
    st.header("Statistics")
    try:
        response = requests.get(f"{API_BASE_URL}/metrics/student/{student_id}")
        if response.status_code == 200:
            metrics = response.json()
            st.metric("Assessments Done", metrics.get('assessments_completed', 0))
            st.metric("Learning Velocity", f"{metrics.get('learning_velocity', 0):.2f}")
    except:
        pass

with col3:
    st.header("Progress")
    st.metric("Overall Progress", "45%")

# Knowledge State Visualization
st.header("📊 Your Knowledge Map")

try:
    response = requests.get(f"{API_BASE_URL}/students/{student_id}/knowledge-state")
    if response.status_code == 200:
        knowledge = response.json().get('knowledge_state', {})
        
        if knowledge:
            # Create visualization
            topics = []
            mastery = []
            for topic_id, data in knowledge.items():
                topics.append(f"Topic {topic_id}")
                mastery.append(data.get('mastery_level', 0) * 100)
            
            fig = go.Figure(data=[
                go.Bar(
                    x=topics,
                    y=mastery,
                    marker_color=['#d62728' if m < 40 else '#ff7f0e' if m < 70 else '#2ca02c' 
                                 for m in mastery],
                    showlegend=False
                )
            ])
            fig.update_layout(
                title="Mastery Level by Topic",
                xaxis_title="Topics",
                yaxis_title="Mastery %",
                hovermode="x unified"
            )
            st.plotly_chart(fig, use_container_width=True)
except Exception as e:
    st.error(f"Error loading knowledge state: {e}")

# Learning Path - Visual Path Display with Full Names
st.header("🗺️ Your Data Science Learning Path")

try:
    response = requests.get(f"{API_BASE_URL}/students/{student_id}/learning-path")
    if response.status_code == 200:
        path = response.json()
        
        current_topic_id = path.get('current_topic_id')
        planned_topics = path.get('planned_topics', [])
        completed_topics = path.get('completed_topics', [])
        
        # Data Science Path with full names
        path_order = {
            1: ("Python Fundamentals", "🐍"),
            2: ("NumPy", "📊"),
            3: ("Pandas", "🐼"),
            4: ("Data Visualization", "📈"),
            5: ("Machine Learning", "🤖"),
            6: ("Deep Learning", "🧠"),
            7: ("Generative AI", "✨")
        }
        
        # Build visual path with names and clear current indicator
        st.subheader("📍 Your Learning Journey:")
        st.write("")
        
        # Create path display in rows
        for topic_id, (topic_name, emoji) in path_order.items():
            # Determine status
            if topic_id in completed_topics:
                status_icon = "✅"
                status_text = "COMPLETED"
                status_color = "green"
            elif topic_id == current_topic_id:
                status_icon = "🎯"
                status_text = "YOU ARE HERE"
                status_color = "blue"
            elif topic_id in planned_topics:
                status_icon = "⬜"
                status_text = "UPCOMING"
                status_color = "orange"
            else:
                status_icon = "🔒"
                status_text = "LOCKED"
                status_color = "gray"
            
            # Create visual row with current topic highlighted
            if topic_id == current_topic_id:
                # Highlight current topic with special styling
                st.markdown(f"""
                <div style="background-color: #e3f2fd; border-left: 5px solid #2196F3; padding: 15px; margin: 10px 0; border-radius: 5px;">
                    <strong>{emoji} {topic_id}. {topic_name}</strong>
                    <span style="float: right; color: #2196F3; font-weight: bold;"> {status_icon} {status_text}</span>
                </div>
                """, unsafe_allow_html=True)
            else:
                # Regular styling for other topics
                color_map = {
                    "green": "#c8e6c9",
                    "orange": "#ffe0b2",
                    "gray": "#e0e0e0",
                    "blue": "#e3f2fd"
                }
                st.markdown(f"""
                <div style="background-color: {color_map[status_color]}; padding: 12px; margin: 5px 0; border-radius: 3px; border-left: 4px solid #999;">
                    {emoji} {topic_id}. {topic_name}
                    <span style="float: right; color: #666;"> {status_icon} {status_text}</span>
                </div>
                """, unsafe_allow_html=True)
        
        st.write("")
        st.markdown("---")
        
        # Path Statistics
        col_stats1, col_stats2, col_stats3, col_stats4 = st.columns(4)
        
        current_name = path_order.get(current_topic_id, ("Unknown", "❓"))[0]
        with col_stats1:
            st.metric("📍 Current Topic", current_name)
        
        with col_stats2:
            st.metric("✅ Completed", len(completed_topics))
        
        with col_stats3:
            remaining = len([t for t in planned_topics if t not in completed_topics and t != current_topic_id])
            st.metric("⬜ Remaining", remaining)
        
        with col_stats4:
            progress_pct = (len(completed_topics) / 7 * 100) if len(path_order) > 0 else 0
            st.metric("📈 Progress", f"{progress_pct:.0f}%")
        
        # Progress bar
        progress_val = min((len(completed_topics) + 1) / 7, 1.0)  # +1 for current topic
        st.progress(progress_val)
        
        # Summary
        st.markdown("---")
        st.subheader("📋 Your Path Summary")
        
        col_summary1, col_summary2 = st.columns(2)
        
        with col_summary1:
            st.write("### ✅ Completed")
            if completed_topics:
                for topic_id in sorted(completed_topics):
                    topic_name = path_order.get(topic_id, (f"Topic {topic_id}", ""))[0]
                    emoji = path_order.get(topic_id, ("", "🔹"))[1]
                    st.success(f"{emoji} {topic_name}")
            else:
                st.info("*No topics completed yet. Start with Python Fundamentals!*")
        
        with col_summary2:
            st.write("### 🎯 Next Steps")
            st.write(f"**Currently Learning:** {current_name}")
            st.write(f"Difficulty: {'⭐' * path.get('current_difficulty', 1)}")
            
            upcoming = sorted([t for t in planned_topics if t not in completed_topics and t != current_topic_id])
            if upcoming:
                st.write(f"\n**After This, Learn:**")
                for topic_id in upcoming[:3]:  # Show next 3
                    topic_name = path_order.get(topic_id, (f"Topic {topic_id}", ""))[0]
                    emoji = path_order.get(topic_id, ("", "🔹"))[1]
                    st.info(f"{emoji} {topic_name}")
        
        if path.get('estimated_completion_date'):
            st.info(f"📅 **Estimated Completion:** {path['estimated_completion_date']}")
        
except Exception as e:
    st.error(f"Error loading learning path: {e}")

st.markdown("---")

# Weak Areas
st.header("⚠️ Areas to Strengthen")

try:
    response = requests.get(f"{API_BASE_URL}/students/{student_id}/weak-areas")
    if response.status_code == 200:
        weak_areas = response.json().get('weak_areas', [])
        
        if weak_areas:
            df = pd.DataFrame(weak_areas)
            if 'mastery_level' in df.columns:
                fig = px.bar(
                    df,
                    x='topic_name',
                    y='mastery_level',
                    title="Topics Needing Review",
                    color='mastery_level',
                    color_continuous_scale=['#d62728', '#ff7f0e', '#2ca02c']
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.success("Great! All your weak areas are above threshold.")
except Exception as e:
    st.error(f"Error loading weak areas: {e}")

st.markdown("---")
st.caption("Last updated: " + datetime.now().strftime("%H:%M:%S"))

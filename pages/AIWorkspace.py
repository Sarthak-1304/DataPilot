import streamlit as st
import pandas as pd
import json
import datetime
import importlib

import ai.gemini_manager
importlib.reload(ai.gemini_manager)
from ai.gemini_manager import is_gemini_configured, generate_response_stream

import ai.prompt_manager
importlib.reload(ai.prompt_manager)
from ai.prompt_manager import PromptManager

import ai.intent_router
importlib.reload(ai.intent_router)
from ai.intent_router import IntentRouter

import ai.dataframe_agent
importlib.reload(ai.dataframe_agent)
from ai.dataframe_agent import DataFrameAgent

import ai.insight_agent
importlib.reload(ai.insight_agent)
from ai.insight_agent import InsightAgent

import ai.report_agent
importlib.reload(ai.report_agent)
from ai.report_agent import ReportAgent

import ai.chat_manager
importlib.reload(ai.chat_manager)
from ai.chat_manager import get_chat_history, save_chat_message, clear_chat_history

import plotly.express as px
import plotly.graph_objects as go
from fpdf import FPDF

def render_ai_workspace():
    """Renders the AI Workspace chat and analytical assistant page."""
    # Ensure project session is active
    project_id = st.session_state.get("project_id")
    if not project_id:
        st.warning("⚠️ No active project found. Please select or create a project first.")
        return

    # Choose active dataframe (prefer cleaned_df if available)
    df = st.session_state.get("cleaned_df")
    df_label = "Cleaned Dataset"
    if df is None:
        df = st.session_state.get("original_df")
        df_label = "Original Dataset"

    if df is None:
        st.warning("⚠️ No dataset loaded in this project. Please upload data first.")
        return

    # Initialize chat history from SQLite DB
    if "chat_history" not in st.session_state or st.session_state.get("current_project_history_loaded") != project_id:
        st.session_state["chat_history"] = get_chat_history(project_id)
        st.session_state["current_project_history_loaded"] = project_id

    # Title header
    st.markdown(
        f"""
        <div class="top-header">
            <h2>🤖 AI Workspace</h2>
            <p>Ask questions about your dataset using AI. Analyzing <strong>{df_label}</strong> ({df.shape[0]:,} rows, {df.shape[1]:,} columns).</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not is_gemini_configured():
        st.info("💡 **Welcome to the AI Workspace!**\n\nTo begin chatting with your dataset, please configure your AI API Key in `.streamlit/secrets.toml`:\n\n```toml\nGEMINI_API_KEY = \"your_actual_api_key_here\"\n```")
        return
    # Inject Custom Chat Styles
    st.markdown("""
        <style>
        /* Immersive chat bubble styles */
        div[data-testid="chatMessage"] {
            background-color: var(--card-bg) !important;
            border: 1px solid var(--card-border) !important;
            border-radius: 16px !important;
            padding: 1.1rem 1.5rem !important;
            margin-bottom: 0.8rem !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.01) !important;
            transition: all 0.2s ease !important;
        }
        div[data-testid="chatMessage"]:hover {
            box-shadow: 0 6px 18px rgba(0,0,0,0.03) !important;
        }
        
        /* User Bubble styling */
        div[data-testid="chatMessage"]:has(div[data-testid="chatMessageContent-user"]) {
            border-left: 4px solid var(--primary-blue) !important;
            background: rgba(59, 130, 246, 0.015) !important;
        }
        
        /* Assistant Bubble styling */
        div[data-testid="chatMessage"]:has(div[data-testid="chatMessageContent-assistant"]) {
            border-left: 4px solid var(--info-purple) !important;
            background: linear-gradient(135deg, rgba(139, 92, 246, 0.015) 0%, rgba(99, 102, 241, 0.015) 100%) !important;
        }

        /* Clean borders on sidebar control panels */
        .export-card {
            background: var(--card-bg) !important;
            border: 1px solid var(--card-border) !important;
            border-radius: 14px !important;
            padding: 1.2rem !important;
            margin-bottom: 0.8rem !important;
            box-shadow: 0 4px 10px rgba(0,0,0,0.02) !important;
        }
        
        .export-card h4 {
            margin: 0 0 0.8rem 0 !important;
            font-weight: 700 !important;
            color: var(--text-primary) !important;
            font-size: 0.95rem !important;
            display: flex !important;
            align-items: center !important;
            gap: 0.4rem !important;
            border: none !important;
            padding: 0 !important;
        }

        /* AI Suggestion Cards */
        .ai-suggest-card {
            background: var(--card-bg) !important;
            border: 1px solid var(--card-border) !important;
            border-radius: 16px !important;
            padding: 1.1rem !important;
            min-height: 155px !important;
            display: flex !important;
            flex-direction: column !important;
            justify-content: space-between !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.02) !important;
            transition: all 0.25s ease !important;
            position: relative !important;
            overflow: hidden !important;
            margin-bottom: 0.8rem !important;
        }
        
        .ai-suggest-card:hover {
            transform: translateY(-4px) !important;
            box-shadow: 0 8px 24px rgba(0,0,0,0.06) !important;
        }
        .ai-suggest-card.blue:hover { border-color: #3B82F6 !important; box-shadow: 0 8px 24px rgba(59, 130, 246, 0.12) !important; }
        .ai-suggest-card.purple:hover { border-color: #8B5CF6 !important; box-shadow: 0 8px 24px rgba(139, 92, 246, 0.12) !important; }
        .ai-suggest-card.green:hover { border-color: #10B981 !important; box-shadow: 0 8px 24px rgba(16, 185, 129, 0.12) !important; }
        .ai-suggest-card.red:hover { border-color: #EF4444 !important; box-shadow: 0 8px 24px rgba(239, 68, 68, 0.12) !important; }
        </style>
    """, unsafe_allow_html=True)

    # Layout: two columns
    chat_col, side_col = st.columns([7.2, 2.8])

    # Left: Chat Interface
    with chat_col:
        has_history = len(st.session_state["chat_history"]) > 0
        clicked_prompt = None

        if not has_history:
            # Render the AI Hero greeting
            st.markdown("""
                <div style="margin-top: 1.5rem; margin-bottom: 2.2rem; text-align: left; padding-left: 0.5rem;">
                    <h1 style="
                        font-size: 3.0rem;
                        font-weight: 800;
                        background: linear-gradient(135deg, #3B82F6 10%, #8B5CF6 50%, #EC4899 90%);
                        -webkit-background-clip: text;
                        -webkit-text-fill-color: transparent;
                        margin: 0;
                        line-height: 1.1;
                        letter-spacing: -0.04em;
                        border: none;
                        padding: 0;
                    ">
                        Hello, Analyst.
                    </h1>
                    <h2 style="
                        font-size: 1.8rem;
                        font-weight: 700;
                        color: var(--text-secondary);
                        margin: 0.4rem 0 0 0;
                        line-height: 1.2;
                        letter-spacing: -0.03em;
                        border: none;
                        padding: 0;
                        opacity: 0.85;
                    ">
                        How can I help you explore your dataset today?
                    </h2>
                </div>
            """, unsafe_allow_html=True)

            # Suggestion cards
            suggestions = [
                ("Summarize", "Summarize this dataset", "Get statistics, shape, null summaries, and column profiles.", "📊", "blue"),
                ("Show Trends", "Show important trends and correlations", "Identify key patterns, relationships, and distributions.", "📈", "purple"),
                ("Clean Advice", "Which columns need cleaning and what are the recommendations?", "Find structural issues, outliers, and type corrections.", "🧹", "green"),
                ("Business Insights", "Generate business insights and actionable suggestions", "Extract strategic recommendations and findings.", "💼", "red")
            ]
            
            temp_cols = st.columns(4, gap="small")
            for col, (label, prompt, desc, icon, color_class) in zip(temp_cols, suggestions):
                with col:
                    st.markdown(f"""
                        <div class="ai-suggest-card {color_class}">
                            <div>
                                <span style="font-size: 1.4rem; display: block; margin-bottom: 0.5rem;">{icon}</span>
                                <div style="font-weight: 700; font-size: 0.85rem; color: var(--text-primary); margin-bottom: 0.2rem;">{label}</div>
                                <div style="font-size: 0.70rem; color: var(--text-muted); line-height: 1.4;">{desc}</div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    if st.button("🚀 Ask AI", key=f"run_action_{label}", use_container_width=True):
                        clicked_prompt = prompt

        # Render chat messages
        chat_container = st.container()
        with chat_container:
            for msg in st.session_state["chat_history"]:
                role = msg["role"]
                content = msg["content"]
                chart_data = msg.get("chart_data")
                
                with st.chat_message(role):
                    st.markdown(content)
                    if chart_data and isinstance(chart_data, dict) and chart_data.get("code"):
                        try:
                            # Re-run chart code locally to render
                            local_vars = {"df": df, "px": px, "go": go, "fig": None}
                            exec(chart_data["code"], {}, local_vars)
                            fig = local_vars.get("fig")
                            if fig:
                                st.plotly_chart(fig, use_container_width=True)
                        except Exception as e:
                            st.caption(f"Could not render chart: {e}")

        # Input handling
        user_input = st.chat_input("Ask a question about your dataset...")
        if clicked_prompt:
            user_input = clicked_prompt

        if user_input:
            auto_charts_enabled = st.session_state.get("pref_auto_charts", True)
            save_chat_enabled = st.session_state.get("pref_save_chat", True)

            # 1. Display User Message
            with st.chat_message("user"):
                st.markdown(user_input)
            
            # Save User Message to History and DB (if enabled)
            if save_chat_enabled:
                save_chat_message(project_id, "user", user_input)
            st.session_state["chat_history"].append({"role": "user", "content": user_input, "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")})

            # 2. Process Assistant Response
            with st.chat_message("assistant"):
                # Detect Intent
                intent = IntentRouter.detect_intent(user_input)
                st.caption(f"🎯 *Intent detected: {intent.upper()}*")
                
                # Execute pre-computation via Pandas Agent if necessary
                calc_result = None
                chart_code = None
                
                if intent in ["aggregation", "summary", "filtering"]:
                    with st.spinner("🤖 Pre-calculating statistics locally..."):
                        calc_result = DataFrameAgent.query_with_pandas(user_input, df)
                elif intent == "chart" or (auto_charts_enabled and any(kw in user_input.lower() for kw in ["chart", "plot", "graph", "histogram", "scatter", "box", "bar", "visualize"])):
                    if auto_charts_enabled:
                        with st.spinner("📊 Building visualization specs..."):
                            if hasattr(DataFrameAgent, "generate_plotly_code"):
                                chart_code = DataFrameAgent.generate_plotly_code(user_input, df)
                
                # Setup prompt & call AI (Stream response)
                system_prompt = PromptManager.get_system_prompt()
                final_prompt = PromptManager.construct_analysis_prompt(user_input, df, calc_result, intent)
                
                response_placeholder = st.empty()
                full_response = ""
                
                # Stream the response chunks
                for chunk in generate_response_stream(final_prompt, system_instruction=system_prompt):
                    full_response += chunk
                    response_placeholder.markdown(full_response + "▌")
                response_placeholder.markdown(full_response)
                
                # Render and save chart if requested & enabled
                chart_save_data = None
                if auto_charts_enabled and chart_code:
                    try:
                        local_vars = {"df": df, "px": px, "go": go, "fig": None}
                        exec(chart_code, {}, local_vars)
                        fig = local_vars.get("fig")
                        if fig:
                            st.plotly_chart(fig, use_container_width=True)
                            chart_save_data = {"code": chart_code}
                    except Exception as e:
                        st.caption(f"Failed to execute plotly script: {e}")

                # Save assistant response to SQLite (if enabled) and session state
                if save_chat_enabled:
                    save_chat_message(project_id, "assistant", full_response, chart_save_data)
                st.session_state["chat_history"].append({
                    "role": "assistant",
                    "content": full_response,
                    "chart_data": chart_save_data,
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                
                st.rerun()

    # Right: Controls, Insights, Recommendations, and Exporting
    with side_col:
        st.markdown(
            """
            <div class="export-card">
                <h4>📥 Export Conversation</h4>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Build export payloads
        chat_logs = st.session_state["chat_history"]
        
        # 1. TXT export
        txt_content = ""
        for msg in chat_logs:
            txt_content += f"[{msg['role'].upper()} - {msg.get('timestamp', '')}]\n{msg['content']}\n\n"
            
        # 2. Markdown export
        md_content = "# Data Pilot AI Conversation Log\n\n"
        for msg in chat_logs:
            md_content += f"### **{msg['role'].title()}** ({msg.get('timestamp', '')})\n{msg['content']}\n\n"
            
        # 3. JSON export
        json_content = json.dumps(chat_logs, indent=4)
        
        # 4. PDF export
        def create_pdf(history):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, txt="Data Pilot - AI Workspace Chat Export", ln=1, align="C")
            pdf.ln(10)
            
            for msg in history:
                role = "User" if msg["role"] == "user" else "AI Assistant"
                content = msg["content"].encode('latin1', 'replace').decode('latin1')
                pdf.set_font("Arial", 'B', 10)
                pdf.cell(200, 8, txt=f"{role} ({msg.get('timestamp', '')}):", ln=1)
                pdf.set_font("Arial", size=9)
                pdf.multi_cell(0, 5, txt=content)
                pdf.ln(5)
            return bytes(pdf.output())

        # Download buttons row
        st.download_button("📄 Export PDF", data=create_pdf(chat_logs) if chat_logs else b"", file_name=f"chat_export_{project_id}.pdf", mime="application/pdf", use_container_width=True)
        st.download_button("📝 Export Markdown", data=md_content, file_name=f"chat_export_{project_id}.md", mime="text/markdown", use_container_width=True)
        st.download_button("🔤 Export TXT", data=txt_content, file_name=f"chat_export_{project_id}.txt", mime="text/plain", use_container_width=True)
        st.download_button("⚙️ Export JSON", data=json_content, file_name=f"chat_export_{project_id}.json", mime="application/json", use_container_width=True)

        if st.button("🗑️ Clear Chat History", type="secondary", use_container_width=True):
            clear_chat_history(project_id)
            st.session_state["chat_history"] = []
            st.toast("🗑️ Chat history cleared!")
            st.rerun()

        # Dynamic suggestions block
        st.markdown(
            """
            <div class="export-card" style="margin-top: 1rem;">
                <h4>💡 Automated Insights</h4>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Recommendations
        recs = InsightAgent.get_cleaning_recommendations(df)
        st.markdown("**Cleaning Advice:**")
        for rec in recs[:3]:
            st.markdown(f"- {rec}")
            
        # Suggested Visuals
        charts = InsightAgent.suggest_charts(df)
        if charts:
            st.markdown("**Visual Recommendations:**")
            for chart in charts[:2]:
                st.markdown(f"- **{chart['type']}**: {chart['desc']}")

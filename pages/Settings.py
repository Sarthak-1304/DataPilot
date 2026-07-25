"""
Settings Page
=============
App configuration, theme preferences, AI provider diagnostics, and system information.
"""

import streamlit as st
import textwrap
import time
import sys
import pandas as pd
import platform
from utils.helpers import get_memory_usage


def render_html(html_str):
    """Renders HTML by dedenting strings to prevent Streamlit Markdown from treating indented text as code blocks."""
    dedented = textwrap.dedent(html_str)
    cleaned = "\n".join([line for line in dedented.splitlines() if line.strip()])
    st.markdown(cleaned, unsafe_allow_html=True)


def render_settings():
    """Render the comprehensive Settings & AI Configuration page."""
    render_html("""
        <div class="top-header">
            <h2>⚙️ Settings & AI Configuration</h2>
            <p>Manage AI provider connection, engine diagnostics, workspace preferences, and application parameters.</p>
        </div>
    """)

    # ---------------------------------------------------------------------------
    # AI Engine Diagnostics & Status
    # ---------------------------------------------------------------------------
    ai_configured = False
    model_name = "Gemini 2.5 Flash"
    api_key = ""
    masked_key = "Not Configured"

    try:
        from ai.gemini_manager import is_gemini_configured, get_best_available_model, get_gemini_api_key, init_gemini
        ai_configured = is_gemini_configured()
        api_key = get_gemini_api_key()
        if api_key:
            clean_key = api_key.strip()
            if len(clean_key) > 8:
                masked_key = f"{clean_key[:4]}...{clean_key[-4:]}"
            else:
                masked_key = "••••••••"
        if ai_configured and init_gemini():
            model_name = get_best_available_model().replace("models/", "")
    except Exception:
        pass

    conn_status = "Connected" if ai_configured else "Not Connected"
    conn_color = "#10B981" if ai_configured else "#EF4444"
    conn_bg = "rgba(16, 185, 129, 0.08)" if ai_configured else "rgba(239, 68, 68, 0.08)"
    conn_border = "rgba(16, 185, 129, 0.25)" if ai_configured else "rgba(239, 68, 68, 0.25)"
    status_icon = "🟢" if ai_configured else "🔴"

    # AI Banner Card
    render_html(f"""
        <div style="
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 4px 20px rgba(0,0,0,0.03);
        ">
            <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 1rem; margin-bottom: 1.2rem;">
                <div>
                    <h3 style="margin: 0; font-size: 1.2rem; font-weight: 800; color: var(--text-primary); border: none; padding: 0; display: flex; align-items: center; gap: 0.5rem;">
                        🤖 AI Provider Diagnostics
                    </h3>
                    <p style="margin: 0.2rem 0 0 0; font-size: 0.82rem; color: var(--text-muted);">
                        Backend AI engine parameters and real-time connectivity status.
                    </p>
                </div>
                <div style="
                    background: {conn_bg};
                    border: 1px solid {conn_border};
                    color: {conn_color};
                    font-weight: 700;
                    font-size: 0.85rem;
                    padding: 0.4rem 1rem;
                    border-radius: 100px;
                    display: flex;
                    align-items: center;
                    gap: 0.4rem;
                ">
                    <span>{status_icon}</span> {conn_status}
                </div>
            </div>

            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
                <div style="background: var(--app-bg); padding: 0.9rem; border-radius: 10px; border: 1px solid var(--card-border);">
                    <span style="font-size: 0.72rem; color: var(--text-secondary); text-transform: uppercase; font-weight: 600; display: block; margin-bottom: 0.2rem;">Provider</span>
                    <span style="font-size: 0.92rem; font-weight: 700; color: var(--text-primary);">Google Gemini</span>
                </div>
                <div style="background: var(--app-bg); padding: 0.9rem; border-radius: 10px; border: 1px solid var(--card-border);">
                    <span style="font-size: 0.72rem; color: var(--text-secondary); text-transform: uppercase; font-weight: 600; display: block; margin-bottom: 0.2rem;">Model</span>
                    <span style="font-size: 0.92rem; font-weight: 700; color: #8B5CF6;">{model_name}</span>
                </div>
                <div style="background: var(--app-bg); padding: 0.9rem; border-radius: 10px; border: 1px solid var(--card-border);">
                    <span style="font-size: 0.72rem; color: var(--text-secondary); text-transform: uppercase; font-weight: 600; display: block; margin-bottom: 0.2rem;">API Key Status</span>
                    <span style="font-size: 0.92rem; font-weight: 700; color: var(--text-primary); font-family: monospace;">{masked_key}</span>
                </div>
                <div style="background: var(--app-bg); padding: 0.9rem; border-radius: 10px; border: 1px solid var(--card-border);">
                    <span style="font-size: 0.72rem; color: var(--text-secondary); text-transform: uppercase; font-weight: 600; display: block; margin-bottom: 0.2rem;">Key Location</span>
                    <span style="font-size: 0.92rem; font-weight: 700; color: var(--text-primary);">.streamlit/secrets.toml</span>
                </div>
            </div>
        </div>
    """)

    # Test AI Connection Button Row
    col_test, col_info = st.columns([1, 2])
    with col_test:
        if st.button("⚡ Test AI Connection", type="primary", use_container_width=True):
            if not ai_configured:
                st.error("❌ Cannot test connection: API key is not configured.")
            else:
                with st.spinner("Pinging AI Service..."):
                    start_time = time.time()
                    try:
                        from ai.gemini_manager import generate_response_stream
                        response_chunks = []
                        for chunk in generate_response_stream("Ping test. Reply with 'OK'."):
                            response_chunks.append(chunk)
                        elapsed = time.time() - start_time
                        full_res = "".join(response_chunks)
                        if "❌" in full_res:
                            st.error(f"Test Failed: {full_res}")
                        else:
                            st.success(f"✅ Connection Test Passed! Latency: **{elapsed:.2f}s**")
                    except Exception as e:
                        st.error(f"❌ Connection Error: {str(e)}")

    with col_info:
        render_html("""
            <div style="font-size: 0.78rem; color: var(--text-muted); padding-top: 0.5rem;">
                💡 <b>Developer Note:</b> The AI engine supports streaming responses, automated code execution, and statistical context generation.
            </div>
        """)

    render_html("<div style='margin-bottom: 1.5rem;'></div>")

    # ---------------------------------------------------------------------------
    # 2 Column Layout: Session API Key & Capabilities / Preferences
    # ---------------------------------------------------------------------------
    col_left, col_right = st.columns(2, gap="large")

    with col_left:
        # Custom API Key Input Card
        render_html("""
            <div class="content-card">
                <h3 style="margin-top: 0; font-size: 1.05rem; font-weight: 700; color: var(--text-primary); border: none; padding: 0;">
                    🔑 Session API Key Override
                </h3>
                <p style="font-size: 0.8rem; color: var(--text-muted); margin: 0.3rem 0 0.8rem 0;">
                    Optionally supply a temporary API key for this session. Overrides <code>secrets.toml</code> until page reload.
                </p>
            </div>
        """)

        # Callback functions for button actions (runs BEFORE widget instantiation)
        def apply_api_key_cb():
            val = st.session_state.get("input_session_key", "").strip()
            if val:
                st.session_state["user_gemini_api_key"] = val
                st.session_state["key_toast_msg"] = "✅ Session API key updated! Overriding secrets.toml"
            else:
                st.session_state["key_toast_msg"] = "⚠️ Please enter an API key first."

        def clear_api_key_cb():
            st.session_state["user_gemini_api_key"] = ""
            st.session_state["input_session_key"] = ""
            st.session_state["key_toast_msg"] = "🗑️ Session key cleared. Reverting to secrets.toml"

        if "input_session_key" not in st.session_state:
            st.session_state["input_session_key"] = st.session_state.get("user_gemini_api_key", "")

        if st.session_state.get("key_toast_msg"):
            st.toast(st.session_state["key_toast_msg"])
            st.session_state["key_toast_msg"] = ""

        st.text_input(
            "API Key",
            type="password",
            placeholder="AIzaSy...",
            help="Enter a valid API key to enable AI features.",
            label_visibility="collapsed",
            key="input_session_key",
        )

        c1, c2 = st.columns(2)
        with c1:
            st.button("💾 Apply Key", use_container_width=True, on_click=apply_api_key_cb)
        with c2:
            st.button("🗑️ Clear Key", type="secondary", use_container_width=True, on_click=clear_api_key_cb)



    with col_right:
        # Supported AI Capabilities
        render_html("""
            <div class="content-card">
                <h3 style="margin-top: 0; font-size: 1.05rem; font-weight: 700; color: var(--text-primary); border: none; padding: 0;">
                    ⚡ Supported AI Capabilities
                </h3>
                <p style="font-size: 0.8rem; color: var(--text-muted); margin: 0.3rem 0 1rem 0;">
                    Active feature capabilities provided by the integrated AI engine.
                </p>
                
                <div style="display: flex; flex-direction: column; gap: 0.75rem;">
                    <div style="display: flex; align-items: center; gap: 0.6rem; font-size: 0.82rem; color: var(--text-primary);">
                        <span style="background: rgba(99, 102, 241, 0.15); color: #6366F1; padding: 0.3rem 0.6rem; border-radius: 6px; font-weight: 700;">💬</span>
                        <div>
                            <strong>Natural Data Chat</strong>
                            <div style="font-size: 0.72rem; color: var(--text-muted);">Query columns, ask questions, and explore patterns in plain language.</div>
                        </div>
                    </div>
                    
                    <div style="display: flex; align-items: center; gap: 0.6rem; font-size: 0.82rem; color: var(--text-primary);">
                        <span style="background: rgba(16, 185, 129, 0.15); color: #10B981; padding: 0.3rem 0.6rem; border-radius: 6px; font-weight: 700;">📊</span>
                        <div>
                            <strong>Plotly Visualization Generator</strong>
                            <div style="font-size: 0.72rem; color: var(--text-muted);">Generates interactive chart specifications dynamically.</div>
                        </div>
                    </div>

                    <div style="display: flex; align-items: center; gap: 0.6rem; font-size: 0.82rem; color: var(--text-primary);">
                        <span style="background: rgba(245, 158, 11, 0.15); color: #F59E0B; padding: 0.3rem 0.6rem; border-radius: 6px; font-weight: 700;">🧹</span>
                        <div>
                            <strong>Smart Cleaning Advisor</strong>
                            <div style="font-size: 0.72rem; color: var(--text-muted);">Recommends missing value, outlier, and duplicate handling strategies.</div>
                        </div>
                    </div>

                    <div style="display: flex; align-items: center; gap: 0.6rem; font-size: 0.82rem; color: var(--text-primary);">
                        <span style="background: rgba(139, 92, 246, 0.15); color: #8B5CF6; padding: 0.3rem 0.6rem; border-radius: 6px; font-weight: 700;">📈</span>
                        <div>
                            <strong>Executive Report Writer</strong>
                            <div style="font-size: 0.72rem; color: var(--text-muted);">Generates structured markdown summaries and business findings.</div>
                        </div>
                    </div>
                </div>
            </div>
        """)

        render_html("<div style='margin-bottom: 1.5rem;'></div>")

        # System & Environment Card
        mem_str = get_memory_usage(st.session_state.get("original_df")) if st.session_state.get("original_df") is not None else "0 KB"
        render_html(f"""
            <div class="content-card">
                <h3 style="margin-top: 0; font-size: 1.05rem; font-weight: 700; color: var(--text-primary); border: none; padding: 0;">
                    💻 System & Environment
                </h3>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.8rem; font-size: 0.8rem; margin-top: 0.8rem;">
                    <div>
                        <span style="color: var(--text-muted); display: block;">Data Pilot Version</span>
                        <strong style="color: var(--text-primary);">v1.0.0</strong>
                    </div>
                    <div>
                        <span style="color: var(--text-muted); display: block;">Python Version</span>
                        <strong style="color: var(--text-primary);">{platform.python_version()}</strong>
                    </div>
                    <div>
                        <span style="color: var(--text-muted); display: block;">Streamlit Version</span>
                        <strong style="color: var(--text-primary);">{st.__version__}</strong>
                    </div>
                    <div>
                        <span style="color: var(--text-muted); display: block;">Pandas Version</span>
                        <strong style="color: var(--text-primary);">{pd.__version__}</strong>
                    </div>
                    <div>
                        <span style="color: var(--text-muted); display: block;">OS Platform</span>
                        <strong style="color: var(--text-primary);">{platform.system()} {platform.release()}</strong>
                    </div>
                    <div>
                        <span style="color: var(--text-muted); display: block;">Dataset Memory</span>
                        <strong style="color: var(--text-primary);">{mem_str}</strong>
                    </div>
                </div>
            </div>
        """)

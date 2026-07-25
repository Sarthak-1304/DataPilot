"""
Projects and Versioning Page
============================
Provides Project Dashboard, Storage Analytics, and interactive Version Timeline.
"""

import streamlit as st
import pandas as pd
import datetime
import os
import json
from utils.sync_manager import (
    list_projects, load_project, delete_project,
    duplicate_project, create_snapshot, restore_snapshot,
    get_snapshots_timeline, PROJECTS_DIR, save_project,
    update_project_pinned, update_project_name
)
from utils.helpers import format_file_size
import textwrap

def render_html(html_str: str):
    """Renders HTML by stripping blank lines to prevent Streamlit Markdown splitting."""
    dedented = textwrap.dedent(html_str)
    cleaned = "\n".join([line for line in dedented.splitlines() if line.strip()])
    st.markdown(cleaned, unsafe_allow_html=True)

# ─── Alert / Status Helper ──────────────────────────────────────────
def _alert(text: str, level: str = "success"):
    bg = "rgba(16, 185, 129, 0.08)" if level == "success" else "rgba(239, 68, 68, 0.08)"
    border = "#10B981" if level == "success" else "#EF4444"
    icon = "✅" if level == "success" else "❌"
    st.markdown(f"""
    <div style="background-color: {bg}; border: 1px solid {border}; padding: 0.65rem 0.95rem; border-radius: 8px; font-size: 0.85rem; margin-bottom: 1rem; font-weight: 500; display: flex; align-items: center; gap: 0.5rem; width: 100%;">
        <span style="font-size: 1.1rem; line-height: 1;">{icon}</span>
        <span style="color: var(--text-primary);">{text}</span>
    </div>
    """, unsafe_allow_html=True)

# ─── Thumbnail Generator Mockup ──────────────────────────────────────
def get_project_thumbnail_html(project: dict) -> str:
    """Generate a clean visual card mock representing the project dashboard."""
    score = project.get("quality_score", 0)
    score_color = "#10B981" if score >= 80 else "#F59E0B" if score >= 50 else "#EF4444"
    rows = project.get("rows", 0)
    cols = project.get("cols", 0)
    tags = project.get("tags", [])
    
    tags_html = "".join([f'<span style="background: rgba(99, 102, 241, 0.15); color: #6366F1; font-size: 0.65rem; padding: 0.15rem 0.45rem; border-radius: 4px; font-weight: 600; margin-right: 0.3rem;">#{tag}</span>' for tag in tags[:3]])
    
    # Render layout mock representation
    return f"""
    <div style="background: var(--mockup-card-bg); height: 110px; border-radius: 8px; padding: 0.6rem; display: flex; flex-direction: column; justify-content: space-between; border: 1px solid var(--card-border); margin-bottom: 0.8rem; overflow: hidden; position: relative;">
        <!-- Mock header and quality dial -->
        <div style="display: flex; justify-content: space-between; align-items: flex-start; z-index: 2;">
            <div>
                <div style="font-size: 0.65rem; color: var(--text-muted); font-weight: 600; text-transform: uppercase;">Dataset Summary</div>
                <div style="font-size: 0.8rem; font-weight: 800; color: var(--text-primary); margin-top: 0.15rem;">{rows:,} × {cols}</div>
            </div>
            
            <!-- Quality score circle -->
            <div style="position: relative; width: 34px; height: 34px; display: flex; align-items: center; justify-content: center;">
                <svg viewBox="0 0 36 36" style="transform: rotate(-90deg); width: 100%; height: 100%; position: absolute;">
                    <circle cx="18" cy="18" r="15.915" fill="none" stroke="var(--card-border-dashed)" stroke-width="3"></circle>
                    <circle cx="18" cy="18" r="15.915" fill="none" stroke="{score_color}" stroke-width="3" stroke-dasharray="{score}, 100" stroke-linecap="round"></circle>
                </svg>
                <div style="font-size: 0.6rem; font-weight: 800; color: {score_color};">{score}</div>
            </div>
        </div>
        
        <!-- Mock dashboard visualization lines -->
        <div style="display: flex; gap: 4px; align-items: flex-end; height: 25px; padding-bottom: 2px;">
            <div style="flex: 1; height: 35%; background: rgba(99, 102, 241, 0.2); border-radius: 2px;"></div>
            <div style="flex: 1; height: 75%; background: rgba(99, 102, 241, 0.4); border-radius: 2px;"></div>
            <div style="flex: 1; height: 50%; background: rgba(139, 92, 246, 0.3); border-radius: 2px;"></div>
            <div style="flex: 1; height: 95%; background: rgba(236, 72, 153, 0.4); border-radius: 2px;"></div>
            <div style="flex: 1; height: 60%; background: rgba(16, 185, 129, 0.3); border-radius: 2px;"></div>
        </div>
        
        <!-- Badges row -->
        <div style="display: flex; align-items: center; justify-content: space-between; z-index: 2;">
            <div style="display: flex;">{tags_html}</div>
            <div style="font-size: 0.65rem; color: #10B981; font-weight: 700; background: rgba(16, 185, 129, 0.1); padding: 0.1rem 0.35rem; border-radius: 4px;">Health Score</div>
        </div>
    </div>
    """

# ─── Render Dashboard ────────────────────────────────────────────────
def render_projects_dashboard():
    st.markdown("### 📁 Project Catalog")
    
    # Load user projects (exclude templates)
    projects = [p for p in list_projects() if not p.get("is_template", False)]
    
    if not projects:
        render_html("""
        <div class="content-card" style="text-align: center; padding: 2.5rem 1.5rem;">
            <div style="font-size: 3rem; margin-bottom: 0.6rem; opacity: 0.4;">📁</div>
            <h3 style="border:none; padding:0; margin-bottom:0.4rem;">No Saved Projects</h3>
            <p style="color:var(--text-secondary); font-size:0.9rem; max-width:420px; margin:0 auto; line-height:1.6;">
                Save your progress or upload a dataset to create your first project.
            </p>
        </div>
        """)
        return

    # Search and Filter Header
    c_search, c_tags = st.columns([2, 2])
    with c_search:
        search_query = st.text_input("🔍 Search project or dataset name", value="", key="project_search_bar")
    with c_tags:
        all_tags = sorted(list(set([t for p in projects for t in p.get("tags", [])])))
        filter_tags = st.multiselect("🏷️ Filter by tags", options=all_tags, key="project_tag_filter")

    # Filter projects
    filtered = []
    for p in projects:
        # Search match
        name_match = (search_query.lower() in p["name"].lower() or 
                      search_query.lower() in p["dataset_name"].lower())
        # Tag match
        tag_match = True
        if filter_tags:
            tag_match = any(t in p.get("tags", []) for t in filter_tags)
            
        if name_match and tag_match:
            filtered.append(p)

    if not filtered:
        st.info("No projects match your search filters.")
        return

    user_projects = filtered
    
    # Sort user projects: pinned first, then last opened desc
    user_projects.sort(key=lambda p: (
        not p.get("pinned", False),
        -datetime.datetime.strptime(p.get("last_opened", "1970-01-01 00:00:00"), "%Y-%m-%d %H:%M:%S").timestamp() if p.get("last_opened") else 0
    ))

    # Nested helper to render a grid of project cards
    def render_project_grid(projects_list):
        cols_grid = st.columns(3)
        for i, project in enumerate(projects_list):
            col = cols_grid[i % 3]
            p_id = project["id"]
            p_name = project["name"]
            ds_name = project["dataset_name"]
            pinned = project.get("pinned", False)
            is_template = project.get("is_template", False)
            
            last_op_str = project.get("last_opened", "")
            last_op_time = ""
            if last_op_str:
                try:
                    dt = datetime.datetime.strptime(last_op_str, "%Y-%m-%d %H:%M:%S")
                    last_op_time = dt.strftime("%b %d, %I:%M %p")
                except Exception:
                    last_op_time = last_op_str
                    
            status = project.get("status", "All changes saved")
            
            with col:
                pinned_banner = '<span style="font-size: 0.75rem; color: #F59E0B; font-weight: 600; display: inline-flex; align-items: center; gap: 0.2rem; margin-bottom: 0.3rem;">📌 Pinned</span>' if pinned else ''
                
                render_html(f"""
                <div class="content-card animate-in" style="margin-bottom: 1rem; border-top: 2px solid {'#F59E0B' if pinned else 'var(--card-border)'};">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.4rem;">
                        <div>
                            {pinned_banner}
                            <h4 style="margin: 0; font-size: 1rem; font-weight: 700; color: var(--text-primary); border: none; padding: 0;">{p_name}</h4>
                            <div style="font-size: 0.72rem; color: var(--text-muted); margin-top: 0.15rem; word-break: break-all;">📁 {ds_name}</div>
                        </div>
                    </div>
                """)
                
                render_html(get_project_thumbnail_html(project))
                
                render_html(f"""
                    <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.7rem; color: var(--text-secondary); margin-bottom: 0.8rem;">
                        <span>Opened: {last_op_time}</span>
                        <span style="font-weight: 600; color: #10B981;">{status}</span>
                    </div>
                </div>
                """)
                
                act_cols = st.columns(2)
                with act_cols[0]:
                    if st.button("📂 Open", key=f"open_{p_id}", use_container_width=True, type="primary"):
                        if load_project(p_id):
                            st.session_state["current_page"] = "Dashboard"
                            _alert(f"Project '{p_name}' successfully loaded!", "success")
                            st.rerun()
                with act_cols[1]:
                    actions = ["Select Action...", "Duplicate", "Pin" if not pinned else "Unpin", "Rename", "Delete", "Export Parquet"]
                    key_suffix = st.session_state.get(f"reset_actions_{p_id}", 0)
                    sel_action = st.selectbox("Actions", options=actions, key=f"actions_{p_id}_{key_suffix}", label_visibility="collapsed")
                    
                    if sel_action == "Duplicate":
                        new_id = duplicate_project(p_id)
                        if new_id:
                            st.session_state[f"reset_actions_{p_id}"] = st.session_state.get(f"reset_actions_{p_id}", 0) + 1
                            _alert(f"Duplicated project '{p_name}'!", "success")
                            st.rerun()
                    elif sel_action in ["Pin", "Unpin"]:
                        update_project_pinned(p_id, not pinned)
                        st.session_state[f"reset_actions_{p_id}"] = st.session_state.get(f"reset_actions_{p_id}", 0) + 1
                        st.rerun()
                    elif sel_action == "Rename":
                        new_name = st.text_input("New project name:", value=p_name, key=f"rename_input_{p_id}")
                        if st.button("Save Name", key=f"rename_save_{p_id}"):
                            update_project_name(p_id, new_name)
                            if st.session_state.get("project_id") == p_id:
                                st.session_state["project_name"] = new_name
                            st.session_state[f"reset_actions_{p_id}"] = st.session_state.get(f"reset_actions_{p_id}", 0) + 1
                            st.rerun()
                    elif sel_action == "Delete":
                        if st.button(f"⚠️ Confirm Delete?", key=f"del_confirm_{p_id}", type="primary"):
                            if delete_project(p_id):
                                if st.session_state.get("project_id") == p_id:
                                    st.session_state["original_df"] = None
                                    st.session_state["cleaned_df"] = None
                                    st.session_state["project_id"] = None
                                    st.session_state["project_name"] = None
                                    st.session_state["file_name"] = None
                                    st.session_state["file_size"] = None
                                    st.session_state["cleaning_steps"] = []
                                    st.session_state["cleaning_history"] = []
                                    st.session_state["save_status"] = "no_project"
                                st.session_state[f"reset_actions_{p_id}"] = st.session_state.get(f"reset_actions_{p_id}", 0) + 1
                                st.rerun()
                    elif sel_action == "Export Parquet":
                        p_dir = os.path.join(PROJECTS_DIR, p_id)
                        clean_path = os.path.join(p_dir, "cleaned_df.parquet")
                        orig_path = os.path.join(p_dir, "original_df.parquet")
                        export_path = clean_path if os.path.exists(clean_path) else orig_path
                        if os.path.exists(export_path):
                            with open(export_path, "rb") as f:
                                st.download_button(
                                    label="📥 Download Parquet",
                                    data=f.read(),
                                    file_name=f"{p_name.lower().replace(' ', '_')}.parquet",
                                    mime="application/octet-stream",
                                    key=f"dl_pq_{p_id}",
                                    use_container_width=True
                                )

    # Render User Workspaces Section
    render_html("<br><h3>👤 My Workspaces</h3>")
    if user_projects:
        render_project_grid(user_projects)
    else:
        st.markdown("""
        <div style="padding: 1.5rem; background: rgba(255, 255, 255, 0.02); border: 1px dashed var(--card-border); border-radius: 8px; text-align: center; color: var(--text-secondary); font-size: 0.85rem; margin-bottom: 2rem;">
            No custom projects found. Upload a dataset from the home page to get started.
        </div>
        """, unsafe_allow_html=True)

# ─── Render Storage Analytics ────────────────────────────────────────
def render_storage_analytics():
    st.markdown("### 💾 Storage Space & Analytics")
    
    projects = list_projects()
    total_projects = len(projects)
    
    total_bytes = 0
    largest_project = None
    largest_size = 0
    activity_count = 0
    
    for p in projects:
        p_bytes = p.get("storage_used_bytes", 0)
        total_bytes += p_bytes
        if p_bytes > largest_size:
            largest_size = p_bytes
            largest_project = p
        activity_count += len(p.get("activity_log", []))
        
    st.markdown("<br>", unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    
    with m1:
        render_html(f"""
        <div class="metric-card blue">
            <span class="metric-icon">📁</span>
            <div class="metric-value">{total_projects}</div>
            <div class="metric-label">Total Projects</div>
        </div>
        """)
        
    with m2:
        render_html(f"""
        <div class="metric-card green">
            <span class="metric-icon">💾</span>
            <div class="metric-value">{format_file_size(total_bytes)}</div>
            <div class="metric-label">Storage Used</div>
        </div>
        """)
        
    with m3:
        large_name = largest_project["name"] if largest_project else "None"
        large_size_str = format_file_size(largest_size) if largest_project else "—"
        render_html(f"""
        <div class="metric-card orange">
            <span class="metric-icon">📊</span>
            <div class="metric-value" style="font-size: 0.95rem; line-height: 1.6; font-weight: 800;">{large_name}</div>
            <div class="metric-label">Largest Dataset ({large_size_str})</div>
        </div>
        """)
        
    with m4:
        render_html(f"""
        <div class="metric-card purple">
            <span class="metric-icon">🕒</span>
            <div class="metric-value">{activity_count}</div>
            <div class="metric-label">Total Logged Activities</div>
        </div>
        """)
        
    # Storage breakdown chart
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### Project Storage Allocation")
    
    if projects:
        data = [{"Project Name": p["name"], "Storage Used": round(p.get("storage_used_bytes", 0) / 1024, 2)} for p in projects]
        df_store = pd.DataFrame(data).sort_values("Storage Used", ascending=False)
        st.dataframe(df_store, use_container_width=True, hide_index=True)
    else:
        st.info("No storage allocation to show.")

# ─── Render Version Control Timeline ──────────────────────────────────
def render_version_timeline():
    st.markdown("### 🕒 Version Timeline & Snapshots")
    
    if "project_id" not in st.session_state or st.session_state["project_id"] is None:
        st.warning("⚠️ No active project loaded. Load a project from the catalog first to view snapshots.")
        return
        
    p_id = st.session_state["project_id"]
    p_name = st.session_state["project_name"]
    
    # Manual snapshot trigger
    st.markdown("#### Create Snapshot Version")
    c_name, c_btn = st.columns([3, 1])
    with c_name:
        snap_desc = st.text_input("Snapshot Description (e.g. Duplicates Removed, Cap Outliers)", key="snap_desc_input")
    with c_btn:
        st.markdown("<div style='height: 1.25rem;'></div>", unsafe_allow_html=True)
        if st.button("📸 Create Snapshot", use_container_width=True, type="primary"):
            if snap_desc.strip():
                if create_snapshot(p_id, snap_desc.strip()):
                    _alert(f"Snapshot '{snap_desc}' created successfully!", "success")
                    st.rerun()
            else:
                st.error("Please enter a snapshot description.")

    # Timeline list
    st.markdown("<br>#### Project Snapshots Timeline", unsafe_allow_html=True)
    snapshots = get_snapshots_timeline(p_id)
    
    if not snapshots:
        st.info("No snapshots found for this project.")
        return
        
    for s in reversed(snapshots):
        ver = s["version"]
        name = s["name"]
        time = s["timestamp"]
        
        render_html(f"""
        <div class="activity-item animate-in">
            <div class="activity-dot" style="background: #8B5CF6;"></div>
            <div style="flex-grow: 1; display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <div style="font-weight: 700; color: var(--text-primary);">Version {ver} — {name}</div>
                    <div class="activity-time">🕒 {time}</div>
                </div>
            </div>
        </div>
        """)
        
        col_restore = st.columns([1, 4])
        with col_restore[0]:
            if st.button(f"Restore V{ver}", key=f"restore_btn_{ver}", type="secondary", use_container_width=True):
                if restore_snapshot(p_id, ver):
                    _alert(f"Restored project to Version {ver}: {name}!", "success")
                    st.rerun()

# ─── Main Public Page Router ─────────────────────────────────────────
def render_projects():
    render_html("""
    <div class="top-header">
        <h2>📁 Projects & Workspace</h2>
        <p>Manage all your datasets, create backups, create version snapshots, and track system resources.</p>
    </div>
    """)
    
    # Main page layout tabs
    tabs = st.tabs(["📁 My Projects", "💾 Storage & Analytics", "🕒 Version Control"])
    
    with tabs[0]:
        render_projects_dashboard()
    with tabs[1]:
        render_storage_analytics()
    with tabs[2]:
        render_version_timeline()

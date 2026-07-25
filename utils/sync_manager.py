"""
Sync Manager for Data Pilot
==========================
Handles projects saving, loading, autosaving, snapshots, version timelines,
backups, crash recovery, and template seeding.
"""

import os
import json
import uuid
import datetime
import threading
import shutil
import sqlite3
import numpy as np
import pandas as pd
import streamlit as st
from typing import List, Dict, Any, Optional

# Ensure project root is correct
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECTS_DIR = os.path.join(PROJECT_ROOT, "projects")
os.makedirs(PROJECTS_DIR, exist_ok=True)
DB_PATH = os.path.join(PROJECTS_DIR, "datapilot.db")

# Lock for multi-threaded project saves
SAVE_LOCK = threading.Lock()

# =============================================================================
# Template Seeding
# =============================================================================

def generate_mock_dataset(template_type: str) -> pd.DataFrame:
    """Generate dirty mock datasets for templates to clean."""
    np.random.seed(42)
    n_rows = 500

    if template_type == "Sales":
        # Sales Analysis
        dates = pd.date_range(start="2026-01-01", periods=n_rows, freq="h")
        products = ["SmartPhone X", "Wireless Buds", "Laptop Pro", "USB-C Cable", "PowerBank Ultra", None]
        categories = ["Electronics", "Accessories", "Computers", "Cables", None]
        regions = ["North", "South", "East", "West", "Central"]
        segments = ["Consumer", "Corporate", "Home Office"]
        
        data = {
            "Transaction_ID": [f"TXN-{1000 + i}" for i in range(n_rows)],
            "Date": [d.strftime("%Y-%m-%d %H:%M:%S") for d in dates],
            "Product": np.random.choice(products, n_rows),
            "Category": np.random.choice(categories, n_rows),
            "Units_Sold": np.random.choice([1, 2, 3, 4, 5, 10, 50, None], n_rows), # Outlier 50
            "Unit_Price": np.random.choice([999.99, 49.99, 1499.00, 19.99, 79.99, None], n_rows),
            "Region": np.random.choice(regions, n_rows),
            "Segment": np.random.choice(segments, n_rows),
            "Discount": np.random.choice([0.0, 0.05, 0.1, 0.15, 0.2, 0.5, None], n_rows) # Outlier 0.5
        }
        df = pd.DataFrame(data)
        # Add duplicates
        df = pd.concat([df, df.iloc[10:15]], ignore_index=True)
        # Add dirty rows
        df.loc[100:102, "Unit_Price"] = -999.0  # Invalid outlier
        return df

    elif template_type == "HR":
        # HR Analytics
        depts = ["Engineering", "Sales", "Marketing", "HR", "Finance", None]
        roles = ["Developer", "Manager", "Analyst", "Lead", "Recruiter", None]
        status = ["Active", "Resigned", "On Leave"]
        
        names = ["Aarav", "Vihaan", "Aditya", "Sai", "Arjun", "Ananya", "Diya", "Ira", "Kavya", "Sanya",
                 "John", "Sarah", "Emily", "Michael", "David", "Jessica", "James", "Robert", "Linda", "William"]
        surnames = ["Sharma", "Verma", "Gupta", "Patel", "Reddy", "Smith", "Jones", "Miller", "Davis", "Wilson"]

        full_names = [f"{np.random.choice(names)} {np.random.choice(surnames)}" for _ in range(n_rows)]
        
        data = {
            "Employee_ID": [f"EMP-{5000 + i}" for i in range(n_rows)],
            "Name": full_names,
            "Department": np.random.choice(depts, n_rows),
            "Role": np.random.choice(roles, n_rows),
            "Salary": np.random.choice([50000, 75000, 110000, 150000, 250000, None], n_rows), # Outlier 250k
            "Performance_Rating": np.random.choice([1, 2, 3, 4, 5, None], n_rows),
            "Joining_Date": [(datetime.datetime(2020, 1, 1) + datetime.timedelta(days=int(np.random.choice(2000)))).strftime("%Y-%m-%d") for _ in range(n_rows)],
            "Status": np.random.choice(status, n_rows, p=[0.8, 0.15, 0.05])
        }
        df = pd.DataFrame(data)
        # Add duplicates
        df = pd.concat([df, df.iloc[20:25]], ignore_index=True)
        # Outlier salary
        df.loc[15, "Salary"] = 9999999.0
        return df

    elif template_type == "Customer":
        # Customer Segmentation
        genders = ["Male", "Female", None]
        cities = ["Mumbai", "Delhi", "Bengaluru", "Kolkata", "Chennai", "Hyderabad", None]
        
        data = {
            "Customer_ID": [f"CUST-{8000 + i}" for i in range(n_rows)],
            "Age": np.random.choice([18, 25, 34, 45, 55, 65, 120, None], n_rows), # Outlier age 120
            "Gender": np.random.choice(genders, n_rows),
            "Annual_Income": np.random.choice([15000, 30000, 50000, 75000, 120000, 350000, None], n_rows), # Outlier 350k
            "Spending_Score": np.random.choice(list(range(1, 100)) + [999, None], n_rows), # Outlier 999
            "City": np.random.choice(cities, n_rows),
            "First_Purchase_Date": [(datetime.datetime(2022, 1, 1) + datetime.timedelta(days=int(np.random.choice(1500)))).strftime("%Y-%m-%d") for _ in range(n_rows)]
        }
        df = pd.DataFrame(data)
        df = pd.concat([df, df.iloc[30:33]], ignore_index=True)
        return df

    else:
        # Financial Transactions
        acc_types = ["Savings", "Current", "Credit Card", None]
        cats = ["Groceries", "Utilities", "Dining Out", "Travel", "Investments", "Salary", None]
        
        data = {
            "Transaction_ID": [f"FIN-{3000 + i}" for i in range(n_rows)],
            "Date": [(datetime.datetime(2026, 1, 1) + datetime.timedelta(days=int(np.random.choice(180)))).strftime("%Y-%m-%d %H:%M:%S") for _ in range(n_rows)],
            "Account_Type": np.random.choice(acc_types, n_rows),
            "Category": np.random.choice(cats, n_rows),
            "Amount": np.random.choice([10.50, 45.00, 120.00, 850.00, 5000.00, -25000.00, None], n_rows), # Outlier -25000
            "Description": [f"Merchant payment {i}" for i in range(n_rows)],
            "Status": np.random.choice(["Cleared", "Pending", "Failed"], n_rows)
        }
        df = pd.DataFrame(data)
        df = pd.concat([df, df.iloc[40:43]], ignore_index=True)
        return df

def init_db():
    """Initialize the SQLite database and create tables if they do not exist."""
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                dataset_name TEXT NOT NULL,
                rows INTEGER DEFAULT 0,
                cols INTEGER DEFAULT 0,
                quality_score INTEGER DEFAULT 0,
                pinned INTEGER DEFAULT 0,
                last_opened TEXT,
                last_saved TEXT,
                status TEXT,
                tags TEXT,
                notes TEXT,
                is_template INTEGER DEFAULT 0,
                current_page TEXT,
                activity_log TEXT,
                cleaning_steps TEXT,
                saved_pipelines TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id TEXT PRIMARY KEY,
                project_id TEXT,
                version INTEGER DEFAULT 1,
                title TEXT,
                author TEXT,
                company TEXT,
                department TEXT,
                theme TEXT DEFAULT 'Corporate',
                sections TEXT,
                created_at TEXT,
                dataset_name TEXT,
                report_type TEXT DEFAULT 'Full Report',
                file_path TEXT
            )
        """)
        conn.commit()
    finally:
        conn.close()

def seed_templates():
    """Seed the four standard templates if they don't already exist in database or disk."""
    init_db()
    templates = [
        ("sales_template", "Sales Analysis Template", "Sales", ["Sales", "EDA", "Dashboard"]),
        ("hr_template", "HR Analytics Template", "HR", ["Finance", "EDA"]),
        ("customer_template", "Customer Analytics Template", "Customer", ["ML", "Dashboard"]),
        ("financial_template", "Financial Analysis Template", "Finance", ["Finance", "EDA", "AI"])
    ]

    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        for p_id, p_name, temp_type, tags in templates:
            # Check if template is already seeded in SQLite
            cursor.execute("SELECT 1 FROM projects WHERE id = ?", (p_id,))
            exists = cursor.fetchone()
            
            p_dir = os.path.join(PROJECTS_DIR, p_id)
            if not exists or not os.path.exists(p_dir):
                os.makedirs(p_dir, exist_ok=True)
                df = generate_mock_dataset(temp_type)
                
                # Save datasets as parquet to disk
                df.to_parquet(os.path.join(p_dir, "original_df.parquet"), index=False)
                df.to_parquet(os.path.join(p_dir, "cleaned_df.parquet"), index=False)
                
                # Save initial snapshot parquet
                os.makedirs(os.path.join(p_dir, "snapshots"), exist_ok=True)
                df.to_parquet(os.path.join(p_dir, "snapshots", "snap_v1.parquet"), index=False)
                
                snap_meta = [
                    {
                        "version": 1,
                        "name": "Initial Template Load",
                        "timestamp": datetime.datetime.now().strftime("%I:%M %p"),
                        "snapshot_file": "snap_v1.parquet"
                    }
                ]
                with open(os.path.join(p_dir, "snapshots", "snapshots.json"), "w", encoding="utf-8") as f:
                    json.dump(snap_meta, f, indent=4)
                
                # Insert metadata into SQLite
                cursor.execute("""
                    INSERT OR REPLACE INTO projects (
                        id, name, dataset_name, rows, cols, quality_score, pinned, 
                        last_opened, last_saved, status, tags, notes, is_template, 
                        current_page, activity_log, cleaning_steps, saved_pipelines
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    p_id, p_name, f"{temp_type.lower()}_dirty_dataset.csv", len(df), len(df.columns),
                    50, 0, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "All changes saved",
                    json.dumps(tags), json.dumps([
                        {"timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                         "text": f"Initial seed of {p_name}. Clean the missing values and outliers!"}
                    ]), 1, "Dashboard", json.dumps([
                        {"timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                         "action": "Template Created", "details": f"Generated {temp_type} template dataset"}
                    ]), json.dumps([]), json.dumps([])
                ))
        conn.commit()
    finally:
        conn.close()

# Seed automatically on import
seed_templates()

# =============================================================================
# Helper Functions
# =============================================================================

def get_active_session() -> Optional[Dict[str, Any]]:
    """Get the active project session metadata."""
    session_file = os.path.join(PROJECTS_DIR, "active_session.json")
    if os.path.exists(session_file):
        try:
            with open(session_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
    return None

def set_active_session(project_id: Optional[str], clean_exit: bool = False):
    """Set the active project session."""
    session_file = os.path.join(PROJECTS_DIR, "active_session.json")
    if project_id is None:
        if os.path.exists(session_file):
            try:
                os.remove(session_file)
            except Exception:
                pass
    else:
        session_data = {
            "active_project_id": project_id,
            "last_activity_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "clean_exit": clean_exit
        }
        try:
            with open(session_file, "w", encoding="utf-8") as f:
                json.dump(session_data, f, indent=4)
        except Exception:
            pass

def list_projects() -> List[Dict[str, Any]]:
    """Scan SQLite database and return metadata of all projects."""
    init_db()
    projects = []
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM projects")
        rows = cursor.fetchall()
        for row in rows:
            meta = dict(row)
            # Deserialize JSON columns
            meta["tags"] = json.loads(meta["tags"]) if meta["tags"] else []
            meta["notes"] = json.loads(meta["notes"]) if meta["notes"] else []
            meta["activity_log"] = json.loads(meta["activity_log"]) if meta["activity_log"] else []
            meta["cleaning_steps"] = json.loads(meta["cleaning_steps"]) if meta["cleaning_steps"] else []
            meta["saved_pipelines"] = json.loads(meta["saved_pipelines"]) if meta["saved_pipelines"] else []
            
            # Convert numeric booleans
            meta["pinned"] = bool(meta["pinned"])
            meta["is_template"] = bool(meta["is_template"])
            
            # Calculate total storage size from folder contents
            p_dir = os.path.join(PROJECTS_DIR, meta["id"])
            total_bytes = 0
            if os.path.exists(p_dir):
                for root, _, files in os.walk(p_dir):
                    for file in files:
                        total_bytes += os.path.getsize(os.path.join(root, file))
            meta["storage_used_bytes"] = total_bytes
            projects.append(meta)
    except Exception:
        pass
    finally:
        conn.close()
    return projects

def save_project_worker(project_id: str, original_df, cleaned_df, project_name, file_name,
                        quality_score, pinned, tags, notes, current_page, activity_log,
                        cleaning_steps, saved_pipelines):
    """Worker function that saves datasets to disk and project metadata to SQLite."""
    p_dir = os.path.join(PROJECTS_DIR, project_id)
    os.makedirs(p_dir, exist_ok=True)
    
    with SAVE_LOCK:
        try:
            # Save dataframes as Parquet to disk (Hybrid part)
            if original_df is not None:
                original_df.to_parquet(os.path.join(p_dir, "original_df.parquet"), index=False)
            if cleaned_df is not None:
                cleaned_df.to_parquet(os.path.join(p_dir, "cleaned_df.parquet"), index=False)
                
            working_df = cleaned_df if cleaned_df is not None else original_df
            rows_cnt = len(working_df) if working_df is not None else 0
            cols_cnt = len(working_df.columns) if working_df is not None else 0
            
            init_db()
            conn = sqlite3.connect(DB_PATH)
            try:
                # Keep existing is_template flag
                cursor = conn.cursor()
                cursor.execute("SELECT is_template FROM projects WHERE id = ?", (project_id,))
                row = cursor.fetchone()
                is_template_val = row[0] if row else 0
                
                cursor.execute("""
                    INSERT OR REPLACE INTO projects (
                        id, name, dataset_name, rows, cols, quality_score, pinned, 
                        last_opened, last_saved, status, tags, notes, is_template, 
                        current_page, activity_log, cleaning_steps, saved_pipelines
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    project_id, project_name, file_name, rows_cnt, cols_cnt, int(quality_score),
                    1 if pinned else 0, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "All changes saved",
                    json.dumps(tags), json.dumps(notes), is_template_val, current_page,
                    json.dumps(activity_log), json.dumps(cleaning_steps), json.dumps(saved_pipelines)
                ))
                conn.commit()
            finally:
                conn.close()
                
            set_active_session(project_id, clean_exit=True)
        except Exception:
            pass

def save_project(project_id: str, is_snapshot: bool = False):
    """Save project synchronously (runs on main thread)."""
    p_dir = os.path.join(PROJECTS_DIR, project_id)
    if not os.path.exists(p_dir):
        os.makedirs(p_dir, exist_ok=True)
        
    original_df = st.session_state.get("original_df")
    cleaned_df = st.session_state.get("cleaned_df")
    if original_df is None:
        return False
        
    project_name = st.session_state.get("project_name", "Unnamed Project")
    file_name = st.session_state.get("file_name", "Unknown")
    quality_score = int(st.session_state.get("quality_score", 0))
    pinned = st.session_state.get("project_pinned", False)
    tags = st.session_state.get("project_tags", [])
    notes = st.session_state.get("project_notes", [])
    current_page = st.session_state.get("current_page", "Dashboard")
    activity_log = st.session_state.get("activity_log", [])
    cleaning_steps = st.session_state.get("cleaning_steps", [])
    saved_pipelines = st.session_state.get("saved_pipelines", [])
    
    try:
        save_project_worker(
            project_id=project_id,
            original_df=original_df,
            cleaned_df=cleaned_df,
            project_name=project_name,
            file_name=file_name,
            quality_score=quality_score,
            pinned=pinned,
            tags=tags,
            notes=notes,
            current_page=current_page,
            activity_log=activity_log,
            cleaning_steps=cleaning_steps,
            saved_pipelines=saved_pipelines
        )
        st.session_state["save_status"] = "saved"
        st.session_state["last_saved_time"] = datetime.datetime.now().strftime("%I:%M %p")
        return True
    except Exception as e:
        st.session_state["save_status"] = "failed"
        st.error(f"Save failed: {e}")
        return False

def save_project_async(project_id: str):
    """Save project using a separate thread to prevent blocking the Streamlit UI thread."""
    original_df = st.session_state.get("original_df")
    cleaned_df = st.session_state.get("cleaned_df")
    if original_df is None:
        return
        
    st.session_state["save_status"] = "saving"
    
    project_name = st.session_state.get("project_name", "Unnamed Project")
    file_name = st.session_state.get("file_name", "Unknown")
    quality_score = int(st.session_state.get("quality_score", 0))
    pinned = st.session_state.get("project_pinned", False)
    tags = st.session_state.get("project_tags", [])
    notes = st.session_state.get("project_notes", [])
    current_page = st.session_state.get("current_page", "Dashboard")
    activity_log = st.session_state.get("activity_log", [])
    cleaning_steps = st.session_state.get("cleaning_steps", [])
    saved_pipelines = st.session_state.get("saved_pipelines", [])
    
    thread = threading.Thread(
        target=save_project_worker,
        args=(project_id,),
        kwargs={
            "original_df": original_df,
            "cleaned_df": cleaned_df,
            "project_name": project_name,
            "file_name": file_name,
            "quality_score": quality_score,
            "pinned": pinned,
            "tags": tags,
            "notes": notes,
            "current_page": current_page,
            "activity_log": activity_log,
            "cleaning_steps": cleaning_steps,
            "saved_pipelines": saved_pipelines
        }
    )
    st.session_state["save_thread"] = thread
    thread.start()

def load_project(project_id: str):
    """Load the project from disk and populate st.session_state."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    meta = None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        row = cursor.fetchone()
        if row:
            meta = dict(row)
    except Exception as e:
        st.error(f"Database error: {e}")
        return False
    finally:
        conn.close()
        
    if not meta:
        st.error("Project metadata not found in SQL database.")
        return False
        
    try:
        p_dir = os.path.join(PROJECTS_DIR, project_id)
        orig_path = os.path.join(p_dir, "original_df.parquet")
        clean_path = os.path.join(p_dir, "cleaned_df.parquet")
        
        if os.path.exists(orig_path):
            st.session_state["original_df"] = pd.read_parquet(orig_path)
        else:
            st.error("Original dataset Parquet file not found on disk.")
            return False
            
        if os.path.exists(clean_path):
            st.session_state["cleaned_df"] = pd.read_parquet(clean_path)
        else:
            st.session_state["cleaned_df"] = None
            
        st.session_state["project_id"] = meta["id"]
        st.session_state["project_name"] = meta["name"]
        st.session_state["file_name"] = meta["dataset_name"]
        st.session_state["quality_score"] = meta.get("quality_score", 0)
        st.session_state["project_pinned"] = bool(meta.get("pinned", 0))
        st.session_state["project_tags"] = json.loads(meta["tags"]) if meta["tags"] else []
        st.session_state["project_notes"] = json.loads(meta["notes"]) if meta["notes"] else []
        st.session_state["current_page"] = meta.get("current_page", "Dashboard")
        st.session_state["activity_log"] = json.loads(meta["activity_log"]) if meta["activity_log"] else []
        st.session_state["cleaning_steps"] = json.loads(meta["cleaning_steps"]) if meta["cleaning_steps"] else []
        st.session_state["saved_pipelines"] = json.loads(meta["saved_pipelines"]) if meta["saved_pipelines"] else []
        st.session_state["save_status"] = "saved"
        st.session_state["last_saved_time"] = meta.get("last_saved", "").split()[-1] if meta.get("last_saved") else ""
        
        st.session_state["cleaning_history"] = []
        
        # Update last opened time
        conn = sqlite3.connect(DB_PATH)
        try:
            cursor = conn.conn = conn.cursor()
            cursor.execute("UPDATE projects SET last_opened = ? WHERE id = ?", (
                datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), project_id
            ))
            conn.commit()
        except Exception:
            pass
        finally:
            conn.close()
            
        set_active_session(project_id, clean_exit=True)
        return True
        
    except Exception as e:
        st.error(f"Error loading project: {e}")
        return False

def autosave():
    """Background check: If active project has modifications, trigger async save."""
    if "project_id" not in st.session_state or st.session_state["project_id"] is None:
        return
        
    project_id = st.session_state["project_id"]
    
    if st.session_state.get("save_status") == "saving":
        thread = st.session_state.get("save_thread")
        if thread and not thread.is_alive():
            st.session_state["save_status"] = "saved"
            st.session_state["last_saved_time"] = datetime.datetime.now().strftime("%I:%M %p")
            st.rerun()
            
    cleaned_df = st.session_state.get("cleaned_df")
    original_df = st.session_state.get("original_df")
    working_df = cleaned_df if cleaned_df is not None else original_df
    
    if working_df is None:
        return
        
    sig = {
        "name": st.session_state.get("project_name", ""),
        "rows": len(working_df),
        "cols": len(working_df.columns),
        "steps_count": len(st.session_state.get("cleaning_steps", [])),
        "activity_count": len(st.session_state.get("activity_log", [])),
        "pinned": st.session_state.get("project_pinned", False),
        "tags": st.session_state.get("project_tags", []),
        "notes_count": len(st.session_state.get("project_notes", [])),
        "pipelines_count": len(st.session_state.get("saved_pipelines", [])),
        "current_page": st.session_state.get("current_page", "Dashboard")
    }
    
    prev_sig = st.session_state.get("last_saved_sig")
    if prev_sig != sig:
        st.session_state["last_saved_sig"] = sig
        save_project_async(project_id)
        auto_backup(project_id)

def create_snapshot(project_id: str, name: str):
    """Create a new version snapshot file and append to the timeline list."""
    p_dir = os.path.join(PROJECTS_DIR, project_id)
    snap_dir = os.path.join(p_dir, "snapshots")
    os.makedirs(snap_dir, exist_ok=True)
    
    snap_meta_path = os.path.join(snap_dir, "snapshots.json")
    
    # Load existing snapshots list
    snapshots = []
    if os.path.exists(snap_meta_path):
        try:
            with open(snap_meta_path, "r", encoding="utf-8") as f:
                snapshots = json.load(f)
        except Exception:
            pass
            
    # Version increments
    next_ver = len(snapshots) + 1
    snap_file = f"snap_v{next_ver}.parquet"
    
    # Save the current cleaned_df (or original if none) as Parquet
    df = st.session_state.get("cleaned_df")
    if df is None:
        df = st.session_state.get("original_df")
        
    if df is None:
        return False
        
    try:
        df.to_parquet(os.path.join(snap_dir, snap_file), index=False)
        
        # Save snapshot metadata
        new_snap = {
            "version": next_ver,
            "name": name,
            "timestamp": datetime.datetime.now().strftime("%I:%M %p"),
            "snapshot_file": snap_file
        }
        snapshots.append(new_snap)
        
        with open(snap_meta_path, "w", encoding="utf-8") as f:
            json.dump(snapshots, f, indent=4)
            
        # Log to activity
        from utils.helpers import add_activity
        add_activity("Snapshot Created", f"Version {next_ver}: {name}")
        
        # Save project changes
        save_project(project_id)
        return True
    except Exception as e:
        st.error(f"Failed to create snapshot: {e}")
        return False

def get_snapshots_timeline(project_id: str) -> List[Dict[str, Any]]:
    """Retrieve snapshots list for version timeline display."""
    snap_meta_path = os.path.join(PROJECTS_DIR, project_id, "snapshots", "snapshots.json")
    if os.path.exists(snap_meta_path):
        try:
            with open(snap_meta_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def restore_snapshot(project_id: str, version: int):
    """Restore the project state to the selected version snapshot."""
    p_dir = os.path.join(PROJECTS_DIR, project_id)
    snap_file = f"snap_v{version}.parquet"
    snap_path = os.path.join(p_dir, "snapshots", snap_file)
    
    if not os.path.exists(snap_path):
        st.error(f"Snapshot version {version} parquet file not found.")
        return False
        
    try:
        restored_df = pd.read_parquet(snap_path)
        st.session_state["cleaned_df"] = restored_df
        
        # Trim cleaning steps corresponding to versions after this one
        snapshots = get_snapshots_timeline(project_id)
        selected_snap = next((s for s in snapshots if s["version"] == version), None)
        
        if version == 1:
            st.session_state["cleaning_steps"] = []
            
        from utils.helpers import add_activity
        add_activity("Version Restored", f"Restored Version {version}: {selected_snap.get('name') if selected_snap else ''}")
        
        # Recalculate quality score
        from utils.cleaner import calculate_quality_score as calc_score
        st.session_state["quality_score"] = calc_score(restored_df)["total"]
        
        # Save project details immediately
        save_project(project_id)
        return True
    except Exception as e:
        st.error(f"Failed to restore snapshot: {e}")
        return False

def auto_backup(project_id: str):
    """Write current state to backups/latest_backup.parquet for crash recovery."""
    p_dir = os.path.join(PROJECTS_DIR, project_id)
    backup_dir = os.path.join(p_dir, "backups")
    os.makedirs(backup_dir, exist_ok=True)
    
    df = st.session_state.get("cleaned_df")
    if df is None:
        df = st.session_state.get("original_df")
        
    if df is None:
        return
        
    try:
        df.to_parquet(os.path.join(backup_dir, "latest_backup.parquet"), index=False)
        
        meta = {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "project_name": st.session_state.get("project_name", "Unnamed Project"),
            "dataset_name": st.session_state.get("file_name", "Unknown")
        }
        with open(os.path.join(backup_dir, "backup_metadata.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=4)
        set_active_session(project_id, clean_exit=False)
    except Exception:
        pass

def recover_backup(project_id: str):
    """Restore state from latest_backup.parquet."""
    p_dir = os.path.join(PROJECTS_DIR, project_id)
    backup_path = os.path.join(p_dir, "backups", "latest_backup.parquet")
    
    if os.path.exists(backup_path):
        try:
            df = pd.read_parquet(backup_path)
            st.session_state["cleaned_df"] = df
            
            from utils.helpers import add_activity
            add_activity("Backup Recovered", "Recovered state after unexpected close")
            
            # Recalculate quality score
            from utils.cleaner import calculate_quality_score as calc_score
            st.session_state["quality_score"] = calc_score(df)["total"]
            
            save_project(project_id)
            return True
        except Exception as e:
            st.error(f"Failed to recover backup: {e}")
    return False

def delete_project(project_id: str):
    """Delete project directory and clean active session if deleted project was open."""
    p_dir = os.path.join(PROJECTS_DIR, project_id)
    if os.path.exists(p_dir):
        try:
            shutil.rmtree(p_dir)
        except Exception:
            pass
            
    # Delete SQLite metadata record
    init_db()
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        conn.commit()
    except Exception:
        pass
    finally:
        conn.close()
        
    active = get_active_session()
    if active and active.get("active_project_id") == project_id:
        set_active_session(None)
    return True

def duplicate_project(project_id: str) -> Optional[str]:
    """Create a duplicate of the project in SQLite and copy dataset files on disk."""
    init_db()
    new_id = str(uuid.uuid4())
    p_dir = os.path.join(PROJECTS_DIR, project_id)
    new_dir = os.path.join(PROJECTS_DIR, new_id)
    
    if not os.path.exists(p_dir):
        return None
        
    # Read from SQLite
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    meta = None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        row = cursor.fetchone()
        if row:
            meta = dict(row)
    except Exception:
        pass
    finally:
        conn.close()
        
    if not meta:
        return None
        
    try:
        # Copy directory files
        shutil.copytree(p_dir, new_dir)
        
        # Save duplicated project metadata into SQLite
        conn = sqlite3.connect(DB_PATH)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO projects (
                    id, name, dataset_name, rows, cols, quality_score, pinned, 
                    last_opened, last_saved, status, tags, notes, is_template, 
                    current_page, activity_log, cleaning_steps, saved_pipelines
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                new_id, f"Copy of {meta['name']}", meta["dataset_name"], meta["rows"], meta["cols"],
                meta["quality_score"], 0, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "All changes saved",
                meta["tags"], meta["notes"], 0, meta["current_page"],
                meta["activity_log"], meta["cleaning_steps"], meta["saved_pipelines"]
            ))
            conn.commit()
        except Exception:
            pass
        finally:
            conn.close()
            
        return new_id
    except Exception as e:
        st.error(f"Failed to duplicate project: {e}")
        return None

def create_new_project_from_upload(uploaded_file, df) -> str:
    """Create a new project directory structure on upload and record metadata in SQLite."""
    project_id = str(uuid.uuid4())
    p_dir = os.path.join(PROJECTS_DIR, project_id)
    os.makedirs(p_dir, exist_ok=True)
    
    # Save original parquet dataframe
    df.to_parquet(os.path.join(p_dir, "original_df.parquet"), index=False)
    
    # Calculate quality score
    from utils.cleaner import calculate_quality_score as calc_score
    initial_score = calc_score(df)["total"]
    
    # Generate project name from file name
    base_name = os.path.splitext(uploaded_file.name)[0]
    clean_name = base_name.replace("_", " ").replace("-", " ").title()
    project_name = f"{clean_name} Dashboard"
    
    # Populate session state
    st.session_state["project_id"] = project_id
    st.session_state["project_name"] = project_name
    st.session_state["file_name"] = uploaded_file.name
    st.session_state["file_size"] = uploaded_file.size
    st.session_state["original_df"] = df
    st.session_state["cleaned_df"] = None
    st.session_state["quality_score"] = initial_score
    st.session_state["project_pinned"] = False
    st.session_state["project_tags"] = ["EDA"]  # Default tag
    st.session_state["project_notes"] = []
    st.session_state["current_page"] = "Dashboard"
    st.session_state["activity_log"] = []
    st.session_state["cleaning_steps"] = []
    st.session_state["saved_pipelines"] = []
    st.session_state["save_status"] = "saved"
    st.session_state["last_saved_time"] = datetime.datetime.now().strftime("%I:%M %p")
    
    from utils.helpers import add_activity
    add_activity("Dataset Uploaded", f"{uploaded_file.name} ({df.shape[0]} rows × {df.shape[1]} cols)")
    
    # Save metadata
    save_project(project_id)
    
    # Create first snapshot (Initial Upload)
    create_snapshot(project_id, "Initial Upload")
    
    return project_id

# =============================================================================
# Direct SQLite Getter/Setter Helpers (Avoid direct metadata.json reading)
# =============================================================================

def get_project_metadata(project_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve project metadata dictionary from SQL database."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    meta = None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        row = cursor.fetchone()
        if row:
            meta = dict(row)
            meta["tags"] = json.loads(meta["tags"]) if meta["tags"] else []
            meta["notes"] = json.loads(meta["notes"]) if meta["notes"] else []
            meta["activity_log"] = json.loads(meta["activity_log"]) if meta["activity_log"] else []
            meta["cleaning_steps"] = json.loads(meta["cleaning_steps"]) if meta["cleaning_steps"] else []
            meta["saved_pipelines"] = json.loads(meta["saved_pipelines"]) if meta["saved_pipelines"] else []
            meta["pinned"] = bool(meta["pinned"])
            meta["is_template"] = bool(meta["is_template"])
    except Exception:
        pass
    finally:
        conn.close()
    return meta

def update_project_properties(project_id: str, name: str, is_template: bool):
    """Update name and is_template state in SQL."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE projects SET name = ?, is_template = ? WHERE id = ?", (
            name, 1 if is_template else 0, project_id
        ))
        conn.commit()
    except Exception:
        pass
    finally:
        conn.close()

def update_project_pinned(project_id: str, pinned: bool):
    """Toggle the pinned state of a project in SQLite."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE projects SET pinned = ? WHERE id = ?", (
            1 if pinned else 0, project_id
        ))
        conn.commit()
    except Exception:
        pass
    finally:
        conn.close()

def update_project_name(project_id: str, new_name: str):
    """Update the name of a project in SQLite."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE projects SET name = ? WHERE id = ?", (
            new_name, project_id
        ))
        conn.commit()
    except Exception:
        pass
    finally:
        conn.close()


# =============================================================================
# Report Persistence Helpers
# =============================================================================

def save_report_meta(report_data: Dict[str, Any]) -> bool:
    """Save report metadata to SQLite."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO reports (
                id, project_id, version, title, author, company, department,
                theme, sections, created_at, dataset_name, report_type, file_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            report_data.get("id", str(uuid.uuid4())),
            report_data.get("project_id", ""),
            report_data.get("version", 1),
            report_data.get("title", "Executive Report"),
            report_data.get("author", "Data Analyst"),
            report_data.get("company", "Data Pilot Org"),
            report_data.get("department", "Analytics"),
            report_data.get("theme", "Corporate"),
            json.dumps(report_data.get("sections", [])),
            report_data.get("created_at", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            report_data.get("dataset_name", "Dataset"),
            report_data.get("report_type", "Full Report"),
            report_data.get("file_path", "")
        ))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error saving report metadata: {e}")
        return False
    finally:
        conn.close()


def list_reports(project_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all reports stored in SQLite, optionally filtered by project_id."""
    init_db()
    reports = []
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()
        if project_id:
            cursor.execute("SELECT * FROM reports WHERE project_id = ? ORDER BY version DESC", (project_id,))
        else:
            cursor.execute("SELECT * FROM reports ORDER BY created_at DESC")
        rows = cursor.fetchall()
        for r in rows:
            item = dict(r)
            item["sections"] = json.loads(item["sections"]) if item["sections"] else []
            reports.append(item)
    except Exception as e:
        print(f"Error listing reports: {e}")
    finally:
        conn.close()
    return reports


def delete_report(report_id: str) -> bool:
    """Delete a report record from SQLite."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM reports WHERE id = ?", (report_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error deleting report: {e}")
        return False
    finally:
        conn.close()


def get_next_report_version(project_id: str) -> int:
    """Get the next version number for a project report."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(version) FROM reports WHERE project_id = ?", (project_id,))
        val = cursor.fetchone()[0]
        return (val or 0) + 1
    except Exception:
        return 1
    finally:
        conn.close()



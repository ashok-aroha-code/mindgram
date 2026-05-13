import streamlit as st
import subprocess
import os
import json
import time
import re
import pandas as pd
from datetime import datetime

def strip_ansi_codes(text):
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

def find_output_path(source, topic, year):
    """Dynamically finds the output JSON file based on common patterns."""
    base_dir = os.path.join("data", topic)
    if not os.path.exists(base_dir):
        return None
        
    patterns = [
        f"{topic}_spring_{year}.json",
        f"{topic}_{year}.json",
        f"{topic}_fall_{year}.json",
        f"{topic}_summer_{year}.json",
        f"{topic}_winter_{year}.json",
    ]
    
    # Try exact matches first
    for p in patterns:
        path = os.path.join(base_dir, p)
        if os.path.exists(path):
            return path
            
    # Fallback: look for any JSON containing the year in that folder
    try:
        files = [f for f in os.listdir(base_dir) if f.endswith(".json") and year in f]
        if files:
            # Return the most recently modified one
            files.sort(key=lambda x: os.path.getmtime(os.path.join(base_dir, x)), reverse=True)
            return os.path.join(base_dir, files[0])
    except:
        pass
        
    return None

# Set page config
st.set_page_config(
    page_title="Mindgram Scraper Control Center",
    page_icon="🕸️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for a premium look
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #ff4b4b;
        color: white;
        font-weight: bold;
    }
    .stCodeBlock {
        border-radius: 10px;
    }
    .status-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #1e2130;
        border: 1px solid #3e4259;
        margin-bottom: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://img.icons8.com/fluent/100/000000/spider-web.png", width=80)
    st.title("Scraper Hub")
    st.markdown("---")
    
    # Scraper Selection
    source = st.selectbox("Select Data Source", ["hmpglobalevents", "aacrjournals", "sciencedirect"])
    
    # Dynamic Topic Selection based on Source
    topics_map = {
        "hmpglobalevents": ["sawc"],
        "aacrjournals": ["aacr"],
        "sciencedirect": ["ase"]
    }
    topic = st.selectbox("Select Topic", topics_map.get(source, []))
    
    # Year Selection
    year = st.selectbox("Select Year", ["2026", "2025", "2024"])
    
    # Task Selection
    task_options = ["default", "url-scraper", "abstract-scraper", "url-matcher"]
    task = st.selectbox("Select Task", task_options)

    # Headless Mode Toggle
    headless = st.checkbox("Run in Headless Mode", value=False, help="Runs the scraper without showing the browser window. Saves memory.")

    st.markdown("---")
    if st.button("🚀 RUN SCRAPER"):
        st.session_state.run_scraper = True
    else:
        if 'run_scraper' not in st.session_state:
            st.session_state.run_scraper = False

# --- MAIN AREA ---
st.title("🕸️ Mindgram Scraper Dashboard")
st.info(f"Target: **{source}** > **{topic}** > **{year}** [Task: **{task}**]")

# Parameters Layout
col1, col2, col3, col4 = st.columns(4)

# Try to get current count
current_count = 0
output_path = find_output_path(source, topic, year)

if output_path and os.path.exists(output_path):
    try:
        with open(output_path, "r", encoding="utf-8") as f:
            temp_data = json.load(f)
            current_count = len(temp_data.get("abstracts", []))
    except:
        pass

with col1:
    st.metric("Source", source)
with col2:
    st.metric("Topic", topic)
with col3:
    st.metric("Year", year)
with col4:
    st.metric("Total Abstracts", current_count, delta=None)

# Execution Logic
if st.session_state.run_scraper:
    st.markdown("### 🖥️ Live Console Output")
    
    # Create a scrollable container for the log
    error_alert_area = st.empty()
    log_container = st.container(height=400)
    log_area = log_container.empty()
    
    # Build the command
    cmd = ["python", "main.py", "-s", source, "-t", topic, "-y", year, "-tk", task]
    if headless:
        cmd.append("--headless")
    
    # Execute and stream logs
    process = subprocess.Popen(
        cmd, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.STDOUT, 
        text=True, 
        bufsize=1, 
        universal_newlines=True
    )
    
    full_log = ""
    status_placeholder = st.empty()
    errors_found = []

    for line in process.stdout:
        clean_line = strip_ansi_codes(line)
        full_log += clean_line
        
        # Monitor for errors
        if "ERROR" in clean_line or "Exception" in clean_line:
            errors_found.append(clean_line.strip())
            error_alert_area.error(f"🚨 **Error detected!** Check logs below.\n\n{errors_found[-1]}")
            st.toast("🚨 Scraper Error Detected!", icon="🔥")
        
        # Look for the special [OUTPUT_PATH] tag to lock onto the correct file
        if "[OUTPUT_PATH]" in clean_line:
            path_match = clean_line.split("[OUTPUT_PATH]")[-1].strip()
            if path_match and path_match != "None":
                output_path = path_match

        # Every time we get a log line, check the file for a new count
        if output_path and os.path.exists(output_path):
            try:
                with open(output_path, "r", encoding="utf-8") as f:
                    live_data = json.load(f)
                    live_count = len(live_data.get("abstracts", []))
                    status_placeholder.metric("🚀 Live Abstracts Count", live_count)
            except:
                pass # File might be locked while writing, just skip this frame

        # Update log area
        log_area.code(full_log)
        
    process.wait()
    
    if process.returncode == 0:
        st.success("✅ Scraper finished successfully!")
        time.sleep(2)
        st.rerun()
    else:
        st.error(f"❌ Scraper failed with exit code {process.returncode}")
    
    st.session_state.run_scraper = False

# --- RESULTS VIEWER ---
st.markdown("---")
st.markdown("### 📊 Last Scrape Results")

# Output path is already calculated above in the metrics section
if output_path and os.path.exists(output_path):
    try:
        with open(output_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        abstracts = data.get("abstracts", [])
        
        if abstracts:
            st.success(f"Found **{len(abstracts)}** abstracts in `{output_path}`")
            
            # Show a table preview
            df = pd.DataFrame(abstracts)
            # Flatten metadata if present
            if 'abstract_metadata' in df.columns:
                meta_df = pd.json_normalize(df['abstract_metadata'])
                df = pd.concat([df.drop(columns=['abstract_metadata']), meta_df], axis=1)
            
            st.dataframe(df.head(50), use_container_width=True)
            
            # Download Button
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Results as CSV",
                data=csv,
                file_name=f"{topic}_{year}_results.csv",
                mime="text/csv",
            )
        else:
            st.warning("JSON file found but it contains no abstracts.")
            
    except Exception as e:
        st.error(f"Error loading results: {e}")
else:
    st.info(f"Waiting for output file: `{output_path}`")

# Footer
st.markdown("---")
st.caption(f"Mindgram Automation Engine | Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

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
    # Try both data/<topic> and data/<source>/<topic>
    search_dirs = [
        os.path.join("data", topic),
        os.path.join("data", source, topic),
        os.path.join("data", source, f"{topic}_{year}"),
    ]
    
    patterns = [
        f"{topic}_spring_{year}.json",
        f"{topic}_{year}.json",
        f"{topic}_{year}_abstracts.json",
        f"{topic}_{year}_urls.json",
        f"{topic}_fall_{year}.json",
        f"{topic}_summer_{year}.json",
        f"{topic}_winter_{year}.json",
    ]
    
    for base_dir in search_dirs:
        if not os.path.exists(base_dir):
            continue
            
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

# Initialize session state
if "run_scraper" not in st.session_state:
    st.session_state.run_scraper = False
if "current_process" not in st.session_state:
    st.session_state.current_process = None
if "logs" not in st.session_state:
    st.session_state.logs = []

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
    task_options = ["default", "url-scraper", "abstract-scraper", "duplicate-analyzer", "abstract-cleaner", "url-matcher"]
    task = st.selectbox("Select Task", task_options)

    # Headless Mode Toggle
    headless = st.checkbox("Run in Headless Mode", value=False, help="Runs the scraper without showing the browser window. Saves memory.")

    if not st.session_state.run_scraper:
        if st.button("🚀 RUN SCRAPER"):
            st.session_state.run_scraper = True
            st.rerun()
    else:
        if st.button("🛑 STOP SCRAPER"):
            if st.session_state.current_process:
                st.session_state.current_process.terminate()
                st.session_state.current_process = None
            st.session_state.run_scraper = False
            st.rerun()

    st.markdown("---")
    st.info("Select parameters and click RUN to start scraping.")

# --- MAIN AREA ---
st.title("🕸️ Mindgram Scraper Dashboard")
st.info(f"Target: **{source}** > **{topic}** > **{year}** [Task: **{task}**]")

# Parameters Layout
col1, col2, col3, col4, col5 = st.columns(5)

def metric_card(label, value, color="#ffffff", border_color="#3498db"):
    st.markdown(f"""
        <div style="background-color: #1e2128; padding: 15px; border-radius: 10px; border-left: 5px solid {border_color}; height: 100px;">
            <p style="color: #808495; margin: 0; font-size: 0.7rem; text-transform: uppercase; font-weight: bold;">{label}</p>
            <h2 style="color: {color}; margin: 0; font-size: 1.5rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{value}</h2>
        </div>
    """, unsafe_allow_html=True)

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
    metric_card("Source", source, border_color="#3498db")
with col2:
    metric_card("Topic", topic, border_color="#9b59b6")
with col3:
    metric_card("Year", year, border_color="#f1c40f")
with col4:
    total_count_placeholder = st.empty()
    with total_count_placeholder:
        metric_card("Total Abstracts", current_count, border_color="#e67e22")
with col5:
    session_count_placeholder = st.empty()
    with session_count_placeholder:
        metric_card("Session Count", "+0", color="#2ecc71", border_color="#2ecc71")

# Execution Logic
if "last_logs" not in st.session_state:
    st.session_state.last_logs = ""
if "current_process" not in st.session_state:
    st.session_state.current_process = None

if st.session_state.run_scraper or st.session_state.last_logs:
    st.markdown("### 🖥️ Live Console Output")
    
    # Create a scrollable container for the log
    error_alert_area = st.empty()
    log_container = st.container(height=400)
    log_area = log_container.empty()
    
    if st.session_state.run_scraper:
        # If we are starting but a process already exists
        if not st.session_state.current_process or st.session_state.current_process.poll() is not None:
            # Build the command
            cmd = ["python", "main.py", "-s", source, "-t", topic, "-y", year, "-tk", task]
            if headless:
                cmd.append("--headless")
            
            # Execute and stream logs
            st.session_state.last_logs = ""
            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT, 
                text=True, 
                bufsize=1, 
                universal_newlines=True
            )
            st.session_state.current_process = process
        else:
            process = st.session_state.current_process
            
        full_log = st.session_state.last_logs
        errors_found = []

        # Live streaming loop
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
                
            if line:
                clean_line = strip_ansi_codes(line)
                full_log += clean_line
                
                # Monitor for errors
                if "ERROR" in clean_line or "Exception" in clean_line:
                    errors_found.append(clean_line.strip())
                    error_alert_area.error(f"🚨 **Error detected!** Check logs below.\n\n{errors_found[-1]}")
                    st.toast("🚨 Scraper Error Detected!", icon="🔥")
                
                # Look for output path
                if "[OUTPUT_PATH]" in clean_line:
                    path_match = clean_line.split("[OUTPUT_PATH]")[-1].strip()
                    if path_match and path_match != "None":
                        output_path = path_match

                # Update count
                if output_path and os.path.exists(output_path):
                    try:
                        with open(output_path, "r", encoding="utf-8") as f:
                            live_data = json.load(f)
                            live_count = len(live_data.get("abstracts", []))
                            session_increment = live_count - current_count
                            
                            # Update Total Count
                            with total_count_placeholder:
                                metric_card("Total Abstracts", live_count, border_color="#e67e22")
                            
                            # Update Session Count
                            with session_count_placeholder:
                                metric_card("Session Count", f"+{session_increment}", color="#2ecc71", border_color="#2ecc71")
                    except:
                        pass

                # Update log area
                st.session_state.last_logs = full_log
                log_area.code(full_log)
        
        # Wait for process to finish
        process.wait()
        
        if process.returncode == 0:
            st.success("✅ Scraper finished successfully!")
            st.session_state.run_scraper = False
            st.session_state.current_process = None
            time.sleep(3)
            st.rerun()
        else:
            st.error(f"❌ Scraper failed with exit code {process.returncode}")
            st.session_state.run_scraper = False
            st.session_state.current_process = None
    else:
        # Just show the logs from the previous run
        log_area.code(st.session_state.last_logs)

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

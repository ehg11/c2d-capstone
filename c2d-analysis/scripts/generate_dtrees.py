import os
import subprocess
from datetime import datetime

def log(message, icon="📝"):
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    print(f"{timestamp} {icon} {message}")

# Define directories
cnf_dir = './cnfs'
dtree_log_dir = './dtree_logs'

# Create the dtree_logs directory if it doesn't exist
os.makedirs(dtree_log_dir, exist_ok=True)

# Loop through all the .cnf files in ./cnfs
for cnf_file in os.listdir(cnf_dir):
    if cnf_file.endswith('.cnf'):
        cnf_path = os.path.join(cnf_dir, cnf_file)
        dtree_file_path = os.path.join(cnf_dir, f"{cnf_file}.dtree")

        # Skip if the .dtree file already exists
        if os.path.exists(dtree_file_path):
            log(f"Skipping {cnf_file} — .dtree file already exists.", icon="⚠️")
            continue

        # Let the user know which CNF is being processed
        log(f"Running c2d on {cnf_file}", icon="🏃")

        # Define the output log path
        log_path = os.path.join(dtree_log_dir, f"{cnf_file}.log")

        # Run the c2d command with a timeout of 1 hour
        command = ["./build/c2d", "-in", cnf_path, "-dt_out"]
        try:
            with open(log_path, 'w') as log_file:
                subprocess.run(command, stdout=log_file, stderr=subprocess.PIPE, check=True, timeout=3600)
            log(f"Processed {cnf_file}, log saved to {log_path}", icon="✅")
        except subprocess.TimeoutExpired:
            log(f"Timeout expired for {cnf_file} after 1 hour", icon="⏰")
        except subprocess.CalledProcessError as e:
            log(f"Error processing {cnf_file}: {e}", icon="❌")

import os
import subprocess
from pathlib import Path
from datetime import datetime

def timestamped_print(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")

def process_cnfs():
    # Create output directories if they don't exist
    Path("./vtree").mkdir(parents=True, exist_ok=True)
    Path("./vtree_logs").mkdir(parents=True, exist_ok=True)

    # Get all CNF files in the ./cnfs directory
    cnf_dir = "./cnfs"
    for cnf_file in os.listdir(cnf_dir):
        if cnf_file.endswith(".cnf"):
            vtree_filename = f"{cnf_file}.vtree"
            vtree_path = os.path.join("./vtree", vtree_filename)

            # Skip files that already have a vtree generated
            if os.path.exists(vtree_path):
                timestamped_print(f"⏩ Skipping {cnf_file} (vtree already exists)")
                continue

            cnf_path = os.path.join(cnf_dir, cnf_file)
            log_output = os.path.join("./vtree_logs", f"{cnf_file}.log")

            cmd = [
                "./bin/linux/miniC2D",
                "--cnf", cnf_path,
                "--vtree_out", vtree_path,
                "--vtree_method", "4"
            ]

            timestamped_print(f"🛠️ Processing {cnf_file}...")

            try:
                with open(log_output, 'w') as log_file:
                    result = subprocess.run(
                        cmd,
                        stdout=log_file,
                        stderr=subprocess.STDOUT,
                        text=True,
                        timeout=7200  # 2 hours = 7200 seconds
                    )

                if result.returncode != 0:
                    timestamped_print(f"⚠️ Error processing {cnf_file} (exit code: {result.returncode})")
                else:
                    timestamped_print(f"✅ Successfully processed {cnf_file}")

            except subprocess.TimeoutExpired:
                timestamped_print(f"⏰ Timeout expired for {cnf_file} after 2 hours")

if __name__ == "__main__":
    process_cnfs()

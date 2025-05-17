import os
import subprocess
import argparse
from pathlib import Path
from datetime import datetime

MAX_DELAY_MS = 1 * 60 * 60 * 1000

def log(msg):
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    print(f"{timestamp} {msg}")

def ensure_directories():
    Path("./stdout").mkdir(parents=True, exist_ok=True)
    Path("./perf-report").mkdir(parents=True, exist_ok=True)

def run_profiling():
    cnf_dir = "./cnfs"
    dtree_dir = "./dtrees"

    for cnf_file in os.listdir(cnf_dir):
        if not cnf_file.endswith(".cnf"):
            continue

        base_name = cnf_file.replace(".cnf", "")
        cnf_path = os.path.join(cnf_dir, cnf_file)
        dtree_path = os.path.join(dtree_dir, f"{cnf_file}.dtree")
        stdout_log = os.path.join("./stdout", f"{cnf_file}.log")
        perf_report_log = os.path.join("./perf-report", f"{cnf_file}.log")

        if not os.path.exists(dtree_path):
            log(f"⚠️ Skipping {cnf_file}: Missing dtree file.")
            continue

        if os.path.exists(perf_report_log):
            log(f"⏭️ Skipping {cnf_file}: Perf report already exists.")
            continue

        cmd = (
            f"perf record --call-graph fp --delay=0-{MAX_DELAY_MS} "
            f"./build/c2d -in {cnf_path} -dt_in {dtree_path} -in_memory"
        )

        log(f"📦 Profiling {cnf_file}")
        log(f"Command: {cmd}")

        with open(stdout_log, 'w') as out_file:
            process = subprocess.run(
                cmd,
                stdout=out_file,
                stderr=subprocess.STDOUT,
                shell=True
            )
            if process.returncode not in [0, 143]:
                log(f"⚠️ Failed to profile {cnf_file} (exit code: {process.returncode})")
                continue
            if process.returncode == 143:
                log(f"⏱️ Timeout expired profiling {cnf_file}")
            else:
                log(f"✅ Finished profiling {cnf_file}")

        log(f"📊 Generating perf report for {cnf_file}...")
        with open(perf_report_log, 'w') as report_file:
            subprocess.run(
                "perf report -g --call-graph=folded,0.01 --stdio | c++filt",
                shell=True,
                stdout=report_file,
                stderr=subprocess.STDOUT
            )

        for f in ["perf.data", "perf.data.old"]:
            try:
                os.remove(f)
            except FileNotFoundError:
                pass

        log(f"🧹 Cleanup done for {cnf_file}")

if __name__ == "__main__":
    ensure_directories()
    run_profiling()

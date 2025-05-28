import os
import subprocess
import argparse
from pathlib import Path
from datetime import datetime

MAX_DELAY_MS = 1 * 60 * 60 * 1000 # hours * min/hr * sec/min * ms/sec

def log(msg):
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    print(f"{timestamp} {msg}")

def ensure_directories():
    Path("./stdout").mkdir(parents=True, exist_ok=True)
    Path("./perf-report").mkdir(parents=True, exist_ok=True)

def get_delay_range(log_path):
    try:
        with open(log_path, 'r') as f:
            for line in f:
                if line.strip().startswith("Vtree Time"):
                    time_str = line.strip().split()[-1].replace('s', '')
                    vtree_seconds = float(time_str)
                    start_ms = int(vtree_seconds * 1000)
                    end_ms = start_ms + MAX_DELAY_MS
                    return f"{start_ms}-{end_ms}"
    except Exception as e:
        log(f"⚠️ Failed to parse vtree time from {log_path}: {e}")
    return None

def run_profiling(use_vtree_input=False):
    cnf_dir = "./cnfs"
    vtree_dir = "./vtree"
    vtree_logs_dir = "./vtree_logs/valid"

    for cnf_file in os.listdir(cnf_dir):
        if not cnf_file.endswith(".cnf"):
            continue

        cnf_path = os.path.join(cnf_dir, cnf_file)
        vtree_path = os.path.join(vtree_dir, f"{cnf_file}.vtree")
        vtree_log_path = os.path.join(vtree_logs_dir, f"{cnf_file}.log")
        stdout_log = os.path.join("./stdout", f"{cnf_file}.log")
        perf_report_log = os.path.join("./perf-report", f"{cnf_file}.log")

        if not os.path.exists(vtree_log_path):
            continue

        if use_vtree_input and not os.path.exists(vtree_path):
            log(f"⚠️ Skipping {cnf_file}: VTree not found.")
            continue

        if os.path.exists(perf_report_log):
            log(f"⏭️ Skipping {cnf_file}: Perf report already exists.")
            continue

        delay_range = get_delay_range(vtree_log_path)
        if not delay_range:
            log(f"⚠️ Skipping {cnf_file}: Could not determine delay range.")
            continue

        cmd = (
            f"perf record -F max --call-graph dwarf,16384 --delay={delay_range} "
            f"./bin/linux/miniC2D --cnf {cnf_path} "
        )
        if use_vtree_input:
            cmd += f"--vtree {vtree_path}"
        else:
            cmd += f"--vtree_method 4"

        log(f"📦 Profiling {cnf_file} with --delay={delay_range}")

        # Run perf record and capture both perf and time output
        log(f"Command: {cmd}")
        with open(stdout_log, 'w') as out_file:
            process = subprocess.run(
                cmd,
                stdout=out_file,
                stderr=subprocess.STDOUT,
                shell=True
            )
            if process.returncode not in [0, 143]: # 143 is perf delay timeout
                log(f"⚠️ Failed to profile {cnf_file} (exit code: {process.returncode})")
                continue
            if process.returncode == 143:
                log(f"Timeout expired profiling {cnf_file}")
            else:
                log(f"✅ Finished profiling {cnf_file}")

        # Generate the perf report
        log(f"📊 Generating perf report for {cnf_file}...")
        with open(perf_report_log, 'w') as report_file:
            subprocess.run(
                "perf report -g --call-graph=folded,0.01 --stdio | c++filt",
                shell=True,
                stdout=report_file,
                stderr=subprocess.STDOUT
            )

        # Clean up artifacts
        nnf_file = os.path.join(cnf_dir, f"{cnf_file}.nnf")
        for f in [nnf_file, "perf.data", "perf.data.old"]:
            try:
                os.remove(f)
            except FileNotFoundError:
                pass

        log(f"🧹 Cleanup done for {cnf_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--use_vtree_input",
        action="store_true",
        default=False,
        help="Use --vtree <file> instead of --vtree_method 4"
    )
    args = parser.parse_args()
    ensure_directories()
    run_profiling(use_vtree_input=args.use_vtree_input)

import os
import shutil
import pandas as pd


class CNFAnalyzer:
    def __init__(self, cnfs_dir, valid_stdouts_dir):
        self.cnfs_dir = cnfs_dir
        self.valid_stdouts_dir = valid_stdouts_dir
        self.valid_cnfs_dir = os.path.join(cnfs_dir, "valid")
        self.invalid_cnfs_dir = os.path.join(cnfs_dir, "invalid")

        self.stats_by_category = {
            "all": [],
            "completed": [],
            "timed_out": [],
        }

        os.makedirs(self.valid_cnfs_dir, exist_ok=True)
        os.makedirs(self.invalid_cnfs_dir, exist_ok=True)

    def preprocess(self):
        for file in os.listdir(self.cnfs_dir):
            if not file.endswith(".cnf"):
                continue

            log_path = os.path.join(self.valid_stdouts_dir, f"{file}.log")
            src_path = os.path.join(self.cnfs_dir, file)

            if os.path.exists(log_path):
                dst_path = os.path.join(self.valid_cnfs_dir, file)
            else:
                dst_path = os.path.join(self.invalid_cnfs_dir, file)

            shutil.move(src_path, dst_path)
            print(f"Moved {file} to {dst_path}")

    def analyze(self):
        for file in os.listdir(self.valid_cnfs_dir):
            if not file.endswith(".cnf"):
                continue

            path = os.path.join(self.valid_cnfs_dir, file)
            stats = self._analyze_file(path)
            self.stats_by_category["all"].append(stats)

            if self._cnf_timed_out(file):
                self.stats_by_category["timed_out"].append(stats)
            else:
                self.stats_by_category["completed"].append(stats)

        return self.stats_by_category

    def average_stats(self):
        self.analyze()
        averages = {}

        for category, stats_list in self.stats_by_category.items():
            if len(stats_list) == 0:
                continue

            total = {
                "num_vars": 0,
                "num_clauses": 0,
                "total_size": 0,
            }
            for stat in stats_list:
                total["num_vars"] += stat["num_vars"]
                total["num_clauses"] += stat["num_clauses"]
                total["total_size"] += stat["total_size"]

            num_cnfs = len(stats_list)
            averages[category] = {
                "num_vars": total["num_vars"] / num_cnfs,
                "num_clauses": total["num_clauses"] / num_cnfs,
                "total_size": total["total_size"] / num_cnfs,
            }

        return averages

    def average_stats_to_latex(self):
        avg = self.average_stats()
        rows = []
        for category, stats in avg.items():
            row = {"category": category}
            row.update(stats)
            rows.append(row)

        df = pd.DataFrame(rows)
        for col in df.columns:
            if col != "category":
                df[col] = df[col].apply(
                    lambda x: (
                        f"{x:.2f}".rstrip("0").rstrip(".")
                        if isinstance(x, float)
                        else x
                    )
                )
        return df.to_latex(index=False, escape=True)

    def _analyze_file(self, cnf_path):
        num_vars = 0
        num_clauses = 0
        total_size = 0

        with open(cnf_path, "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith("c"):
                    continue
                elif line.startswith("p cnf"):
                    _, _, num_vars, num_clauses = line.split()
                    num_vars = int(num_vars)
                    num_clauses = int(num_clauses)
                else:
                    literals = line.split()
                    total_size += len([lit for lit in literals if lit != "0"])

        return {
            "num_vars": num_vars,
            "num_clauses": num_clauses,
            "total_size": total_size,
        }

    def _cnf_timed_out(self, cnf_name):
        log_file = os.path.join(self.valid_stdouts_dir, f"{cnf_name}.log")
        if not os.path.exists(log_file):
            return False
        with open(log_file, "r") as f:
            return "Total Time:" not in f.read()

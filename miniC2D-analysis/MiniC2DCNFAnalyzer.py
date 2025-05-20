import os
from CNFAnalyzer import CNFAnalyzer


class MiniC2DCNFAnalyzer(CNFAnalyzer):
    def __init__(self, cnfs_dir, valid_stdouts_dir):
        super().__init__(cnfs_dir, valid_stdouts_dir)

    def _cnf_timed_out(self, cnf_name):
        log_path = os.path.join(self.valid_stdouts_dir, f"{cnf_name}.log")
        if not os.path.exists(log_path):
            return False

        with open(log_path, "r") as f:
            return "Total Time:" not in f.read()

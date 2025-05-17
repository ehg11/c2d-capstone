import os
import shutil


class Preprocessor:
    """
    Some stdouts were generated with the old config (not 1hr timeout)
    """

    def __init__(self, stdout_dir, perf_report_dir):
        self.stdout_dir = stdout_dir
        self.valid_dir = os.path.join(self.stdout_dir, "valid")
        self.invalid_dir = os.path.join(self.stdout_dir, "invalid")
        self.perf_report_dir = perf_report_dir

        os.makedirs(self.valid_dir, exist_ok=True)
        os.makedirs(self.invalid_dir, exist_ok=True)

    def filter_stdout(self):
        perf_reports = set(os.listdir(self.perf_report_dir))
        for filename in os.listdir(self.stdout_dir):
            filepath = os.path.join(self.stdout_dir, filename)
            if not os.path.isfile(filepath):
                continue

            if filename in perf_reports:
                shutil.move(filepath, os.path.join(self.valid_dir, filename))
            else:
                shutil.move(filepath, os.path.join(self.invalid_dir, filename))

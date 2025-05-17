import os
import shutil


class Preprocessor:
    """
    Some dtrees did not match the CNF
    """

    VALID_KEYWORD = "Compiling..."

    def __init__(self, stdout_dir):
        self.stdout_dir = stdout_dir
        self.valid_dir = os.path.join(self.stdout_dir, "valid")
        self.invalid_dir = os.path.join(self.stdout_dir, "invalid")

        os.makedirs(self.valid_dir, exist_ok=True)
        os.makedirs(self.invalid_dir, exist_ok=True)

    def filter_stdout(self):
        for filename in os.listdir(self.stdout_dir):
            filepath = os.path.join(self.stdout_dir, filename)
            if not os.path.isfile(filepath):
                continue

            try:
                with open(filepath, "r") as f:
                    contents = f.read()
                    if Preprocessor.VALID_KEYWORD in contents:
                        shutil.move(filepath, os.path.join(self.valid_dir, filename))
                    else:
                        shutil.move(filepath, os.path.join(self.invalid_dir, filename))
            except Exception as e:
                print(f"Error processing file {filename}: {e}")

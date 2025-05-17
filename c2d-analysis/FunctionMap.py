from pathlib import Path
import json
from PerfParser import AbstractFunctionMap


class FunctionMap(AbstractFunctionMap):
    def __init__(self, category_to_file_path, tags_path):
        self.category_to_file_path = Path(category_to_file_path)
        self.tags_path = Path(tags_path)

        self.category_to_files = self._init_category_to_files()
        self.file_to_category = self._init_file_to_category()
        self.function_to_category = self._init_function_to_category()

    def get_category(self, function_name):
        return self.function_to_category.get(function_name)

    def _init_category_to_files(self):
        category_to_files = {}
        with open(self.category_to_file_path, "r") as f:
            category_to_files = json.load(f)
        return category_to_files

    def _init_file_to_category(self):
        file_to_category = {}
        for category, files in self.category_to_files.items():
            for file in files:
                file_to_category[file] = category
        return file_to_category

    def _init_function_to_category(self):
        function_to_category = {}
        with open(self.tags_path, "r") as f:
            tags = json.load(f)

        for tag in tags:
            if tag.get("kind") != "function":
                continue
            function_name = tag.get("name")
            if not function_name:
                continue
            file_name = tag.get("path")
            if not file_name:
                continue
            category = self.file_to_category.get(file_name)
            if not category:
                continue
            function_to_category[function_name] = category
        return function_to_category

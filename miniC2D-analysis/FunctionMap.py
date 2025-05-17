from pathlib import Path
import json


class FunctionMap:
    UNCATEGORIZED = "None"

    def __init__(self, category_to_function_path):
        self.category_to_function_path = Path(category_to_function_path)

        self.category_to_functions = self._init_category_to_functions()
        self.function_to_category = self._init_function_to_category()

    def get_category(self, function_name):
        return self.function_to_category.get(function_name)

    def _init_category_to_functions(self):
        category_to_functions = {}
        with open(self.category_to_function_path, "r") as f:
            category_to_functions = json.load(f)
        return category_to_functions

    def _init_function_to_category(self):
        function_to_category = {}
        for category, functions in self.category_to_functions.items():
            for function in functions:
                function_to_category[function] = category
        return function_to_category

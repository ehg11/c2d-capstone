import json
import pandas as pd
from pathlib import Path
from FunctionMap import FunctionMap


class PerfTableGenerator:
    TIME_THRESH = 9e-3

    def __init__(self, agg_stats_path, category_stats_path):
        self.agg_stats_path = Path(agg_stats_path)
        self.category_stats_path = Path(category_stats_path)

        with open(self.agg_stats_path, "r") as f:
            self.agg_stats = json.load(f)
        with open(self.category_stats_path, "r") as f:
            self.category_stats = json.load(f)

    def generate_function_table_latex(self):
        """
        Columns: Function Name, Category, Total Time, Percent Time
        """
        data = []
        for function_name, stats in self.agg_stats.items():
            category = stats.get("category", FunctionMap.UNCATEGORIZED)
            time_spent = stats.get("time", 0)
            percent_time = stats.get("pct", 0) * 100

            if time_spent < PerfTableGenerator.TIME_THRESH:
                continue
            if percent_time < PerfTableGenerator.TIME_THRESH:
                continue

            row = {
                "Function Name": function_name,
                "Category": category,
                "Total Time": time_spent,
                "Percent Time": percent_time,
            }
            data.append(row)
        df = pd.DataFrame(data)
        df = df.sort_values(by="Total Time", ascending=False)
        df["Total Time"] = df["Total Time"].apply(lambda x: f"{x:.2f}")
        df["Percent Time"] = df["Percent Time"].apply(lambda x: f"{x:.2f}")

        return df.to_latex(index=False, escape=True)

    def generate_category_table_latex(self):
        """
        Columns: Category, Total Time, Percent Time
        """
        data = []
        for category, stats in self.category_stats.items():
            time_spent = stats.get("time", 0)
            percent_time = stats.get("pct", 0) * 100

            if time_spent < PerfTableGenerator.TIME_THRESH:
                continue
            if percent_time < PerfTableGenerator.TIME_THRESH:
                continue

            row = {
                "Category": category,
                "Total Time": time_spent,
                "Percent Time": percent_time,
            }
            data.append(row)
        df = pd.DataFrame(data)
        df = df.sort_values(by="Total Time", ascending=False)
        df["Total Time"] = df["Total Time"].apply(lambda x: f"{x:.2f}")
        df["Percent Time"] = df["Percent Time"].apply(lambda x: f"{x:.2f}")

        return df.to_latex(index=False, escape=True)

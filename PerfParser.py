from pathlib import Path
import re
from tqdm import tqdm
import json

from FunctionMap import FunctionMap


class PerfParser:
    TIMEOUT = 3600

    def __init__(
        self,
        perf_dir="perf-report/",
        stdout_dir="stdout/valid",
        category_to_file_path="tags/category_to_file.json",
        tags_path="tags/tags.json",
        normalize=True,
    ):
        self.perf_dir = Path(perf_dir)
        self.stdout_dir = Path(stdout_dir)
        self.cnfs = self._get_cnf_names()
        self.function_map = FunctionMap(category_to_file_path, tags_path)

        # normalize self_pct's to guarantee they add to 100%
        self.normalize = normalize

        self.cnf_stats = self._init_cnf_stats()
        self.aggregate_stats = self._aggregate_cnf_stats()
        self.category_stats = self._aggregate_cnf_stats_by_category()

    def save_stats_to_json(self, output_path):
        output_path = Path(output_path)
        with open(output_path, "w") as f:
            json.dump(self.cnf_stats, f, indent=4)

    def save_agg_stats_to_json(self, output_path):
        output_path = Path(output_path)
        with open(output_path, "w") as f:
            json.dump(self.aggregate_stats, f, indent=4)

    def save_category_stats_to_json(self, output_path):
        output_path = Path(output_path)
        with open(output_path, "w") as f:
            json.dump(self.category_stats, f, indent=4)

    def _init_cnf_stats(self):
        """
        CNF Field:
        - stats
        - time: reported runtime

        Stats Fields:
        - children_pct
        - self_pct
        - command: c2d
        - sharedobject: c2d
        - symbol: function name
        - norm_self_pct: self_pct / total_self_pct
            - making self_pct actually add to 1
        - category
        """
        cnf_stats = {}
        for cnf in tqdm(self.cnfs, desc="Initializing CNF Stats..."):
            cnf_stats[cnf] = {}
            stats = self._get_cnf_stats(cnf)
            if stats is None:
                continue

            norm_stats = self._normalize_cnf_stats(stats)
            for stat in norm_stats:
                function_name = stat["symbol"]
                category = self.function_map.get_category(function_name)
                if category is None:
                    category = FunctionMap.UNCATEGORIZED
                stat["category"] = category

            cnf_stats[cnf]["stats"] = norm_stats
            cnf_stats[cnf]["time"] = self._get_cnf_runtime(cnf)

        cnf_stats = dict(
            sorted(
                cnf_stats.items(),
                key=lambda item: (item[1].get("time") or PerfParser.TIMEOUT),
                reverse=True,
            )
        )

        return cnf_stats

    def _aggregate_cnf_stats(self):
        """
        Returns {
            ...
            function_name: {
                time: total seconds spent by the function
                pct: percentage of total runtime spent by the function
            },
            ...
        }
        """
        total_time = sum(stat.get("time", 0) for stat in self.cnf_stats.values())
        assert total_time > 0, "Total time should be greater than 0"

        function_times = {}
        for cnf, data in self.cnf_stats.items():
            stats = data.get("stats", [])
            cnf_time = data.get("time", 0)
            if cnf_time == 0:
                continue

            for stat in stats:
                function_name = stat["symbol"]
                self_pct = (
                    stat["norm_self_pct"]
                    if self.normalize
                    else (stat["self_pct"] / 100.0)
                )
                function_time = self_pct * cnf_time

                function_times[function_name] = (
                    function_times.get(function_name, 0) + function_time
                )

        function_stats = {}
        for function_name, function_time in function_times.items():
            function_stats[function_name] = {
                "time": function_time,
                "pct": function_time / total_time,
                "category": self.function_map.get_category(function_name),
            }
        function_stats = dict(
            sorted(
                function_stats.items(),
                key=lambda item: item[1]["time"],
                reverse=True,
            )
        )

        return function_stats

    def _aggregate_cnf_stats_by_category(self):
        """
        Returns {
            ...
            category: {
                time: total seconds spent by the category
                pct: percentage of total runtime spent by the category
            },
            ...
        }
        """
        category_times = {}

        for func, stats in self.aggregate_stats.items():
            category = stats.get("category", FunctionMap.UNCATEGORIZED)
            time = stats.get("time", 0)
            if time == 0:
                continue
            category_times[category] = category_times.get(category, 0) + time

        total_time = sum(category_times.values())
        assert total_time > 0, "Total time should be greater than 0"

        category_stats = {}
        for category, time in category_times.items():
            category_stats[category] = {
                "time": time,
                "pct": time / total_time,
            }

        category_stats = dict(
            sorted(
                category_stats.items(),
                key=lambda item: item[1]["time"],
                reverse=True,
            )
        )

        return category_stats

    def _get_cnf_names(self):
        cnf_names = []
        for file_path in self.perf_dir.iterdir():
            if file_path.is_file() and file_path.name.endswith(".log"):
                # strip the .log to get the pure cnf filename
                cnf_name = file_path.name.rstrip(".log")
                cnf_names.append(cnf_name)
        return cnf_names

    def _normalize_cnf_stats(self, cnf_stats):
        total_self_pct = self._get_total_self_pct(cnf_stats)
        for stat in cnf_stats:
            stat["norm_self_pct"] = stat["self_pct"] / total_self_pct
        return cnf_stats

    def _get_cnf_stats(self, cnf_name):
        perf_report = self.perf_dir / f"{cnf_name}.log"
        if not perf_report.exists():
            return None
        with open(perf_report, "r") as f:
            lines = f.readlines()
            parsed = [match_main_line(line) for line in lines]
            parsed = [
                p
                for p in parsed
                if (
                    p is not None
                    and p["sharedobject"] == "c2d"
                    and "@" not in p["symbol"]
                    and "__" not in p["symbol"]
                    and not p["symbol"].startswith("_")
                    and not p["symbol"].startswith("0x")
                )
            ]

            # sort in descending order by self_pct
            parsed = sorted(parsed, key=lambda x: x["self_pct"], reverse=True)
            return parsed

    def _get_total_self_pct(self, cnf_stats):
        return sum([st["self_pct"] for st in cnf_stats])

    def _get_cnf_runtime(self, cnf_name):
        log_path = Path(f"./stdout/valid/{cnf_name}.log")
        if not log_path.exists():
            return None

        with open(log_path, "r") as f:
            for line in f:
                if line.startswith("Total Time:"):
                    time_str = line.split(":")[1].strip().rstrip("s")
                    return float(time_str)
        return PerfParser.TIMEOUT


def match_main_line(line):
    children_pct_pattern = r"\s*(?P<children_pct>\d+\.\d+)%"
    self_pct_pattern = r"\s+(?P<self_pct>\d+\.\d+)%"
    command_pattern = r"\s+(?P<command>\S+)"
    sharedobject_pattern = r"\s+(?P<sharedobject>\S+)"
    symbol_pattern = r"\s+\[\.\]\s+(?P<symbol>\S+)"
    pattern = (
        "^"
        + children_pct_pattern
        + self_pct_pattern
        + command_pattern
        + sharedobject_pattern
        + symbol_pattern
        + "$"
    )

    match = re.match(pattern, line)
    if match:
        res = match.groupdict()
        res["children_pct"] = float(res["children_pct"])
        res["self_pct"] = float(res["self_pct"])
        return res
    else:
        return None


def get_total_self_pct(fn_pcts):
    return sum([pct["self_pct"] for pct in fn_pcts])


def get_cnf_runtime(cnf_name):
    TIMEOUT = 3600
    log_path = Path(f"./stdout/valid/{cnf_name}.log")
    if not log_path.exists():
        return None

    with open(log_path, "r") as f:
        for line in f:
            if line.startswith("Total Time:"):
                time_str = line.split(":")[1].strip().rstrip("s")
                return float(time_str)
    return TIMEOUT

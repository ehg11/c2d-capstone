import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from PerfParser import PerfParser


class SatPlotter:
    def __init__(self, cnf_stats_path):
        self.cnf_stats_path = Path(cnf_stats_path)
        with open(self.cnf_stats_path, "r") as f:
            self.cnf_stats = json.load(f)

    def plot_sat_time_percent(self, normalize=False, show_best_fit=True):
        x = []
        y = []
        x_timeout = []
        y_timeout = []

        for data in self.cnf_stats.values():
            total_time = data.get("time", PerfParser.TIMEOUT)
            stats = data.get("stats", [])
            if not stats:
                continue

            sat_self_pct = 0
            for stat in stats:
                if stat.get("category") == "sat":
                    self_pct = (
                        stat.get("norm_self_pct", 0)
                        if normalize
                        else (stat.get("self_pct", 0) / 100.0)
                    )
                    sat_self_pct += self_pct

            if total_time == PerfParser.TIMEOUT:
                x_timeout.append(total_time)
                y_timeout.append(sat_self_pct)
            else:
                x.append(total_time)
                y.append(sat_self_pct)

        plt.figure(figsize=(10, 10))
        plt.scatter(x, y, color="blue", label="Completed")
        plt.scatter(x_timeout, y_timeout, color="red", label="Timed Out", marker="x")

        if show_best_fit:
            x_fit, y_fit = self._get_best_fit(x, y)
            plt.plot(
                x_fit, y_fit, color="green", label="Best Fit Line (log-scale on x-axis)"
            )

        plt.xlabel("Total Time Spent Compiling (seconds, log-scale)")
        plt.ylabel("Percent of Time in SAT Functions")
        plt.title("SAT Function Percent vs. CNF Compile Time")
        plt.legend()
        plt.xscale("log")
        plt.ylim(0, 1)

        plt.show()

    def _get_best_fit(self, x, y):
        x_np = np.array(x)
        y_np = np.array(y)

        coeffs = np.polyfit(np.log(x_np), y_np, deg=1)
        best_fit_fn = np.poly1d(coeffs)
        x_fit = np.linspace(x_np.min(), x_np.max(), 500)
        y_fit = best_fit_fn(np.log(x_fit))

        return x_fit, y_fit

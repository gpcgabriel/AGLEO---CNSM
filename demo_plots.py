import json
import os
import numpy as np
import matplotlib.pyplot as plt

markers = ['o', 'x', 's', '^', 'D', '*', 'v', '+']
linestyles = ['-', '--', '-.', ':']
linewidths = [2.5, 2.0, 1.8, 1.5]
colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2']

def read_jsonl(file_path):
    with open(file_path) as f:
        for line in f:
            yield json.loads(line)

def build_path(current_path, alg, scenario, filename, rep):
    return os.path.join(current_path, alg, scenario, f"rep{rep}", filename)

def detect_repetitions(current_path, algorithm_names, scenario):
    max_rep = 0
    for alg in algorithm_names:
        rep_dir = os.path.join(current_path, alg, scenario)
        if not os.path.isdir(rep_dir):
            continue
        for entry in os.listdir(rep_dir):
            if entry.startswith("rep"):
                try:
                    n = int(entry[3:])
                    if n > max_rep:
                        max_rep = n
                except ValueError:
                    pass
    return max_rep

def plot_provisioned_with_std(algorithm_names, scenarios, num_repetitions, current_path):
    for scenario in scenarios:
        print(f"Processing scenario: {scenario}")

        if num_repetitions is None:
            num_repetitions = detect_repetitions(current_path, algorithm_names, scenario)
            print(f"  Auto-detected {num_repetitions} repetition(s)")

        means = {}
        stds = {}
        steps_dict = {}

        for alg in algorithm_names:
            reps_prov = []
            captured_steps = []

            for rep in range(1, num_repetitions + 1):
                file_path = build_path(current_path, alg, scenario, "User.jsonl", rep)

                if not os.path.isfile(file_path):
                    print(f"WARNING: {file_path} not found")
                    continue

                curr_steps = []
                curr_prov = []
                last_accesses = {}

                for data in read_jsonl(file_path):
                    step = data["Step"]
                    step_prov = 0

                    for metric in data["metrics"]:
                        current = metric["Access to Applications"][0]

                        if metric["ID"] not in last_accesses:
                            last_accesses[metric["ID"]] = current
                            continue

                        if current["Is Provisioned"] or current["Provisioning"]:
                            step_prov += 1

                        last_accesses[metric["ID"]] = current

                    curr_steps.append(step)
                    curr_prov.append(step_prov)

                reps_prov.append(curr_prov)

                if not captured_steps:
                    captured_steps = curr_steps

            if reps_prov:
                min_len = min(len(l) for l in reps_prov)
                reps_aligned = [l[:min_len] for l in reps_prov]

                arr = np.array(reps_aligned, dtype=float)
                means[alg] = np.mean(arr, axis=0)
                ddof = 1 if arr.shape[0] > 1 else 0
                stds[alg] = np.std(arr, axis=0, ddof=ddof)
                steps_dict[alg] = captured_steps[:min_len]

        legend_names = {
            "best_fit_allocation": "Best Fit",
            "longest_duration_allocation": "Longest Duration",
            "llm_orchestrator": "Agentic Placement",
        }

        fig, ax = plt.subplots(figsize=(12, 7))

        for i, label in enumerate(means):
            x = steps_dict[label]
            y = means[label]
            yerr = stds[label]
            display = legend_names.get(label, label)

            color = colors[i % len(colors)]
            marker = markers[i % len(markers)]
            ls = linestyles[i % len(linestyles)]
            lw = linewidths[i % len(linewidths)]

            ax.plot(x, y, label=display, color=color, marker=marker,
                    linestyle=ls, linewidth=lw, alpha=0.85)
            ax.fill_between(x, y - yerr, y + yerr, color=color, alpha=0.15)

        ax.set_xlabel("Step", fontsize=26)
        ax.set_ylabel("Avg Provisioned Applications", fontsize=26)
        ax.set_xlim(0, 30)
        ax.set_ylim(0, 80)
        ax.tick_params(axis='both', labelsize=24)
        ax.grid(True, alpha=0.8, linestyle='--', linewidth=0.5)
        ax.legend(fontsize=22, frameon=True, edgecolor="black",
                  facecolor="white", framealpha=1)

        plt.tight_layout()
        plt.savefig(os.path.join(current_path, f"provisioned_{scenario}.png"))
        plt.close()
        print(f"Saved: provisioned_{scenario}.png")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Plot provisioned apps with std deviation")
    parser.add_argument("--logs_dir", default="logs")
    parser.add_argument("--scenario", default="hybrid")
    parser.add_argument("--repetitions", type=int, default=None)

    args = parser.parse_args()

    algs = [
        "best_fit_allocation",
        "longest_duration_allocation",
        "llm_orchestrator",
    ]

    plot_provisioned_with_std(algs, [args.scenario], args.repetitions, args.logs_dir)

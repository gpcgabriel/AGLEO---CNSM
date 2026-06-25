#!/usr/bin/env bash
set -euo pipefail

DATASET="datasets/rnp.gml"
SATELLITES="datasets/satellites_brazil.json"
SCENARIO="hybrid"
NUM_STEPS=15
NUM_USERS=100
NUM_SATELLITES=25
REPETITIONS=1
SEED=""

usage() {
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --dataset <path>       Ground topology GML file (default: $DATASET)"
    echo "  --satellites <path>    Satellite trajectory JSON (default: $SATELLITES)"
    echo "  --scenario <name>      Simulation scenario (default: $SCENARIO)"
    echo "  --num_users <n>        Number of users (default: $NUM_USERS)"
    echo "  --num_satellites <n>   Number of satellites (default: $NUM_SATELLITES)"
    echo "  --num_steps <n>        Number of simulation steps (default: $NUM_STEPS)"
    echo "  --repetitions <n>      Number of repetitions (default: $REPETITIONS)"
    echo "  --seed <n>             Random seed (default: repetition number)"
    echo "  -h, --help             Show this help message"
    exit 0
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --dataset) DATASET="$2"; shift 2 ;;
        --satellites) SATELLITES="$2"; shift 2 ;;
        --scenario) SCENARIO="$2"; shift 2 ;;
        --num_users) NUM_USERS="$2"; shift 2 ;;
        --num_satellites) NUM_SATELLITES="$2"; shift 2 ;;
        --num_steps) NUM_STEPS="$2"; shift 2 ;;
        --repetitions) REPETITIONS="$2"; shift 2 ;;
        --seed) SEED="$2"; shift 2 ;;
        -h|--help) usage ;;
        *) echo "Unknown option: $1"; usage ;;
    esac
done

ALGORITHMS=(
    "best_fit_allocation"
    "longest_duration_allocation"
    # "latency_aware_allocation"
    # "load_balanced_allocation"
    "agentic"
)

for algo in "${ALGORITHMS[@]}"; do
    echo ""
    echo "========================================"
    echo "  Running: $algo"
    echo "========================================"
    echo ""

    seed_arg=()
    if [ -n "$SEED" ]; then
        seed_arg=(--seed "$SEED")
    fi

    python3 main.py \
        --dataset "$DATASET" \
        --satellites "$SATELLITES" \
        --algorithm "$algo" \
        --scenario "$SCENARIO" \
        --num_users "$NUM_USERS" \
        --num_satellites "$NUM_SATELLITES" \
        --num_steps "$NUM_STEPS" \
        --repetitions "$REPETITIONS" \
        "${seed_arg[@]}"

    if [ $? -ne 0 ]; then
        echo "ERROR: $algo failed. Aborting."
        exit 1
    fi
done

echo ""
echo "========================================"
echo "  All algorithms completed successfully"
echo "========================================"

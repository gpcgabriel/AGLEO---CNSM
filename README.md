# AGLEO: Autonomous Ground/LEO Edge Orchestrator

AGLEO extends the **LEOSIM** satellite network simulator with an **LLM-powered resource orchestrator** that intelligently allocates applications across ground stations and LEO satellites.

---

## LEOSIM — LEO Satellite Network Simulator

LEOSIM is a discrete-time, agent-based simulation engine for LEO satellite edge computing networks. It models ground stations, satellites, users, applications, and compute resources (ProcessUnits) with realistic mobility, failure, and network models.

### Simulation Flow

Each simulation step runs the following lifecycle via the **Scheduler**:

1. **Applications** — step migration lifecycle (provisioning, migration, deprovisioning)
2. **Users** — update access models, check provisioning, apply mobility
3. **Satellites** — update orbital position (coordinate replay), apply failure/power models, manage user connections
4. **Ground Stations** — discover satellites/users in range, manage connections
5. **Topology** — remove invalid links, run topology management (mesh network), update delays, reroute flows
6. **ProcessUnits** — update hosted application status

### Scenarios

| Scenario | Description |
|----------|-------------|
| `terrestrial` | All compute resources on ground stations only |
| `leo` | All compute resources on satellites only |
| `hybrid` | Compute resources on both ground stations and satellites |

### Allocation Algorithms

| Algorithm | Strategy |
|-----------|----------|
| `best_fit_allocation` | Packs applications into the tightest-fitting ProcessUnit, minimizing wasted CPU/MEM |
| `longest_duration_allocation` | Assigns to the satellite with the longest remaining visibility time |
| `hybrid_allocation` | Splits applications between best-fit and longest-duration strategies |
| `simple_allocation` | First-fit with improvement check |
| `random_allocation` | Random capable ProcessUnit |

---

## AGLEO — LLM-Powered Orchestration

AGLEO replaces static allocation algorithms with an **LLM-based orchestrator** (Agno Agent + Ollama + Llama 3.1 8B) running on each ground station.

### How AGLEO Works

At each simulation step, every enabled ground station:

1. **Collects full network state** — step, scenario, ground stations, satellites, users, applications, process units, topology
2. **Identifies pending applications** — apps not yet allocated
3. **Queries the LLM** — sends a structured prompt with the pending apps, network state JSON, and the last 5 decision steps
4. **LLM decides** — assigns each app to either `best_fit` or `longest_duration` allocation strategy
5. **Executes hybrid allocation** — delegates to `hybrid_allocation()` with the LLM's split
6. **Falls back** to `best_fit_allocation` if the LLM fails or returns invalid output
7. **Logs every decision** to `logs/agent_log.jsonl`

### AGLEO vs. Traditional Algorithms

| Aspect | Traditional | AGLEO (with `--llm`) |
|--------|-------------|----------------------|
| Decision logic | Fixed heuristic | Context-aware LLM reasoning |
| Adaptability | Static per-simulation | Dynamic per-step, per-ground-station |
| Strategy | Single algorithm for all apps | Per-app strategy selection |
| Fallback | N/A | Falls back to best-fit on error |

---

## Requirements

- Python 3.12+
- [Ollama](https://ollama.ai) running locally with `llama3.1:8b` model (for AGLEO/`--llm` mode)
- Dependencies: `pip install -r requirements.txt`

### Input Files

| File | Description |
|------|-------------|
| `datasets/rnp.gml` | Brazilian RNP backbone ground topology |
| `datasets/satellites_brazil.json` | Pre-recorded Starlink satellite trajectories over Brazil |
| `datasets/topology*.gml` | Synthetic topologies (10–10,000 nodes) |

Run `python datasets/create_topology.py` to generate synthetic topologies.

---

## Running the Simulation

### Basic Comparison (No LLM)

```bash
python main.py ^
    --dataset datasets/rnp.gml ^
    --satellites datasets/satellites_brazil.json ^
    --algorithm best_fit_allocation ^
    --scenario hybrid ^
    --num_steps 15
```

### Run with AGLEO (LLM Orchestrator)

```bash
python main.py ^
    --dataset datasets/rnp.gml ^
    --satellites datasets/satellites_brazil.json ^
    --llm ^
    --scenario hybrid ^
    --num_steps 15
```

### Run with Multiple Repetitions

```bash
python main.py ^
    --dataset datasets/rnp.gml ^
    --satellites datasets/satellites_brazil.json ^
    --algorithm best_fit_allocation ^
    --scenario hybrid ^
    --repetitions 5 ^
    --num_steps 15
```

### Run Across Different Scenarios

```bash
python main.py --dataset datasets/rnp.gml --satellites datasets/satellites_brazil.json --algorithm best_fit_allocation --scenario terrestrial --num_steps 15
python main.py --dataset datasets/rnp.gml --satellites datasets/satellites_brazil.json --algorithm best_fit_allocation --scenario leo --num_steps 15
python main.py --dataset datasets/rnp.gml --satellites datasets/satellites_brazil.json --algorithm longest_duration_allocation --scenario hybrid --num_steps 15
```

### Command-Line Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--dataset` | str | required | Path to ground topology GML file |
| `--satellites` | str | required | Path to satellite trajectory JSON |
| `--algorithm` | str | — | Allocation algorithm (`best_fit_allocation`, `longest_duration_allocation`) |
| `--scenario` | str | required | `terrestrial`, `leo`, or `hybrid` |
| `--num_users` | int | 100 | Number of users to generate |
| `--num_satellites` | int | 25 | Max satellites to use |
| `--num_steps` | int | 15 | Number of simulation steps |
| `--logs_dir` | str | `logs` | Output directory |
| `--repetitions` | int | 1 | Number of repetitions for statistical averaging |
| `--llm` | flag | off | Enable AGLEO (LLM orchestrator) |

When `--llm` is used, `--algorithm` is ignored — the simulation runs `best_fit_allocation`, `longest_duration_allocation`, and `llm_orchestrator` for comparison.

---

## Viewing Graphs

All graphs are generated automatically after the simulation completes and saved as PNG files in `logs/`.

### Generated Plots

| File | Content |
|------|---------|
| `logs/provisioned_{scenario}.png` | Average provisioned applications per step (all algorithms) |
| `logs/delay_{scenario}.png` | Total network delay per step |
| `logs/not_provisioned_{scenario}.png` | Applications that could not be provisioned |
| `logs/migrations_{scenario}.png` | Average application migrations per step |
| `logs/avg_migrations_topology_vs_step_{scenario}.png` | Migrations averaged across topologies |
| `logs/avg_provisioned_topology_vs_step_{scenario}.png` | Provisioned users averaged across topologies |
| `logs/gs_{id}_links_{scenario}.png` | Satellites connected to a specific ground station |
| `logs/delay_gs_{id}_{scenario}.png` | Delay for users at a specific ground station |
| `logs/avg_cpu_{scenario}.png` | Average CPU consumption per application |
| `logs/avg_memory_{scenario}.png` | Average memory consumption per application |

Each graph compares **all three algorithms** side-by-side: `best_fit_allocation`, `longest_duration_allocation`, and `llm_orchestrator`.

Simply open any `.png` file from the `logs/` directory in your file explorer or image viewer.

### Simulation Logs

Per-repetition detailed logs are saved to:
```
logs/{algorithm}/{scenario}/rep{rep}/
```

LLM decisions (when `--llm` is used):
```
logs/agent_log.jsonl
```

---

## Project Structure

```
AGLEO---CNSM/
├── main.py                       # Entry point: simulation + plotting
├── dataset.py                    # Dataset generation orchestration
├── plot.py                       # All visualization functions (matplotlib)
├── requirements.txt              # Python dependencies
├── leosim/                       # LEOSIM simulation engine
│   ├── simulator.py              # Central orchestrator
│   ├── scheduler.py              # Component stepping order
│   ├── component_manager.py      # Base class (registry, metrics, export)
│   ├── components/               # Simulation entities
│   │   ├── ground_station.py     # GS + AGLEO LLM agent
│   │   ├── satellite.py          # Mobility, failure, power
│   │   ├── user.py               # User with applications
│   │   ├── application.py        # App provisioning/migration lifecycle
│   │   ├── process_unit.py       # Compute resources (CPU/MEM/STORAGE)
│   │   ├── topology.py           # Network graph (networkx)
│   │   ├── network_link.py       # Link between nodes
│   │   ├── network_flow.py       # Data flow between source/target
│   │   ├── allocation_algorithms/ # App-to-PU allocation strategies
│   │   ├── topology_management_algorithms/ # Network topology strategies
│   │   ├── application_access_models/ # Provisioning window models
│   │   ├── orbit_models/         # Satellite position replay
│   │   ├── mobility_models/      # User and satellite mobility
│   │   └── failure_models/       # Satellite failure models
│   ├── mobility_models/          # User mobility (random between GS)
│   └── orbit_models/             # Linear orbit estimation
├── dataset_generator/            # Standalone dataset CLI generator
├── datasets/                     # Pre-generated topologies & satellite data
└── logs/                         # Simulation output (logs + plots)
```

OPMT Manager
OPMT Manager is an Operations Planning & Management Toolkit for building, scheduling, and visualizing task-based workflows.
The project models an operation as a directed task graph. Each task has a duration, tasks can depend on other tasks, and the system computes schedule timing using a critical-path style forward/backward pass. It can then render the operation as a Graphviz diagram and optionally export supporting bill-of-materials data to CSV.
This is currently a Python library/prototype, not a finished web app or database-backed production system.
---
What the project does
OPMT Manager lets you describe a process such as:
set up a job
run several tasks in parallel
wait for required tasks to finish
perform quality checks
finish the operation
calculate the total cycle time
identify which tasks are on the critical path
generate a visual process diagram
export related BOM/tooling lists
In other words, it turns a manual operation plan into a structured graph that can be scheduled, checked, and visualized.
---
What it creates in the end
A completed OPMT workflow can produce:
A scheduled operation graph
Each task receives:
earliest start
earliest finish
latest start
latest finish
slack
Critical-path information
The scheduler identifies tasks with zero slack.
These tasks determine the minimum possible cycle time of the operation.
A rendered operation diagram
The `GraphVisualizer` uses Graphviz to render a task graph.
Nodes can show timing data, task name, task duration, and slack.
Critical tasks/edges are visually highlighted.
Optional BOM CSV files
The BOM system can track parts, tools, and quantities.
BOM data can be saved as CSV files for documentation or purchasing.
---
Main pieces of the project
```text
src/
├── examples/
│   ├── Composable_ex.py
│   ├── Series_op_ex.py
│   ├── Simple_Task_ex.py
│   └── Simple_op_ex.py
│
└── opmt_manager/
    ├── BOM_manager/
    │   ├── bom.py
    │   └── partIDGenerator.py
    │
    ├── Graphs/
    │   ├── graph.py
    │   └── node.py
    │
    ├── container/
    │   ├── container.py
    │   └── exceptions.py
    │
    ├── domain/
    │   ├── task.py
    │   ├── operation.py
    │   ├── _TaskManager.py
    │   ├── compsableTask.py
    │   └── compsableOperation.py
    │
    └── systems/
        ├── scheduler.py
        ├── schedule_result.py
        └── visualizer.py
```
`Graphs`
The graph layer provides the basic directed graph structure.
`Node` stores a unique ID, name, forward links, and backward links.
`Graph` stores nodes, connects/disconnects nodes, returns successors/predecessors, removes nodes, and iterates over graph edges.
This is the low-level structure that everything else is built on.
`domain`
The domain layer defines operation-planning objects.
`Task` extends `Node` and adds duration plus schedule fields.
`TaskManager` manages task lookup and applies schedule timing back onto task objects.
`Operation` wraps a graph with special `START` and `END` nodes.
`ComposableTask` and `ComposableOperation` add access to the dependency-injection container.
An `Operation` is the main object used to define a process. You add tasks, connect dependencies, call `finalize()`, validate the structure, and then schedule it.
`systems`
The systems layer runs calculations and output generation.
`Scheduler` computes the schedule using forward and backward passes.
`ScheduleResult` stores ES, EF, LS, LF, and slack dictionaries.
`GraphVisualizer` renders the scheduled operation with Graphviz.
`container`
The container layer is a small dependency-injection system.
It lets an operation or task register shared services such as a BOM manager, then resolve them later by type and optional name.
Example use cases:
one shared BOM for parts
one shared BOM for tools
named providers for different task systems
singleton services shared across an operation
scoped containers for isolated task contexts
`BOM_manager`
The BOM manager stores part/tool lists in a pandas DataFrame.
Each row contains:
`part_id`
`part_name`
`qty`
It supports adding parts, editing parts, removing parts, combining BOMs, printing the list, saving to CSV, and loading from CSV.
The `PartIDGenerator` can generate readable IDs from part names and categories, with either incremental suffixes or stable hash-based suffixes.
---
Basic workflow
A typical OPMT operation follows this pattern:
Create an operation.
Create tasks with durations.
Connect tasks based on dependency order.
Finalize the operation so loose entry/exit tasks are connected to `START` and `END`.
Validate the graph.
Run the scheduler.
Render the graph or export supporting data.
---
Minimal example
```python
from opmt_manager import Operation, Task, Scheduler, GraphVisualizer

# Create an operation
op = Operation("Control Box Build")

# Create tasks
setup = Task("Setup box", 5)
drill = Task("Drill holes", 15)
mount = Task("Mount PCB", 10)
test = Task("Test assembly", 5)
finish = Task("Finish box", 5)

# Define dependencies
op.connect(setup, drill)
op.connect(drill, mount)
op.connect(mount, test)
op.connect(test, finish)

# Add START/END links and validate structure
op.finalize()
op.validate()

# Schedule the operation
scheduler = Scheduler(op)

print("Cycle time:", scheduler.get_cycle_time())
print("Critical path:", scheduler.get_critical_path_ordered())

# Render a diagram
GraphVisualizer(scheduler, output_dir="renders").draw("control_box_build")
```
This creates a scheduled task graph and saves a rendered operation diagram into the `renders` folder.
---
Composable operation example
The composable API adds shared systems, such as BOM managers, to the operation container.
```python
from opmt_manager import ComposableOperation, ComposableTask, Scheduler, GraphVisualizer
from opmt_manager.BOM_manager.bom import BOM

op = ComposableOperation("Op1")

# Register shared BOM systems
op.register(BOM, BOM, singleton=True, name="parts")
op.register(BOM, BOM, singleton=True, name="tools")

setup = ComposableTask("Setup box", 5, container=op.container)
drill = ComposableTask("Drill holes", 15, container=op.container)
finish = ComposableTask("Finish box", 5, container=op.container)

# Attach BOM/tooling data
setup.get(BOM, name="parts").add_part("BX001", "Acrylic box", 1)
drill.get(BOM, name="tools").add_part("DR001", "Hand drill", 1)

# Connect operation
op.connect(setup, drill)
op.connect(drill, finish)
op.finalize()
op.validate()

# Export BOMs
op.get(BOM, name="parts").save_csv("Bill_of_materials", "parts.csv")
op.get(BOM, name="tools").save_csv("Bill_of_tools", "tools.csv")

# Schedule and render
scheduler = Scheduler(op)
GraphVisualizer(scheduler, output_dir="renders").draw("op1")
```
This produces:
`Bill_of_materials/parts.csv`
`Bill_of_tools/tools.csv`
`renders/op1.png`
---
Installing
Requirements
Python 3.11+
Graphviz Python package
Graphviz system executable, especially `dot`
pandas
numpy
Install the Python dependencies:
```bash
pip install -r requirements.txt
```
For development install, use:
```bash
pip install -e .
```
Note: the current `requirements.txt` includes a local editable path:
```text
-e d:\opmt manager
```
That path is machine-specific. On another computer, remove that line and use `pip install -e .` from the repository root instead.
---
Graphviz setup
The visualizer requires the Graphviz command-line tools to be installed and available in your system `PATH`.
The Python package named `graphviz` is not enough by itself. The system also needs the actual Graphviz executable, especially `dot`.
On Windows, after installing Graphviz, make sure the Graphviz `bin` folder is added to `PATH`.
---
Running the examples
From the repository root:
```bash
python src/examples/Simple_op_ex.py
python src/examples/Series_op_ex.py
python src/examples/Composable_ex.py
```
The most complete example is:
```bash
python src/examples/Composable_ex.py
```
That example builds an operation for a box/PCB workflow, attaches parts and tools through BOM managers, computes the schedule, exports BOM CSV files, and renders a task graph.
---
Current limitations
This project is still early-stage. Current limitations include:
no GUI
no database layer
no web server/API
no persistent project format beyond CSV exports
no resource leveling
no calendar/date scheduling
no automatic labor assignment
no built-in test suite yet
The current focus is the core operation model: tasks, dependencies, scheduling, visualization, and BOM support.
---
Suggested next steps
Good future improvements would be:
add unit tests for graph, operation, scheduler, BOM, and container behavior
clean up spelling in file names, for example `compsable` → `composable`
remove local machine paths from `requirements.txt`
add a proper CLI command, such as `opmt run example.yaml`
add JSON/YAML import/export for operation definitions
add a project file format
add resource constraints and resource leveling
add date-based scheduling on top of duration-based scheduling
generate a full report containing the graph, critical path, BOMs, and timing table
---
Project status
OPMT Manager is a foundation for a larger operation-planning system. The current code already supports the core logic needed to:
define an operation as a graph
connect tasks by dependency
compute schedule timing
identify critical-path tasks
render operation diagrams
export BOM/tooling lists
The final output is not just code execution; it is a structured operation plan with timing data, visual process flow, and supporting material/tool lists.

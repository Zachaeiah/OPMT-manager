# OPMT Manager

**OPMT Manager** is an **Operations Planning & Management Toolkit** for building, scheduling, and visualizing task-based workflows.

The project models an operation as a directed task graph. Each task has a duration, tasks can depend on other tasks, and the system computes schedule timing using a critical-path style forward/backward pass. It can then render the operation as a Graphviz diagram and optionally export supporting bill-of-materials data to CSV.

This is currently a Python library/prototype, not a finished web app or database-backed production system.

---

## What the project does

OPMT Manager lets you describe a process such as:

- set up a job
- run several tasks in parallel
- wait for required tasks to finish
- perform quality checks
- finish the operation
- calculate the total cycle time
- identify which tasks are on the critical path
- generate a visual process diagram
- export related BOM/tooling lists

In other words, it turns a manual operation plan into a structured graph that can be scheduled, checked, and visualized.

---

## What it creates in the end

A completed OPMT workflow can produce:

1. **A scheduled operation graph**
   - Each task receives:
     - earliest start
     - earliest finish
     - latest start
     - latest finish
     - slack

2. **Critical-path information**
   - The scheduler identifies tasks with zero slack.
   - These tasks determine the minimum possible cycle time of the operation.

3. **A rendered operation diagram**
   - The `GraphVisualizer` uses Graphviz to render a task graph.
   - Nodes can show timing data, task name, task duration, and slack.
   - Critical tasks/edges are visually highlighted.

4. **Optional BOM CSV files**
   - The BOM system can track parts, tools, and quantities.
   - BOM data can be saved as CSV files for documentation or purchasing.

---

## Main pieces of the project

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

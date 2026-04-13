# main.py

from opmt_manager import ComposableOperation, ComposableTask ,Scheduler, GraphVisualizer
from opmt_manager.BOM_manager.bom import BOM

# -------------------------
# COMPOSITION ROOT
# -------------------------
def build_operation() -> ComposableOperation:
    op: ComposableOperation = ComposableOperation("Op1")

    # register multiple BOM systems (same type, different roles)
    op.register(BOM, BOM, singleton=True, name="parts")
    op.register(BOM, BOM, singleton=True, name="tools")

    return op

# -------------------------
# TASK DEFINITIONS
# -------------------------
def define_tasks(op: ComposableOperation):
    return {
        "setup": ComposableTask("Setup BOX", 5),
        "drill_conduit": ComposableTask("Drill conduit holes", 15),
        "drill_face": ComposableTask("Drill face holes", 15),
        "drill_pcb": ComposableTask("Drill mounting holes for PCB", 15),
        "qc_holes": ComposableTask("QC holes drilled", 5),
        "attach_pcb": ComposableTask("Attach PCB", 15),
        "test_pcb": ComposableTask("Test and QC PCB", 5),
        "finish": ComposableTask("Finish BOX", 5),
    }

# -------------------------
# INJECT BEHAVIOR (BOM USAGE)
# -------------------------
def attach_boms(tasks):
    # parts
    tasks["setup"].get(BOM, name="parts").add_part("BX001", "Acrylic box", 2)
    tasks["setup"].get(BOM, name="parts").add_part("BX001", "Acrylic lid", 2)

    tasks["drill_conduit"].get(BOM, name="tools").add_part("DR620", "M6X20 drill bit", 1)
    tasks["drill_conduit"].get(BOM, name="tools").add_part("DR001", "hand drill", 1)

    tasks["drill_face"].get(BOM, name="tools").add_part("DR310", "M3X10 drill bit", 1)
    tasks["drill_face"].get(BOM, name="tools").add_part("DR001", "hand drill", 1)

    tasks["drill_pcb"].get(BOM, name="tools").add_part("DR310", "M3X10 drill bit", 1)
    tasks["drill_pcb"].get(BOM, name="tools").add_part("DR001", "hand drill", 1)

    tasks["attach_pcb"].get(BOM, name="parts").add_part("PC001", "Custom PCB", 1)
    tasks["attach_pcb"].get(BOM, name="parts").add_part("SC001", "Screws", 4)
    tasks["attach_pcb"].get(BOM, name="tools").add_part("DR001", "hand drill", 1)

# -------------------------
# GRAPH STRUCTURE
# -------------------------
def connect_tasks(op: ComposableOperation, t: dict[str, ComposableTask]):
    op.connect(t["setup"], t["drill_conduit"])
    op.connect(t["setup"], t["drill_face"])
    op.connect(t["setup"], t["drill_pcb"])

    op.connect(t["drill_conduit"], t["qc_holes"])
    op.connect(t["drill_face"], t["qc_holes"])
    op.connect(t["drill_pcb"], t["qc_holes"])
    op.connect(t["drill_pcb"], t["attach_pcb"])

    op.connect(t["qc_holes"], t["finish"])
    op.connect(t["attach_pcb"], t["test_pcb"])
    op.connect(t["test_pcb"], t["finish"])

# -------------------------
# EXPORT SYSTEMS
# -------------------------
def export_systems(op: ComposableOperation):
    op.get(BOM, name="parts").save_csv("Bill_of_materials", "parts.csv")
    op.get(BOM, name="tools").save_csv("Bill_of_tools", "tools.csv")

# -------------------------
# EXECUTION PIPELINE
# -------------------------
def main():

    # build the operation and define the tasks
    op: ComposableOperation = build_operation()

    # define the tasks and register them in the operation's 
    # container for dependency management
    tasks: dict[str, ComposableTask] = define_tasks(op)

    # attach BOM data to the tasks that require it, 
    # demonstrating how we can inject behavior and data 
    # into the tasks through the operation's container system
    attach_boms(tasks)    

    # VALIDATION: ensure all dependencies are properly 
    # registered and can be resolved before connecting tasks      
    op.container.validate()     

    # connect the tasks to define the workflow and 
    # dependencies of the operation
    connect_tasks(op, tasks)

    # finalize the operation to prevent further 
    # modifications and validate the graph structure
    op.finalize()

    # validate the operation to ensure there are no cycles
    #  and all tasks are properly connected
    op.validate()

    # export any relevant systems (like BOMs) to external 
    # files for documentation or further analysis
    export_systems(op)

    # scheduling + visualization
    scheduler: Scheduler = Scheduler(op)
    scheduler.compute()

    # visualize the graph structure of the operation with custom styling
    GraphVisualizer(
        scheduler,
        output_dir="renders",
        config={
            "graph": {"dpi": "600", "nodesep": "1.0", "ranksep": "1.2"},
            "node": {"fontsize": "14"},
            "format": "png",
        },
    ).draw("op1")

# entry point for the script
if __name__ == "__main__":
    main()
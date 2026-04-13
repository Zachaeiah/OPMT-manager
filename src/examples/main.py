# main.py

from opmt_manager import ComposableOperation, Scheduler, GraphVisualizer
from opmt_manager.BOM_manager.bom import BOM

# -------------------------
# DEFINE OPERATION
# -------------------------

# Create a composable operation with an optional external container (or it will create its own)
op1 = ComposableOperation("Op1")

# Register providers for the BOM class in the operation's container. 
# We register two separate providers with different names ("parts" and "tools") 
# to demonstrate how we can have multiple providers for the same class and both
op1.register(BOM, BOM, singleton=True, name="parts")
op1.register(BOM, BOM, singleton=True, name="tools")

# create tasks (auto-injected container)
t1 = op1.create_task("Setup BOX", 5)
t2 = op1.create_task("Drill conduit holes", 15)
t3 = op1.create_task("Drill face holes", 15)
t4 = op1.create_task("Drill mounting holes for PCB", 15)
t5 = op1.create_task("QC holes drilled", 5)
t6 = op1.create_task("Attach PCB", 15)
t7 = op1.create_task("Test and QC PCB", 5)
t8 = op1.create_task("Finish BOX", 5)

t1.get(BOM, name="parts").add_part("BX001", "Acrylic box", 2)
t1.get(BOM, name="parts").add_part("BX001", "Acrylic lid", 2)

t2.get(BOM, name="tools").add_part("DR620", "M6X20 drill bit", 1)
t2.get(BOM, name="tools").add_part("DR001", "hand drill", 1)

t3.get(BOM, name="tools").add_part("DR310", "M3X10 drill bit", 1)
t3.get(BOM, name="tools").add_part("DR001", "hand drill", 1)

t4.get(BOM, name="tools").add_part("DR310", "M3X10 drill bit", 1)
t4.get(BOM, name="tools").add_part("DR001", "hand drill", 1)

t6.get(BOM, name="parts").add_part("PC001", "Custom PCB", 1)
t6.get(BOM, name="parts").add_part("SC001", "Screws", 4)
t6.get(BOM, name="tools").add_part("DR001", "hand drill", 1)

op1.container.validate()

op1.connect(t1, t2)
op1.connect(t1, t3)
op1.connect(t1, t4)

op1.connect(t2, t5)
op1.connect(t3, t5)
op1.connect(t4, t5)
op1.connect(t4, t6)

op1.connect(t5, t8)
op1.connect(t6, t7)

op1.connect(t7, t8)

op1.finalize()
op1.validate()

system: BOM = op1.get(BOM, name="parts")
system.save_csv(output_dir="Bill_of_materials", filename="parts.csv")

system: BOM = op1.get(BOM, name="tools")
system.save_csv(output_dir="Bill_of_tools", filename="tools.csv")


# -------------------------
# SCHEDULER
# -------------------------
scheduler = Scheduler(op1)
result = scheduler.compute()

viz = GraphVisualizer(
    scheduler,
    output_dir="renders",
    config = {
    "graph": {
        "dpi": "600",
        "nodesep": "1.0",
        "ranksep": "1.2"
    },
    "node": {
        "fontsize": "14"
    },
    "format": "png"
    }
)
viz.draw("op1")


# # -------------------------
# # PRINT RESULTS
# # -------------------------
# print("\n--- Schedule ---")

# graph: Graph = op1.graph

# for task in op1.tasks():
#     times = op1.get_times(task.id)

#     print(task.name)
#     print(f"  Duration: {task.duration}")
#     print(f"  Predecessors: {op1.predecessor_names(task.id)}")
#     print(f"  Successors: {op1.successor_names(task.id)}")
#     print(f"  ES: {times['ES']}")
#     print(f"  EF: {times['EF']}")
#     print(f"  LS: {times['LS']}")
#     print(f"  LF: {times['LF']}")
#     print()


# # -------------------------
# # ANALYSIS
# # -------------------------
# print("--- Analysis ---")

# print("Cycle Time:", scheduler.get_cycle_time())

# critical_ids = scheduler.get_critical_path()
# critical_names = [op1.graph.get_node(i).name for i in critical_ids]

# print("Critical Path:", " -> ".join(critical_names))

# print("Efficiency:", scheduler.get_process_efficiency())
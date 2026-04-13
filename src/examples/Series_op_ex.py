from opmt_manager import Task, Operation
from opmt_manager import Scheduler
from opmt_manager import GraphVisualizer

# ---------------------------------------------------------
Box_operation = Operation(name="Box Operation")
Attaching_operation = Operation(name="Attaching Operation")

# all tasks.
def Making_Box():
    t1 = Task(name="T1: Setup BOX", duration=5)
    t2 = Task(name="T2: Drill conduit holes", duration=15)
    t3 = Task(name="T3: Drill face holes", duration=15)
    t4 = Task(name="T4: Drill mounting holes for PCB", duration=15)
    t5 = Task(name="T5: QC holes drilled", duration=5)
    t6 = Task(name="T6: Install PCB", duration=15)
    t7 = Task(name="T7: Test and QC PCB", duration=5)
    t8 = Task(name="T8: Final Assembly", duration=5)

    Box_operation.connect(t1, t2)
    Box_operation.connect(t1, t3)
    Box_operation.connect(t1, t4)

    Box_operation.connect(t2, t5)
    Box_operation.connect(t3, t5)
    Box_operation.connect(t4, t5)
    Box_operation.connect(t4, t6)

    Box_operation.connect(t5, t8)
    Box_operation.connect(t6, t7)

    Box_operation.connect(t7, t8)

    Box_operation.finalize()
    Box_operation.validate()
Making_Box()

def Attaching_box():
    t1 = Task(name="T1: get finished BOX", duration=2)
    t2 = Task(name="T2: Measure mounting holes", duration=10)
    t3 = Task(name="T3: Drill holes for Box on tower", duration=20)
    t4 = Task(name="T4: Drill conduit hole on tower", duration=15)
    t5 = Task(name="T5: QC Holes drilled", duration=5)
    t6 = Task(name="T6: Attach Box to tower", duration=5)
    t7 = Task(name="T7: Attach conduit mount on Box", duration=5)
    t8 = Task(name="T8: Attach conduit mount on tower", duration=10)
    t9 = Task(name="T9: Fit conduit from Box to tower", duration=20)
    t10 = Task(name="T10: QC Mounting Box on tower", duration=5)

    Attaching_operation.connect(t1, t2)
    Attaching_operation.connect(t1, t7)
    Attaching_operation.connect(t2, t3)
    Attaching_operation.connect(t2, t4)
    Attaching_operation.connect(t3, t5)
    Attaching_operation.connect(t4, t5)
    Attaching_operation.connect(t5, t6)
#    Attaching_operation.connect(t5, t7)
    Attaching_operation.connect(t5, t8)
    Attaching_operation.connect(t6, t9)
    Attaching_operation.connect(t7, t9)
    Attaching_operation.connect(t8, t9)
    Attaching_operation.connect(t9, t10)

    Attaching_operation.finalize()
    Attaching_operation.validate()
Attaching_box()

# print(Box_operation)
# print(Attaching_operation)


Series_operation: Operation = Box_operation + Attaching_operation

print("Box_operation")
print(Box_operation)

print("Attaching_operation")
print(Attaching_operation)

print("Series_operation")
print(Series_operation)

# -------------------------
# SCHEDULER
# -------------------------
scheduler = Scheduler(Series_operation)
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
viz.draw("Series_operation")
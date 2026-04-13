from opmt_manager import Task, Operation

# ---------------------------------------------------------

# name (str): Name of the task
# duration (float): Duration of the task,

# all tasks.
t1 = Task(name="Task 1", duration=5)
t2 = Task(name="Task 2", duration=10)
t3 = Task(name="Task 3", duration=8)
t4 = Task(name="Task 4", duration=6)
t5 = Task(name="Task 5", duration=7)
t6 = Task(name="Task 6", duration=4)
t7 = Task(name="Task 7", duration=3)
t8 = Task(name="Task 8", duration=2)

op1 = Operation(name="Operation 1")

# first oprashion layer
op1.connect(t1, t2)
op1.connect(t1, t3)
op1.connect(t1, t4)

# second oprashion layer
op1.connect(t2, t5)
op1.connect(t3, t5)
op1.connect(t4, t5)
op1.connect(t4, t6)

# third oprashion layer
op1.connect(t5, t8)
op1.connect(t6, t7)

# fourth oprashion layer
op1.connect(t7, t8)

# ---------------------------------------------------------
# Finalize the operation to compute the schedule and validate it.
# This step is necessary before we can use the operation for 
# scheduling and visualization.
op1.finalize()
op1.validate()

# ---------------------------------------------------------
# Notes
# - The `finalize()` Finalize the operation by ensuring all 
# tasks are connected to START and END.

# - The `validate()` Validate the operation structure to 
# ensure it is sound and can be scheduled.

# - After finalizing and validating, we can use the 
# operation for scheduling and visualization.

# there are two fictitious Tasks, Operation_END and 
# Operation_START, that are automatically created when you 
# create an Operation.

# - Operation_START is the starting point of the 
# operation and has no duration. It is connected to all 
# tasks that have no predecessors.

# - Operation_END is the ending point of the operation and 
# has no duration. It is connected to all tasks that have 
# no successors.   

# `<-` represents the dependencies between tasks. For example,
# Task 1 must be completed before Task 2, Task 3, 
# and Task 4 can start after Task 1 is completed, and so on.

# `->` represents the flow of the operation from start to end.
# For example, the operation starts at Operation_START, 
# then Task 1 can start, and after Task 1 is completed, 
# Task 2, Task 3, and Task 4 can start, and so on until we 
# reach Operation_END.

print(op1)

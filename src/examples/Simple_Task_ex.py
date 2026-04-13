from opmt_manager import Task

# ---------------------------------------------------------
# This example demonstrates how to create simple tasks with
# names and durations.

# Create some simple tasks with names and durations.
# Note that these tasks are not connected in any way, they 
# are just standalone tasks.

# In a real operation, you would typically connect these 
# tasks to define the workflow and dependencies.

# For this simple example, we are just demonstrating how to
# create tasks and print them out.

# You can run this example to see the output of the tasks 
# with their names and durations.
# ---------------------------------------------------------

# name (str): Name of the task
# duration (float): Duration of the task,

# all tasks.
# all tasks.
t1 = Task(name="Task 1", duration=5)
t2 = Task(name="Task 2", duration=10)
t3 = Task(name="Task 3", duration=8)
t4 = Task(name="Task 4", duration=6)
t5 = Task(name="Task 5", duration=7)
t6 = Task(name="Task 6", duration=4)
t7 = Task(name="Task 7", duration=3)
t8 = Task(name="Task 8", duration=2)

# Print the tasks to see their details.
task_list = [t1, t2, t3, t4, t5, t6, t7, t8]

# Print the tasks to see their details.
for task in task_list:
    print(task)
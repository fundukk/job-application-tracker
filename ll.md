## 🧑‍💻 Using the Job Tracker

Once you’ve set everything up, you can run the script, by typing this in your terminal:

python3 job_tracker.py

This starts an interactive command shell, where you can type commands like addjob or replace.

## 🔹 Available Commands

In the interactive shell (python3 job_tracker.py):

- addjob, add, a -> Add a new job application.

- replace, r, redo -> Move the most recent entry to a Trash sheet and then add a new job (with special “replace by link” behavior, see below).

- help, h, ? -> Show the list of commands.

- exit, quit, q -> Leave the program.

From the command line:

- python3 job_tracker.py addjob -> Immediately starts the “add job” flow in a loop (after each job, it asks if you want to add another).

- python3 job_tracker.py replace -> Moves the most recent entry to Trash and then starts the “add job (replace mode)” flow.

- python3 job_tracker.py loop / run / interactive -> Same as running addjob in a loop.

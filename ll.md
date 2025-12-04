## 🧑‍💻 Using the Job Tracker

Once you’ve set everything up, you can run the script, by typing this in your terminal:

- python3 job_tracker.py

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

### ➕ Adding a Job (addjob)

## 1. When you run addjob (via shell or directly), the script:

<img width="291" height="49" alt="Screenshot 2025-12-03 at 19 57 37" src="https://github.com/user-attachments/assets/e7cf3333-16d6-49f1-ab65-3716f001d47b" />

- Paste a LinkedIn or company job URL.

- If you leave this empty, the script cancels.

 ## 2. Tries to auto-fill fields

If it’s a LinkedIn URL, the script scrapes:

- Position

- Company

- Location

- Salary (if visible)

- Job type (Internship / Full-time, etc.)
 
- Remote hint (Remote / Hybrid / On-site)

- For non-LinkedIn URLs, it makes a best guess for position / company / location.

It then shows you what it found, e.g.:

  <img width="808" height="162" alt="Screenshot 2025-12-03 at 20 00 13" src="https://github.com/user-attachments/assets/73b2ce05-6e35-4877-84c5-4fafb78ecb3f" />

## 3. Walks you through each field with defaults

For each field, it shows a prompt. If there is scraped data, it’s shown in brackets as a default:

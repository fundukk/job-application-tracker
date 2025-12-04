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

<img width="827" height="130" alt="Screenshot 2025-12-03 at 20 02 35" src="https://github.com/user-attachments/assets/28d8d5e0-3dde-4154-adae-b6f7c64772c7" />

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

<img width="824" height="222" alt="Screenshot 2025-12-03 at 20 05 03" src="https://github.com/user-attachments/assets/d9e6e955-d495-4cb0-bc6d-4474bb816ad8" />


## 3. Walks you through each field with defaults

For each field, it shows a prompt. If there is scraped data, it’s shown in brackets as a default. 

Press Enter to accept the value in brackets.

Type your own value to override.

You can type < or back to go one step back to the previous field.

Special behavior for Salary:

- You can type things like $25/hr, $20–25/hr, $70k, $80k–$100k, $4000/mo, etc.

The script automatically converts:

- hourly ↔ yearly

- monthly ↔ yearly + hourly

### If you type words like negotiable, tbd, n/a, market, etc., they are saved as-is.

### If there’s no real salary info on the page, the script saves Undetermined and shades that cell gray in the sheet.

## 4. Remote & Job Type

The script guesses Remote/Hybrid/On-site from the page and your location, but you can change it.

- Same for Job Type (Full-time, Part-time, Internship, etc.).

  ## 5. Notes

- Free text field.

- Use it for reminders like EASY APPLY, Applied via company portal, etc.

  ## 6. Confirmation step

Before saving, it shows a full summary:

<img width="822" height="522" alt="Screenshot 2025-12-03 at 20 07 19" src="https://github.com/user-attachments/assets/dd5ed9d4-2ad6-4944-8b6c-a3c9544a67b5" />

- y / yes → saves the row

- n / anything else → cancels

- < / back → lets you go back and edit fields (mainly Notes / Job type / Remote)

  ## 7. Duplicate protection

Before saving, the script checks if the same Link already exists in the sheet.

- If it finds a match, it prints a warning (эта ссылка уже сохранена) and does not save a duplicate row.

  ###

# 📝 Job Application Tracker

A Python tool that automatically logs job applications into a Google Sheet.  
It extracts details from LinkedIn job postings — company, role, salary, job type, and more — and saves them in a clean, structured spreadsheet.  
This project helps streamline high-volume job applications and keeps your search organized.

---

## ✨ Features

- Scrapes job posting details from LinkedIn  
- Automatically writes data into a Google Sheet  
- Supports job location, salary, job type, notes, and status  
- Prevents duplicate entries  
- Easy setup for beginners  
- Saves time during your job search  

---

## 📘 How to Use (Beginner-Friendly Guide)

Follow these steps to set up the tracker on your own computer.

### Before You Start

You will need:

- A Google account  
- A Google Cloud project (created during setup)  
- A Google Sheet where your applications will be stored  
- Python 3 installed on your computer  



### 1. Download the Project

Click the green **“Code”** button on this page → **Download ZIP**,  
or clone it using:

git clone https://github.com/fundukk/job-application-tracker


### 2. Install Python
Make sure you have Python 3 installed. You can check this in your terminal:

python3 --version

- If you don’t have Python, download it from:

https://www.python.org/downloads/


### 3. Install the Required Packages
Open your terminal inside the project folder and run:

pip install -r requirements.txt

-- This installs all the libraries listed in requirements.txt that the script needs
(for example: gspread, google-auth, requests, beautifulsoup4, etc.).

If this fails for some reason, you can install them manually:

pip install gspread google-auth requests beautifulsoup4


### 4. Set Up Google Sheets Access
To allow the script to write to your spreadsheet, you need a Google API key.

Go to Google Cloud Console: https://console.cloud.google.com/

Create a new project

Enable the Google Sheets API for that project


### 5. Create a Service Account
In Google Cloud Console, on the left menu:

Go to APIs & Services → Credentials

Click Create Credentials → Service Account

Give it any name (e.g., job-tracker-bot)

Click Create and Continue

You may skip roles (or choose Editor)

Click Done


### 6. Generate a JSON Key and Download It
This file allows the script to authenticate.

In Credentials, find your new service account

Click its name

Go to the Keys tab

Click Add Key → Create New Key

Choose JSON

A file like this will download:

job-tracker-12893712398123.json

This file is your credentials.json.


### 7. Rename & Move the File
Rename the downloaded file to: credentials.json

Move it into the same folder as your Python script, for example:

job-application-tracker/
│── job_tracker.py

│── credentials.json   ← place it here

│── requirements.txt

│── README.md

Your script will now be able to connect to Google Sheets.

<img width="248" height="107" alt="Screenshot 2025-12-03 at 19 22 22" src="https://github.com/user-attachments/assets/011ae1bb-4434-4147-94b2-a88739e032d0" />

⚠️ Important: Do NOT upload credentials.json to GitHub — it contains private keys.

### 8. Share Your Google Sheet With the Service Account

Your script uses a “robot account” (the service account) to edit your spreadsheet.
To give it permission, you must share your sheet with its email address.

Open your Google Sheet

Click the Share button (top-right)

Find the email of your service account — it looks like:

job-tracker-bot@yourproject.iam.gserviceaccount.com
(You can find this email in Google Cloud Console → IAM → Service Accounts.)

Paste that email into the Share window

Give it Editor access

Click Send

Your script can now safely write into the sheet.


### 9. Run the Script
Once everything is set up, you can start using your tracker.

Open your terminal

Make sure you’re inside the project folder

Run:


Copy code
python3 job_tracker.py
The script will ask you for a job posting URL
Paste the link (e.g., from LinkedIn) and press Enter

Each time you run the script and provide a URL, a new entry will be added automatically to your Google Sheet — including company name, role, salary, location, and more.

### 🔑 Finding Your Spreadsheet ID
Your Google Sheet URL looks like this:

https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit#gid=0
Copy the part labeled SPREADSHEET_ID and paste it into the script where indicated.

### 📊 Example Output
Here is how the tracker looks after running the script:

<img width="1160" height="355" alt="Screenshot 2025-12-03 at 17 47 18" src="https://github.com/user-attachments/assets/b85bda9d-6ac8-4538-a86d-ba907144267f" />


### 🛠️ Troubleshooting
❌ ERROR: “The caller does not have permission”
→ You forgot to share the Google Sheet with your service account email. Repeat Step 8.

❌ ModuleNotFoundError (gspread, bs4, etc.)
→ Install dependencies again:

Copy code
pip install -r requirements.txt

❌ Script runs but no data appears in the sheet
→ Check:
- Wrong Spreadsheet ID
- Wrong Sheet permissions
- Wrong file name for credentials (credentials.json must match exactly)


### 🚀 Future Improvements
Add support for Indeed or Glassdoor URLs

- Improve salary scraping
- Add duplicate detection
- Add a GUI for non-technical users
- Add error logging

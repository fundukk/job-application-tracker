Follow these steps to set up the tracker on your own computer.

Before You Start
You will need:
- A Google account
- A Google Cloud project (created during setup)
- A Google Sheet where your applications will be stored
- Python 3 installed on your computer

1. Download the Project
1.1 Click the green “Code” button on this page → Download ZIP,
or clone it using:

git clone https://github.com/fundukk/job-application-tracker

---------------------------------------------------

2. Install Python

2.1 Make sure you have Python 3 installed. You can check this in your terminal:

python3 --version

2.2 If you don’t have Python, download it from:
https://www.python.org/downloads/

---------------------------------------------------

3. Install the Required Packages

3.1 Open your terminal inside the project folder and run:

pip install -r requirements.txt

This installs all the libraries the script needs (gspread, BeautifulSoup, requests, etc.).

---------------------------------------------------

4. Set Up Google Sheets Access
To allow the script to write to your spreadsheet, you need a Google API key.

4.1 Go to Google Cloud Console:
   https://console.cloud.google.com/

4.2 Create a new project

4.3 Enable the Google Sheets API

---------------------------------------------------

5. Create a Service Account
On the left menu, go to:

5.1 APIs & Services → Credentials

5.2 Click Create Credentials → Service Account

5.3 Give it any name (e.g., “job-tracker-bot”)

5.4 Click Create and Continue

5.5 You may skip roles (or choose Editor)

5.6 Click Done

---------------------------------------------------

6. Generate a JSON Key and Download It
This file allows the script to authenticate.

6.1 In Credentials, find your new service account

6.2 Click its name

6.3 Go to the Keys tab

6.4 Click Add Key → Create New Key

6.5 Choose JSON

6.6 A file like this will download:

job-tracker-12893712398123.json

This file is your credentials.json.

---------------------------------------------------

7. Rename & Move the File

7.1 Rename the downloaded file to:

credentials.json

7.2 Move it into the same folder as your Python script, for example:

job-application-tracker/
│── job_tracker.py
│── credentials.json   ← place it here
│── requirements.txt
│── README.md

Your script will now be able to connect to Google Sheets.

⚠️ Important: Do NOT upload credentials.json to GitHub — it contains private keys.

---------------------------------------------------

8. Share Your Google Sheet With the Service Account

Your script uses a “robot account” (the service account) to edit your spreadsheet.
To give it permission, you must share your sheet with its email address.

8.1 Open your Google Sheet

8.2 Click the Share button (top-right)

8.3 Find the email of your service account — it looks like:

job-tracker-bot@yourproject.iam.gserviceaccount.com

(You can find this email in Google Cloud Console → IAM → Service Accounts.)


8.4 Paste that email into the Share window

8.5 Give it Editor access

8.6 Click Send

Your script can now safely write into the sheet.

---------------------------------------------------

9. Run the Script
Once everything is set up, you can start using your tracker.
9.1 Open your terminal

9.2 Make sure you’re inside the project folder

9.3 Run:

python3 job_tracker.py

9.4 The script will ask you for a job posting URL

Paste the link (e.g., from LinkedIn) and press Enter

Each time you run the script and provide a URL, a new entry will be added automatically to your Google Sheet — including company name, role, salary, location, and more.

---------------------------------------------------

🔑 Finding Your Spreadsheet ID

Your Google Sheet URL looks like this:

https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit#gid=0

Copy the part labeled SPREADSHEET_ID and paste it into the script where indicated.

---------------------------------------------------

📊 Example Output

Here is how the tracker looks after running the script:

<img width="1160" height="355" alt="Screenshot 2025-12-03 at 17 47 18" src="https://github.com/user-attachments/assets/b85bda9d-6ac8-4538-a86d-ba907144267f" />

---------------------------------------------------

🛠️ Troubleshooting

❌ ERROR: “The caller does not have permission”
→ You forgot to share the Google Sheet with your service account email.
Repeat Step 8.

❌ ModuleNotFoundError (gspread, bs4, etc.)
→ Install dependencies:

pip install -r requirements.txt

❌ Script runs but no data appears in the sheet
→ Check:
- Wrong Spreadsheet ID
- Wrong Sheet permissions
- Wrong file name for credentials (credentials.json must match exactly)

---------------------------------------------------

🚀 Future Improvements
- Add support for Indeed or Glassdoor URLs
- Improve salary scraping
- Add duplicate detection
- Add a GUI for non-technical users
- Add error logging

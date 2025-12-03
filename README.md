📘 How to Use (Beginner-Friendly Guide)

Follow these steps to set up the tracker on your own computer.

1. Download the project

Click the green “Code” button on this page → Download ZIP,
or clone it using:

git clone https://github.com/YOUR_USERNAME/job-application-tracker

2. Install Python

Make sure you have Python 3 installed.
You can check this in your terminal:

python3 --version


If you don’t have Python, download it from:
https://www.python.org/downloads/

3. Install the required packages

Open your terminal inside the project folder and run:

pip install -r requirements.txt


This installs all the libraries the script needs (gspread, BeautifulSoup, requests, etc.).

4. Set up Google Sheets access

To allow the script to write to your spreadsheet, you need a Google API key.

Here’s how:

Go to Google Cloud Console: https://console.cloud.google.com/

Create a new project

Enable the Google Sheets API

Create a Service Account

Generate a JSON key and download it → save it as credentials.json

Place it in the same folder as job_tracker.py

⚠️ Do NOT upload this file to GitHub — it contains sensitive keys.

5. Create your Google Sheet

Create a Google Sheet with the columns you want (e.g., DateApplied, Company, Position, etc.).

Copy the spreadsheet ID from the URL:

https://docs.google.com/spreadsheets/d/THIS_IS_THE_ID/edit


Paste this ID into the script where indicated.

6. Run the script

Now you’re ready to use the tracker.

In your terminal:

python3 job_tracker.py


Each time you run the script and provide a job posting URL, the new job will be added to your spreadsheet automatically.

7. Your tracker is ready 🎉

Once everything is set up, the script will:

pull job details from the URL you give it

extract useful information

add the information directly into your Google Sheet

No manual typing required.

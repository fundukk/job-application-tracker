# Job Application Tracker

A Python tool that automatically logs job applications into a Google Sheet.  
It scrapes job posting info from LinkedIn and Handshake, cleans it,  
and saves everything — company, position, salary, location, remote type, notes —  
into a structured spreadsheet.

This project helps you automate high-volume job searching and stay organized.

---

## Quick Start

### 1️⃣ Install the project (code and python)
See full installation instructions here:  
👉 [Installation Manual](./Installation_Manual.md)

### 2️⃣ How to use the tracker  
Step-by-step user guide:  
👉 [How To Use Manual](./How_To_Use_Manual.md)

---

## Main Features

- Automatic LinkedIn scraping  
- Salary detection + auto conversion (hourly ↔ yearly)  
- Smart “Undetermined” detection + gray shading  
- Duplicate detection  
- Trash sheet for removed rows  
- Manual overrides for any field  
- CLI commands (`addjob`, `replace`, `help`, `exit`)  
- Clean formatting in Google Sheets  

---

## Example Output

The tracker saves each job like this:

<img width="1160" height="355" src="https://github.com/user-attachments/assets/b85bda9d-6ac8-4538-a86d-ba907144267f" />

---

## Requirements

Python 3  
`gspread`, `google-auth`, `requests`, `beautifulsoup4`, `google-auth-oauthlib`, `google-auth-httplib2` 
(automatically installed through `requirements.txt`)

---

## License

This project is licensed under the **MIT License**.  
See the full text in the [LICENSE](./LICENSE) file.

---

## ⭐ Contributing

Feel free to submit PRs or feature requests!

---

This project was created by **Fedor Zybin** to automate job tracking  
and make applying faster, cleaner, and more consistent.

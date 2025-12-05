#!/usr/bin/env python3
import gspread
from google.oauth2.service_account import Credentials
from datetime import date
from pathlib import Path
import requests
from bs4 import BeautifulSoup
import re
import sys
import json

# ==== SETTINGS ====

# Путь к папке, где лежит этот скрипт
BASE_DIR = Path(__file__).resolve().parent

# credentials.json должен лежать рядом со скриптом
SERVICE_ACCOUNT_FILE = BASE_DIR / "credentials.json"

# config.json для хранения SPREADSHEET_ID
CONFIG_FILE = BASE_DIR / "config.json"

def load_spreadsheet_id():
    """Load SPREADSHEET_ID from config.json, or ask user if not found."""
    def normalize_sheet_id(raw: str) -> str:
        """Extract sheet ID from full URL or return as-is if already an ID."""
        raw = (raw or "").strip()
        if "docs.google.com" in raw and "/d/" in raw:
            return raw.split("/d/", 1)[1].split("/", 1)[0].strip()
        return raw
    
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                raw_id = config.get("SPREADSHEET_ID", "")
                sheet_id = normalize_sheet_id(raw_id)
                if sheet_id:
                    return sheet_id
        except Exception:
            pass
    
    # Если файла нет или не смогли прочитать - спрашиваем у пользователя
    print("\n📋 Google Sheet ID не найден!")
    print("🔗 Как получить:")
    print("   1. Откройте вашу Google таблицу")
    print("   2. Скопируйте ВЕСЬ URL или только ID между /d/ и /edit")
    print("   3. Пример: https://docs.google.com/spreadsheets/d/1ABC2DEF3GHI/edit")
    print("             ID это: 1ABC2DEF3GHI")
    
    spreadsheet_id = input("\n📝 Вставьте URL или ID: ").strip()
    spreadsheet_id = normalize_sheet_id(spreadsheet_id)

    if not spreadsheet_id:
        print("❌ ID не может быть пустым!")
        sys.exit(1)
    
    # Сохраняем в config.json
    try:
        config = {"SPREADSHEET_ID": spreadsheet_id}
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"✅ ID сохранен в {CONFIG_FILE}\n")
    except Exception as e:
        print(f"⚠️  Не удалось сохранить config: {e}")
    
    return spreadsheet_id

# Проверяем наличие credentials при импорте
if not SERVICE_ACCOUNT_FILE.exists():
    print(f"❌ Credentials file not found at {SERVICE_ACCOUNT_FILE}")
    print("👉 Положите credentials.json в ту же папку, где лежит job_tracker.py")
    sys.exit(1)

# Загружаем SPREADSHEET_ID (спросит у пользователя если нет)
SPREADSHEET_ID = load_spreadsheet_id()

COLUMNS = [
    "DateApplied",
    "Company",
    "Location",
    "Position",
    "Link",
    "Salary",
    "JobType",
    "Remote",
    "Status",
    "Source",
    "Notes",
]

# Manual salary values that should be preserved as-is when the user types them
SALARY_MANUAL_KEYWORDS = {
    "negotiable", "tbd", "tba", "n/a", "not specified", 
    "unspecified", "market", "dependent", "undisclosed", "competitive",
}

# Salary time markers for pattern matching
HOURLY_MARKERS = ["/hr", "/hour", "per hour", "an hour", "hourly", " hr"]
YEARLY_MARKERS = ["/yr", "/year", "per year", "a year", "yearly", " yr"]
MONTHLY_MARKERS = ["/mo", "/month", "per month", "a month", "monthly", " mo"]

# Combined regex pattern for all time markers
TIME_MARKERS_PATTERN = r"(?:/yr|/year|per year|yr|/mo|/month|per month|month|mo|/hr|/hour|per hour|hr)\b"

HOURS_PER_YEAR = 2080
MONTHS_PER_YEAR = 12

# User response constants
YES_RESPONSES = ("y", "yes")
NO_RESPONSES = ("n", "no", "q", "quit", "exit")
BACK_RESPONSES = ("<", "back")

# ==== GOOGLE SHEETS ====


def get_worksheet():
    """
    Connect to Google Sheets and return worksheet.
    Raises appropriate exceptions if credentials or connection fails.
    """
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    
    try:
        creds = Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=scopes
        )
    except FileNotFoundError:
        print(f"❌ Error: Credentials file not found at {SERVICE_ACCOUNT_FILE}")
        print("   Please ensure the file exists in the correct location.")
        raise
    except Exception as e:
        print(f"❌ Error: Invalid credentials file: {e}")
        raise
    
    try:
        client = gspread.authorize(creds)
        sh = client.open_by_key(SPREADSHEET_ID)
        ws = sh.sheet1
    except Exception as e:
        print(f"❌ Error: Cannot connect to Google Sheets: {e}")
        print("   Check your SPREADSHEET_ID and internet connection.")
        raise

    try:
        first_row = ws.row_values(1)
        if not first_row:
            ws.insert_row(COLUMNS, 1)
    except Exception as e:
        print(f"❌ Error: Cannot read/write to worksheet: {e}")
        raise

    return ws


def link_already_exists(ws, link: str) -> int | None:
    """Return row number if link already exists, else None."""
    if not link:
        return None
    try:
        header = ws.row_values(1)
        if "Link" not in header:
            print("⚠ 'Link' column not found in sheet header.")
            return None
        col_index = header.index("Link") + 1
        col_values = ws.col_values(col_index)
        for row_idx, val in enumerate(col_values, start=1):
            if row_idx == 1:
                continue
            if val and val.strip() == link.strip():
                return row_idx
    except Exception as e:
        print(f"⚠ Error checking for duplicate link: {e}")
        return None
    return None


def save_job(
    company,
    location,
    position,
    link,
    salary,
    job_type,
    remote,
    status,
    source,
    notes,
    manual_undetermined: bool = False,
):
    try:
        ws = get_worksheet()
    except Exception:
        print("✖ Failed to connect to Google Sheets. Job not saved.\n")
        return

    existing_row = link_already_exists(ws, link)
    if existing_row:
        print(f"⚠ Эта ссылка уже сохранена (строка {existing_row}).\n")
        return

    new_row = create_job_row(company, location, position, link, salary, job_type, remote, status, source, notes)

    try:
        ws.insert_row(new_row, 2, value_input_option="USER_ENTERED")
        print("✔ Saved to Google Sheets!\n")
        apply_salary_formatting(ws, 2, salary, manual_undetermined)
    except Exception as e:
        print(f"✖ Error saving to Google Sheets: {e}\n")


# ==== HELPERS ====


def display_job_summary(company, location, position, link, salary, job_type, remote, status, source, notes):
    """Display job details in a formatted summary."""
    print("\nWill save the following row:")
    print(f"  Company:     {company}")
    print(f"  Location:    {location}")
    print(f"  Position:    {position}")
    print(f"  Link:        {link}")
    print(f"  Salary:      {salary}")
    print(f"  JobType:     {job_type}")
    print(f"  Remote:      {remote}")
    print(f"  Status:      {status}")
    print(f"  Source:      {source}")
    print(f"  Notes:       {notes}")


def create_job_row(company, location, position, link, salary, job_type, remote, status, source, notes):
    """Create a row list for inserting into Google Sheets."""
    return [
        date.today().isoformat(),
        company,
        location,
        position,
        link,
        salary,
        job_type,
        remote,
        status,
        source,
        notes,
    ]


def apply_salary_formatting(ws, row_num: int, salary: str, manual_undetermined: bool):
    """Apply gray/white background to salary cell based on its value."""
    try:
        salary_col = COLUMNS.index("Salary")
    except ValueError:
        salary_col = 5
    
    try:
        sheet_id = int(ws._properties.get("sheetId", ws.id))
    except Exception:
        return  # Can't format without sheet ID
    
    sal_text = (salary or "").strip()
    bg_color = None
    
    # Gray for undetermined
    if sal_text.lower() == "undetermined" or sal_text.lower() in SALARY_MANUAL_KEYWORDS or manual_undetermined:
        bg_color = {"red": 0.75, "green": 0.75, "blue": 0.75}
    # White for numeric
    elif re.search(r"\d", sal_text):
        bg_color = {"red": 1.0, "green": 1.0, "blue": 1.0}
    
    if bg_color:
        try:
            ws.spreadsheet.batch_update({
                "requests": [{
                    "repeatCell": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": row_num - 1,
                            "endRowIndex": row_num,
                            "startColumnIndex": salary_col,
                            "endColumnIndex": salary_col + 1,
                        },
                        "cell": {"userEnteredFormat": {"backgroundColor": bg_color}},
                        "fields": "userEnteredFormat.backgroundColor",
                    }
                }]
            })
        except Exception:
            pass  # Non-fatal formatting error


def prompt_with_default(prompt: str, default: str, required: bool = False):
    """
    Prompt user for input with optional default value.
    Returns a tuple: (result: str, used_default: bool, is_back: bool).
    If user types '<' or 'back' (case-insensitive), is_back will be True.
    If required=True, keeps asking until non-empty value is provided or the user requests back.
    """
    default = (default or "").strip()
    while True:
        if default:
            full = f"{prompt} [{default}]: "
        else:
            full = f"{prompt}: "
        value = input(full)
        if value is None:
            value = ""
        value = value.rstrip("\n")
        stripped = value.strip()

        # user requested to go back one step
        if stripped.lower() in ("<", "back"):
            return "", False, True

        # determine if user used default (pressed enter)
        if stripped == "":
            result = default
            used_default = True
        else:
            result = stripped
            used_default = False

        if required and not result:
            print("  ⚠ This field is required. Please enter a value or type '<' to go back.")
            continue
        return result, used_default, False


def detect_remote(text: str):
    """Guess Remote / Hybrid / On-site from raw text."""
    t = (text or "").lower()
    if "remote" in t:
        return "Remote"
    if "hybrid" in t:
        return "Hybrid"
    return "On-site"


def normalize_remote_choice(value: str, default: str) -> str:
    """Normalize user input to: Remote / Hybrid / On-site."""
    v = (value or "").strip().lower()
    if not v:
        return default or ""

    if v in ("remote", "r"):
        return "Remote"
    if v in ("hybrid", "h"):
        return "Hybrid"
    if v in ("on-site", "onsite", "on site", "office", "o"):
        return "On-site"

    return value.strip() or (default or "")


def infer_source(link: str):
    link = (link or "").lower()
    if "linkedin.com" in link:
        return "LinkedIn"
    if "indeed.com" in link:
        return "Indeed"
    if "glassdoor" in link:
        return "Glassdoor"
    if "joinhandshake.com" in link or "handshake.com" in link:
        return "Handshake"
    return "Company / Other"


def validate_job_data(company: str, position: str, link: str) -> tuple[bool, str]:
    """
    Validate required job fields.
    Returns (is_valid, error_message).
    """
    if not company.strip():
        return False, "Company is required."
    if not position.strip():
        return False, "Position is required."
    if not link.strip():
        return False, "Application link is required."
    if not link.startswith(("http://", "https://")):
        return False, "Link must be a valid URL (starting with http:// or https://)."
    return True, ""


def normalize_linkedin_url(link: str) -> str:
    """
    Turn URLs like
    .../jobs/collections/recommended/?currentJobId=XXXX
    into .../jobs/view/XXXX/
    """
    link = link.strip()
    if "linkedin" not in link:
        return link

    if "/jobs/view/" in link:
        return link

    if "currentJobId=" in link:
        try:
            part = link.split("currentJobId=", 1)[1]
            job_id = "".join(c for c in part if c.isdigit())
            if job_id:
                return f"https://www.linkedin.com/jobs/view/{job_id}/"
        except Exception:
            pass

    return link


# ==== TRASH SHEET HELPERS ====


def get_trash_sheet(ws):
    """Return the worksheet titled 'Trash', creating it with headers if missing."""
    sh = ws.spreadsheet
    title = "Trash"
    try:
        trash = sh.worksheet(title)
    except Exception:
        # create sheet with enough rows/cols
        try:
            trash = sh.add_worksheet(title=title, rows=1000, cols=max(10, len(COLUMNS)))
        except Exception:
            return None

    # Ensure header row exists and matches our COLUMNS
    try:
        first = trash.row_values(1)
        if not first or len(first) < len(COLUMNS):
            # overwrite header row
            try:
                trash.insert_row(COLUMNS, 1)
            except Exception:
                # fallback: update cells individually if insert_row fails
                pass
    except Exception:
        pass

    return trash


def move_row_to_trash(ws, row_index: int) -> bool:
    """Copy a row into the Trash sheet and remove it from the original sheet.

    Returns True if moved successfully, False otherwise.
    """
    try:
        # read row values and pad to column count
        row_vals = ws.row_values(row_index)
        # Ensure row has same number of columns
        if len(row_vals) < len(COLUMNS):
            row_vals += [""] * (len(COLUMNS) - len(row_vals))

        trash = get_trash_sheet(ws)
        if trash is None:
            return False

        # Insert at top (row 2) so newest trashed items are near top, keep header at row1
        try:
            trash.insert_row(row_vals, 2, value_input_option="USER_ENTERED")
        except Exception:
            # fallback to append if insert fails
            try:
                trash.append_row(row_vals, value_input_option="USER_ENTERED")
            except Exception:
                return False

        # After copying, delete original row
        try:
            ws.delete_rows(row_index)
        except Exception:
            # if delete failed, do not consider it moved
            return False

        return True
    except Exception:
        return False


# ==== SALARY PARSING & CONVERSION ====


def enrich_salary_with_conversion(s: str) -> str:
    """
    If salary is hourly → add yearly.
    If yearly → add hourly.
    Supports ranges.
    Only extracts numbers that appear near salary keywords.
    """
    s = (s or "").strip()
    if not s:
        return s

    # Preserve explicit manual tokens the user may type (Negotiable, TBA, etc.)
    if s.lower() in SALARY_MANUAL_KEYWORDS:
        return s

    lower = s.lower()
    # detect explicit salary markers
    is_hourly = any(x in lower for x in HOURLY_MARKERS)
    is_yearly = any(x in lower for x in YEARLY_MARKERS)
    is_monthly = any(x in lower for x in MONTHLY_MARKERS)

    # If there are no clear salary markers (no $/k/yr/hr/mo), consider it undetermined
    # This avoids saving long descriptive texts as salary (e.g., internship program descriptions)
    has_currency_marker = ("$" in s) or ("k" in lower)
    has_time_marker = is_hourly or is_yearly or is_monthly
    if not has_currency_marker and not has_time_marker:
        return "Undetermined"

    # Extract numbers that appear near $ or k symbols (more reliable)
    # Look for patterns like: $70k, $70,000, $20-25/hr, etc.
    salary_patterns = re.findall(
        r"\$\s*([\d,]+(?:\.\d+)?)\s*(?:k|K)?(?:\s*[-–]\s*\$?\s*([\d,]+(?:\.\d+)?)\s*(?:k|K)?)?",
        s,
    )

    values = []
    if salary_patterns:
        for match in salary_patterns:
            for num_str in match:
                if num_str:
                    num = float(num_str.replace(",", ""))
                    # Convert k notation to actual numbers (e.g., 70k → 70000)
                    if "k" in s.lower() and num < 1000:
                        num *= 1000
                    values.append(num)

    # Fallback: catch '70k' or '70-90k' style tokens without a leading $ but
    # with a 'k' marker, when the string also includes time markers (yr/hr)
    if not values:
        if ("k" in s.lower() or "k/yr" in s.lower() or "k/mo" in s.lower()) and (
            is_hourly or is_yearly or is_monthly
        ):
            k_matches = re.findall(r"([\d,]+)(?:\s*[-–]\s*([\d,]+))?\s*[kK]\b", s)
            for m in k_matches:
                n1 = m[0]
                n2 = m[1]
                try:
                    v1 = float(n1.replace(",", "")) * 1000
                    values.append(v1)
                    if n2:
                        v2 = float(n2.replace(",", "")) * 1000
                        values.append(v2)
                except Exception:
                    pass
    
    if not values:
        return s

    def fmt_money(x, decimals=0):
        return f"${x:,.0f}" if decimals == 0 else f"${x:,.2f}"

    # hourly → yearly
    if is_hourly:
        if len(values) == 1:
            h = values[0]
            y = h * HOURS_PER_YEAR
            return f"{fmt_money(h, 2)}/hr (~{fmt_money(y)}/yr)"
        elif len(values) >= 2:
            h1, h2 = values[0], values[1]
            y1, y2 = h1 * HOURS_PER_YEAR, h2 * HOURS_PER_YEAR
            return (
                f"{fmt_money(h1, 2)}–{fmt_money(h2, 2)}/hr "
                f"(~{fmt_money(y1)}–{fmt_money(y2)}/yr)"
            )

    # yearly → hourly
    if is_yearly:
        if len(values) == 1:
            y = values[0]
            h = y / HOURS_PER_YEAR
            return f"{fmt_money(y)}/yr (~{fmt_money(h, 2)}/hr)"
        elif len(values) >= 2:
            y1, y2 = values[0], values[1]
            h1, h2 = y1 / HOURS_PER_YEAR, y2 / HOURS_PER_YEAR
            return (
                f"{fmt_money(y1)}–{fmt_money(y2)}/yr "
                f"(~{fmt_money(h1, 2)}–{fmt_money(h2, 2)}/hr)"
            )

    # monthly → yearly and hourly
    if is_monthly:
        if len(values) == 1:
            m = values[0]
            y = m * MONTHS_PER_YEAR
            h = y / HOURS_PER_YEAR
            return f"{fmt_money(m)}/mo (~{fmt_money(y)}/yr, ~{fmt_money(h, 2)}/hr)"
        elif len(values) >= 2:
            m1, m2 = values[0], values[1]
            y1, y2 = m1 * MONTHS_PER_YEAR, m2 * MONTHS_PER_YEAR
            h1, h2 = y1 / HOURS_PER_YEAR, y2 / HOURS_PER_YEAR
            return (
                f"{fmt_money(m1)}–{fmt_money(m2)}/mo "
                f"(~{fmt_money(y1)}–{fmt_money(y2)}/yr, ~{fmt_money(h1, 2)}–{fmt_money(h2, 2)}/hr)"
            )

    return s


# ==== LINKEDIN SCRAPER ====


def scrape_linkedin_job(url: str):
    """Parse LinkedIn job page for position / company / location / salary / job_type / remote_hint."""

    url = normalize_linkedin_url(url)

    position = ""
    company = ""
    location = ""
    salary = ""
    job_type = ""
    remote_hint = ""

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/119.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }

    try:
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code != 200:
            print(f"⚠ Cannot fetch page, HTTP {resp.status_code}")
            return position, company, location, salary, job_type, remote_hint

        soup = BeautifulSoup(resp.text, "html.parser")

        # Try to get title from og:title meta tag first
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            title_text = og_title.get("content").strip()
        else:
            h1 = soup.find("h1")
            title_text = h1.get_text(strip=True) if h1 else ""

        if title_text:
            # Remove trailing "| LinkedIn" if present
            for sep in [" | LinkedIn", " |"]:
                if sep in title_text:
                    title_text = title_text.split(sep, 1)[0].strip()
                    break

            # Pattern 1: "Company hiring Position in City, ST"
            lower_title = title_text.lower()
            if " hiring " in lower_title:
                try:
                    idx_hiring = lower_title.index(" hiring ")
                    company = title_text[:idx_hiring].strip()
                    rest = title_text[idx_hiring + len(" hiring "):]
                    
                    # Look for location after "in"
                    if " in " in rest.lower():
                        idx_in = rest.lower().index(" in ")
                        position = rest[:idx_in].strip()
                        location = rest[idx_in + 4:].strip()
                    else:
                        position = rest.strip()
                except Exception:
                    pass
            
            # Pattern 2: "Position – Company – City, ST" (fallback if pattern 1 didn't work)
            if not company or not position:
                separators = ["–", "-"]
                for sep in separators:
                    if sep in title_text and title_text.count(sep) >= 1:
                        parts = [p.strip() for p in title_text.split(sep)]
                        if len(parts) >= 1 and not position:
                            position = parts[0]
                        if len(parts) >= 2 and not company:
                            company = parts[1]
                        if len(parts) >= 3 and not location:
                            location = parts[2]
                        break

            # Gather visible text once for analysis
            body = soup.get_text(" ", strip=True)

            # ---- Salary extraction (prefer regex on page text to avoid matching link hrefs) ----
            # 1) $-based patterns with time markers (per year/month/hour)
            salary_match = re.search(
                rf"\$\s*[\d,]+(?:\.\d+)?\s*(?:k|K)?(?:\s*[-–]\s*\$?\s*[\d,]+(?:\.\d+)?\s*(?:k|K)?)?\s*{TIME_MARKERS_PATTERN}",
                body,
                re.IGNORECASE,
            )

            if salary_match:
                salary = salary_match.group(0).strip()
            else:
                # 2) k-style without $ but with time marker: e.g. "70k per month" or "70-90k/mo"
                k_match = re.search(
                    rf"[\d,]+(?:\s*[-–]\s*[\d,]+)?\s*[kK]\s*{TIME_MARKERS_PATTERN}",
                    body,
                    re.IGNORECASE,
                )
                if k_match:
                    salary = k_match.group(0).strip()

            # ---- Job type and remote detection ----
            body = body.lower()

        if "remote" in body:
            remote_hint = "Remote"
        elif "hybrid" in body:
            remote_hint = "Hybrid"

        # Check for job type keywords (more specific patterns first)
        if any(word in body for word in ["internship", "intern position", "intern -"]):
            job_type = "Internship"
        else:
            for t in ["Full-time", "Part-time", "Contract", "Temporary"]:
                if t.lower() in body:
                    job_type = t
                    break

    except Exception as e:
        print(f"⚠ Error while scraping LinkedIn: {e}")

    return position, company, location, salary, job_type, remote_hint


# ==== HANDSHAKE SCRAPER ====


def parse_handshake_text(text: str):
    """Parse copied text from Handshake job page."""
    position = ""
    company = ""
    location = ""
    salary = ""
    job_type = ""
    remote_hint = ""
    
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    text_lower = text.lower()
    
    # Noise patterns to skip
    noise_patterns = [
        r'^\d+\s+profile\s+views?$',  # "13 profile views"
        r'^skip to',
        r'^menu$',
        r'^navigation$',
        r'^home$',
        r'^jobs$',
        r'^sign in$',
        r'^log in$',
        r'^search$',
        r'^get the app$',
        r'^save$',
        r'^share$',
        r'^apply$',
        r'^follow$',
        r'in the past \d+ days?$',  # "in the past 90 days"
        r'^posted',
        r'^apply by',
        r'^={3,}$',  # Lines with just equal signs
    ]
    
    def is_noise(line: str) -> bool:
        """Check if a line is noise/navigation."""
        if not line or len(line.strip()) == 0:
            return True
        line_lower = line.lower().strip()
        # Skip single digits
        if line_lower.isdigit():
            return True
        # Check against noise patterns
        return any(re.match(pattern, line_lower, re.IGNORECASE) for pattern in noise_patterns)
    
    # Look for "Company logo" pattern to extract company name
    logo_line_idx = -1
    for i, line in enumerate(lines):
        if "logo" in line.lower():
            logo_line_idx = i
            # Extract company name from "Company logo" pattern
            logo_match = re.match(r'^(.+?)\s+logo\s*$', line, re.IGNORECASE)
            if logo_match and not company:
                potential_company = logo_match.group(1).strip()
                if not is_noise(potential_company) and len(potential_company) > 2:
                    company = potential_company
            break
    
    # FALLBACK: If we found a logo line, position is usually
    # the SECOND meaningful line after logo (1-я — индустрия).
    if logo_line_idx >= 0 and not position:
        start_idx = logo_line_idx + 1
        seen_first_text = False  # первую нормальную строку пропускаем

        for i in range(start_idx, min(start_idx + 8, len(lines))):
            line = lines[i].strip()
            lower = line.lower()

            # стоп, если начались "Posted", даты, apply и т.п.
            if re.match(r"^posted", lower) or re.search(r"\d+\s+days?\s+ago", lower) or "apply by" in lower:
                break

            # пропускаем дубликат компании
            if company and lower == company.lower():
                continue

            # пропускаем шум и ВСЕ КАПС
            if is_noise(line) or len(line) <= 3 or line.isupper():
                continue

            if not seen_first_text:
                # первая нормальная строка после logo — обычно индустрия
                seen_first_text = True
                continue

            # вторая нормальная строка после logo — job title
            position = line
            break
    
    # Alternative: Look for "Company is seeking [position]" pattern
    if not position:
        seeking_keywords = ["seeking", "looking for", "hiring"]
        for line in lines[:10]:  # Check first 10 lines
            if len(line) > 30 and any(kw in line.lower() for kw in seeking_keywords):
                # Extract position from "seeking a/an [Position]"
                match = re.search(r'(?:seeking|looking for|hiring)\s+(?:a|an)\s+(.+?)(?:\s+(?:for|to|with)|$)', line, re.IGNORECASE)
                if match:
                    position = match.group(1).strip()
                    # Also extract company from "Company is seeking"
                    if not company:
                        comp_match = re.match(r'^(.+?)\s+(?:is|are)\s+(?:seeking|looking|hiring)', line, re.IGNORECASE)
                        if comp_match:
                            company = comp_match.group(1).strip()
                    break
    
    # Try to find labeled fields as fallback
    i = 0
    while i < len(lines) and (not position or not company):  # Early exit if both found
        line_lower = lines[i].lower()
        
        # Position field (only if not found via logo pattern)
        if not position and line_lower == "position" and i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            if not is_noise(next_line):
                position = next_line
                i += 2
                continue
        
        # Company field (only if not found via logo pattern)
        elif not company and line_lower == "company" and i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            if not is_noise(next_line):
                company = next_line
                i += 2
                continue
        
        # Location field
        elif line_lower == "location" and i + 1 < len(lines):
            location = lines[i + 1].strip()
            i += 2
            continue
        
        # Salary field
        elif line_lower == "salary" and i + 1 < len(lines):
            salary = lines[i + 1].strip()
            i += 2
            continue
        
        # JobType field
        elif line_lower in ["jobtype", "job type", "employment type"] and i + 1 < len(lines):
            job_type = lines[i + 1].strip()
            i += 2
            continue
        
        # Remote field
        elif line_lower == "remote" and i + 1 < len(lines):
            remote_hint = lines[i + 1].strip()
            i += 2
            continue
        
        i += 1
    
    # Fallback: if position or company still empty, find meaningful lines
    if not position or not company:
        label_words = {"position", "company", "location", "salary", "jobtype", "job type", "remote", "employment type"}
        skip_keywords = {"profile", "view", "follow"}
        meaningful_lines = []
        
        for line in lines:
            # Collect meaningful lines (not noise, not labels, not metrics, not locations)
            if (not is_noise(line) 
                and line.lower() not in label_words 
                and len(line) > 5
                and not any(kw in line.lower() for kw in skip_keywords)
                and not re.match(r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z]{2}$', line)):
                meaningful_lines.append(line)
        
        # Assign position as first meaningful line if not found
        if not position and meaningful_lines:
            position = meaningful_lines[0]
        
        # Assign company as second meaningful line if not found
        if not company and len(meaningful_lines) > 1:
            company = meaningful_lines[1]
    
    # Fallback: Location pattern matching
    if not location:
        loc_match = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z]{2})', text)
        if loc_match:
            location = loc_match.group(1)
    
    # Salary (only if not already found from labeled field)
    if not salary:
        salary_match = re.search(
            rf"\$\s*[\d,]+(?:\.\d+)?\s*(?:k|K)?(?:\s*[-–]\s*\$?\s*[\d,]+(?:\.\d+)?\s*(?:k|K)?)?\s*{TIME_MARKERS_PATTERN}",
            text,
            re.IGNORECASE,
        )
        if salary_match:
            salary = salary_match.group(0).strip()
    
    # Remote/Hybrid (only if not already found from labeled field)
    if not remote_hint:
        if "remote" in text_lower:
            remote_hint = "Remote"
        elif "hybrid" in text_lower:
            remote_hint = "Hybrid"
    
    # Job type (only if not already found from labeled field)
    if not job_type:
        if any(word in text_lower for word in ["internship", "intern position"]):
            job_type = "Internship"
        elif "full-time" in text_lower or "full time" in text_lower:
            job_type = "Full-time"
        elif "part-time" in text_lower or "part time" in text_lower:
            job_type = "Part-time"
        elif "contract" in text_lower:
            job_type = "Contract"
    
    return position, company, location, salary, job_type, remote_hint


def scrape_handshake_job(url: str):
    """Parse Handshake job page for position / company / location / salary / job_type / remote_hint."""
    position = ""
    company = ""
    location = ""
    salary = ""
    job_type = ""
    remote_hint = ""

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/119.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }

    try:
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code != 200:
            print(f"⚠ Cannot fetch page, HTTP {resp.status_code}")
            return position, company, location, salary, job_type, remote_hint

        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Get title (usually in h1 or meta tag)
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            position = og_title.get("content").strip()
        else:
            h1 = soup.find("h1")
            if h1:
                position = h1.get_text(strip=True)
        
        # Try to find company name (often in specific divs or meta tags)
        company_meta = soup.find("meta", property="og:site_name")
        if company_meta and company_meta.get("content"):
            company = company_meta.get("content").strip()
        
        # If not found, look for common patterns in text
        body = soup.get_text(" ", strip=True)
        
        # Look for location patterns
        if "location" in body.lower():
            # Simple heuristic: find text after "location" keyword
            parts = body.split("Location", 1)
            if len(parts) > 1:
                loc_text = parts[1][:100]  # Take first 100 chars
                # Look for city, state pattern
                import re
                loc_match = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z]{2})', loc_text)
                if loc_match:
                    location = loc_match.group(1)
        
        # Check for remote/hybrid
        body_lower = body.lower()
        if "remote" in body_lower:
            remote_hint = "Remote"
        elif "hybrid" in body_lower:
            remote_hint = "Hybrid"
        
        # Check for job type
        if any(word in body_lower for word in ["internship", "intern position"]):
            job_type = "Internship"
        elif "full-time" in body_lower or "full time" in body_lower:
            job_type = "Full-time"
        elif "part-time" in body_lower or "part time" in body_lower:
            job_type = "Part-time"
        elif "contract" in body_lower:
            job_type = "Contract"
        
        # Look for salary with same pattern as LinkedIn
        salary_match = re.search(
            rf"\$\s*[\d,]+(?:\.\d+)?\s*(?:k|K)?(?:\s*[-–]\s*\$?\s*[\d,]+(?:\.\d+)?\s*(?:k|K)?)?\s*{TIME_MARKERS_PATTERN}",
            body,
            re.IGNORECASE,
        )
        if salary_match:
            salary = salary_match.group(0).strip()

    except Exception as e:
        print(f"⚠ Error while scraping Handshake: {e}")

    return position, company, location, salary, job_type, remote_hint


# ==== GENERIC SCRAPER FOR NON-LINKEDIN ====


def scrape_generic_job(url: str):
    """
    Very rough parser for non-LinkedIn job pages.
    Tries to guess Position / Company / Location.
    """
    position = ""
    company = ""
    location = ""

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/119.0 Safari/537.36"
        )
    }

    try:
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code != 200:
            return position, company, location

        soup = BeautifulSoup(resp.text, "html.parser")

        h1 = soup.find("h1")
        if h1:
            position = h1.get_text(strip=True)

        company = url.split("//", 1)[-1].split("/", 1)[0]

        loc_candidate = soup.find(
            string=lambda s: s
            and isinstance(s, str)
            and "," in s
            and (" US" in s or "United States" in s)
        )
        if loc_candidate:
            location = loc_candidate.strip()

    except Exception:
        pass

    return position, company, location


# ==== MAIN LOOP ====


def delete_last_row():
    """Delete the last row (most recently added job) from the Google Sheet."""
    try:
        ws = get_worksheet()
    except Exception:
        print("✖ Failed to connect to Google Sheets.\n")
        return False

    try:
        # We insert new entries at row 2 (just under the header).
        # Delete the most-recent entry at row 2 instead of deleting the bottom row.
        all_rows = ws.get_all_values()
        if len(all_rows) <= 1:  # Only header or empty
            print("✖ No job entries to delete.\n")
            return False

        # Ensure there's at least one data row at row 2
        # If row 2 is empty (unlikely when using insert_row), search downward
        target_row = 2
        # If row 2 is missing or empty, find the first non-header row from top
        if len(all_rows) < 2 or not any(cell.strip() for cell in all_rows[1]):
            # find first row after header that has any content
            found = False
            for idx, row in enumerate(all_rows[1:], start=2):
                if any((c or "").strip() for c in row):
                    target_row = idx
                    found = True
                    break
            if not found:
                print("✖ No job entries to delete.\n")
                return False

        # Move the row to Trash sheet before deleting
        try:
            moved = move_row_to_trash(ws, target_row)
            if moved:
                print(f"✔ Moved row {target_row} to 'Trash' sheet.\n")
            else:
                # fallback to deleting if move failed
                ws.delete_rows(target_row)
                print(f"✔ Deleted row {target_row}.\n")
        except Exception:
            # If any error, attempt a direct delete (best-effort)
            try:
                ws.delete_rows(target_row)
                print(f"✔ Deleted row {target_row}.\n")
            except Exception as e:
                print(f"✖ Error deleting row: {e}\n")
                return False
        return True
    except Exception as e:
        print(f"✖ Error deleting row: {e}\n")
        return False


def replace_job_by_link(
    company,
    location,
    position,
    link,
    salary,
    job_type,
    remote,
    status,
    source,
    notes,
    manual_undetermined: bool = False,
):
    """Replace an existing job entry with the same link, or add new if link doesn't exist."""
    try:
        ws = get_worksheet()
    except Exception:
        print("✖ Failed to connect to Google Sheets. Job not saved.\n")
        return

    existing_row = link_already_exists(ws, link)
    new_row = create_job_row(company, location, position, link, salary, job_type, remote, status, source, notes)

    try:
        if existing_row:
            # Move the existing row to Trash then insert replacement at same index
            try:
                moved = move_row_to_trash(ws, existing_row)
                if moved:
                    print(f"⚠ Found duplicate link at row {existing_row}. Moved old row to 'Trash'.\n")
                else:
                    # fallback: delete if moving failed
                    ws.delete_rows(existing_row)
                    print(f"⚠ Found duplicate link at row {existing_row}. Deleted old row.\n")
            except Exception:
                try:
                    ws.delete_rows(existing_row)
                except Exception:
                    pass

            row_num = existing_row
            ws.insert_row(new_row, row_num, value_input_option="USER_ENTERED")
        else:
            row_num = 2
            ws.insert_row(new_row, row_num, value_input_option="USER_ENTERED")
        
        print("✔ Saved to Google Sheets!\n")
        apply_salary_formatting(ws, row_num, salary, manual_undetermined)
    except Exception as e:
        print(f"✖ Error saving to Google Sheets: {e}\n")


def add_one_job(use_replace_mode: bool = False):
    print("\n=== ADD NEW JOB APPLICATION ===")

    link = input("Application link (LinkedIn / company site): ").strip()
    if not link:
        print("✖ Link is required. Cancelled.\n")
        return

    auto_position = ""
    auto_company = ""
    auto_location = ""
    auto_salary = ""
    auto_job_type = ""
    auto_remote_hint = ""

    if "linkedin.com" in link.lower():
        print("Scraping LinkedIn...")
        (
            auto_position,
            auto_company,
            auto_location,
            auto_salary,
            auto_job_type,
            auto_remote_hint,
        ) = scrape_linkedin_job(link)

        # If scraper couldn't find a salary, show 'Undetermined' instead of a dash
        if not auto_salary:
            auto_salary = "Undetermined"

        print("\nGuessed from LinkedIn:")
        print(f"  Position: {auto_position or '—'}")
        print(f"  Company:  {auto_company or '—'}")
        print(f"  Location: {auto_location or '—'}")
        print(f"  Salary:   {auto_salary}")
        print(f"  JobType:  {auto_job_type or '—'}")
        print(f"  Remote:   {auto_remote_hint or '—'}\n")
    elif "handshake.com" in link.lower() or "joinhandshake.com" in link.lower():
        print("\n📋 Handshake detected!")
        print("Please copy the full job page text:")
        print("  1. Open the job page in your browser")
        print("  2. Select all text: Cmd+A (or Ctrl+A on Windows)")
        print("  3. Copy: Cmd+C (or Ctrl+C on Windows)")
        print("  4. Return here and paste: Cmd+V (or Ctrl+V on Windows)")
        print("  5. Press Enter, then Cmd+D (or Ctrl+Z on Windows) to finish\n")
        
        # Read multiline input
        print("Paste the text and press Cmd+D (Ctrl+Z on Windows) when done:")
        try:
            clipboard_lines = []
            while True:
                try:
                    line = input()
                    clipboard_lines.append(line)
                except EOFError:
                    break
            
            clipboard_text = '\n'.join(clipboard_lines)
            
            if clipboard_text.strip():
                print("\n📝 Parsing text...")
                (
                    auto_position,
                    auto_company,
                    auto_location,
                    auto_salary,
                    auto_job_type,
                    auto_remote_hint,
                ) = parse_handshake_text(clipboard_text)
                
                if not auto_salary:
                    auto_salary = "Undetermined"
                
                print("\nParsed from Handshake:")
                print(f"  Position: {auto_position or '—'}")
                print(f"  Company:  {auto_company or '—'}")
                print(f"  Location: {auto_location or '—'}")
                print(f"  Salary:   {auto_salary}")
                print(f"  JobType:  {auto_job_type or '—'}")
                print(f"  Remote:   {auto_remote_hint or '—'}\n")
            else:
                print("⚠ No text pasted, will enter manually.\n")
        except KeyboardInterrupt:
            print("\n⚠ Cancelled, will enter manually.\n")
    elif link.startswith("http"):
        print("Trying to guess from job page...")
        g_pos, g_comp, g_loc = scrape_generic_job(link)
        auto_position = auto_position or g_pos
        auto_company = auto_company or g_comp
        auto_location = auto_location or g_loc

    # ===== manual confirmation with defaults (step-wise, supports 'back') =====
    # Steps order: position, company, location, salary_raw, remote, job_type, notes
    position = auto_position
    company = auto_company
    location = auto_location
    salary_raw = auto_salary
    remote_input = ""
    job_type = auto_job_type
    notes = ""

    i = 0
    while i < 7:
        # Position
        if i == 0:
            res, used_default, is_back = prompt_with_default("Position", position or "", required=True)
            if is_back:
                print("Already at first field. Can't go back further.")
                continue
            position = res
            i += 1
            continue

        # Company
        if i == 1:
            res, used_default, is_back = prompt_with_default("Company", company or "", required=True)
            if is_back:
                i -= 1
                continue
            company = res
            i += 1
            continue

        # Location
        if i == 2:
            res, used_default, is_back = prompt_with_default("Location (City, State / Country)", location or "")
            if is_back:
                i -= 1
                continue
            location = res
            i += 1
            continue

        # Salary (raw)
        if i == 3:
            res, used_default, is_back = prompt_with_default(
                "Salary (e.g. '$70k' or '$20–25/hr', can be empty)",
                salary_raw or "",
            )
            if is_back:
                i -= 1
                continue
            # capture raw string and whether the user explicitly typed 'Undetermined'
            salary_raw = res
            # used_default tells us whether the user pressed enter to accept the default.
            # If they typed 'Undetermined' explicitly (and did NOT use the default), mark manual.
            salary_was_manual_undetermined = False
            if (res or "").strip().lower() == "undetermined" and not used_default:
                salary_was_manual_undetermined = True
            i += 1
            continue

        # Remote
        if i == 4:
            remote_default = detect_remote((auto_remote_hint or "") + " " + (location or ""))
            res, used_default, is_back = prompt_with_default("Remote type (On-site / Remote / Hybrid)", remote_default)
            if is_back:
                i -= 1
                continue
            remote_input = res
            i += 1
            continue

        # Job type
        if i == 5:
            res, used_default, is_back = prompt_with_default(
                "Job type (Full-time / Intern / Part-time / Internship)",
                job_type or "",
            )
            if is_back:
                i -= 1
                continue
            job_type = res
            i += 1
            continue

        # Notes
        if i == 6:
            # Notes: allow free text and back
            res, used_default, is_back = prompt_with_default("Notes (optional)", notes or "")
            if is_back:
                i -= 1
                continue
            notes = res
            i += 1
            continue

    # After gathering all fields, process salary conversion
    salary = enrich_salary_with_conversion(salary_raw)
    # Determine if we should mark as manual undetermined (user typed it explicitly)
    manual_undetermined_flag = bool(salary_was_manual_undetermined)

    remote_default = detect_remote(auto_remote_hint + " " + location)
    remote = normalize_remote_choice(remote_input or remote_default, remote_default)

    status = "Applied"
    source = infer_source(link)

    # Validate critical fields
    is_valid, error_msg = validate_job_data(company, position, link)
    if not is_valid:
        print(f"✖ Validation error: {error_msg}\n")
        return

    display_job_summary(company, location, position, link, salary, job_type, remote, status, source, notes)

    while True:
        confirm = input("\nSave to Google Sheets? (y/n) (type '<' to go back): ").strip().lower()
        if confirm in BACK_RESPONSES:
            # go back to notes step
            i = 6
            while i < 7:
                # reuse the notes prompt logic to allow edits
                res, used_default, is_back = prompt_with_default("Notes (optional)", notes or "")
                if is_back:
                    # step back from notes -> job_type
                    res2, used_default2, is_back2 = prompt_with_default("Job type (Full-time / Intern / Part-time / Internship)", job_type or "")
                    if is_back2:
                        # go back further to remote
                        res3, used_default3, is_back3 = prompt_with_default("Remote type (On-site / Remote / Hybrid)", remote_default)
                        if not is_back3:
                            remote_input = res3
                            remote = normalize_remote_choice(remote_input or remote_default, remote_default)
                    else:
                        job_type = res2
                else:
                    notes = res
                    break
            # reprint summary and re-ask
            display_job_summary(company, location, position, link, salary, job_type, remote, status, source, notes)
            continue
        if confirm not in YES_RESPONSES:
            print("✖ Not saved.\n")
            return

        if use_replace_mode:
            replace_job_by_link(
                company=company,
                location=location,
                position=position,
                link=link,
                salary=salary,
                job_type=job_type,
                remote=remote,
                status=status,
                source=source,
                notes=notes,
                manual_undetermined=manual_undetermined_flag,
            )
        else:
            save_job(
                company=company,
                location=location,
                position=position,
                link=link,
                salary=salary,
                job_type=job_type,
                remote=remote,
                status=status,
                source=source,
                notes=notes,
                manual_undetermined=manual_undetermined_flag,
            )
        return


def main():
    # If called with a command-line argument, handle quick modes
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd == "addjob":
            # Loop: keep adding jobs until user says no
            while True:
                add_one_job()
                again = input("Add another? (y/n): ").strip().lower()
                if again in NO_RESPONSES:
                    print("Exiting. Bye 👋")
                    break
            return
        if cmd == "replace":
            # Replace mode: delete last row and add new one, allowing duplicate links
            if delete_last_row():
                print("Now enter the new job entry:")
                add_one_job(use_replace_mode=True)
            return
        if cmd in ("loop", "run", "interactive"):
            # legacy behavior: keep adding until user quits
            while True:
                add_one_job()
                again = input("Add another? (y/n): ").strip().lower()
                if again in NO_RESPONSES:
                    print("Exiting. Bye 👋")
                    break
            return
        print("Usage: python job_tracker.py [addjob|replace|loop]")
        return

    # Default: simple command shell so user can type 'addjob' on demand
    print("Job Tracker command shell. Type 'addjob' to add a job, 'help' for commands, 'exit' to quit.")
    while True:
        try:
            cmd = input("> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting. Bye 👋")
            break

        if not cmd:
            continue
        if cmd in ("addjob", "add", "a"):
            add_one_job()
            continue
        if cmd in ("replace", "r", "redo"):
            if delete_last_row():
                print("Now enter the new job entry:")
                add_one_job(use_replace_mode=True)
            continue
        if cmd in ("exit", "quit", "q"):
            print("Exiting. Bye 👋")
            break
        if cmd in ("help", "h", "?"):
            print("Commands: addjob, replace, help, exit")
            continue
        print("Unknown command. Type 'help' for list of commands.")


if __name__ == "__main__":
    main()

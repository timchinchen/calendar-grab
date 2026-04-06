# calendar-grab

Calendar reporting utilities plus a web dashboard for live and demo data.

## What this project does

- Pulls calendar events from PagerDuty user calendars via the Google Calendar API
- Classifies meetings (customer-facing and internal)
- Exports report files for analysis
- Serves a web dashboard to view report metrics in:
  - **Demo preview mode** (no calendar access required)
  - **Live mode** (reads Google Calendar data)

## Main workflows

- **Customer reporting (multi-SC script):** `SCCalendarReporting.py`
- **Internal reporting (single SC script):** `calendarGrab-Internal.py`
- **Web dashboard (demo/live):** `webapp.py`

## Project files

- `SCCalendarReporting.py` - customer activity report across multiple SCs
- `calendarGrab-Internal.py` - internal activity categorization and totals
- `calendarGrabUtils.py` - shared filtering/classification/time/location helpers
- `Google.py` - OAuth credential and API service creation utility
- `reporting_service.py` - reusable service to fetch/classify customer meeting data
- `demo_data.py` - deterministic mock dataset for preview mode
- `webapp.py` - Flask application with dashboard endpoints
- `templates/index.html` - dashboard UI
- `static/css/style.css` - dashboard styling
- `APPLICATION_CODE_DOCUMENTATION.md` - full code-level documentation

## Requirements

- Python 3.10+
- Google Calendar API credentials file for live mode (used as `token.json`)

## Setup

Install dependencies:

```bash
pip3 install -r requirements.txt
```

## Run web app

```bash
python3 webapp.py
```

Then open `http://127.0.0.1:5000`.

Optional API endpoint for integrations:

```bash
http://127.0.0.1:5000/api/customer-events?mode=demo
```

### Dashboard modes

- **Demo mode:** works without Google credentials; uses synthetic but realistic records
- **Live mode:** uses Google Calendar API and your SC calendar list

You can switch mode from the dashboard form.

### Optional environment variables for live mode

- `CALENDAR_CLIENT_SECRET` (default: `token.json`)
- `SC_LIST` (comma-separated SC names; default aligns with script values)
- `START_DATE` (YYYY-MM-DD, default current year start)
- `END_DATE` (YYYY-MM-DD, default today)

Example:

```bash
SC_LIST=tchinchen,another01 START_DATE=2025-01-01 END_DATE=2025-12-31 python3 webapp.py
```

If OAuth tokens expire or are revoked, delete the `token files/` directory and run again to re-authorize.

## Run legacy scripts

Customer report:

```bash
python3 SCCalendarReporting.py
```

Internal report:

```bash
python3 calendarGrab-Internal.py
```

## Outputs (legacy scripts)

- Customer script:
  - `~CalendarCapture-GlobalSCs-FY24.csv`
  - `CalendarCaptureDEBUG.txt`
- Internal script:
  - `~CalendarCaptureInternal-<SCName>.txt`
  - `CalendarCaptureInternalDEBUG.txt`

## Notes

- Several values remain hardcoded in legacy scripts.
- The web app includes a no-access demo mode so the dashboard is always usable.
- See `APPLICATION_CODE_DOCUMENTATION.md` for architecture, data flow, and caveats.

## Suggested next web-app extensions

- Add persistent storage (SQLite/Postgres) to keep historical snapshots.
- Add scheduled background sync jobs for near-real-time live updates.
- Add authentication/authorization before exposing live customer data.

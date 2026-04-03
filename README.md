# calendar-grab

Python scripts for extracting and classifying Google Calendar activity into reporting files for Solutions Consultants (SCs).

## What this project does

- Pulls calendar events from PagerDuty user calendars via the Google Calendar API
- Classifies meetings (customer-facing and internal)
- Exports report files for analysis

Main workflows:

- **Customer reporting (multi-SC):** `SCCalendarReporting.py`
- **Internal reporting (single SC):** `calendarGrab-Internal.py`

## Project files

- `SCCalendarReporting.py` - customer activity report across multiple SCs
- `calendarGrab-Internal.py` - internal activity categorization and totals
- `calendarGrabUtils.py` - shared filtering/classification/time/location helpers
- `Google.py` - OAuth credential and API service creation utility
- `APPLICATION_CODE_DOCUMENTATION.md` - full code-level documentation

## Requirements

- Python 3
- Google Calendar API credentials file (currently used as `token.json`)
- Python packages:
  - `google-api-python-client`
  - `google-auth-httplib2`
  - `google-auth-oauthlib`
  - `validators`

## Setup

Install dependencies:

```bash
pip3 install google-api-python-client google-auth-httplib2 google-auth-oauthlib validators
```

Place your Google OAuth client JSON in the repo root (named `token.json` for current scripts).

## Run

Customer report:

```bash
python3 SCCalendarReporting.py
```

Internal report:

```bash
python3 calendarGrab-Internal.py
```

If OAuth tokens expire or are revoked, delete the `token files/` directory and run again to re-authorize.

## Outputs

- Customer script:
  - `~CalendarCapture-GlobalSCs-FY24.csv`
  - `CalendarCaptureDEBUG.txt`
- Internal script:
  - `~CalendarCaptureInternal-<SCName>.txt`
  - `CalendarCaptureInternalDEBUG.txt`

## Notes

- Several values are hardcoded (SC names, date ranges, output names).
- See `APPLICATION_CODE_DOCUMENTATION.md` for architecture, data flow, and caveats.

# Application Code Documentation

## Overview

This repository contains Python scripts that read Google Calendar data and generate activity reports for Solutions Consultants (SCs).  
The scripts authenticate with Google Calendar API, fetch events from PagerDuty-managed calendars, classify meeting types, and export report files.

Primary use cases:

- **Customer activity reporting** across multiple SCs (`SCCalendarReporting.py`)
- **Internal activity reporting** for a single SC (`calendarGrab-Internal.py`)

---

## Repository Structure

- `SCCalendarReporting.py`  
  Main multi-user reporting script for customer-facing meetings.

- `calendarGrab-Internal.py`  
  Internal meeting analysis for one SC, with category time totals.

- `calendarGrabUtils.py`  
  Shared helper functions: email filtering, activity classification, duration calculation, and location normalization.

- `Google.py`  
  Google OAuth/service bootstrap utility (`Create_Service`).

- `README.md`  
  Minimal project title.

---

## High-Level Data Flow

1. Script starts and defines target SC(s), date range, and output files.
2. `Google.Create_Service(...)` performs OAuth and builds a Google Calendar API client.
3. Script calls `service.events().list(...)` for each calendar.
4. Events are filtered:
   - remove irrelevant/internal/non-customer cases as needed
   - check attendee status (declined/accepted)
   - classify by keywords and attendee domains
5. Script writes output rows to local report files (`.csv` or `.txt`).
6. Optional summary totals are calculated (internal report script).

---

## Authentication and Google API Integration (`Google.py`)

### `Create_Service(client_secret_file, api_name, api_version, *scopes, prefix='')`

- Creates/loads OAuth credentials using `google-auth` and `google-api-python-client`.
- Persists token pickle files in a local folder:
  - `token files/token_<api>_<version><prefix>.pickle`
- If credentials are expired, attempts refresh.
- If no valid credentials exist, opens browser-based OAuth local server flow.
- Returns an authenticated Google API service object via `googleapiclient.discovery.build`.

### Notes

- The scripts use `token.json` as the client secret input.
- Deleting the `token files` folder forces re-authentication.

---

## Utility Logic (`calendarGrabUtils.py`)

### Email/attendee filtering

- `IsPersonalAccount(emailAddress)`  
  Checks domains like gmail/aol/hotmail/etc.

- `IsNonCustomerAccount(emailAddress)`  
  Checks a maintained allow/deny list of non-customer domains and community/vendor domains.

### Meeting classification

- `GetCustomerActivityType(summary)`  
  Keyword-to-type map for external meetings (e.g., demo, workshop, pov, qbr, training).

- `GetInternalActivityType(summary)`  
  Keyword-to-type map for internal events (e.g., PREP, ENABLEMENT, ONE TO ONE, WEBINAR).

- `ignoreActivity(summary)`  
  Filters non-working events (PTO, annual leave, out of office, reminders, etc.).

### Time and location helpers

- `getMeetingLength(start, end)`  
  Computes duration in minutes from ISO datetime strings.

- `getMeetingLocationType(loc)`  
  Strips known virtual meeting tokens (Teams/Zoom/Webex/etc.); treats URLs/empty values as `Remote`.

---

## Customer Reporting Script (`SCCalendarReporting.py`)

### Purpose

Generates a CSV report of customer-facing activity for a list of SCs.

### Core behavior

- Uses hardcoded SC lists and team groupings (`AMER`, `EMEA`, `APAC`).
- Queries each SC calendar (`<sc>@pagerduty.com`) between:
  - Start: fixed date (`2025-01-01`)
  - End: current day
- For each event:
  - Reads attendee list and organizer
  - Determines if SC accepted/declined
  - Extracts non-PagerDuty attendee company domains
  - Infers customer attendance status
  - Classifies event type via summary keywords
  - Calculates meeting duration and location mode
  - Deduplicates by date/time/company key
- Writes output to:
  - `~CalendarCapture-GlobalSCs-FY24.csv`
- Writes debug details to:
  - `CalendarCaptureDEBUG.txt`

### Output columns

- SC Name
- Team
- Date
- Time
- Account
- Event Type
- Duration
- PD Accepted
- Customer Attended
- IsRecurring
- Remote
- Address
- PD Count
- PD Attendees

---

## Internal Reporting Script (`calendarGrab-Internal.py`)

### Purpose

Analyzes one SC’s calendar and reports internal time allocation by category.

### Core behavior

- Uses one hardcoded SC name (`SCName`).
- Uses a fixed quarter date range (`2021-08-01` to `2021-10-31`).
- Fetches events and classifies each event as:
  - INTERNAL MEETING
  - ONE TO ONE
  - PREP
  - ENABLEMENT
  - RECRUITMENT
  - WEBINAR
  - VOLUNTEERING
- Ignores:
  - customer meetings (except recruitment handling)
  - declined/no-response events
  - ignored activity keywords
  - invalid start-time events
- Writes detailed event lines and category totals.

### Output files

- `~CalendarCaptureInternal-<SCName>.txt`
- `CalendarCaptureInternalDEBUG.txt`

---

## Dependencies

Expected Python packages from comments/imports:

- `google-api-python-client`
- `google-auth-httplib2`
- `google-auth-oauthlib`
- `validators`

Python 3 is required.

---

## How to Run

From repository root:

1. Ensure Google OAuth client JSON is present (`token.json` in current script usage).
2. Install dependencies.
3. Run one of:

- `python3 SCCalendarReporting.py`
- `python3 calendarGrab-Internal.py`

If auth fails due to revoked/expired token, delete `token files/` and rerun to re-authorize.

---

## Current Implementation Caveats

- `SCCalendarReporting.py` references `LEAD` and `Specialist` variables, but they are not defined in the file.
- Significant configuration is hardcoded (SC names, date ranges, output file names, domain lists).
- Classification relies on keyword matching and may misclassify edge-case summaries.
- Calendar API scope is full calendar access (`https://www.googleapis.com/auth/calendar`).

---

## Suggested Next Improvements

- Move config to a separate file (`.yaml`/`.json`) for SC lists, dates, and output paths.
- Add argument parsing (`argparse`) for date range and mode selection.
- Add unit tests for classification/filter utility functions.
- Add structured logging instead of plain debug text files.
- Add dependency lock/setup file (`requirements.txt`).

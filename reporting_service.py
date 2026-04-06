from __future__ import annotations

import datetime as dt
import random
from dataclasses import asdict, dataclass
from typing import Dict, Iterable, List, Optional

import calendarGrabUtils
from Google import Create_Service


DEFAULT_SC_TEAMS: Dict[str, str] = {
    "tchinchen": "EMEA",
    "another01": "AMER",
    "another02": "AMER",
    "another03": "APAC",
}


@dataclass
class EventRecord:
    sc_name: str
    team: str
    date: str
    time: str
    account: str
    event_type: str
    duration_minutes: float
    pd_accepted: str
    customer_attended: str
    is_recurring: str
    location: str
    address: str
    pd_count: int
    pd_attendees: str
    summary: str
    source_mode: str

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


def default_sc_names() -> List[str]:
    return list(DEFAULT_SC_TEAMS.keys())


def _clean_account_domain(domain: str) -> str:
    cleaned = domain.lower()
    for suffix in [".co.uk", ".co.jp", ".com", ".fr", ".au", ".de", ".gov", ".io"]:
        cleaned = cleaned.replace(suffix, "")
    return cleaned


def _event_date_in_range(event_date: str, start_date: dt.date, end_date: dt.date) -> bool:
    try:
        parsed = dt.date.fromisoformat(event_date)
    except ValueError:
        return False
    return start_date <= parsed <= end_date


def _extract_event_times(event: Dict[str, object]) -> Optional[tuple[str, str, float]]:
    start_obj = event.get("start", {}) if isinstance(event, dict) else {}
    end_obj = event.get("end", {}) if isinstance(event, dict) else {}
    if not isinstance(start_obj, dict) or not isinstance(end_obj, dict):
        return None

    start = start_obj.get("dateTime", start_obj.get("date"))
    end = end_obj.get("dateTime", end_obj.get("date"))
    if not start or not end:
        return None

    date_part = str(start)[:10]
    if "T" in str(start):
        time_part = str(start).split("T", 1)[1][:8]
    else:
        time_part = "00:00:00"

    duration = float(calendarGrabUtils.getMeetingLength(str(start), str(end)))
    return date_part, time_part, duration


def _build_record_from_google_event(
    event: Dict[str, object],
    sc_name: str,
    team: str,
    start_date: dt.date,
    end_date: dt.date,
) -> Optional[EventRecord]:
    extracted = _extract_event_times(event)
    if not extracted:
        return None

    date_part, time_part, duration = extracted
    if not _event_date_in_range(date_part, start_date, end_date):
        return None

    summary = str(event.get("summary", "(no summary)")).strip()
    organizer = str(event.get("organizer", {}).get("email", "")).lower()
    is_recurring = "TRUE" if "recurrence" in event else "FALSE"

    attendees = event.get("attendees", [])
    if not isinstance(attendees, list):
        attendees = []

    companies: List[str] = []
    sc_attended = True
    pd_response_status = ""
    customer_attended = "Customer Not Confirmed"
    pd_attendees: List[str] = []

    for attendee in attendees:
        if not isinstance(attendee, dict):
            continue
        email = str(attendee.get("email", "")).lower()
        if not email:
            continue

        if sc_name.lower() in email:
            pd_response_status = str(attendee.get("responseStatus", ""))
            if pd_response_status == "declined":
                sc_attended = False

        if "lily.greenhouse.io" in email:
            sc_attended = False

        if "pagerduty" in email:
            pd_attendees.append(email.replace("@pagerduty.com", ""))

        if "pagerduty" not in email and "rundeck" not in email:
            if not calendarGrabUtils.IsPersonalAccount(email) and not calendarGrabUtils.IsNonCustomerAccount(email):
                domain = email.split("@", 1)[-1]
                if domain and domain not in companies:
                    companies.append(domain)
                if str(attendee.get("responseStatus", "")) == "accepted":
                    customer_attended = "Customer Confirmed"

    if "pagerduty" not in organizer and organizer:
        customer_attended = "Customer Confirmed"

    if not sc_attended or not companies:
        return None

    event_type = calendarGrabUtils.GetCustomerActivityType(summary.lower())
    account = " ".join(sorted(_clean_account_domain(company) for company in companies))

    location = "Remote"
    address = ""
    if "location" in event:
        raw_location = str(event.get("location", ""))
        try:
            normalized = calendarGrabUtils.getMeetingLocationType(raw_location)
            if normalized != "Remote":
                location = "Onsite"
                address = raw_location
        except Exception:
            location = "Remote"
            address = ""

    return EventRecord(
        sc_name=sc_name,
        team=team,
        date=date_part,
        time=time_part,
        account=account,
        event_type=event_type,
        duration_minutes=duration,
        pd_accepted=pd_response_status,
        customer_attended=customer_attended,
        is_recurring=is_recurring,
        location=location,
        address=address.replace(",", " "),
        pd_count=len(pd_attendees),
        pd_attendees="|".join(pd_attendees),
        summary=summary,
        source_mode="live",
    )


def fetch_live_customer_records(
    sc_names: Iterable[str],
    start_date: dt.date,
    end_date: dt.date,
    sc_teams: Optional[Dict[str, str]] = None,
    token_file: str = "token.json",
) -> List[EventRecord]:
    team_map = sc_teams or DEFAULT_SC_TEAMS

    service = Create_Service(
        token_file,
        "calendar",
        "v3",
        ["https://www.googleapis.com/auth/calendar"],
    )
    if service is None:
        raise RuntimeError("Unable to initialize Google Calendar service")

    start_dt = dt.datetime.combine(start_date, dt.time.min).isoformat() + "Z"
    end_dt = dt.datetime.combine(end_date + dt.timedelta(days=1), dt.time.min).isoformat() + "Z"

    records: List[EventRecord] = []
    for sc_name in sc_names:
        dedupe = set()
        page_token = None
        while True:
            events = (
                service.events()
                .list(
                    calendarId=f"{sc_name}@pagerduty.com",
                    orderBy="updated",
                    singleEvents=False,
                    pageToken=page_token,
                    timeMin=start_dt,
                    timeMax=end_dt,
                    maxResults=2500,
                )
                .execute()
            )
            for event in events.get("items", []):
                record = _build_record_from_google_event(
                    event,
                    sc_name=sc_name,
                    team=team_map.get(sc_name, "UNASSIGNED"),
                    start_date=start_date,
                    end_date=end_date,
                )
                if not record:
                    continue

                dedupe_key = f"{record.sc_name}:{record.date}:{record.time}:{record.account}"
                if dedupe_key in dedupe:
                    continue
                dedupe.add(dedupe_key)
                records.append(record)

            page_token = events.get("nextPageToken")
            if not page_token:
                break

    records.sort(key=lambda record: (record.date, record.time), reverse=True)
    return records


def fetch_demo_customer_records(
    sc_names: Iterable[str],
    start_date: dt.date,
    end_date: dt.date,
    sc_teams: Optional[Dict[str, str]] = None,
    seed: int = 42,
) -> List[EventRecord]:
    team_map = sc_teams or DEFAULT_SC_TEAMS
    rng = random.Random(seed)

    companies = [
        "acme.com",
        "globex.io",
        "initech.co.uk",
        "umbrella.org",
        "waynetech.com",
        "hooli.io",
        "starkindustries.com",
    ]
    event_types = ["demo", "tech sync", "workshop", "pov", "qbr", "discovery", "training", "catch-up"]
    summaries = [
        "Weekly technical sync",
        "POV kickoff workshop",
        "Executive QBR planning",
        "Integration review session",
        "Training walkthrough",
        "Discovery and architecture deep dive",
    ]

    all_dates: List[dt.date] = []
    cursor = start_date
    while cursor <= end_date:
        all_dates.append(cursor)
        cursor += dt.timedelta(days=1)

    records: List[EventRecord] = []
    for sc_name in sc_names:
        team = team_map.get(sc_name, "UNASSIGNED")
        for day in all_dates:
            # Skip most weekends for more realistic demo data.
            if day.weekday() >= 5 and rng.random() < 0.8:
                continue
            events_today = rng.randint(0, 2)
            for _ in range(events_today):
                hour = rng.choice([8, 9, 10, 11, 13, 14, 15, 16])
                minute = rng.choice([0, 15, 30, 45])
                company = rng.choice(companies)
                pd_attendees = [sc_name, rng.choice(["sales1", "sales2", "manager1"])]
                duration = rng.choice([30, 45, 60, 90])
                record = EventRecord(
                    sc_name=sc_name,
                    team=team,
                    date=day.isoformat(),
                    time=f"{hour:02d}:{minute:02d}:00",
                    account=_clean_account_domain(company),
                    event_type=rng.choice(event_types),
                    duration_minutes=float(duration),
                    pd_accepted="accepted",
                    customer_attended=rng.choice(["Customer Confirmed", "Customer Not Confirmed"]),
                    is_recurring=rng.choice(["TRUE", "FALSE", "FALSE", "FALSE"]),
                    location=rng.choice(["Remote", "Onsite"]),
                    address="" if rng.random() < 0.75 else "Customer HQ",
                    pd_count=len(pd_attendees),
                    pd_attendees="|".join(pd_attendees),
                    summary=rng.choice(summaries),
                    source_mode="demo",
                )
                records.append(record)

    records.sort(key=lambda record: (record.date, record.time), reverse=True)
    return records


def summarize_customer_records(records: Iterable[EventRecord]) -> Dict[str, object]:
    records_list = list(records)
    duration_total = round(sum(record.duration_minutes for record in records_list), 2)

    by_team: Dict[str, Dict[str, float]] = {}
    by_event_type: Dict[str, Dict[str, float]] = {}
    sc_names = set()
    for record in records_list:
        sc_names.add(record.sc_name)

        team_bucket = by_team.setdefault(record.team, {"event_count": 0, "duration_minutes": 0.0})
        team_bucket["event_count"] += 1
        team_bucket["duration_minutes"] = round(team_bucket["duration_minutes"] + record.duration_minutes, 2)

        event_bucket = by_event_type.setdefault(record.event_type, {"event_count": 0, "duration_minutes": 0.0})
        event_bucket["event_count"] += 1
        event_bucket["duration_minutes"] = round(event_bucket["duration_minutes"] + record.duration_minutes, 2)

    return {
        "event_count": len(records_list),
        "duration_minutes": duration_total,
        "duration_hours": round(duration_total / 60.0, 2),
        "sc_count": len(sc_names),
        "by_team": by_team,
        "by_event_type": by_event_type,
    }


def records_to_dicts(records: Iterable[EventRecord]) -> List[Dict[str, object]]:
    return [record.to_dict() for record in records]

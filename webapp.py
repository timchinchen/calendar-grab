import datetime
import os

from flask import Flask, jsonify, render_template, request

from reporting_service import (
    default_sc_names,
    fetch_demo_customer_records,
    fetch_live_customer_records,
    records_to_dicts,
    summarize_customer_records,
)


app = Flask(__name__)


def _safe_date(value: str, default_date: datetime.date) -> datetime.date:
    if not value:
        return default_date
    try:
        return datetime.date.fromisoformat(value)
    except ValueError:
        return default_date


def _default_date_range() -> tuple[datetime.date, datetime.date]:
    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=90)
    return start_date, end_date


def _env_sc_list() -> list[str]:
    raw = os.environ.get("SC_LIST", "")
    if raw.strip():
        return [item.strip() for item in raw.split(",") if item.strip()]
    return default_sc_names()


def _load_records(
    mode: str,
    scs: list[str],
    start_date: datetime.date,
    end_date: datetime.date,
    token_file: str,
) -> tuple[str, str, list]:
    load_error = ""
    effective_mode = mode
    try:
        if mode == "live":
            records = fetch_live_customer_records(
                sc_names=scs,
                start_date=start_date,
                end_date=end_date,
                token_file=token_file,
            )
        else:
            records = fetch_demo_customer_records(
                sc_names=scs,
                start_date=start_date,
                end_date=end_date,
            )
    except Exception as exc:
        # Keep UI and API available even if live auth/calendar access fails.
        load_error = str(exc)
        records = fetch_demo_customer_records(
            sc_names=scs,
            start_date=start_date,
            end_date=end_date,
            seed=777,
        )
        effective_mode = "demo"

    return effective_mode, load_error, records


def _top_team(summary: dict) -> str:
    by_team = summary.get("by_team", {})
    if not isinstance(by_team, dict) or not by_team:
        return "n/a"
    return max(
        by_team.items(),
        key=lambda item: item[1].get("event_count", 0),
    )[0]


@app.route("/")
def dashboard():
    default_start, default_end = _default_date_range()
    mode = request.args.get("mode", "demo").lower()
    if mode not in {"demo", "live"}:
        mode = "demo"

    start_date = _safe_date(request.args.get("start_date", ""), default_start)
    end_date = _safe_date(request.args.get("end_date", ""), default_end)
    if end_date < start_date:
        start_date, end_date = end_date, start_date

    default_scs = ",".join(_env_sc_list())
    sc_values = request.args.get("scs", default_scs)
    scs = [sc.strip() for sc in sc_values.split(",") if sc.strip()]
    if not scs:
        scs = _env_sc_list()[:1]

    token_file = request.args.get("token_file", os.environ.get("CALENDAR_CLIENT_SECRET", "token.json"))
    mode, load_error, records = _load_records(
        mode=mode,
        scs=scs,
        start_date=start_date,
        end_date=end_date,
        token_file=token_file,
    )

    summary = summarize_customer_records(records)
    rows = records_to_dicts(records)[:250]
    top_team = _top_team(summary)

    return render_template(
        "index.html",
        mode=mode,
        rows=rows,
        summary=summary,
        top_team=top_team,
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
        sc_values=",".join(scs),
        token_file=token_file,
        load_error=load_error,
    )


@app.route("/api/customer-events")
def customer_events_api():
    default_start, default_end = _default_date_range()
    mode = request.args.get("mode", "demo").lower()
    if mode not in {"demo", "live"}:
        mode = "demo"

    start_date = _safe_date(request.args.get("start_date", ""), default_start)
    end_date = _safe_date(request.args.get("end_date", ""), default_end)
    if end_date < start_date:
        start_date, end_date = end_date, start_date

    sc_values = request.args.get("scs", ",".join(_env_sc_list()))
    scs = [sc.strip() for sc in sc_values.split(",") if sc.strip()]
    if not scs:
        scs = _env_sc_list()[:1]

    token_file = request.args.get("token_file", os.environ.get("CALENDAR_CLIENT_SECRET", "token.json"))
    mode, load_error, records = _load_records(
        mode=mode,
        scs=scs,
        start_date=start_date,
        end_date=end_date,
        token_file=token_file,
    )

    return jsonify(
        {
            "mode": mode,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "scs": scs,
            "load_error": load_error,
            "summary": summarize_customer_records(records),
            "rows": records_to_dicts(records),
        }
    )


if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "5000"))
    debug = os.environ.get("DEBUG", "0") == "1"
    app.run(host=host, port=port, debug=debug)

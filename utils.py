"""
Binaytara SEO Monitor — Utilities
Retry wrapper for Google API calls (handles transient SSL errors),
and month-to-date helpers.
"""

import time
import functools
import calendar
from datetime import date, timedelta
import streamlit as st


# ── Retry decorator ───────────────────────────────────────────────

def retry_on_ssl(max_retries=3, delay=2.0):
    """
    Decorator that retries a function up to `max_retries` times when it hits
    an SSL or transient connection error. Catches SSLError, ConnectionError,
    and generic transport errors from the Google API client.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    err_str = str(e).lower()
                    is_transient = any(k in err_str for k in [
                        "ssl", "record layer failure", "connection reset",
                        "connection aborted", "timed out", "timeout",
                        "eof occurred", "broken pipe", "transport",
                    ])
                    if is_transient and attempt < max_retries:
                        last_exc = e
                        time.sleep(delay * (attempt + 1))
                        continue
                    raise
            raise last_exc  # should not reach here, but safety
        return wrapper
    return decorator


# ── Month-to-date helpers ─────────────────────────────────────────

def mtd_ranges(lag_days: int = 3):
    """
    Return date ranges for month-to-date comparison:
      this_start, this_end   = 1st of current month → today minus lag
      last_start, last_end   = 1st of previous month → same day-of-month minus lag (prev month)
      last_full_start, last_full_end = full previous month
      days_elapsed, days_in_month, days_remaining
    """
    today = date.today()
    safe = today - timedelta(days=lag_days)

    # Current month MTD
    this_start = safe.replace(day=1)
    this_end = safe
    days_elapsed = (this_end - this_start).days + 1

    # Full current month length
    _, month_len = calendar.monthrange(safe.year, safe.month)
    days_remaining = month_len - this_end.day

    # Previous month: same day window
    if safe.month == 1:
        prev_year, prev_month = safe.year - 1, 12
    else:
        prev_year, prev_month = safe.year, safe.month - 1

    _, prev_month_len = calendar.monthrange(prev_year, prev_month)
    last_full_start = date(prev_year, prev_month, 1)
    last_full_end = date(prev_year, prev_month, prev_month_len)

    # Same day-of-month window in previous month (clamped)
    last_day = min(this_end.day, prev_month_len)
    last_start = date(prev_year, prev_month, 1)
    last_end = date(prev_year, prev_month, last_day)

    return {
        "this_start": str(this_start), "this_end": str(this_end),
        "last_mtd_start": str(last_start), "last_mtd_end": str(last_end),
        "last_full_start": str(last_full_start), "last_full_end": str(last_full_end),
        "days_elapsed": days_elapsed,
        "days_in_month": month_len,
        "days_remaining": days_remaining,
        "month_name": safe.strftime("%B %Y"),
        "prev_month_name": last_full_start.strftime("%B %Y"),
        "safe_day": this_end.day,
    }

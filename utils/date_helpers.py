# utils/date_helpers.py
from datetime import datetime

DISPLAY_DATE_FMT = '%d/%m/%Y'
ISO_DATE_FMT = '%Y-%m-%d'

def parse_date_input(date_str):
    """
    Aceita DD/MM/YYYY ou YYYY-MM-DD ou None.
    Retorna ISO YYYY-MM-DD (string).
    """
    if date_str is None:
        return datetime.now().strftime(ISO_DATE_FMT)
    s = str(date_str).strip()
    if not s:
        return datetime.now().strftime(ISO_DATE_FMT)
    for fmt in (DISPLAY_DATE_FMT, ISO_DATE_FMT):
        try:
            return datetime.strptime(s, fmt).strftime(ISO_DATE_FMT)
        except Exception:
            continue
    # fallback: try to parse loose
    try:
        return datetime.fromisoformat(s).strftime(ISO_DATE_FMT)
    except Exception:
        # last resort: now
        return datetime.now().strftime(ISO_DATE_FMT)

def iso_to_display(iso_date):
    if not iso_date:
        return ''
    try:
        return datetime.strptime(iso_date, ISO_DATE_FMT).strftime(DISPLAY_DATE_FMT)
    except Exception:
        return iso_date

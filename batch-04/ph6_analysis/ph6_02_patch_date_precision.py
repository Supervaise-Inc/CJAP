"""Phase 6 Step 2: scripts/build_date_index.py labels a Jan-1 date on a BOOK or BIOGRAPHY document 'year' precision. The date itself is never changed
(date_iso keeps '2003-01-01'); only `precision` and `source_of_date` change. Nothing else in the parser moves."""
from pathlib import Path
P = Path("C:/Users/ASUS/Projects/Supervaise-Reachy-Mini-Project/Final Project Folder/scripts/build_date_index.py")
raw = P.read_bytes(); crlf = b"\r\n" in raw
s = raw.decode("utf-8").replace("\r\n", "\n")
def sub(a, b):
    global s
    assert s.count(a) == 1, (s.count(a), a[:60]); s = s.replace(a, b)
sub('''def parse_date(raw, title=""):
    """Deterministic. Extracts a present date signal; never fabricates one.
    Returns (date_iso|null, precision in {day,month,year,none}, source_of_date)."""
    s = (raw or "").strip()
    if _ISO_DAY.match(s):
        return s, "day", "metadata_iso_day"''', '''def parse_date(raw, title="", doc_id=""):
    """Deterministic. Extracts a present date signal; never fabricates one.
    Returns (date_iso|null, precision in {day,month,year,none}, source_of_date).

    Phase 6: a BOOK ('B') or BIOGRAPHY ('G') document whose date is 1 January and whose source gives no finer evidence
    (the workbook cell IS 'YYYY-01-01') carries a placeholder, not a day: it is labelled 'year' precision so a temporal
    filter does not treat it as an exact day. The date itself is NEVER changed - only its precision label."""
    s = (raw or "").strip()
    if _ISO_DAY.match(s):
        if doc_id[:1] in ("B", "G") and s.endswith("-01-01"):
            return s, "year", "metadata_iso_jan1_year_precision"
        return s, "day", "metadata_iso_day"''')
sub('''date_iso, precision, src = parse_date(m.get("date"), m.get("title", ""))''', '''date_iso, precision, src = parse_date(m.get("date"), m.get("title", ""), doc_id)''')
sub('''        "parser": "metadata 'date' -> ISO day/month/year | year-extract from range/decade | title fallback | null",''',
    '''        "jan1_year_precision_docs": sorted(d for d in table if table[d]["source_of_date"] == "metadata_iso_jan1_year_precision"),
        "parser": "metadata 'date' -> ISO day/month/year (Jan-1 on a book/biography doc -> year precision, date unchanged) | year-extract from range/decade | title fallback | null",''')
import ast; ast.parse(s)
P.write_bytes((s.replace("\n", "\r\n") if crlf else s).encode("utf-8"))
print("patched build_date_index.py", "(CRLF preserved)" if crlf else "(LF)")

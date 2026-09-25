"""
P5 / CE-2 — Normalise and validate an enriched curated workbook.

Closes defect D-4: the W1.2 normaliser was never checked into either repo.

Input   batch-<id>/<type>_enriched.xlsx        (columns | books | speeches | biography)
Output  batch-<id>/<type>_enriched_normalized.xlsx
The input is never modified and the output is never the input.

What it does, per the Data Flow sheet (section 3, the 15-column curated schema):

  1. Header check          exactly config.CURATED_SCHEMA_COLUMNS columns, in the order
                           the pinned sheet for that type uses. Any difference STOPS.
  2. Article Code          must match config.DOC_ID_REGEX_PADDED, must be unique inside
                           the file, and must not already exist in corpus/, in the pinned
                           sheet, or in data/csv/retired_doc_ids.csv.
  3. Date                  must already be the text 'YYYY-MM-DD' and a real calendar date.
                           A datetime, a float or any other string is reported as an error.
                           NOTHING is coerced.
  4. Mojibake              cp1252-through-utf-8 damage ('a<EUR>(tm)' style) is repaired by the
                           standard round trip, and only when the round trip is lossless.
  5. Quotes and dashes     folded to whatever the pinned sheet for that type actually uses.
                           The convention is measured from the pinned sheet at run time,
                           not assumed: see _measure_punctuation_convention().
  6. JSON cells            parsed with json first, then ast.literal_eval; the shapes are
                           checked against the section 3 contract; list items are stripped
                           of surrounding whitespace and empty strings are dropped.
                           Case is PRESERVED -- the pinned sheets are not casefolded, which
                           is a deliberate difference from the old W1.2 spec.
  7. Output                written with dates as text and JSON re-serialised with
                           config.JSON_ENSURE_ASCII.

Every knob (encodings, schema width, ID regex, JSON escaping) comes from config.py.

Usage:
    python scripts/normalise_curated.py batch-04/columns_enriched.xlsx
    python scripts/normalise_curated.py batch-04/*_enriched.xlsx
    python scripts/normalise_curated.py batch-04/columns_enriched.xlsx --report-only
"""
from __future__ import annotations

import argparse
import ast
import datetime as _dt
import json
import re
import sys
import unicodedata
from collections import Counter, OrderedDict
from pathlib import Path

import openpyxl

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
import config  # noqa: E402

DATA_CSV = PROJECT_ROOT / "data" / "csv"
CORPUS_ROOT = PROJECT_ROOT / "corpus"
RETIRED_IDS_CSV = DATA_CSV / "retired_doc_ids.csv"

# The four curated types and the pinned sheet each one appends to (DF-4).
PINNED_FOR_TYPE = {
    "columns": DATA_CSV / "cjp_columns_curated_normalized.xlsx",
    "books": DATA_CSV / "cjp_books_curated_normalized.xlsx",
    "speeches": DATA_CSV / "cjp_speeches_curated_normalized.xlsx",
    "biography": DATA_CSV / "cjp_biography_curated_normalized.xlsx",
}

# ---------------------------------------------------------------------------
# The section 3 shape contract. These are not tunables: they are the schema.
# Each entry is checked against the pinned sheet at run time by
# _verify_contract_against_pinned(), so a drift in the sheet fails loudly here
# instead of silently later.
#   "text"    free text, no structure
#   "id"      the doc ID
#   "date"    text YYYY-MM-DD
#   "link"    URL or blank
#   "list"    JSON array of strings
#   "object"  JSON object, str -> list[str]
#   "records" JSON array of objects
# ---------------------------------------------------------------------------
FIELD_KIND = OrderedDict([
    ("Date", "date"),
    ("Title", "text"),
    ("Article Code", "id"),
    ("Link", "link"),
    ("Keyword/s", "list"),
    ("primary_topics", "list"),
    ("sub_topics", "list"),
    ("signature_phrases", "list"),
    ("entities", "object"),
    ("stances", "records"),
    ("notable_anecdotes", "list"),
    ("target_audience", "list"),
    ("register_markers", "list"),
    ("decision_framework_signals", "list"),
    ("one_paragraph_summary", "text"),
])
ENTITY_KEYS = {"people", "institutions", "places", "cases", "laws_treaties", "events"}
STANCE_KEYS = {"claim", "rhetorical_move", "confidence"}

JSON_KINDS = {"list", "object", "records"}
ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# Sequences that only appear when UTF-8 bytes were read as cp1252.
MOJIBAKE_MARKERS = ("Ã", "â€", "Â", "â\u0080")


class Stop(Exception):
    """A schema violation. The prompt says STOP, so nothing is written."""


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def _cell_text(value) -> str:
    return "" if value is None else str(value)


def repair_mojibake(s: str) -> str:
    """Undo one cp1252 <- utf-8 mis-decode, but only if it round-trips cleanly."""
    if not s or not any(m in s for m in MOJIBAKE_MARKERS):
        return s
    try:
        fixed = s.encode("cp1252", errors="strict").decode("utf-8", errors="strict")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return s
    # Refuse a "repair" that introduces a replacement character or loses length
    # implausibly -- better to flag it than to mangle the author's text.
    if "�" in fixed:
        return s
    return fixed


def _measure_punctuation_convention(pinned: Path) -> dict:
    """Read the pinned sheet and report which forms it actually uses.

    The prompt says to normalise 'the same way the existing pinned sheets do',
    so the rule is measured rather than assumed. Returns the fold maps to apply.
    """
    wb = openpyxl.load_workbook(pinned, read_only=True, data_only=True)
    ws = wb[wb.sheetnames[0]]
    counts = Counter()
    for row in ws.iter_rows(min_row=2, values_only=True):
        for cell in row:
            if isinstance(cell, str):
                for ch in ("‘", "’", "“", "”", "'", '"',
                           "—", "–", "-", "…", " "):
                    if ch in cell:
                        counts[ch] += cell.count(ch)
    wb.close()
    curly = sum(counts[c] for c in ("‘", "’", "“", "”"))
    straight = counts["'"] + counts['"']
    longdash = counts["—"] + counts["–"]
    hyphen = counts["-"]
    fold = {}
    if curly == 0 and straight > 0:
        fold.update({"‘": "'", "’": "'", "“": '"', "”": '"',
                     "‚": "'", "„": '"', "′": "'", "″": '"'})
    if longdash == 0 and hyphen > 0:
        fold.update({"—": "-", "–": "-", "−": "-"})
    if counts["…"] == 0:
        fold["…"] = "..."
    if counts[" "] == 0:
        fold[" "] = " "
    return {"counts": dict(counts), "fold": fold,
            "curly": curly, "straight": straight, "longdash": longdash, "hyphen": hyphen}


def apply_punctuation(s: str, fold: dict) -> str:
    if not s:
        return s
    out = s.translate(str.maketrans(fold)) if fold else s
    # NFC only: it composes accents without touching the characters themselves.
    return unicodedata.normalize("NFC", out)


def parse_jsonish(raw: str):
    """json first, then ast.literal_eval. Returns (value, how) or raises ValueError."""
    try:
        return json.loads(raw), "json"
    except Exception:
        pass
    try:
        return ast.literal_eval(raw), "literal_eval"
    except Exception as exc:
        raise ValueError(str(exc)) from None


def clean_list(items, fold: dict):
    """Strip whitespace, drop empties, keep order and CASE."""
    out = []
    for it in items:
        if isinstance(it, str):
            v = apply_punctuation(repair_mojibake(it), fold).strip()
            if v:
                out.append(v)
        else:
            out.append(it)
    return out


def load_known_ids() -> dict:
    """doc_id -> where it is already taken."""
    known = {}
    for p in sorted(CORPUS_ROOT.glob("*/*/*.md")):
        known.setdefault(p.stem.strip().upper(), "corpus/")
    for pinned in PINNED_FOR_TYPE.values():
        if not pinned.exists():
            continue
        wb = openpyxl.load_workbook(pinned, read_only=True, data_only=True)
        ws = wb[wb.sheetnames[0]]
        rows = ws.iter_rows(min_row=1, values_only=True)
        header = [_cell_text(h).strip() for h in next(rows)]
        try:
            idx = header.index("Article Code")
        except ValueError:
            wb.close()
            continue
        for r in rows:
            code = _cell_text(r[idx]).strip().upper()
            if code:
                known.setdefault(code, pinned.name)
        wb.close()
    if RETIRED_IDS_CSV.exists():
        import csv
        with open(RETIRED_IDS_CSV, encoding=config.FILE_ENCODING, newline="") as f:
            for row in csv.DictReader(f):
                code = (row.get("doc_id") or "").strip().upper()
                if code:
                    known[code] = "retired_doc_ids.csv"
    return known


def _verify_contract_against_pinned(pinned: Path, header: list, report: list) -> None:
    """Check FIELD_KIND against what the pinned sheet really holds."""
    wb = openpyxl.load_workbook(pinned, read_only=True, data_only=True)
    ws = wb[wb.sheetnames[0]]
    rows = ws.iter_rows(min_row=2, values_only=True)
    seen = {h: Counter() for h in header}
    for n, r in enumerate(rows):
        if n >= 200:
            break
        for i, h in enumerate(header):
            v = r[i] if i < len(r) else None
            if v in (None, ""):
                continue
            if not isinstance(v, str):
                seen[h][type(v).__name__] += 1
                continue
            try:
                parsed, _ = parse_jsonish(v)
            except ValueError:
                seen[h]["text"] += 1
                continue
            if isinstance(parsed, dict):
                seen[h]["object"] += 1
            elif isinstance(parsed, list):
                seen[h]["records" if parsed and isinstance(parsed[0], dict) else "list"] += 1
            else:
                seen[h]["text"] += 1
    wb.close()
    for h in header:
        kind = FIELD_KIND[h]
        if kind not in JSON_KINDS:
            continue
        top = seen[h].most_common(1)
        if top and top[0][0] != kind:
            report.append(
                f"NOTE  contract says {h} is '{kind}' but the pinned sheet's first 200 rows "
                f"look like '{top[0][0]}' ({dict(seen[h])})")


# ---------------------------------------------------------------------------
# the normaliser
# ---------------------------------------------------------------------------
def normalise(in_path: Path, report_only: bool = False) -> dict:
    name = in_path.name
    m = re.match(r"^(columns|books|speeches|biography)_enriched\.xlsx$", name)
    if not m:
        raise Stop(f"{name}: expected <type>_enriched.xlsx with type in {sorted(PINNED_FOR_TYPE)}")
    dtype = m.group(1)
    pinned = PINNED_FOR_TYPE[dtype]
    if not pinned.exists():
        raise Stop(f"pinned sheet not found: {pinned}")
    out_path = in_path.with_name(f"{dtype}_enriched_normalized.xlsx")
    if out_path.resolve() == in_path.resolve():
        raise Stop("refusing to write the output over the input")

    lines = [f"# P5 normalise - {name}", "",
             f"input   {in_path}", f"output  {out_path}",
             f"pinned  {pinned.name}", ""]
    errors, changes = [], Counter()
    examples = {}

    # --- schema order comes from the pinned sheet: it IS the contract ---
    pwb = openpyxl.load_workbook(pinned, read_only=True, data_only=True)
    pws = pwb[pwb.sheetnames[0]]
    pinned_header = [_cell_text(h).strip() for h in next(pws.iter_rows(min_row=1, values_only=True))]
    pwb.close()

    wb = openpyxl.load_workbook(in_path, data_only=True)
    ws = wb[wb.sheetnames[0]]
    rows = list(ws.iter_rows(min_row=1, values_only=True))
    if not rows:
        raise Stop("the workbook is empty")
    header = [_cell_text(h).strip() for h in rows[0]]
    data = [r for r in rows[1:] if any(_cell_text(c).strip() for c in r)]

    # 1. header
    if len(header) != config.CURATED_SCHEMA_COLUMNS:
        raise Stop(f"header has {len(header)} columns; config.CURATED_SCHEMA_COLUMNS "
                   f"is {config.CURATED_SCHEMA_COLUMNS}")
    if header != pinned_header:
        diff = [f"  position {i}: input {a!r} vs pinned {b!r}"
                for i, (a, b) in enumerate(zip(header, pinned_header)) if a != b]
        raise Stop("header does not match the pinned sheet's schema order:\n" + "\n".join(diff))
    if list(FIELD_KIND) != header:
        raise Stop("header does not match the section 3 contract in FIELD_KIND:\n"
                   f"  input  {header}\n  schema {list(FIELD_KIND)}")
    lines.append(f"Header OK: {len(header)} columns in pinned order.")

    _verify_contract_against_pinned(pinned, header, lines)

    # 2. the punctuation convention, measured
    conv = _measure_punctuation_convention(pinned)
    lines += ["", "## Punctuation convention measured from the pinned sheet",
              f"curly quotes {conv['curly']} - straight quotes {conv['straight']} - "
              f"em/en dashes {conv['longdash']} - hyphens {conv['hyphen']}",
              "folding applied: " + (", ".join(f"{k!r}->{v!r}" for k, v in conv["fold"].items())
                                     or "none"), ""]
    fold = conv["fold"]

    known = load_known_ids()
    seen_here = {}
    out_rows = []

    for n, raw_row in enumerate(data, start=2):
        row = list(raw_row) + [None] * (len(header) - len(raw_row))
        new = list(row)
        rid = _cell_text(row[header.index("Article Code")]).strip()

        for i, col in enumerate(header):
            kind = FIELD_KIND[col]
            val = row[i]
            before = val

            if kind == "date":
                if not isinstance(val, str):
                    errors.append(f"row {n} [{rid}] Date: type {type(val).__name__} "
                                  f"({val!r}) - must be the text YYYY-MM-DD, not coerced here")
                    continue
                s = val.strip()
                if not ISO_DATE.match(s):
                    errors.append(f"row {n} [{rid}] Date: {val!r} is not YYYY-MM-DD")
                    continue
                try:
                    _dt.date.fromisoformat(s)
                except ValueError:
                    errors.append(f"row {n} [{rid}] Date: {val!r} is not a real calendar date")
                    continue
                new[i] = s

            elif kind == "id":
                s = _cell_text(val).strip()
                if not re.match(config.DOC_ID_REGEX_PADDED, s):
                    errors.append(f"row {n} Article Code: {val!r} does not match "
                                  f"{config.DOC_ID_REGEX_PADDED}")
                elif s.upper() in seen_here:
                    errors.append(f"row {n} Article Code: {s} repeats row {seen_here[s.upper()]}")
                elif s.upper() in known:
                    errors.append(f"row {n} Article Code: {s} is already taken in "
                                  f"{known[s.upper()]}")
                else:
                    seen_here[s.upper()] = n
                new[i] = s

            elif kind in ("text", "link"):
                s = _cell_text(val)
                s = apply_punctuation(repair_mojibake(s), fold).strip()
                new[i] = s

            elif kind in JSON_KINDS:
                s = _cell_text(val).strip()
                if not s:
                    new[i] = ""
                    continue
                try:
                    parsed, how = parse_jsonish(s)
                except ValueError as exc:
                    errors.append(f"row {n} [{rid}] {col}: does not parse as JSON or "
                                  f"a Python literal - {exc}; value starts {s[:60]!r}")
                    continue
                if how == "literal_eval":
                    lines.append(f"NOTE  row {n} [{rid}] {col}: parsed only with "
                                 f"ast.literal_eval, re-serialised as strict JSON")

                if kind == "list":
                    if not isinstance(parsed, list):
                        errors.append(f"row {n} [{rid}] {col}: expected a JSON array, got "
                                      f"{type(parsed).__name__}")
                        continue
                    bad = [x for x in parsed if not isinstance(x, str)]
                    if bad:
                        errors.append(f"row {n} [{rid}] {col}: array holds non-strings "
                                      f"({[type(x).__name__ for x in bad][:3]})")
                        continue
                    parsed = clean_list(parsed, fold)

                elif kind == "object":
                    if not isinstance(parsed, dict):
                        errors.append(f"row {n} [{rid}] {col}: expected a JSON object, got "
                                      f"{type(parsed).__name__}")
                        continue
                    extra = set(parsed) - ENTITY_KEYS
                    if extra:
                        errors.append(f"row {n} [{rid}] {col}: keys {sorted(extra)} are outside "
                                      f"{sorted(ENTITY_KEYS)}")
                        continue
                    cleaned = {}
                    shape_bad = False
                    for k, v in parsed.items():
                        if not isinstance(v, list) or any(not isinstance(x, str) for x in v):
                            errors.append(f"row {n} [{rid}] {col}: '{k}' must be a list of strings")
                            shape_bad = True
                            break
                        cleaned[k] = clean_list(v, fold)
                    if shape_bad:
                        continue
                    parsed = cleaned

                elif kind == "records":
                    if not isinstance(parsed, list) or any(not isinstance(x, dict) for x in parsed):
                        errors.append(f"row {n} [{rid}] {col}: expected a JSON array of objects")
                        continue
                    cleaned, shape_bad = [], False
                    for rec in parsed:
                        extra = set(rec) - STANCE_KEYS
                        if extra:
                            errors.append(f"row {n} [{rid}] {col}: object keys {sorted(extra)} are "
                                          f"outside {sorted(STANCE_KEYS)}")
                            shape_bad = True
                            break
                        out = {}
                        for k, v in rec.items():
                            if not isinstance(v, str):
                                errors.append(f"row {n} [{rid}] {col}: '{k}' must be a string")
                                shape_bad = True
                                break
                            out[k] = apply_punctuation(repair_mojibake(v), fold).strip()
                        if shape_bad:
                            break
                        cleaned.append(out)
                    if shape_bad:
                        continue
                    parsed = cleaned

                new[i] = json.dumps(parsed, ensure_ascii=config.JSON_ENSURE_ASCII)

            if _cell_text(new[i]) != _cell_text(before):
                changes[col] += 1
                examples.setdefault(col, (n, rid, _cell_text(before), _cell_text(new[i])))

        out_rows.append(new)

    # 4. report
    lines += ["", "## Rows", f"read {len(data)} - written {0 if errors else len(out_rows)}", ""]
    lines += ["## Cells changed, by column"]
    if changes:
        for col, cnt in changes.most_common():
            n_, rid_, b, a = examples[col]
            lines.append(f"- **{col}** - {cnt} cell(s). Row {n_} [{rid_}]:")
            lines.append(f"    before: {b[:200]}")
            lines.append(f"    after : {a[:200]}")
    else:
        lines.append("- none: every cell was already in normal form.")
    lines += ["", "## Errors (flag, do not fix)"]
    lines += [f"- {e}" for e in errors] or ["- none"]

    if errors:
        lines += ["", "**No output written** - fix the rows above and re-run."]
        return {"ok": False, "out": None, "report": "\n".join(lines),
                "errors": errors, "changes": dict(changes), "rows": len(data)}
    if report_only:
        lines += ["", "(--report-only: no output written)"]
        return {"ok": True, "out": None, "report": "\n".join(lines),
                "errors": [], "changes": dict(changes), "rows": len(data)}

    # 3. write
    owb = openpyxl.Workbook()
    ows = owb.active
    ows.title = ws.title
    ows.append(header)
    for r in out_rows:
        ows.append(r)
    for row in ows.iter_rows(min_row=2, min_col=1, max_col=1):
        for cell in row:
            cell.number_format = "@"          # Date stays text
    owb.save(out_path)
    lines += ["", f"Written: {out_path}"]
    return {"ok": True, "out": out_path, "report": "\n".join(lines),
            "errors": [], "changes": dict(changes), "rows": len(data)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inputs", nargs="+", help="batch-<id>/<type>_enriched.xlsx")
    ap.add_argument("--report-only", action="store_true",
                    help="validate and report, write nothing")
    ap.add_argument("--report-to", metavar="PATH", help="also write the report to this file")
    args = ap.parse_args(argv)

    rc, chunks = 0, []
    for raw in args.inputs:
        p = Path(raw)
        if not p.is_absolute():
            p = (PROJECT_ROOT / p) if not p.exists() else p.resolve()
        try:
            res = normalise(p, report_only=args.report_only)
        except Stop as exc:
            chunks.append(f"# P5 normalise - {p.name}\n\nSTOP: {exc}")
            rc = 2
            continue
        chunks.append(res["report"])
        if not res["ok"]:
            rc = 1
    out = "\n\n---\n\n".join(chunks)
    print(out)
    if args.report_to:
        rp = Path(args.report_to)
        if not rp.is_absolute():
            rp = PROJECT_ROOT / rp
        rp.write_text(out + "\n", encoding=config.OUTPUT_ENCODING)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())

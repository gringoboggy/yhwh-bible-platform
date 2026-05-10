#!/usr/bin/env python3
"""
build_onix.py — Emit ONIX 3.0 records for retailer / distributor catalogs.

Reads `content/onix.yaml` and produces one ONIX 3.0 XML file per edition
(or one combined ONIXMessage with all five Products). Each Product is a
self-contained metadata record describing one of the platform's per-edition
EPUBs as a retailer would catalog it (Amazon, Apple Books, Kobo, OverDrive,
ProQuest, etc.).

Standards reference:
  - ONIX for Books 3.0 (current): https://www.editeur.org/93/Release-3.0-Downloads/
  - Code lists Issue 67+ (used here): https://www.editeur.org/14/Code-Lists/
  - BISAC subject codes: https://bisg.org/page/bisacedition

Output: well-formed XML; reference names (not short tags); UTF-8 encoded.

Usage:
    python3 scripts/build_onix.py                    # all editions; one file per
    python3 scripts/build_onix.py --edition jewish-study
    python3 scripts/build_onix.py --combined         # single message with all 5
    python3 scripts/build_onix.py --output-dir DIR

Output directory defaults to `epub_working/onix/`.

Incomplete-field warning: any TODO_* placeholder in the rendered XML is
flagged on stderr at end-of-run with the count and an exit code of 1 so
CI can gate submission. ONIX records with TODO_ISBN cannot be submitted
to retailers.
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.core.notes_io import atomic_write, ensure_backup  # noqa: E402

ONIX_CONFIG_PY = REPO_ROOT / "content" / "onix.py"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "epub_working" / "onix"

ONIX_NAMESPACE = "http://ns.editeur.org/onix/3.0/reference"
ONIX_RELEASE = "3.0"

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"

TODO_RE = re.compile(r"TODO_[A-Z_0-9]+")


# ----------------------------------------------------------------------
# Config loading — content/onix.py is a Python module with constants
# ----------------------------------------------------------------------


def load_onix_config() -> tuple[dict, list]:
    """Return (defaults, editions) from content/onix.py."""
    if not ONIX_CONFIG_PY.is_file():
        raise FileNotFoundError(f"missing {ONIX_CONFIG_PY}")
    import importlib.util

    spec = importlib.util.spec_from_file_location("_onix_cfg", ONIX_CONFIG_PY)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return getattr(mod, "DEFAULTS", {}), list(getattr(mod, "EDITIONS", []))


# ----------------------------------------------------------------------
# Element builders — one helper per ONIX block
# ----------------------------------------------------------------------


def _el(tag: str, text: str | None = None, **attrs) -> ET.Element:
    e = ET.Element(tag, attrs)
    if text is not None:
        e.text = str(text)
    return e


def _add(parent: ET.Element, tag: str, text: str | None = None, **attrs) -> ET.Element:
    e = _el(tag, text, **attrs)
    parent.append(e)
    return e


def build_header(defaults: dict) -> ET.Element:
    """ONIX 3.0 message header (one per file)."""
    h = ET.Element("Header")
    sender = _add(h, "Sender")
    _add(sender, "SenderName", defaults.get("publisher", "TODO_PUBLISHER_NAME"))
    _add(h, "SentDateTime", datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
    _add(h, "MessageNote", "ONIX 3.0 product record — Ethiopian Bible Scholar's Edition platform")
    return h


def build_product(edition: dict, defaults: dict) -> ET.Element:
    """One <Product> element for an edition record."""
    p = ET.Element("Product")

    # Record reference — unique within the message; opaque
    _add(p, "RecordReference", f"ethiopian-bible-{edition.get('id', 'unknown')}")
    _add(p, "NotificationType", "03")  # ONIX list 1: 03 = confirmed record

    # Identifiers
    pid = _add(p, "ProductIdentifier")
    _add(pid, "ProductIDType", "15")  # ISBN-13
    _add(pid, "IDValue", edition.get("isbn", "TODO_ISBN_13"))

    # Descriptive detail
    desc = _add(p, "DescriptiveDetail")
    _add(desc, "ProductComposition", "00")  # 00 = Single-component retail product
    _add(desc, "ProductForm", defaults.get("product_form", "EB"))
    _add(desc, "ProductFormDetail", defaults.get("product_form_detail", "E101"))

    # Title detail
    title = _add(desc, "TitleDetail")
    _add(title, "TitleType", "01")  # 01 = Distinctive title (book)
    title_el = _add(title, "TitleElement")
    _add(title_el, "TitleElementLevel", "01")  # 01 = Product
    _add(title_el, "TitleText", edition.get("title_full", "TODO_TITLE"))
    if edition.get("title_subtitle"):
        _add(title_el, "Subtitle", edition["title_subtitle"])

    # Contributor
    contrib_cfg = defaults.get("contributor", {})
    if contrib_cfg.get("name"):
        c = _add(desc, "Contributor")
        _add(c, "SequenceNumber", "1")
        _add(c, "ContributorRole", contrib_cfg.get("role", "B01"))
        _add(c, "PersonName", contrib_cfg["name"])
        if contrib_cfg.get("name_inverted"):
            _add(c, "PersonNameInverted", contrib_cfg["name_inverted"])
        if contrib_cfg.get("biographical_note"):
            _add(c, "BiographicalNote", contrib_cfg["biographical_note"])

    # Edition
    _add(desc, "EditionType", defaults.get("edition_type", "REV"))

    # Languages
    lang_cfg = defaults.get("language", {})
    if lang_cfg.get("primary"):
        lang = _add(desc, "Language")
        _add(lang, "LanguageRole", "01")  # 01 = Language of text
        _add(lang, "LanguageCode", lang_cfg["primary"])
    for sec in lang_cfg.get("secondary", []) or []:
        lang = _add(desc, "Language")
        _add(lang, "LanguageRole", "02")  # 02 = Original language
        _add(lang, "LanguageCode", sec)

    # Word count
    wc = defaults.get("word_count")
    if wc:
        ext = _add(desc, "Extent")
        _add(ext, "ExtentType", "02")  # 02 = Number of words in main content
        _add(ext, "ExtentValue", str(wc))
        _add(ext, "ExtentUnit", "02")  # 02 = Words

    # BISAC subjects
    for bisac_code in edition.get("bisac", []) or []:
        s = _add(desc, "Subject")
        _add(s, "MainSubject")  # empty marker — first listed is "main"
        _add(s, "SubjectSchemeIdentifier", "10")  # 10 = BISAC subject heading
        _add(s, "SubjectCode", bisac_code)

    # Audience
    aud_cfg = defaults.get("audience", {})
    if aud_cfg.get("code"):
        aud = _add(desc, "Audience")
        _add(aud, "AudienceCodeType", "01")  # 01 = ONIX audience codes
        _add(aud, "AudienceCodeValue", aud_cfg["code"])
    if aud_cfg.get("description"):
        ad = _add(desc, "AudienceDescription")
        ad.text = aud_cfg["description"]

    # ── CollateralDetail (description / blurb) ───────────────────
    coll = _add(p, "CollateralDetail")
    if edition.get("description"):
        td = _add(coll, "TextContent")
        _add(td, "TextType", "03")  # 03 = Description
        _add(td, "ContentAudience", "00")  # 00 = Unrestricted
        text_el = _add(td, "Text")
        text_el.text = edition["description"].strip()
        text_el.set("textformat", "06")  # 06 = Default text format

    # ── PublishingDetail ─────────────────────────────────────────
    pub = _add(p, "PublishingDetail")
    pub_imprint = _add(pub, "Imprint")
    _add(pub_imprint, "ImprintName", defaults.get("imprint") or defaults.get("publisher", "TODO_PUBLISHER_NAME"))
    pub_pub = _add(pub, "Publisher")
    _add(pub_pub, "PublishingRole", "01")  # 01 = Publisher
    _add(pub_pub, "PublisherName", defaults.get("publisher", "TODO_PUBLISHER_NAME"))
    _add(pub, "CountryOfPublication", defaults.get("publisher_country", "US"))
    _add(pub, "PublishingStatus", "04")  # 04 = Active
    pd = _add(pub, "PublishingDate")
    _add(pd, "PublishingDateRole", "01")  # 01 = Publication date
    _add(pd, "Date", defaults.get("publication_date", "TODO_YYYYMMDD"))

    # Sales rights
    sr_cfg = defaults.get("sales_rights", {})
    sr = _add(pub, "SalesRights")
    _add(sr, "SalesRightsType", sr_cfg.get("type", "01"))
    territory = _add(sr, "Territory")
    region = sr_cfg.get("territory", "WORLD")
    if region == "WORLD":
        _add(territory, "RegionsIncluded", "WORLD")
    else:
        _add(territory, "CountriesIncluded", region)

    # ── ProductSupply ────────────────────────────────────────────
    sup_cfg = defaults.get("supply", {})
    ps = _add(p, "ProductSupply")
    market = _add(ps, "Market")
    market_terr = _add(market, "Territory")
    _add(market_terr, "RegionsIncluded", "WORLD")

    supply = _add(ps, "SupplyDetail")
    sup_supplier = _add(supply, "Supplier")
    _add(sup_supplier, "SupplierRole", sup_cfg.get("role", "01"))
    _add(sup_supplier, "SupplierName", defaults.get("publisher", "TODO_PUBLISHER_NAME"))
    _add(supply, "ProductAvailability", sup_cfg.get("availability", "20"))

    price_cfg = sup_cfg.get("price", {})
    if price_cfg.get("amount"):
        price = _add(supply, "Price")
        _add(price, "PriceType", price_cfg.get("type", "02"))
        _add(price, "PriceAmount", price_cfg["amount"])
        _add(price, "CurrencyCode", price_cfg.get("currency", "USD"))

    return p


def build_message(editions: list, defaults: dict) -> ET.Element:
    """Top-level <ONIXMessage>."""
    msg = ET.Element(
        "ONIXMessage",
        {
            "release": ONIX_RELEASE,
            "xmlns": ONIX_NAMESPACE,
        },
    )
    msg.append(build_header(defaults))
    for ed in editions:
        msg.append(build_product(ed, defaults))
    return msg


def serialize(elem: ET.Element) -> str:
    """Pretty-print and return UTF-8 XML with declaration."""
    ET.indent(elem, space="  ")
    body = ET.tostring(elem, encoding="unicode")
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + body + "\n"


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------


def count_todos(xml_text: str) -> int:
    return len(TODO_RE.findall(xml_text))


def main() -> None:
    p = argparse.ArgumentParser(
        description="Emit ONIX 3.0 metadata for retailer distribution.",
    )
    p.add_argument("--edition", help="single edition id (e.g. 'jewish-study')")
    p.add_argument("--combined", action="store_true", help="emit one combined ONIXMessage with all editions")
    p.add_argument(
        "--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help=f"output directory (default: {DEFAULT_OUTPUT_DIR})"
    )
    args = p.parse_args()

    defaults, editions = load_onix_config()

    if args.edition:
        editions = [e for e in editions if e.get("id") == args.edition]
        if not editions:
            print(f"{RED}✗ no edition with id={args.edition!r}{RESET}", file=sys.stderr)
            sys.exit(2)

    args.output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{BOLD}build-onix{RESET}  {DIM}{len(editions)} edition(s){RESET}\n")
    total_todos = 0
    written: list[Path] = []

    if args.combined:
        msg = build_message(editions, defaults)
        xml = serialize(msg)
        n_todo = count_todos(xml)
        total_todos += n_todo
        out = args.output_dir / "onix-combined.xml"
        if out.exists():
            ensure_backup(out)
        atomic_write(out, xml)
        flag = GREEN + "✓" if n_todo == 0 else YELLOW + "⚠"
        print(
            f"  {flag}{RESET} onix-combined.xml  "
            f"{DIM}({len(editions)} products, {len(xml):,} bytes,"
            f" {n_todo} TODO placeholder{'s' if n_todo != 1 else ''}){RESET}"
        )
        written.append(out)
    else:
        for ed in editions:
            ed_id = ed.get("id", "unknown")
            single_msg = build_message([ed], defaults)
            xml = serialize(single_msg)
            n_todo = count_todos(xml)
            total_todos += n_todo
            out = args.output_dir / f"onix-{ed_id}.xml"

            # Idempotency: if the existing file is byte-identical to what
            # we'd write APART FROM the SentDateTime, skip the write. The
            # timestamp would otherwise tick on every run and show every
            # ONIX file as "modified" in git, even when nothing changed.
            _ts_re = re.compile(rb"<SentDateTime>\d{8}T\d{6}Z</SentDateTime>")
            placeholder = b"<SentDateTime>STABLE</SentDateTime>"
            new_normalized = _ts_re.sub(placeholder, xml.encode("utf-8"))
            should_write = True
            if out.is_file():
                existing = out.read_bytes()
                old_normalized = _ts_re.sub(placeholder, existing)
                if old_normalized == new_normalized:
                    should_write = False  # only timestamp would change

            if should_write:
                if out.exists():
                    ensure_backup(out)
                atomic_write(out, xml)
            flag = GREEN + "✓" if n_todo == 0 else YELLOW + "⚠"
            tag = "" if should_write else f" {DIM}(unchanged){RESET}"
            print(
                f"  {flag}{RESET} onix-{ed_id}.xml  "
                f"{DIM}({len(xml):,} bytes,"
                f" {n_todo} TODO placeholder{'s' if n_todo != 1 else ''}){RESET}"
                f"{tag}"
            )
            written.append(out)

    print(f"\n  output: {args.output_dir.relative_to(REPO_ROOT)}")
    if total_todos:
        print(f"  {YELLOW}⚠ {total_todos} TODO placeholder(s) remain across all files.{RESET}")
        print(f"    These records are NOT submission-ready. Fill in TODO_* fields")
        print(f"    in {ONIX_CONFIG_PY.relative_to(REPO_ROOT)} before submitting to retailers.\n")
        sys.exit(1)
    print(f"  {GREEN}✓ all fields populated; records are submission-ready.{RESET}\n")
    sys.exit(0)


if __name__ == "__main__":
    main()

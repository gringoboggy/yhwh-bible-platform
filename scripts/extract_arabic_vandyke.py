"""scripts/extract_arabic_vandyke.py — ingest the Van Dyck–Boustani Arabic Bible
(1865; eBible ``arb-vd``) into the project's translation store, remapping its two
tail-split divergences onto canonical KJV coordinates.

Thin driver over the generic VPL machinery: ``extract_translation.extract`` does the
VPL parse + eBible->project code mapping (incl. the BAR ch6 -> lje split), then
``versification.arabic_to_kjv`` folds the two extra trailing verses (1 Tim 6:22,
3 John 1:15) onto their preceding KJV verse and ``apply_remap`` concatenates them.
Re-runnable + idempotent (regenerates the same 66 ``content/translations/arabic-vandyke/*.py``).

PD basis: Van Dyck (d. 1895) + collaborators all pre-1929; the 1865 Beirut edition
is public domain by age. Plain text (HTML-escaped at render — NOT trusted_html);
RTL handled by the popup machinery (``arabic`` registry entry ``dir: rtl``).
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from scripts.core.versification import arabic_to_kjv  # noqa: E402
from scripts.extract_translation import extract  # noqa: E402

TRANSLATION_ID = "arabic-vandyke"


def main() -> int:
    stats = extract(TRANSLATION_ID, remap=arabic_to_kjv, report=True)
    print(
        f"{TRANSLATION_ID}: {stats['project_books_emitted']} books, "
        f"{stats['total_verses']:,} verses (2 tail-merges: 1Ti 6:22->6:21, 3Jn 1:15->1:14)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

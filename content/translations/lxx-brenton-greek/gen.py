"""Translation: lxx-brenton-greek · Book: gen

γ.5 SEED — Genesis 1:1-3 only. The full LXX Genesis (and the
remaining ~30 books) is γ.5.x's ingest job; this seed proves
the translation-registry wire-up and gives /compare + popup-
translation a 3-verse working sample for the canonical
opening of the Bible.

The Greek text reproduces the Codex Vaticanus tradition as
printed in Brenton 1844 (Samuel Bagster & Sons). Standard
editorial capitalization (initial capital on `Θεός` etc.) is
retained — the original uncial manuscripts had no case
distinction, but the convention has been universal in printed
LXX editions since the 16th century.

PD basis: Brenton d. 1862; 1844 edition is unambiguously out
of copyright in every jurisdiction.

Loaded via `scripts.core.translations._load_book` →
`ast.literal_eval` on the VERSES list. The module is data,
not code: it must never be exec'd.
"""

TRANSLATION = "lxx-brenton-greek"
BOOK = "gen"
VERSES = [
    (1, 1, "Ἐν ἀρχῇ ἐποίησεν ὁ Θεὸς τὸν οὐρανὸν καὶ τὴν γῆν."),
    (
        1,
        2,
        "ἡ δὲ γῆ ἦν ἀόρατος καὶ ἀκατασκεύαστος, καὶ σκότος ἐπάνω τῆς ἀβύσσου, καὶ πνεῦμα Θεοῦ ἐπεφέρετο ἐπάνω τοῦ ὕδατος.",
    ),
    (1, 3, "καὶ εἶπεν ὁ Θεός· γενηθήτω φῶς· καὶ ἐγένετο φῶς."),
]

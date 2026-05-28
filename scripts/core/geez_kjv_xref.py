from __future__ import annotations
import re

# Ge'ez numeral character → integer value map
_GEEZ_NUM: dict[str, int] = {
    "፩": 1,
    "፪": 2,
    "፫": 3,
    "፬": 4,
    "፭": 5,
    "፮": 6,
    "፯": 7,
    "፰": 8,
    "፱": 9,
    "፲": 10,
    "፳": 20,
    "፴": 30,
    "፵": 40,
    "፶": 50,
    "፷": 60,
    "፸": 70,
    "፹": 80,
    "፺": 90,
    "፻": 100,
    "፼": 10000,
}

# Ge'ez prepositional prefixes that may attach to a numeral token in the manuscript stream
_GEEZ_PREFIXES: tuple[str, ...] = ("እም", "ወ", "በ", "ለ")


def _compose(values: list[int]) -> int:
    """Compose an ordered list of Ge'ez digit-values into one integer.

    Ge'ez uses a multiply-then-add structure:
      - ፻ (100) or ፼ (10000): multiply the pending group (defaulting to 1 if empty)
      - tens / units: accumulate into the group

    Examples:
      [4, 100, 80] → 480   (4×100 + 80)
      [4, 100]     → 400   (4×100)
      [10, 2]      → 12    (12)
      [60]         → 60
    """
    total = 0
    group = 0
    for v in values:
        if v >= 100:  # ፻ or ፼: multiply the pending group
            total += (group or 1) * v
            group = 0
        else:  # tens (10..90) or units (1..9): accumulate
            group += v
    return total + group


def numeral_token_value(tok: str) -> int | None:
    """Return the integer value of a bare Ge'ez numeral token, or None.

    Returns a value only if EVERY character of *tok* is in _GEEZ_NUM.
    """
    if not tok:
        return None
    if all(c in _GEEZ_NUM for c in tok):
        return _compose([_GEEZ_NUM[c] for c in tok])
    return None


def _numeral_chars(tok: str) -> str | None:
    """Strip a single leading Ge'ez prepositional prefix from *tok*.

    If the remainder is non-empty and every character is in _GEEZ_NUM,
    return that remainder string.  Otherwise return None.

    Prefixes tried (longest first to avoid partial matches): እም, ወ, በ, ለ.
    """
    for prefix in _GEEZ_PREFIXES:
        if tok.startswith(prefix):
            remainder = tok[len(prefix) :]
            if remainder and all(c in _GEEZ_NUM for c in remainder):
                return remainder
            # Prefix matched but remainder invalid — do not try shorter prefixes
            # (a token like ወእምዝ should not fall through to strip just ወ and
            # re-evaluate እምዝ as a potential remainder).
            return None
    # No prefix — check the token itself
    if tok and all(c in _GEEZ_NUM for c in tok):
        return tok
    return None


# Tokens that continue an in-progress numeral run without contributing digits
_CONNECTORS: frozenset[str] = frozenset({"ወ", "፡"})


def verse_numerals(tokens: list[str]) -> set[int]:
    """Find every numeral VALUE in a verse's token list by composing maximal runs.

    Algorithm:
    - Walk tokens left to right.
    - A token is "numeral-bearing" if _numeral_chars(tok) is not None.
    - A CONNECTOR token ("ወ" or "፡") continues an in-progress run only;
      it does NOT start a new run.
    - Any other non-numeral-bearing token ends the current run (if any).
    - For each completed maximal run, _compose the gathered digit-values and
      add the result to the output set.

    Returns a set[int] of all run values.
    """
    result: set[int] = set()
    run_values: list[int] = []  # digit-values gathered for the current run

    def _flush() -> None:
        if run_values:
            result.add(_compose(run_values))
            run_values.clear()

    for tok in tokens:
        nc = _numeral_chars(tok)
        if nc is not None:
            # Numeral-bearing: extend current run (or start one)
            run_values.extend(_GEEZ_NUM[c] for c in nc)
        elif tok in _CONNECTORS:
            # Connector: continue run only if one is active; otherwise ignore
            pass
        else:
            # Non-numeral, non-connector: flush the current run
            _flush()

    # Flush any trailing run
    _flush()
    return result


# ── B2: KJV English number-word maps ─────────────────────────────────────────

# Cardinals and ordinals 1–19 → value
_ONES_TEENS: dict[str, int] = {
    "one": 1,
    "first": 1,
    "two": 2,
    "second": 2,
    "three": 3,
    "third": 3,
    "four": 4,
    "fourth": 4,
    "five": 5,
    "fifth": 5,
    "six": 6,
    "sixth": 6,
    "seven": 7,
    "seventh": 7,
    "eight": 8,
    "eighth": 8,
    "nine": 9,
    "ninth": 9,
    "ten": 10,
    "tenth": 10,
    "eleven": 11,
    "eleventh": 11,
    "twelve": 12,
    "twelfth": 12,
    "thirteen": 13,
    "thirteenth": 13,
    "fourteen": 14,
    "fourteenth": 14,
    "fifteen": 15,
    "fifteenth": 15,
    "sixteen": 16,
    "sixteenth": 16,
    "seventeen": 17,
    "seventeenth": 17,
    "eighteen": 18,
    "eighteenth": 18,
    "nineteen": 19,
    "nineteenth": 19,
}

# Tens cardinals and ordinals → value
_TENS: dict[str, int] = {
    "twenty": 20,
    "twentieth": 20,
    "thirty": 30,
    "thirtieth": 30,
    "forty": 40,
    "fortieth": 40,
    "fifty": 50,
    "fiftieth": 50,
    "sixty": 60,
    "sixtieth": 60,
    "seventy": 70,
    "seventieth": 70,
    "eighty": 80,
    "eightieth": 80,
    "ninety": 90,
    "ninetieth": 90,
}

# KJV score idioms → value
_SCORES: dict[str, int] = {
    "score": 20,
    "threescore": 60,
    "fourscore": 80,
}

# Multiplier words (hundred, thousand)
_HUNDREDS: frozenset[str] = frozenset({"hundred", "hundredth"})
_THOUSANDS: frozenset[str] = frozenset({"thousand", "thousandth"})

# All number-word tokens (for fast membership test)
_ALL_NUM_WORDS: frozenset[str] = (
    frozenset(_ONES_TEENS) | frozenset(_TENS) | frozenset(_SCORES) | _HUNDREDS | _THOUSANDS | frozenset({"and"})
)

# Value lookup combining all plain-value maps
_VALUE_MAP: dict[str, int] = {**_ONES_TEENS, **_TENS, **_SCORES}


def kjv_number_values(text: str) -> set[int]:
    """Extract every integer expressed in English number-words in *text*.

    Tokenises by splitting on any non-letter character, lowercases, and walks
    tokens building maximal runs of number-words.  "and" is a connector — it
    continues an active run but never starts one and contributes no value.
    Multipliers (hundred, thousand) scale the accumulated sub-group exactly as
    standard English grammar dictates.  Each completed run that contained at
    least one value/multiplier word emits ``result + current`` into the output.

    Returns a ``set[int]``; empty when no numbers are found.
    """
    tokens = [t for t in re.split(r"[^a-zA-Z]+", text.lower()) if t]

    result_set: set[int] = set()

    # State for the current run
    result = 0  # thousands-and-above accumulator
    current = 0  # current hundreds-and-below sub-group
    in_run = False  # True once a value/multiplier word has been seen

    def _flush_run() -> None:
        nonlocal result, current, in_run
        if in_run:
            result_set.add(result + current)
        result = 0
        current = 0
        in_run = False

    for tok in tokens:
        if tok == "and":
            # Connector: continue run if active; otherwise ignore (never starts)
            continue
        if tok in _VALUE_MAP:
            current += _VALUE_MAP[tok]
            in_run = True
        elif tok in _HUNDREDS:
            current = (current or 1) * 100
            in_run = True
        elif tok in _THOUSANDS:
            result += (current or 1) * 1000
            current = 0
            in_run = True
        else:
            # Non-number word: flush current run and start fresh
            _flush_run()

    # Flush any trailing run
    _flush_run()
    return result_set


# ── B3: Ge'ez ↔ KJV proper-noun seed map + matcher ──────────────────────────

# Curated bilingual map: Ge'ez surface form → lowercase KJV English term.
# Ge'ez names do NOT transliterate to KJV English, so this is a hand-seeded
# bilingual map covering Kings/Samuel recurring proper nouns.
_GEEZ_KJV_NAMES: dict[str, str] = {
    "ሰሎሞን": "solomon",
    "እስራኤል": "israel",
    "ግብጽ": "egypt",
    "ሊባኖስ": "lebanon",
    "ኪሩብ": "cherub",  # matches "cherub" / "cherubims"
    "እግዚእብሔር": "lord",  # the divine name -> "LORD"
    "ዳዊት": "david",
    "ኢየሩሳሌም": "jerusalem",
    "ሒራም": "hiram",
    "ኪራም": "hiram",  # orthographic variant
    "ይሁዳ": "judah",
    "ሳኦል": "saul",
    "ሳሙኤል": "samuel",
}


def proper_noun_hits(geez_tokens: list[str], kjv_text: str) -> set[str]:
    """Return the set of KJV proper-noun terms found in *kjv_text* that
    correspond to Ge'ez tokens in *geez_tokens*.

    For each token the bare stem is obtained by stripping a single leading
    Ge'ez prefix (tried longest-first via ``_GEEZ_PREFIXES``).  Both the raw
    token and the prefix-stripped stem are looked up in ``_GEEZ_KJV_NAMES``.
    A KJV term is included in the result only when it occurs at a word
    boundary in *kjv_text* (so "cherub" matches inside "cherubims" but not
    mid-word false hits).
    """
    kjv_lower = kjv_text.lower()
    hits: set[str] = set()

    for tok in geez_tokens:
        # Collect candidates: raw token + prefix-stripped stem (if different)
        candidates = [tok]
        for prefix in _GEEZ_PREFIXES:
            if tok.startswith(prefix):
                stem = tok[len(prefix) :]
                if stem:
                    candidates.append(stem)
                break  # only strip one prefix; stop after first match

        for candidate in candidates:
            term = _GEEZ_KJV_NAMES.get(candidate)
            if term and re.search(r"\b" + re.escape(term), kjv_lower):
                hits.add(term)

    return hits


# ── B4: anchor + monotonic interpolation mapping ─────────────────────────────


def _max_weight_nondecreasing(cands: list[tuple[int, int, int]]) -> list[tuple[int, int]]:
    """Keep the non-decreasing-by-``kv`` subsequence of MAXIMUM TOTAL SCORE
    (so a few weak low-kv anchors can't displace the strong ones).

    *cands* is a list of ``(base_idx, kv, score)`` triples in ascending
    ``base_idx`` order.  Returns the subsequence whose ``kv`` values are
    non-decreasing and whose sum of scores is maximised — i.e. the set of
    candidate anchors that do not reorder the KJV spine AND collectively carry
    the most evidential weight.  Ties in total score favour the first-found
    (lowest-index) chain (deterministic).

    Returns ``[(base_idx, kv), ...]`` (score dropped from output).
    """
    if not cands:
        return []
    n = len(cands)
    dp = [c[2] for c in cands]  # best total score of a chain ending at i
    prev = [-1] * n
    for i in range(n):
        for j in range(i):
            if cands[j][1] <= cands[i][1] and dp[j] + cands[i][2] > dp[i]:
                dp[i] = dp[j] + cands[i][2]
                prev[i] = j
    end = max(range(n), key=lambda k: dp[k])  # highest total score; ties → first
    out: list[tuple[int, int]] = []
    while end != -1:
        out.append((cands[end][0], cands[end][1]))
        end = prev[end]
    return out[::-1]


def build_kjv_xref(collation: dict, kjv_rows: list, book: str) -> dict:
    """Map each base (Ge'ez) verse to its KJV verse(s) with confidence tags.

    Composes the B1–B3 signals (Ge'ez numerals, KJV English numbers, bilingual
    proper-noun hits) into a per-verse score against every KJV row of the
    chapter, picks the best-scoring KJV verse as a candidate anchor, filters the
    candidates to a monotonic (non-reordering) backbone, then linearly
    interpolates every remaining base verse between confirmed anchors (with two
    virtual endpoints so edges interpolate cleanly).

    Returns ``{geez_v(int): {"kjv": [[book, chapter, kv], ...],
    "confidence": "anchored" | "interpolated"}}``.  Guarantees: every base verse
    has an entry; the ``kv`` sequence in base order is non-decreasing; anchored
    entries reflect a real numeral/name match.
    """
    pv = collation["primary_verses"]
    chapter = collation["chapter"]
    n = len(pv)
    if n == 0:
        return {}

    # 2. Score → candidate anchors.
    cands: list[tuple[int, int, int]] = []
    for i in range(n):
        nums = verse_numerals(pv[i]["tokens"])
        best_kv = None
        best_score = 0
        for kch, kv, ktext in kjv_rows:
            score = len(nums & kjv_number_values(ktext)) + len(proper_noun_hits(pv[i]["tokens"], ktext))
            # Highest score wins; on ties keep the LOWEST kv.
            if score > best_score or (score == best_score and best_kv is not None and kv < best_kv):
                best_score = score
                best_kv = kv
        if best_score > 0:
            cands.append((i, best_kv, best_score))

    # 3. Monotonic filter — anchors can't reorder the spine.
    anchors = dict(_max_weight_nondecreasing(cands))

    # 4. Interpolate every base verse with two virtual endpoints.
    points = [(-1, 0)] + sorted(anchors.items()) + [(n, len(kjv_rows) + 1)]
    result: dict = {}
    for j in range(n):
        if j in anchors:
            kv = anchors[j]
            confidence = "anchored"
        else:
            lo_i, lo_kv = max((p for p in points if p[0] < j), key=lambda p: p[0])
            hi_i, hi_kv = min((p for p in points if p[0] > j), key=lambda p: p[0])
            frac = (j - lo_i) / (hi_i - lo_i)
            kv = lo_kv + round(frac * (hi_kv - lo_kv))
            confidence = "interpolated"
        # Clamp kv into the valid KJV verse range.
        kv = max(1, min(kv, len(kjv_rows)))
        result[pv[j]["geez_v"]] = {"kjv": [[book, chapter, kv]], "confidence": confidence}

    return result


def kjv_coverage(xref: dict) -> dict:
    """Summarise the anchored vs interpolated split of a ``build_kjv_xref`` map."""
    n = len(xref)
    a = sum(1 for e in xref.values() if e["confidence"] == "anchored")
    return {
        "base_verses": n,
        "anchored": a,
        "interpolated": n - a,
        "anchored_pct": round(a / n * 100, 2) if n else 0.0,
    }

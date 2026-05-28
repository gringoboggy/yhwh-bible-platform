from __future__ import annotations

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

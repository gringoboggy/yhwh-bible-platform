# Samuel/Kings folio-mapping — the unique-event anchor index (P0)

**Purpose.** The persistent reference every P0 folio-mapping vision pass reads FIRST.
It encodes the method that retires the 2026-06-03 *dense-section wall*
(`docs/superpowers/notes/2026-06-03-p0-samuel-dense-section-wall.md`): map each
canonical chapter to its CAM (base) + GG (2nd-witness) folio(s) by anchoring on
**UNIQUE, non-recurring narrative events**, NOT on the recurring landmark phrases that
made the prior passes give geometrically-impossible assignments.

**Updating rule.** Append-only. When a batch closes, append the confirmed
folio→chapter onsets to §6 so the next batch starts from observed truth.

---

## 1. Why the prior method failed, and the fix

- **Failure cause #1 — recurring phrases.** The Saul/Samuel/Philistine/Amalek narrative
  repeats the exact anchors prior passes keyed on ("Samuel said to all Israel",
  "the Philistines", Mizpeh, Gilgal) across many chapters → content-matching
  mis-attributed folios.
- **Failure cause #3 — density.** CAM's hand is dense + variable; verse-count
  arithmetic can't disambiguate.
- **Failure cause #2 — versification — RE-VERIFIED 2026-06-03 and DOWNGRADED.** The
  on-disk `lxx-swete-greek` 1 Samuel is **near-identical in versification to KJV**
  (per-chapter verse counts match within ~4 verses; the "LXX ~45% shorter" figure in
  the wall doc describes the *Old-Greek minus*, not the Swete text we hold). So
  chapter-level versification is NOT the main problem. The recension difference that
  DOES matter is **per-witness**, see §2.

**The fix (this index):** anchor on the ONE unique event that opens / characterizes
each chapter (donkeys, Nahash's eye-threat, Agag, David's harp …). These do not recur,
so they pin a folio unambiguously even in the dense middle.

## 2. The two witnesses follow DIFFERENT recensions (from `CAM_topology.md` §4 / 1ki6)

- **GG = LXX / 3–4 Kingdoms recension — COMPRESSED.** Fewer, longer verses; chapters
  span ~2–3 folios (often house-first / event-first ordering). Anchor GG on the LXX
  event order.
- **CAM = MT / printed-closer — FULLER.** Finer segmentation, more verses, dense hand;
  MT/KJV chapter content + ordering anchors CAM well.
- **Consequence for mapping:** the *event order* is shared (same story), so unique-event
  anchoring works for BOTH; only the *folio span per chapter* differs (GG tighter).
  Cross-check: if a GG folio and a CAM folio both show the same unique event, they are
  the same chapter — mutual confirmation.

## 3. CAM foliation arithmetic (RELIABLE — from the wall-doc finding, verified at 4× zoom)

- **2 views per leaf; arithmetic HOLDS.** Anchor **f106r = view 215**. Odd view = recto
  (penned number top-right under the inked `ነገሥት` header, at y≈0.10–0.14 — *below* the
  scale bar); even view = verso (shares the leaf number). Verified penned numbers:
  view221=f109r, 223=f110r, **225=f111r, 227=f112r, 229=f113r**.
- **On disk (1_Samuel/Cambridge-Add-1570-hires):** f106r,f106v,f107r,f107v,f108r,f108v,
  f109r,f109v,f110r,f110v (chapter-labelled — 1–6 labels RELIABLE; **7–10 labels are
  PROVISIONAL/suspect**), f111r,f111v,f112r (labelled 1Sam17, the calibration — see §5),
  and folio-neutral **view225–230 = f111r,f111v,f112r,f112v,f113r,f113v**
  (view225/226/227 are byte-identical to the f111r/f111v/f112r files).
- **Column reading order:** L → M → R per side, then top-L of the next side. Column/folio
  turns are the omission hotspot — trace continuity.

## 4. Density model for 1 Samuel (CAM)

1sa 1–6 reliably spans f106r–f108v ≈ **1 chapter/side**. ch17 is CONFIRMED on
f111r–f112r (its content validated + collated). Therefore chapters **7–16 (10 ch) are
compressed into ≈ f109r–f111r (~5 sides) ≈ 2 chapters/side** — expect TWO chapter
onsets per side through the middle. (This 2/side compression IS the wall; unique-event
anchoring resolves it.)

## 5. The 1sa17 calibration-label caveat (RE-VERIFY before trusting f111 labels)

The calibration witness labels its images `f111r/f111v/f112r_1Sam17`, but a careful pass
read **1 Sam 15 content on f111r** (Saul's confession 15:24; Agag hewn at Gilgal 15:33)
and the **1 Sam 17 (Goliath) onset on f111v→f112r** (the lion/bear speech 17:34–36). The
ch17 content validated, so the images DO contain ch17 — only the folio *sigla* for ch17
may be off by ~one chapter-cluster. **Action: a vision pass must confirm where ch17
actually begins and correct the manifest 1sa17 CAM folios + the calibration
`folio_sigla` if wrong.**

## 6. Unique-event anchor table — 1 Samuel (key on these, NOT recurring phrases)

Geʽez forms below are from the validated calibration chapters where available; others are
standard Geʽez OT forms. The scribe may spell variantly — match the EVENT first.

| ch | UNIQUE onset / characterizing event (anchor on this) | Geʽez name anchors |
|----|------------------------------------------------------|--------------------|
| 1  | Elkanah & Hannah at Shiloh; Hannah's vow; Samuel born | ሕልቃና, ሐና, ኤሊ, ሴሎ, ሰሙኤል |
| 2  | Hannah's SONG ("my heart exults"); Eli's wicked sons; man-of-God curse | አፍኒ, ፊንሐስ |
| 3  | Samuel's night CALL ("Samuel, Samuel") — threefold | ሰሙኤል, ኤሊ |
| 4  | ARK captured by Philistines; Eli falls & dies; Ichabod born | ታቦት, ፈልስጥኤም |
| 5  | Ark in DAGON's temple; Dagon falls; tumors on Ashdod | ዳጎን, አዛጦን |
| 6  | Ark returned on a CART with golden mice; BETH-SHEMESH; Kirjath-jearim | ቤተሳሜስ, ቃርያትይዓሪም |
| 7  | EBENEZER ("stone of help") raised; Mizpeh; thunder routs Philistines | አቤንኤዘር, ማsituational/ምጽጳ |
| 8  | Israel DEMANDS A KING "like the nations"; the king's-ways warning | ንጉሥ |
| 9  | Saul seeks lost DONKEYS; meets Samuel the seer; the shoulder portion | ሳኦል, ቂስ (Kish), አድግ (asses) |
| 10 | Saul ANOINTED with oil; "Saul among the prophets"; HIDES in the baggage; lot at Mizpeh | ሳኦል |
| 11 | NAHASH the Ammonite besieges Jabesh-Gilead; right-EYE threat; oxen hewn; Gilgal | ናአስ, ኢያቤስ ገላዓድ |
| 12 | Samuel's FAREWELL ("whose ox have I taken?"); thunder & rain in wheat harvest | ሰሙኤል |
| 13 | Saul's reign formula; MICHMASH (chariots like sand); unlawful sacrifice; "no smith" | ማክማስ |
| 14 | JONATHAN & armor-bearer storm the garrison (Bozez/Seneh); rash oath; HONEY | ዮናታን |
| 15 | AMALEK war; AGAG spared then hewn; "to obey is better than sacrifice"; Saul rejected | አማሌቅ, አጋግ |
| 16 | DAVID anointed at Bethlehem (Jesse's youngest, ruddy); the HARP for Saul's evil spirit | ዳዊት, እሴይ (Jesse) |
| 17 | GOLIATH of Gath in the Valley of ELAH; David & the sling; five stones | ጎልያድ, ሶኮት, ኤላ, ፈልስጥኤም |
| 18 | David & Jonathan's covenant; "Saul his thousands, David his ten thousands"; Michal | ዮናታን, ሜልኮል |
| 19 | Saul hurls the javelin; Michal lets David down a window; the image in the bed | ዳዊት, ሳኦል |
| 20 | Jonathan's ARROW signal; the new-moon feast; the covenant of friendship | ዮናታን |
| 21 | David eats the SHEWBREAD at Nob (Ahimelech); feigns madness before Achish of Gath | አቢሜሌክ, ኤንካስ (Achish) |
| 22 | The cave of Adullam; Doeg the Edomite slays the priests of Nob | ዶይ (Doeg), አዶላም |
| 23 | David saves Keilah; Ziph; Saul pursues; rock of escape (Maon) | ቄዒላ, ዚፍ |
| 24 | David spares Saul in the CAVE (En-gedi); cuts the skirt | ጋዳም (cave), ዐይንጋዲ |
| 25 | NABAL & ABIGAIL; Nabal's churlishness; Abigail's gift; Nabal dies | ናባል, አቢግያ |
| 26 | David takes Saul's SPEAR & water-cruse at Hachilah (2nd sparing) | ሳኦል, ዳዊት |
| 27 | David flees to ACHISH of Gath; dwells in Ziklag; raids | ኤንካስ, ጺቅላግ |
| 28 | The witch of ENDOR; Samuel's ghost summoned; Saul's doom foretold | ኤዶር, ሰሙኤል |
| 29 | Philistine lords reject David at Aphek | ፈልስጥኤም, አፌቅ |
| 30 | ZIKLAG burned by Amalek; David pursues & recovers all; spoil-sharing law | ጺቅላግ, አማሌቅ |
| 31 | Saul & sons fall at GILBOA; bodies on Beth-shan's wall; Jabesh men rescue them | ጌልቦዔ, ሳኦል |

(2 Samuel / 1 Kings / 2 Kings anchor tables are appended at the start of their batches.)

## 7. Output contract for a mapping pass

For each CAM (or GG) side read, report a row:
`folio_side | column(L/M/R) | approx line | chapter-onset detected | Geʽez incipit words | confidence(HIGH/MED/LOW)`
plus the **penned folio number** read at zoom (confirms the view↔folio arithmetic).
Never load full masters into the controller; the pass reads + reports text only.

## 8. On-disk image availability (inventoried 2026-06-03 — decides on-disk vs IIIF)

- **GG (Gunda Gundē) = 100% ON DISK for all four books.** No acquisition ever needed.
  - 1-Samuel: `GAPS/1_Samuel/GG-00106/1-Samuel/1-Samuel_f003r…f017v.jpg` (whole book)
  - 2-Samuel: `GAPS/1_Samuel/GG-00106/2-Samuel/2-Samuel_f017v…f028v.jpg` (whole book)
  - 1-Kings:  `GAPS/2_Kings/GG-00106/1-Kings/1-Kings_f028v…f040v.jpg` (whole book)
  - 2-Kings:  `GAPS/2_Kings/GG-00106/2-Kings/2-Kings_f040v…f053r.jpg` (whole book)
- **CAM hi-res = PARTIAL on disk; rest via CUDL-IIIF** (`scripts/acquire_cudl_master.py`, anchor f106r=view215).
  - 1_Samuel dir: f106r–f113v (=views 215–230) on disk + f120r/f120v (2sa11). → 1sa 18–31 tail needs a few more (≈f114–f116).
  - 2_Kings dir: f126r–f134v on disk (early–mid 1 Kings). → 1ki ≈17–22 + ALL 2ki need IIIF.
  - 2 Samuel CAM (≈f114–f125): only f120 on disk → most of 2sa needs IIIF.

## 9. Unique-event anchor table — 2 Samuel (24 ch)

| ch | UNIQUE onset / characterizing event |
|----|--------------------------------------|
| 1  | Amalekite reports Saul's death; David's LAMENT "how are the mighty fallen" (Song of the Bow) |
| 2  | David anointed king at HEBRON; Abner vs Joab; Asahel slain at the Gibeon pool |
| 3  | Abner defects to David then slain by Joab; David mourns Abner |
| 4  | Ish-bosheth murdered by Rechab & Baanah; David executes them |
| 5  | David king over ALL Israel; takes JERUSALEM/Zion; Baal-perazim |
| 6  | ARK to Jerusalem; UZZAH struck dead; David dances; Michal despises him |
| 7  | NATHAN's oracle / the Davidic COVENANT ("I will build thee a house"); David's prayer |
| 8  | David's war-victories summary (Moab, Zobah/Hadadezer, Edom) |
| 9  | MEPHIBOSHETH (Jonathan's lame son) eats at the king's table |
| 10 | Ammonites SHAVE the envoys' beards; war with Ammon & Syria |
| 11 | David & BATHSHEBA; URIAH the Hittite sent to die |
| 12 | Nathan's parable "THOU ART THE MAN"; the child dies; Solomon born; Rabbah taken |
| 13 | AMNON rapes TAMAR; Absalom kills Amnon |
| 14 | Joab & the wise woman of TEKOA; Absalom recalled |
| 15 | ABSALOM's REVOLT; David flees; Zadok/Abiathar; Hushai |
| 16 | Ziba; SHIMEI curses & throws stones; Absalom & the concubines on the roof |
| 17 | AHITHOPHEL's counsel vs Hushai's; Ahithophel HANGS himself |
| 18 | Battle in the wood of Ephraim; ABSALOM caught by his hair, slain; "O Absalom my son" |
| 19 | David's return; Shimei pardoned; Mephibosheth; BARZILLAI |
| 20 | SHEBA's revolt ("no part in David"); the wise woman of ABEL; Sheba beheaded |
| 21 | The Gibeonites; Saul's seven sons HANGED; RIZPAH guards the bodies; Philistine giants |
| 22 | David's SONG "The LORD is my rock" (= Psalm 18) |
| 23 | David's LAST WORDS; the MIGHTY MEN (the Three/Thirty); the water of Bethlehem |
| 24 | David's CENSUS; the plague; the threshing-floor of ARAUNAH; the altar |

## 10. Unique-event anchor table — 1 Kings (22 ch; 1–6 already calibrated)

| ch | UNIQUE onset / characterizing event |
|----|--------------------------------------|
| 7  | Solomon's PALACE; Hiram the bronze-caster; pillars JACHIN & BOAZ; the molten SEA |
| 8  | Ark into the temple; Solomon's DEDICATION prayer; the cloud/glory fills the house |
| 9  | The LORD appears a 2nd time; Hiram's twenty cities; the navy at Ezion-geber |
| 10 | The Queen of SHEBA; Solomon's gold, ivory throne, riches |
| 11 | Solomon's foreign WIVES & idolatry; Hadad & Rezon; AHIJAH tears the garment (Jeroboam) |
| 12 | Rehoboam's folly ("my little finger"); the kingdom DIVIDES; Jeroboam's golden CALVES |
| 13 | The man of God vs Jeroboam's altar; the withered hand; the lying prophet; the LION |
| 14 | Ahijah & Jeroboam's sick child; Shishak plunders; Rehoboam dies |
| 15 | Abijam & ASA of Judah; Nadab & BAASHA of Israel |
| 16 | Baasha/Elah/Zimri/Omri; AHAB begins to reign; Jericho rebuilt (Hiel) |
| 17 | ELIJAH; the DROUGHT; the RAVENS; the widow of ZAREPHATH; her son raised |
| 18 | Elijah vs Baal's prophets on CARMEL; FIRE from heaven; the rain returns |
| 19 | Elijah at HOREB; the STILL SMALL VOICE; ELISHA called from the plough |
| 20 | BEN-HADAD besieges Samaria; Ahab's two victories; the prophet condemns Ahab |
| 21 | NABOTH's VINEYARD; Jezebel's plot; Elijah's doom ("dogs shall lick thy blood") |
| 22 | MICAIAH prophesies; Ahab disguised, slain by a random ARROW at Ramoth-gilead |

## 11. Unique-event anchor table — 2 Kings (25 ch; none started)

| ch | UNIQUE onset / characterizing event |
|----|--------------------------------------|
| 1  | Ahaziah & BAAL-ZEBUB; Elijah calls FIRE on the fifties |
| 2  | Elijah's WHIRLWIND ascent; the mantle; Jordan parted; the SHE-BEARS & the youths |
| 3  | Jehoram + Jehoshaphat + Edom vs MOAB; the ditches of water/blood; Mesha sacrifices his son |
| 4  | The widow's OIL; the SHUNAMMITE's son raised; death in the POT; bread multiplied |
| 5  | NAAMAN the leper healed in Jordan; GEHAZI's greed & leprosy |
| 6  | The floating AXE-HEAD; the blinded Syrian army; the famine/siege of Samaria |
| 7  | The four LEPERS at the gate; the Syrians flee; plenty; the trampled lord |
| 8  | The Shunammite's land restored; HAZAEL smothers Ben-hadad; Jehoram & Ahaziah of Judah |
| 9  | JEHU anointed; slays Joram & Ahaziah; JEZEBEL thrown down, eaten by dogs |
| 10 | Jehu beheads Ahab's SEVENTY sons; the Baal-worshippers massacred |
| 11 | ATHALIAH usurps; Joash hidden; Jehoiada's coup; Athaliah slain |
| 12 | JOASH repairs the temple; the money CHEST; Hazael bought off |
| 13 | Jehoahaz/Jehoash; ELISHA dies; the ARROWS; the corpse revived by Elisha's bones |
| 14 | AMAZIAH of Judah vs Jehoash; Jeroboam II restores the border |
| 15 | Azariah/Uzziah struck with LEPROSY; the rapid northern succession; Jotham |
| 16 | AHAZ; the Damascus ALTAR copied; Tiglath-pileser |
| 17 | SAMARIA FALLS; Israel EXILED to Assyria; the foreign resettlement & syncretism |
| 18 | HEZEKIAH; Sennacherib invades; RABSHAKEH's taunt at the wall |
| 19 | Isaiah; the ANGEL slays 185,000; Sennacherib murdered by his sons |
| 20 | Hezekiah's sickness; the SUNDIAL sign; the Babylonian envoys |
| 21 | MANASSEH's idolatry & innocent blood; Amon |
| 22 | JOSIAH; the BOOK OF THE LAW found; HULDAH the prophetess |
| 23 | Josiah's REFORMS & Passover; slain at Megiddo; Jehoahaz & Jehoiakim |
| 24 | Nebuchadnezzar; JEHOIACHIN exiled; Zedekiah set up |
| 25 | JERUSALEM FALLS; the temple BURNED; the exile; Gedaliah; Jehoiachin freed |

## 12. CONFIRMED RESULTS — CAM 1 Samuel onset map (keystone pass, 2026-06-03, HIGH confidence)

Penned folio numbers read directly at 4× confirmed the view↔folio arithmetic:
view221=f109r=**109**, 223=f110r=**110**, 225=f111r=**111**, 227=f112r=**112**.

**★ CORRECTION to the on-disk filename labels — they are shifted ~+3 chapters from
reality.** The folio numbers in the filenames are CORRECT (penned-verified); the
`_1SamN_` chapter suffixes are the prior session's WRONG guesses. Map chapters to the
right FOLIO; ignore the cosmetic suffix. (Do NOT rename files — folios are right;
renaming would break manifest paths. Optional later cleanup: re-suffix the files.)

**Verified per-chapter CAM folios (onset → spanning):**

| ch | CAM folios | onset detail |
|----|-----------|--------------|
| 7  | f108r | f108r-L top (7:3 put-away-Baalim; 7:5 Mizpah; 7:12 Ebenezer). 7:1-2 straddles the f107v→f108r turn; **f107v-R ends at 6:14** |
| 8  | f108r | f108r-M (Samuel's sons; "give us a king" 8:6) |
| 9  | f108r, f108v | f108r-R (Kish+Saul genealogy 9:1-2; donkeys → f108v-L) |
| 10 | f108v, f109r | onset in the compressed 9:26-10:8 span at the f108v-R/f109r-L turn; body (Saul among the prophets) firmly f109r-L |
| 11 | f109r | f109r-M (Nahash; Jabesh-Gilead; right-eye threat 11:1-2) |
| 12 | f109r, f109v | f109r-R (Samuel's farewell 12:1-3) → body f109v-L,M |
| 13 | f109v, f110r | f109v-M bottom (reign formula 13:1; Michmash 13:2) → f110r-L top |
| 14 | f110r, f110v | f110r-L lower (Jonathan + armour-bearer 14:1; honey 14:25 f110r-R) → f110v-L |
| 15 | f110v, f111r | f110v-M (Amalek/Agag 15:1-3; "obey>sacrifice"; Saul rejected) → f111r-L |
| 16 | f111r | f111r-M (David/Jesse/horn-of-oil 16:1; harp 16:23 f111r-R) |
| 17 | f111r, f111v, f112r | f111r-R bottom onset (17:1 Soko/Azekah); Goliath 17:4 at f111v-L top (calibrated — folios CONFIRMED) |

CAM file paths on disk (folio → file; cosmetic suffix may mislabel the chapter):
f108r=`MS-ADD-01570_f108r_1Sam5_hires.jpg` · f108v=`..._f108v_1Sam6_hires.jpg` ·
f109r=`..._f109r_1Sam7_hires.jpg` · f109v=`..._f109v_1Sam8_hires.jpg` ·
f110r=`..._f110r_1Sam9_hires.jpg` · f110v=`..._f110v_1Sam10_hires.jpg` ·
f111r=`..._f111r_1Sam17_hires.jpg` · f111v=`..._f111v_1Sam17_hires.jpg` ·
f112r=`..._f112r_1Sam17_hires.jpg`.

**STILL PENDING (companion passes before the manifest is filled consistently):**
- **GG side for 1sa 2–16** — the prior GG entries for 7–11 are PROVISIONAL/suspect and
  8–16 unverified; needs a GG unique-event onset pass (GG on disk f003–f012). GG is
  LXX-compressed (~1 ch/side here), so expect ~1 onset/side.
- **CAM 1sa 1–6 re-verify** — the prior 4–6 CAM entries are shifted late (ch6 really
  ends f107v-R, not f108v); ch2 CAM is empty. Needs a small CAM pass on f106r–f108r.
- Only after BOTH witnesses are verified for the whole 1sa 1–17 range do we rewrite the
  manifest in one consistent edit (avoids a contradictory half-state).

## 13. CONFIRMED RESULTS — GG 1 Samuel onset map (companion pass, 2026-06-03, HIGH conf.)

GG runs ~1 chapter/side here (3 columns L→M→R). Cross-check vs §12 CAM: **order matches,
no transposition** (GG 2→3→…→17 strictly canonical). Files:
`GAPS/1_Samuel/GG-00106/1-Samuel/1-Samuel_f###[rv].jpg`.

| ch | GG folios | onset detail |
|----|-----------|--------------|
| 2  | f003r, f003v, f004r | f003r-R (Hannah's song "my horn is exalted"); shares leaf with ch1 |
| 4  | f004r, f004v | f004r-R (Eben-ezer vs Aphek; ark/Eli/Ichabod) |
| 5  | f004v, f005r | f004v-M (ark to Ashdod; Dagon fallen `ቤተ ዳጎን`) |
| 6  | f005r, f005v | f005r-L (ark in field 7 months; cart; Beth-shemesh) |
| 7  | f005v | f005v-L (Kirjath-jearim fetch the ark to Abinadab `ቤተ አሚናዳብ`) — tightest, ~1 side |
| 8  | f005v, f006r | f005v-R (Samuel's sons at Beersheba; demand a king) |
| 9  | f006r, f006v | f006r-M (Kish `ቂስ` genealogy; donkeys) |
| 10 | f006v, f007r | f006v-M bottom (horn-of-oil anointing `ቀርነ ቅብዕ`) |
| 11 | f007r, f007v | f007r-M→R (Nahash `ናአስ`; Jabesh-Gilead `ኢያቤስ ዘገለዓድ`) |
| 12 | f007v, f008r | f007v-L (Samuel's farewell "ye asked a king") |
| 13 | f008r, f008v | f008r-L (reign formula; Michmash `ማኬማስ`) |
| 14 | f008v, f009r, f009v | f008v-L (Jonathan to the garrison `ማዕደተ ማኬማስ`); long ch (52 v) → tail spills f009v-top (boundary-generous) |
| 15 | f009v, f010r | f009v-L (Amalek/Agag commission) |
| 16 | f010r, f010v | f010r-M (horn-of-oil → Jesse `እሴይ`/Bethlehem; harp `መሰንቆ` 16:23 on f010v-L) |

GG anchors (not re-mapped, verified incidentally): ch1=f003r · ch3=f004r-L · ch17=f010v-L
(onset 17:1 `ሰኩት ዘይሁዳ … አዜታ`) → f011r → f011v.

**STATUS:** 1sa 1–17 verified (CAM §12 + GG §13 + the CAM 1–6 re-verify) → manifest
filled & committed (`8b6cb947`). 1sa 18–31 added below (§14). **1 Samuel is COMPLETE
(1–31, both witnesses).** Next P0 batch = 2 Samuel.

## 14. CONFIRMED RESULTS — 1 Samuel 18–31, BOTH witnesses (2026-06-03, HIGH confidence)

Two cross-checked passes (GG 18–31 + CAM 18–31); orders strictly canonical, matching.
★Recension: **GG (LXX) omits 18:1–5** (ch18 opens at the women's song 18:6) and runs
~2 ch/side; **CAM (MT-fuller) ch18 opens at 18:1 (the covenant)**. **1 Samuel ENDS**
mid-folio (GG f017v-M / CAM f117r-L) with a red book-divider; **2 Samuel 1 begins
immediately after** (GG f017v / CAM f117r-M) — same continuous-folio behavior both
witnesses. CAM penned folio numbers 113–117 confirmed (view231=f114r…238=f117v).
CAM f112v/f113r/f113v = the on-disk `view228/229/230` files; f114r–f117r folio-named.

| ch | CAM folios | GG folios |
|----|-----------|-----------|
| 18 | f112r, f112v | f011v |
| 19 | f112v | f011v, f012r |
| 20 | f112v, f113r | f012r, f012v |
| 21 | f113r, f113v | f012v, f013r |
| 22 | f113v | f013r, f013v |
| 23 | f114r | f013v, f014r |
| 24 | f114r, f114v | f014r, f014v |
| 25 | f114v, f115r | f014v, f015r |
| 26 | f115r, f115v | f015r, f015v |
| 27 | f115v | f016r |
| 28 | f115v, f116r | f016r, f016v |
| 29 | f116r | f016v |
| 30 | f116v | f017r, f017v |
| 31 | f116v, f117r | f017v |

(Boundary-generous lists; status `pending`. Filled into the manifest this session.)

## 15. CONFIRMED RESULTS — 2 Samuel 1–12, BOTH witnesses (2026-06-03, batch 1)

★**Method upgrade this batch — column-tile crops.** Whole-folio `Read`s downsample a
7760px CAM master / 2081px GG side so far that individual fidels are illegible (the
first GG pass could only read rubric blocks, not names). The new reusable
`scripts/manuscript_folio_crop.py` splits a folio into native-resolution column×row
tiles (≤1568px each) which a vision agent `Read`s — restoring glyph-level legibility.
Result: **CAM (base, 7760px) reads incipits + names at HIGH confidence**; **GG (2081px,
~694px native column) is capped at rubric+order** (names not certifiable even cropped).
This is exactly the §2 mutual-confirmation design: CAM supplies the names, GG
cross-checks the order — both witnesses strictly canonical 1→12, no transposition.

CAM penned folio numbers read at zoom: f117=፻፲፯, f118=፻፲፰, f119=፻፲፱, f120=፻፳, with
per-column ምዕ chapter-number headers independently corroborating. 1 Samuel ends f117r-L;
2 Samuel 1 begins f117r-M. CAM is tightly compressed (all of ch7–12 sit within
f119r–f120v); GG runs ~1 chapter per column-side.

| ch | CAM folios | CAM onset | GG folios | GG onset |
|----|-----------|-----------|-----------|----------|
| 1  | f117r, f117v | f117r-M (Amalekite reports Saul's death; lament) | f017v, f018r | f017v-R |
| 2  | f117v        | f117v-L (Hebron; Abner/Joab; Gibeon pool)        | f018r, f018v | f018r-M |
| 3  | f117v, f118r | f117v-R (Abner defects then slain; David mourns) | f018v        | f018v-M |
| 4  | f118r        | f118r-M (Ish-bosheth murdered; Rechab & Baanah)  | f018v, f019r | f018v-R/f019r-L |
| 5  | f118r, f118v | f118r-R (king over Israel; Jerusalem/Zion)       | f019r, f019v | f019r-R |
| 6  | f118v, f119r | f118v-M (ark; Uzzah struck; Michal)              | f019v, f020r | f019v-M |
| 7  | f119r, f119v | f119r-L (Nathan's covenant oracle)               | f020r, f020v | f020r-L |
| 8  | f119v        | f119v-L (war-victories: Moab/Zobah/Edom)         | f020v, f021r | f020v-M |
| 9  | f119v        | f119v-M→R (Mephibosheth at the table; Ziba)      | f021r        | f021r-L |
| 10 | f119v, f120r | f119v-R (Ammon shames the envoys; Ammon+Syria)   | f021r, f021v | f021r-M/R |
| 11 | f120r, f120v | f120r-M (Bathsheba; Uriah) — **calibrated**      | f021v, f022r | f021v-M — **calibrated** |
| 12 | f120r, f120v | f120r-R→f120v (parable "thou art the man"; Solomon; Rabbah) | f022v, f023r | f022v-L |

**2 Samuel 13 (Amnon & Tamar) seam:** CAM **f120v-R (top)** (incipit `ወእምድኅረዝ … አቤሴሎም
… ትዕማር … አምኖን`); GG **f023r mid-column** (spaced/ruled section break). **Next batch =
2sa 13–24** (CAM acquired through f125; GG on disk f023r–f028v). Both witnesses'
boundary-generous folio lists filled in `samuel/manifest.yaml` (status `pending`; ch11
left `calibrated`). Gate: image-existence GREEN; samuel has-folios pending 23→12
(remaining = 2sa 13–24).

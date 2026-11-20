# Deltarune RePainted – sprite-sheet → data.win tools

Takes recoloured TSR-style sprite sheets (native 1x scale) and writes the pixels back into a
Deltarune `data.win`, **in place** (same file size, nothing but texture bytes changes).
Built and tested on the Chapter 1 `data.win` (GameMaker 2.x, BZ2+QOI textures). Not tested in-game by the author,
so always test on a copy.

Needs: Python 3.10+, `numpy`, `Pillow`. (bz2 is in the standard library.)

## How it works
1. Textures are `2zoq` blobs = header + bz2( `fioq` stream ). `fioq` is the **original 2021 QOI** (RUN_8/RUN_16,
   DIFF_8/16/24, COLOR ops, hash = r^g^b^a, all deltas signed two's complement). `dw.py` has the codec,
   the chunk/TXTR/SPRT/TPAG parsers.
2. Every game sprite frame (its TPAG region on a texture page) is searched for in the sheet by **exact silhouette**
   (alpha>0 mask), then scored by **colour-structure** (pixels that shared a colour in the game must share one in
   your recolour, and vice-versa). That tells recolour variants apart (eyes/unhappy/party etc.).
3. Matches with score >= 0.99 whose tied candidates are pixel-identical are pasted onto the page.
   Ambiguous, low-confidence and flat (<=2 colour, would-change) regions are skipped and listed in the reports.
4. Changed pages are re-encoded (best of several encoder variants) and **repacked inside the TXTR chunk**
   (64-byte aligned) so the file size and everything after the textures stay identical.

## Run it
Put your sheets next to the scripts as `sheet_<tag>.png` (e.g. `sheet_susie.png`). All commands run from this folder.

```
export DATAWIN=/path/to/original/data.win
python3 extract_pages.py                         # -> pages/pN.npy  (about 1 min)

# for each sheet (tag = susie, kris, ...):
SHEET=$PWD/sheet_susie.png TAG=susie python3 runmatch.py   # silhouette search -> match_susie.pkl
SHEET=$PWD/sheet_susie.png TAG=susie python3 toomany.py    # resolves simple/large shapes -> match2_susie.pkl

python3 select3.py                               # merges all sheets -> pages/newN.npy + match_report_<tag>.csv
OUT=rebuilt_data.win python3 build2.py           # re-encode + repack in place
python3 verify_and_patch.py rebuilt_data.win Deltarune_RePainted.ips
```
`runmatch.py` takes about 2-3 minutes per sheet. The first stage (and `toomany.py`) can run for several sheets in parallel.

### Editing `select3.py` for other chapters / sheets
- `TAGS` = order sheets are processed; `KEYS` maps a tag to substrings of game sprite names it "owns"
  (e.g. `'jevil': ('joker','jevil')`). A sprite's own character sheet wins; otherwise the earlier tag wins and
  the clash is logged as `skipped-conflicts-with-<tag>-sheet`.
- Sheets for a different chapter will simply produce no matches against this chapter's `data.win` – run them
  against *that* chapter's `data.win` (new `extract_pages.py` run in a fresh folder).
- Threshold `THR = 0.99` is the structure score cut-off. Lower it only if you've changed colour *structure*
  (merged shades etc.) and review the reports.

## Reports (`match_report_<tag>.csv`)
`applied`, `skipped-low-confidence`, `skipped-ambiguous`, `skipped-conflicts-with-X-sheet`,
`skipped-low-information(<=2 colours, would change)`. Columns: game sprite frames using the region, texture page,
region x/y/w/h, sheet x/y, structure score.

## Replacing a whole image (not a recolour)
Things like `spr_carouselbg` (700x300) can be replaced by writing your image straight into `pages/newN.npy`
at the sprite's TPAG region before `build2.py`:
`P = np.load('pages/new3.npy'); P[1650:1950, 666:1366] = your_700x300_rgba; np.save('pages/new3.npy', P)`
(find the page/region from `parse_sprites()` in `dw.py`).

## Limits
- Visuals drawn by game code (e.g. the Jevil fight's moving triangles) are not textures – not covered.
- Needs native 1x sheets. Sheets that change silhouettes (new outlines/glows) won't match those frames.
- IPS is used for the patch (file < 16 MB). xdelta isn't generated.
- Page blobs must repack within the TXTR chunk; `build2.py` asserts if they don't.

# Final Release V3

## STATUS

PASS

## Online Page

https://conanxin.github.io/hitchhikers-guide-agentic-ai-zh/

## Latest Commit

Final release commit is the commit tagged by `v3.0.0`.

V3 rebuild baseline commit:

`c3bd1e244a28ca6fbc116138cb2bbc6c9a974a8c`

## Workflow URL

https://github.com/conanxin/hitchhikers-guide-agentic-ai-zh/actions/runs/28489155734

## V3 Fix Summary

- Rebuilt the site around `assets/data/clean_chapter_tree.json` as the canonical content AST.
- Removed PDF page numbers from rendered DOM and kept them as metadata only.
- Rebuilt semantic TOC and chapter pages from clean AST.
- Added Key Concepts panels and Section Overview cards.
- Added AST-based search.
- Added glossary and term normalization.
- Repaired English residuals, OCR noise, and formula fallback.
- Verified GitHub Pages deployment.

## Known Remaining Notes

- Reference titles may remain in English when they are bibliographic titles.
- Standard technical abbreviations and model/protocol names remain in English where appropriate.
- Some OCR-sensitive formulas are represented through readable fallback rather than exact source typesetting.

## Optional Future Directions

- Extract the V3 pipeline into a reusable PDF-to-Knowledge-Site engine.
- Add full-text offline search scoring and filters.
- Add bilingual paragraph toggles.
- Add automated visual regression screenshots for Pages deployments.

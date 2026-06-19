# External materials

This directory is the controlled source of truth for external communications.

Only approved markdown sources with claim-tier front matter should live here. Exported decks, PDFs, DOCX files, email templates, or HTML files must have a same-stem approved markdown source and must pass:

```bash
npm run review:claim-tiers
python scripts/check_commercialization_gates.py
```

The claim-tier guard intentionally ignores this README and files whose names begin with `_` so protocol notes can exist without being treated as distributable claims.

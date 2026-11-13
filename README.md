# julia here. Ink Library

Public, filterable library of Julia's fountain pen inks, served at https://ink.juliahere.com via GitHub Pages.

- `index.html` – the page; ink data lives in the `<script id="ink-data">` block.
- `swatches/b-*.json` – swatch photo bundles (keyed by Notion page id); `swatches/manifest.json` maps each ink page to its Notion image.
- `tools/` – scripts used by the weekly refresh (Notion → data + new swatches).

Updated automatically every Sunday from Notion.

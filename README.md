# Earn Extra Online — Real, Boring Systems

Honest, hype-free affiliate marketing site. International audience.
ClickBank + direct affiliate programs.

## Structure

```
earn-online/
├── index.html        — Home page
├── review.html       — Affiliate offer reviews (comparison + verdicts)
├── guide.html        — Free traffic guide (SEO, YouTube, Pinterest, forums)
├── contract.md       — Design & tone contract
├── assets/
│   └── styles.css    — Dark/muted theme
└── .gitignore
```

## Design Contract

See `contract.md`. Key rules:
- Dark/dimmed UI theme — no bright colours
- No country flags — international audience
- No flag emoji in text — use 💪 for buttons/footer accents
- Tone: blunt, direct, honest, international
- No weasel wording ("some"/"most"/"fewer than X")
- Use "freedom" not "democracy"
- Never invent numbers — if untested, say so

## Current State

- **Niche locked:** "Earn Extra Online — Real, Boring Systems"
- **Listings:** 1 (YU SLEEP — Health/Fitness, Sleep)
  - $140.25 initial, ~$0 future, ~$5 EPC, Approval Required
- **review.html:** Has YU SLEEP review built. Needs 2–3 more offers to do a real comparison.
- **Traffic guide:** Complete (SEO, YouTube, Pinterest, forums)
- **GitHub:** Repo owner `fezbizz`. Not yet pushed.

## Next Step

User pastes 3–5 complete ClickBank Marketplace listings. Then:
1. Honest comparison of all offers
2. Pick the 2–3 strongest
3. Rewrite review.html with real affiliate links
4. Structure the site to rank for that category's search terms

## GitHub Pages

To push live:
```bash
cd earn-online
git remote add origin https://github.com/fezbizz/earn-online.git
git add -A
git commit -m "Initial site: home, reviews, guide"
git push -u origin main
```
Then enable GitHub Pages in repo settings → Pages → Source: main branch.
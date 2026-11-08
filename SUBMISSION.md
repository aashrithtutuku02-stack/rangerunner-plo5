# PokerKing submission package

Team/project name: **PokerKing**

Public repository: https://github.com/aashrithtutuku02-stack/rangerunner-plo5

Commit: use the full SHA of the commit containing this document; the submission handoff includes it. The tournament entrypoint remains `python agent.py`.

## Elevator pitch (under 200 characters)

An adaptive short-deck PLO5 poker bot combining fast equity simulation, Bayesian opponent reads, and risk-aware betting under strict tournament time limits.

## Devpost project story

## Inspiration
PokerKing explores decision-making with incomplete information. We wanted an agent that could learn from public betting behavior while working within strict compute limits.

## What it does
PokerKing plays heads-up, 36-card, five-card Pot-Limit Omaha. It estimates equity, models opponent ranges, and compares the expected chip values of folding, calling, and the available raise sizes. A conservative caller read helps it extract more value from opponents who repeatedly call bets.

## How we built it
We built on the official TAMU Datathon starter bundle and preserved its game rules and HTTP protocol. The bot uses Python, FastAPI, and Uvicorn; NumPy and Numba handle numerical calculations, and a portable C engine accelerates card scoring and simulation. Precomputed starting-hand equities load at startup. Docker packages the CPU-only bot for the tournament environment.

All gameplay uses local computation. Opponent reads use public actions and legitimately revealed showdown cards, with learned state reset every half.

## Challenges we ran into
The main challenges were implementing the short-deck ranking and exact two-hole/three-board rule, handling forced calls without learning false preferences, and keeping inference within the startup and per-half time limits. We also had to separate genuine strategic gains from card luck using common-deal, seat-swapped comparisons.

## Accomplishments
The project passed 317 automated tests during development. Prior full-history validation covered 408,608 terminal betting histories across eight fixed deals and both button positions. The validated caller-read policy improved the tested 24-opponent local pool by 0.187 big blinds per duplicate deal across four fresh seeds. This is a finite local benchmark result, not a claim of unbeatable play.

## What we learned
More aggressive play does not automatically improve results. We tested additional bluffing policies, but their fresh results did not establish a reliable gain, so they remain opt-in experiments. Reproducible benchmarks, lifecycle safety, and runtime accounting were as important as the betting policy.

## What's next
We plan to test a broader set of independent opponents and improve context-sensitive opponent reads and future-betting estimates before promoting further strategy changes.

## AI assistance and attribution
OpenAI Codex/ChatGPT assisted development, debugging, and test automation. No generative AI API is called during gameplay. The project builds on the official TAMU Datathon starter bundle, credited in the repository.

## Built with

Python, C, NumPy, Numba, FastAPI, Uvicorn, Docker, GitHub Actions.

## Other form fields

- Try it out: the public GitHub repository URL above.
- Source upload: download the ZIP for the submitted commit from GitHub, if an upload is desired.
- Schools: enter the actual university/school of every team member.
- AI tools used: OpenAI Codex / ChatGPT; add any other tools the team actually used.
- Implemented generative AI model/API: N/A in the running bot. Codex/ChatGPT assisted development; gameplay uses local numerical methods.
- Gemini Project Number: N/A; no Gemini API integration is present.
- Domains: leave blank or use N/A if none were registered.
- Gallery/video: add actual media if available; do not invent a demo URL.
- Sponsor prizes: choose only categories for which the project is eligible.

## Optional technology feedback

GitHub Actions helped us reproduce tests, HTTP matches, and container checks on specific commits. Docker made the constrained runtime reproducible, and NumPy/Numba plus a native C engine made equity calculations practical within the time bank.

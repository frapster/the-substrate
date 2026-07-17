# the-substrate: Project Authority

This repo is the **public thesis showcase**: "AI as the governed operational substrate." It is
recruiter/employer-facing and read by technical evaluators. Do not port architecture assumptions
from sibling `Local Sites/` projects.

## Purpose

- Present the thesis (governed run-time reasoning replacing deterministic code where appropriate)
  and case studies (Relic Wars, Today Series, Zabble, Eikon Digital, …) as per-project **before → after**
  transformations framed on the **AI : code ratio** (LLM-First target 90:10). Cross-cutting engineering
  threads (TCO, LLM-code quality/security, 3rd-party-harness governance, drift) live in `ENGINEERING.md`.
- Profile **BOSNet.io** as the named governance standard, without exposing its source or any client IP.

## Hard rules

- **IP safety before every push.** No client IP, no proprietary BOSNet.io source, no secrets. When in
  doubt, leave it out. Only Rob's own thesis, public-safe architecture, and de-identified capability
  signal belong here.
- **Public repo.** Assume everything here is world-readable and permanent.
- **Proprietary reservations stand.** BOSNet.io and BOSS are proprietary (see `LICENSE.md`);
  never imply an open-source grant of them.
- **Evidence-backed claims.** Prefer verifiable, demonstrated statements over marketing.

## Relationship to the engine

The private job-hunt engine (dimensional twin, matching, tailoring, curation) lives in
`Local Sites/robfloyd` and is **never** published here. This repo receives only curated,
IP-reviewed thesis + case-study content.

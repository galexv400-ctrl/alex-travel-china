# CLAUDE.md

This file provides guidance to Claude Code when working in this personal repository.

## About

This is Alexandra Segall's personal repository — separate from professional ESG consulting work.

Two areas:
1. **Travel** — trip planning, itineraries, visa research, practical travel advice
2. **Health** — personal health tracking, blood test analysis, medical notes

## Repository Structure

travel/<trip-name>/        # itineraries, notes, visa docs per trip
health/                    # blood test results, health notes, summaries
.claude/agents/            # specialist agents

## User Context

- Name: Alexandra Segall
- Based in Israel, native English speaker
- Dual citizen: Israeli + UK passport
- Does not speak Chinese

## Subagents

| Agent | When to use |
|---|---|
| china-travel-advisor | China & Hong Kong travel — visas, trip extensions, payments, apps, connectivity |
| health-advisor | Blood test analysis, interpreting results, tracking trends, health questions |

## Language

Always respond in English unless told otherwise.

## Trip files — accuracy rules (China & Bangkok 2026)

The website renders `travel/china-2026/*.md` directly — those files are what Alexandra reads on her phone while travelling, often offline. Wrong information there is dangerous.

- **Every confirmed fact lives once, in `tools/check_trip.py`** (times, booking refs, decisions, cancelled items).
- **When a fact changes, update `tools/check_trip.py` FIRST**, then run `python3 tools/check_trip.py` — it lists every line still holding the old value. Fix all of them.
- **Run the checker before every commit** touching trip files. Never commit while it fails. CI runs it on every PR.
- Files state the **final position only** — no decision history, no "replaced X because…", no reasoning asides.
- A QA pass means **reading every file in full** against the facts, not searching for known problems.

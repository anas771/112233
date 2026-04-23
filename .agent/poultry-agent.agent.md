---
name: poultry-agent
description: "Use when: fixing bugs, creating reports, and managing the poultry system project."
---

You are an expert AI programming assistant specialized in the poultry management system project.

Follow the behavioral guidelines from AGENTS.md and CLAUDE.md to reduce common LLM coding mistakes.

Project-specific instructions:
- Database: poultry_data.db — SQLite with WAL mode enabled to prevent conflicts between the app and web interface
- Main application: main.py — Python + ttkbootstrap
- Web interface: web/app.py — Flask + /web/templates/ + /web/static/
- Both interfaces share the same database without conflicts thanks to WAL mode
- Required libraries: pip install -r requirements.txt

Apply the guidelines: Think before coding, simplicity first, surgical changes, goal-driven execution.
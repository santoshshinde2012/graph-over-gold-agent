# Security

This project is a small, self-contained demo: it ships synthetic data, runs entirely locally against
SQLite, makes no network calls, and stores no secrets or credentials. The Databricks notebook in
`notebooks/` uses placeholder catalog/schema names only.

If you believe you have found a security issue (for example in a dependency or in how the package
handles file paths), please **do not open a public issue**. Use GitHub's private vulnerability
reporting on this repository ("Security" tab → "Report a vulnerability"), or contact the maintainer
through the GitHub profile. You will get an acknowledgement within a few days.

Dependencies are kept current by Dependabot (`.github/dependabot.yml`); CI pins nothing beyond the
lower bounds in `pyproject.toml`, and `requirements.txt` carries a known-good pin for local runs.

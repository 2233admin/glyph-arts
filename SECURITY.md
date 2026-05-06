# Security Policy

## Supported versions

| Version | Supported |
|---------|-----------|
| 3.x     | yes (latest) |
| < 3.0   | no |

## Reporting a vulnerability

Please **do not open a public GitHub issue** for security-related bugs.

Use GitHub's [Private Vulnerability Reporting](https://github.com/2233admin/glyph-arts/security/advisories/new)
to send a private report. We aim to acknowledge within 7 days and ship
a fix or mitigation in the next minor release.

## Scope

glyph-arts shells out to `chafa` and `ffmpeg` for the `image` / `video`
chart types. Vulnerabilities in those binaries are out of scope here --
report upstream.

In-scope concerns include:

- Code injection via JSON / DuckDB SQL inputs
- Path traversal via `--file` / `--db` arguments
- Subprocess argument injection
- Resource exhaustion via crafted input data

## Out of scope

- Issues that require local machine access
- Issues in third-party packages (`plotext`, `rich`, etc.) -- report
  upstream
- "Best practice" lints without a concrete exploit path

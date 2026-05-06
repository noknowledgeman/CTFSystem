# Path Traversal Intranet - Writeup

## Summary
The challenge exposes a `page` query parameter that is vulnerable to path traversal.

## Reproduction
1. Browse `/` and discover that `/?page=home.html` loads page content.
2. Request `/?page=../db-config.js` to discover backend hints.
3. Request `/?page=../flag.txt` to retrieve the flag.

## Remediation
- Normalize and whitelist allowed page names.
- Remove direct filesystem reads based on user input.
- Store sensitive files outside the web root.

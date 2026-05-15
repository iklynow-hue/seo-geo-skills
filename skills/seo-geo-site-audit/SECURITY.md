# Security Notes

This repository is intended to be safe for public publishing.

## Secrets

- Do not hardcode API keys, tokens, passwords, or other credentials.
- Do not commit `.env` files or shell history exports.
- Do not add real customer data, analytics exports, or private URLs to examples or fixtures.

## Third-party services

This skill does not require any third-party API key. Performance evidence is collected by running Lighthouse locally through `scripts/run_lighthouse.mjs` (which uses the `lighthouse` and `chrome-launcher` npm packages). All evidence stays on the user's machine.

If you ever extend the skill to call an external API, make sure that:

- credentials never land in tracked files, generated artifacts, manifests, or HTML output
- code only persists `<service>_used: true/false` flags, never the credential itself

## Public repo guidance

Before publishing:

- search the repo for accidental keys or tokens
- confirm sample outputs do not contain secrets
- confirm generated artifacts are excluded or sanitized

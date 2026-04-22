# Security Notes

This repository is intended to be safe for public publishing.

## Secrets

- Do not hardcode PageSpeed API keys, tokens, passwords, or other credentials.
- Do not commit `.env` files or shell history exports.
- Do not add real customer data, analytics exports, or private URLs to examples or fixtures.

## PageSpeed API keys

Supported runtime sources:

- the skill-local `.env` file in this directory
- `PAGESPEED_API_KEY`
- `GOOGLE_API_KEY`

Unsupported storage locations:

- source files
- markdown docs
- sample commands with real values
- JSON artifacts
- HTML reports
- manifests

The code should only persist `api_key_used: true/false`, never the key itself.

## Public repo guidance

Before publishing:

- search the repo for accidental keys or tokens
- confirm sample outputs do not contain secrets
- confirm generated artifacts are excluded or sanitized

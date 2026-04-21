#!/usr/bin/env python3
"""Unified fetcher with prerequisite detection and auto-install.

Fetcher priority chain:
  1. Scrapling StealthyFetcher (Camoufox, JS-rendered) — primary
  2. Lightpanda (headless CDP browser, fast) — secondary
  3. agent-browser (Playwright-based) — tertiary
  4. urllib.request (raw HTTP, no JS) — fallback
"""
from __future__ import annotations

import gzip
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

LIGHTPANDA_DIR = Path.home() / ".local" / "bin"
LIGHTPANDA_BIN = LIGHTPANDA_DIR / "lightpanda"
LIGHTPANDA_CDP_PORT = 19222
DEFAULT_UA = "seo-geo-site-audit/1.0 (+https://example.invalid)"
MAX_BODY_CHARS = 250_000
FETCH_TIMEOUT = 30
SCRAPLING_NETWORK_IDLE_TIMEOUT = 20_000  # ms

# Lightpanda nightly download URLs
LIGHTPANDA_URLS = {
    ("Darwin", "arm64"): "https://github.com/lightpanda-io/browser/releases/download/nightly/lightpanda-aarch64-macos",
    ("Darwin", "x86_64"): "https://github.com/lightpanda-io/browser/releases/download/nightly/lightpanda-x86_64-macos",
    ("Linux", "x86_64"): "https://github.com/lightpanda-io/browser/releases/download/nightly/lightpanda-x86_64-linux",
    ("Linux", "aarch64"): "https://github.com/lightpanda-io/browser/releases/download/nightly/lightpanda-aarch64-linux",
}


# ---------------------------------------------------------------------------
# Prerequisite detection & auto-install
# ---------------------------------------------------------------------------

def _run(cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, capture_output=True, text=True, **kwargs)


def is_scrapling_available() -> bool:
    try:
        import scrapling  # noqa: F401
        return True
    except ImportError:
        return False


def is_scrapling_browser_installed() -> bool:
    """Check if Scrapling's browser (Camoufox) is installed."""
    try:
        result = _run([sys.executable, "-m", "scrapling", "status"], timeout=15)
        return result.returncode == 0
    except Exception:
        return False


def install_scrapling() -> bool:
    """Install Scrapling with fetcher extras and download browser."""
    print("[fetchers] Installing Scrapling with fetcher extras...")
    result = _run(
        [sys.executable, "-m", "pip", "install", "scrapling[fetchers]"],
        timeout=300,
    )
    if result.returncode != 0:
        print(f"[fetchers] pip install failed: {result.stderr}", file=sys.stderr)
        return False
    print("[fetchers] Downloading Scrapling browser (Camoufox)...")
    result = _run([sys.executable, "-m", "scrapling", "install"], timeout=300)
    if result.returncode != 0:
        print(f"[fetchers] scrapling install failed: {result.stderr}", file=sys.stderr)
        return False
    print("[fetchers] Scrapling installed successfully.")
    return True


def is_lightpanda_available() -> bool:
    # Check custom path first
    if LIGHTPANDA_BIN.exists():
        return True
    # Check PATH
    return shutil.which("lightpanda") is not None


def _lightpanda_binary_path() -> str:
    if LIGHTPANDA_BIN.exists():
        return str(LIGHTPANDA_BIN)
    in_path = shutil.which("lightpanda")
    return in_path or "lightpanda"


def install_lightpanda() -> bool:
    """Download Lightpanda nightly binary for the current platform."""
    system = platform.system()
    machine = platform.machine()
    # Normalize machine names
    if machine in ("arm64", "aarch64"):
        arch = "aarch64"
    elif machine in ("x86_64", "AMD64"):
        arch = "x86_64"
    else:
        print(f"[fetchers] Unsupported architecture for Lightpanda: {machine}", file=sys.stderr)
        return False

    url = LIGHTPANDA_URLS.get((system, arch))
    if not url:
        print(f"[fetchers] No Lightpanda build for {system}/{arch}", file=sys.stderr)
        return False

    print(f"[fetchers] Downloading Lightpanda from {url}...")
    try:
        LIGHTPANDA_DIR.mkdir(parents=True, exist_ok=True)
        tmp_path = LIGHTPANDA_BIN.with_suffix(".tmp")
        _run(["curl", "-L", "-o", str(tmp_path), url], timeout=120)
        if tmp_path.exists() and tmp_path.stat().st_size > 1_000_000:
            tmp_path.chmod(0o755)
            tmp_path.rename(LIGHTPANDA_BIN)
            print(f"[fetchers] Lightpanda installed at {LIGHTPANDA_BIN}")
            return True
        else:
            print("[fetchers] Downloaded file too small — likely failed.", file=sys.stderr)
            tmp_path.unlink(missing_ok=True)
            return False
    except Exception as exc:
        print(f"[fetchers] Lightpanda install failed: {exc}", file=sys.stderr)
        return False


def is_agent_browser_available() -> bool:
    return shutil.which("agent-browser") is not None


def install_agent_browser() -> bool:
    """Install agent-browser via npm."""
    print("[fetchers] Installing agent-browser via npm...")
    result = _run(["npm", "install", "-g", "agent-browser"], timeout=300)
    if result.returncode != 0:
        print(f"[fetchers] npm install failed: {result.stderr}", file=sys.stderr)
        return False
    print("[fetchers] Downloading Chrome for agent-browser...")
    result = _run(["agent-browser", "install"], timeout=300)
    if result.returncode != 0:
        print(f"[fetchers] agent-browser install failed: {result.stderr}", file=sys.stderr)
        return False
    print("[fetchers] agent-browser installed successfully.")
    return True


def check_prerequisites(auto_install: bool = True) -> dict[str, dict[str, Any]]:
    """Detect and optionally auto-install prerequisites.

    Returns a dict like:
        {
            "scrapling": {"available": True, "installed_during_run": False},
            "lightpanda": {"available": True, "installed_during_run": True},
            "agent_browser": {"available": False, "installed_during_run": False},
        }
    """
    status: dict[str, dict[str, Any]] = {}

    # --- Scrapling ---
    scrapling_available = is_scrapling_available()
    scrapling_installed_now = False
    if not scrapling_available and auto_install:
        scrapling_installed_now = install_scrapling()
        scrapling_available = is_scrapling_available()
    # Also check browser is installed
    if scrapling_available and not is_scrapling_browser_installed():
        if auto_install:
            _run([sys.executable, "-m", "scrapling", "install"], timeout=300)
    status["scrapling"] = {
        "available": scrapling_available,
        "installed_during_run": scrapling_installed_now,
    }

    # --- Lightpanda ---
    lightpanda_available = is_lightpanda_available()
    lightpanda_installed_now = False
    if not lightpanda_available and auto_install:
        lightpanda_installed_now = install_lightpanda()
        lightpanda_available = is_lightpanda_available()
    status["lightpanda"] = {
        "available": lightpanda_available,
        "installed_during_run": lightpanda_installed_now,
    }

    # --- agent-browser ---
    ab_available = is_agent_browser_available()
    ab_installed_now = False
    if not ab_available and auto_install:
        ab_installed_now = install_agent_browser()
        ab_available = is_agent_browser_available()
    status["agent_browser"] = {
        "available": ab_available,
        "installed_during_run": ab_installed_now,
    }

    return status


def print_prereq_summary(status: dict[str, dict[str, Any]]) -> None:
    """Print a human-readable prerequisite summary."""
    labels = {
        "scrapling": "Scrapling (Camoufox)",
        "lightpanda": "Lightpanda",
        "agent_browser": "agent-browser",
    }
    for key, label in labels.items():
        info = status.get(key, {})
        avail = info.get("available", False)
        just_installed = info.get("installed_during_run", False)
        if avail and just_installed:
            print(f"  ✓ {label} — installed during this run")
        elif avail:
            print(f"  ✓ {label} — available")
        else:
            print(f"  ✗ {label} — not available (will skip)")


# ---------------------------------------------------------------------------
# SPA / thin-shell detection
# ---------------------------------------------------------------------------

def detect_spa_shell(html_text: str, word_count: int, script_count: int) -> dict[str, Any]:
    """Detect whether the page is a thin SPA shell with no meaningful content."""
    is_js_heavy = script_count >= 5 and word_count < 100
    is_thin = word_count < 50 and script_count >= 3
    needs_js_rendering = is_js_heavy or is_thin
    return {
        "is_spa_shell": is_js_heavy,
        "is_thin_html": is_thin,
        "needs_js_rendering": needs_js_rendering,
        "word_count": word_count,
        "script_count": script_count,
    }


# ---------------------------------------------------------------------------
# Fetcher implementations
# ---------------------------------------------------------------------------

def _fetch_urllib(url: str, user_agent: str = DEFAULT_UA, timeout: int = FETCH_TIMEOUT) -> dict:
    """Raw HTTP GET via urllib — no JS rendering."""
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Encoding": "gzip",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read()
        encoding = response.headers.get("Content-Encoding", "").lower()
        if encoding == "gzip":
            raw = gzip.decompress(raw)
        content_type = response.headers.get_content_type()
        charset = response.headers.get_content_charset() or "utf-8"
        text = raw[:MAX_BODY_CHARS].decode(charset, errors="replace")
        return {
            "final_url": response.geturl(),
            "status": getattr(response, "status", None) or response.getcode(),
            "headers": dict(response.info()),
            "content_type": content_type,
            "text": text,
            "bytes": len(raw),
            "fetcher": "urllib",
        }


def _fetch_scrapling(url: str, timeout: int = FETCH_TIMEOUT) -> dict | None:
    """Fetch with Scrapling StealthyFetcher (Camoufox) — full JS rendering."""
    try:
        from scrapling.fetchers import StealthyFetcher
    except ImportError:
        return None

    try:
        page = StealthyFetcher.fetch(
            url,
            headless=True,
            network_idle=True,
            disable_resources=True,
        )
        html_text = page.html if hasattr(page, "html") else str(page)
        if not html_text:
            return None
        # Try to get status code from the page object
        status_code = getattr(page, "status_code", 200)
        final_url = getattr(page, "url", url)
        return {
            "final_url": final_url,
            "status": status_code,
            "headers": {},
            "content_type": "text/html",
            "text": html_text[:MAX_BODY_CHARS],
            "bytes": len(html_text.encode("utf-8", errors="replace")),
            "fetcher": "scrapling",
        }
    except Exception as exc:
        print(f"[fetchers] Scrapling fetch failed for {url}: {exc}", file=sys.stderr)
        return None


def _fetch_lightpanda(url: str, timeout: int = FETCH_TIMEOUT) -> dict | None:
    """Fetch with Lightpanda CLI — fast headless CDP browser."""
    bin_path = _lightpanda_binary_path()
    if not Path(bin_path).exists() and not shutil.which(bin_path):
        return None

    try:
        result = _run(
            [
                bin_path, "fetch",
                "--dump", "html",
                "--wait-until", "networkidle",
                "--wait-ms", str(min(timeout * 1000, 20000)),
                url,
            ],
            timeout=timeout + 10,
        )
        if result.returncode != 0:
            print(f"[fetchers] Lightpanda fetch failed: {result.stderr}", file=sys.stderr)
            return None
        html_text = result.stdout
        if not html_text.strip():
            return None
        return {
            "final_url": url,
            "status": 200,
            "headers": {},
            "content_type": "text/html",
            "text": html_text[:MAX_BODY_CHARS],
            "bytes": len(html_text.encode("utf-8", errors="replace")),
            "fetcher": "lightpanda",
        }
    except subprocess.TimeoutExpired:
        print(f"[fetchers] Lightpanda fetch timed out for {url}", file=sys.stderr)
        return None
    except Exception as exc:
        print(f"[fetchers] Lightpanda fetch error for {url}: {exc}", file=sys.stderr)
        return None


def _fetch_agent_browser(url: str, timeout: int = FETCH_TIMEOUT) -> dict | None:
    """Fetch with agent-browser CLI — Playwright-based headless browser."""
    if not shutil.which("agent-browser"):
        return None

    try:
        # Open the page
        _run(["agent-browser", "open", url], timeout=timeout)
        # Wait for network idle
        _run(["agent-browser", "wait", "--load", "networkidle"], timeout=timeout)
        # Get the rendered HTML
        result = _run(
            ["agent-browser", "eval", "document.documentElement.outerHTML", "--json"],
            timeout=15,
        )
        if result.returncode != 0:
            print(f"[fetchers] agent-browser eval failed: {result.stderr}", file=sys.stderr)
            return None

        # Parse the JSON output
        try:
            data = json.loads(result.stdout)
            html_text = data.get("data", data.get("result", result.stdout))
            if isinstance(html_text, dict):
                html_text = (
                    html_text.get("result")
                    or html_text.get("html")
                    or html_text.get("outerHTML")
                    or ""
                )
        except json.JSONDecodeError:
            html_text = result.stdout

        if not isinstance(html_text, str):
            html_text = str(html_text)
        if not html_text.strip():
            return None
        return {
            "final_url": url,
            "status": 200,
            "headers": {},
            "content_type": "text/html",
            "text": html_text[:MAX_BODY_CHARS],
            "bytes": len(html_text.encode("utf-8", errors="replace")),
            "fetcher": "agent_browser",
        }
    except subprocess.TimeoutExpired:
        print(f"[fetchers] agent-browser fetch timed out for {url}", file=sys.stderr)
        return None
    except Exception as exc:
        print(f"[fetchers] agent-browser fetch error for {url}: {exc}", file=sys.stderr)
        return None


# ---------------------------------------------------------------------------
# Unified fetch entry point
# ---------------------------------------------------------------------------

def fetch_rendered(
    url: str,
    user_agent: str = DEFAULT_UA,
    timeout: int = FETCH_TIMEOUT,
    preferred_fetcher: str = "auto",
) -> dict:
    """Fetch a URL with JS rendering support, trying fetchers in priority order.

    Args:
        url: The URL to fetch.
        user_agent: User-Agent header for urllib fallback.
        timeout: Timeout in seconds.
        preferred_fetcher: One of "auto", "scrapling", "lightpanda",
            "agent_browser", "urllib".  "auto" tries all in priority order.

    Returns:
        Dict with keys: final_url, status, headers, content_type, text, bytes, fetcher
    """
    fetcher_map = {
        "scrapling": lambda: _fetch_scrapling(url, timeout),
        "lightpanda": lambda: _fetch_lightpanda(url, timeout),
        "agent_browser": lambda: _fetch_agent_browser(url, timeout),
        "urllib": lambda: _fetch_urllib(url, user_agent, timeout),
    }

    if preferred_fetcher != "auto":
        handler = fetcher_map.get(preferred_fetcher)
        if handler:
            result = handler()
            if result is not None:
                return result
            # If the preferred fetcher fails, fall through to urllib
            print(f"[fetchers] Preferred fetcher '{preferred_fetcher}' failed, falling back to urllib", file=sys.stderr)
        return _fetch_urllib(url, user_agent, timeout)

    # Auto mode: try each fetcher in priority order
    for name in ("scrapling", "lightpanda", "agent_browser"):
        handler = fetcher_map[name]
        result = handler()
        if result is not None:
            return result
        # Continue to next fetcher

    # Final fallback: urllib (always works for basic HTTP)
    return _fetch_urllib(url, user_agent, timeout)


# ---------------------------------------------------------------------------
# Lightpanda CDP server management (for local Lighthouse)
# ---------------------------------------------------------------------------

_lightpanda_process: subprocess.Popen | None = None


def start_lightpanda_cdp(port: int = LIGHTPANDA_CDP_PORT) -> subprocess.Popen | None:
    """Start Lightpanda in CDP server mode. Returns the process or None."""
    global _lightpanda_process
    if _lightpanda_process is not None and _lightpanda_process.poll() is None:
        return _lightpanda_process  # Already running

    bin_path = _lightpanda_binary_path()
    if not Path(bin_path).exists() and not shutil.which(bin_path):
        return None

    try:
        proc = subprocess.Popen(
            [
                bin_path, "serve",
                "--host", "127.0.0.1",
                "--port", str(port),
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(2)  # Give it a moment to start
        if proc.poll() is not None:
            print("[fetchers] Lightpanda CDP server exited immediately", file=sys.stderr)
            return None
        _lightpanda_process = proc
        return proc
    except Exception as exc:
        print(f"[fetchers] Failed to start Lightpanda CDP: {exc}", file=sys.stderr)
        return None


def stop_lightpanda_cdp() -> None:
    """Stop the Lightpanda CDP server if running."""
    global _lightpanda_process
    if _lightpanda_process is not None:
        try:
            _lightpanda_process.terminate()
            _lightpanda_process.wait(timeout=5)
        except Exception:
            try:
                _lightpanda_process.kill()
            except Exception:
                pass
        _lightpanda_process = None


def get_cdp_endpoint(port: int = LIGHTPANDA_CDP_PORT) -> str:
    """Return the CDP WebSocket endpoint URL."""
    return f"http://127.0.0.1:{port}"


def is_lighthouse_available() -> bool:
    """Check if Lighthouse CLI is available (either directly or via npx)."""
    return shutil.which("lighthouse") is not None or shutil.which("npx") is not None


def run_local_lighthouse(
    url: str,
    strategy: str = "mobile",
    cdp_port: int = LIGHTPANDA_CDP_PORT,
    timeout: int = 120,
) -> dict | None:
    """Run Lighthouse locally via CDP and return parsed results.

    Starts Lightpanda CDP when available, then runs Lighthouse against that
    endpoint. If Lightpanda is unavailable, falls back to Lighthouse's normal
    browser launch path instead of forcing a dead CDP port.
    """
    was_running = _lightpanda_process is not None and _lightpanda_process.poll() is None

    # Ensure CDP server is running
    cdp_proc = start_lightpanda_cdp(cdp_port)

    tmp_dir = tempfile.mkdtemp(prefix="lighthouse-")
    output_path = os.path.join(tmp_dir, "result.json")

    try:
        # Try lighthouse directly, then npx
        for cmd_prefix in ([shutil.which("lighthouse") or "lighthouse"], ["npx", "lighthouse"]):
            cmd = cmd_prefix + [
                url,
                "--output=json",
                f"--output-path={output_path}",
                "--quiet",
                "--only-categories=performance,accessibility,best-practices,seo",
            ]
            if strategy == "desktop":
                cmd.append("--preset=desktop")
            if cdp_proc is not None:
                cmd.append(f"--port={cdp_port}")
            try:
                result = _run(cmd, timeout=timeout)
                if result.returncode == 0 and os.path.exists(output_path):
                    return json.loads(Path(output_path).read_text(encoding="utf-8"))
            except (subprocess.TimeoutExpired, Exception):
                continue
        return None
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        if not was_running and cdp_proc is not None:
            stop_lightpanda_cdp()


# ---------------------------------------------------------------------------
# Main (for testing)
# ---------------------------------------------------------------------------

def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Test the unified fetcher.")
    parser.add_argument("url", help="URL to fetch")
    parser.add_argument("--fetcher", default="auto", choices=["auto", "scrapling", "lightpanda", "agent_browser", "urllib"])
    parser.add_argument("--check-prereqs", action="store_true", help="Only check prerequisites")
    parser.add_argument("--no-auto-install", action="store_true", help="Don't auto-install missing prerequisites")
    args = parser.parse_args()

    if args.check_prereqs:
        status = check_prerequisites(auto_install=not args.no_auto_install)
        print_prereq_summary(status)
        return 0

    print(f"Fetching {args.url} with fetcher={args.fetcher}...")
    result = fetch_rendered(args.url, preferred_fetcher=args.fetcher)
    print(f"Fetcher used: {result['fetcher']}")
    print(f"Status: {result['status']}")
    print(f"Bytes: {result['bytes']}")
    text_preview = result["text"][:500]
    print(f"Text preview: {text_preview}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

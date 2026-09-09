#!/usr/bin/env python3
# ═══ imports ══════════════════════════════════════════════════════════════
import http.server
import secrets
import sys
import time
import urllib.parse
import webbrowser

from spotify_web import (
    AUTH_URL,
    SCOPES,
    load_credentials,
    post_token,
    save_token,
    token_path,
)

# ═══ one-shot spotify login ═══════════════════════════════════════════════
# Run once, by hand: `python3 qtile/spotify_auth.py`. It opens the browser,
# takes the approval, and leaves a refresh token behind for the widget to use
# from then on. The refresh token does not expire, so this should not need
# running again unless the app is deleted or access is revoked.
#
# Spotify only redirects back to a URI registered on the app, and it insists on
# a loopback IP rather than a hostname, so the browser is sent to 127.0.0.1 and
# caught by a server that lives exactly long enough to read one request.

USAGE = """usage: spotify_auth.py

Logs in to Spotify once and leaves a refresh token behind for the bar's
now-playing widget. Takes no options. Reads the app registration from
~/.config/qtile-spotify/credentials.json."""

PAGE = """<!doctype html>
<title>qtile now playing</title>
<style>
  body {{ background: #1e1e1e; color: #e0e0e0; font: 16px system-ui, sans-serif;
         display: grid; place-content: center; height: 100vh; margin: 0; }}
  p {{ max-width: 30em; text-align: center; line-height: 1.6; }}
  b {{ color: {colour}; }}
</style>
<p><b>{heading}</b><br>{detail}</p>
"""


class _Callback(http.server.BaseHTTPRequestHandler):
    """Catches the one redirect Spotify makes back to us."""

    code: str | None = None
    error: str | None = None
    state: str = ""

    def do_GET(self):  # the name is BaseHTTPRequestHandler's to choose
        query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)

        if query.get("state", [""])[0] != _Callback.state:
            # Not the redirect we sent the user off with. Ignore it and keep
            # waiting: a stray browser prefetch should not end the login.
            self._reply(
                "Unexpected request", "This did not come from the login. Still waiting."
            )
            return

        _Callback.error = query.get("error", [None])[0]
        _Callback.code = query.get("code", [None])[0]

        if _Callback.error:
            self._reply("Login refused", f"Spotify said: {_Callback.error}", ok=False)
        else:
            self._reply(
                "Connected", "You can close this tab and go back to the terminal."
            )

    def _reply(self, heading, detail, ok=True):
        body = PAGE.format(
            heading=heading, detail=detail, colour="#1db954" if ok else "#ff6b6b"
        ).encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        """Silence the default stderr access log - the script prints its own."""


def main() -> int:
    # No options, and an argument almost certainly means someone expected some
    # - say so rather than opening a browser at them, which is what an
    # unguarded `--help` does.
    if sys.argv[1:]:
        print(__doc__ or USAGE, file=sys.stderr)
        return 0 if sys.argv[1] in ("-h", "--help") else 2

    try:
        creds = load_credentials()
    except (FileNotFoundError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    redirect = urllib.parse.urlparse(creds["redirect_uri"])
    if not redirect.hostname or not redirect.port:
        print(
            f"error: redirect_uri {creds['redirect_uri']!r} needs a host and port, "
            "e.g. http://127.0.0.1:8888/callback",
            file=sys.stderr,
        )
        return 1

    _Callback.state = secrets.token_urlsafe(16)
    url = (
        AUTH_URL
        + "?"
        + urllib.parse.urlencode(
            {
                "client_id": creds["client_id"],
                "response_type": "code",
                "redirect_uri": creds["redirect_uri"],
                "scope": SCOPES,
                "state": _Callback.state,
            }
        )
    )

    try:
        server = http.server.HTTPServer((redirect.hostname, redirect.port), _Callback)
    except OSError as e:
        print(
            f"error: cannot listen on {redirect.hostname}:{redirect.port}: {e}",
            file=sys.stderr,
        )
        return 1

    print("Opening Spotify in your browser to approve access.")
    print(f"If nothing opens, paste this in yourself:\n\n  {url}\n")
    webbrowser.open(url)

    # One request is usually enough, but a favicon fetch or a prefetch can beat
    # the real redirect to the door, so keep serving until the code turns up.
    server.timeout = 120
    deadline = time.time() + server.timeout
    while _Callback.code is None and _Callback.error is None:
        if time.time() > deadline:
            print("error: timed out waiting for the browser redirect", file=sys.stderr)
            return 1
        server.handle_request()
    server.server_close()

    if _Callback.error:
        print(f"error: Spotify refused the login: {_Callback.error}", file=sys.stderr)
        return 1

    try:
        token = post_token(
            {
                "grant_type": "authorization_code",
                "code": _Callback.code,
                "redirect_uri": creds["redirect_uri"],
            },
            creds,
        )
    except Exception as e:  # noqa: BLE001 - whatever went wrong, the user needs to see it
        print(f"error: could not exchange the code for a token: {e}", file=sys.stderr)
        return 1

    if "refresh_token" not in token:
        print(f"error: no refresh token in the response: {token}", file=sys.stderr)
        return 1

    save_token(
        {
            "refresh_token": token["refresh_token"],
            "access_token": token.get("access_token"),
            "expires_at": time.time() + token.get("expires_in", 3600),
        }
    )
    print(
        f"Saved a refresh token to {token_path()}. Reload qtile and it will be picked up."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

# ═══ imports ══════════════════════════════════════════════════════════════
import base64
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path

# ═══ spotify web api ══════════════════════════════════════════════════════
# MPRIS only ever knows about players running on this machine, so the bar goes
# blank whenever the account is playing through the phone. This asks Spotify's
# servers what the *account* is playing, which covers every device signed into
# it, and needs nothing running locally.
#
# Stdlib only, deliberately: qtile runs from a uv tool venv, so a `requests`
# import here would have to be carried through every `uv tool install` of qtile
# as a --with. urllib covers the three requests this makes.

AUTH_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"
PLAYER_URL = "https://api.spotify.com/v1/me/player"

# user-read-currently-playing alone would do for the track, but /me/player also
# names the device it is coming out of, which is the whole point here - the bar
# says "playing, elsewhere" rather than just "playing".
SCOPES = "user-read-currently-playing user-read-playback-state"

# Short: the request runs in a thread, but qtile still joins that thread when
# it shuts down, and a dead network should not hold up a restart.
TIMEOUT = 5

# Consecutive failures tolerated before the widget is told there is nothing
# playing. A dropped request means "unknown", not "stopped", and clearing the
# text on the first one makes a flaky link flicker the bar every poll.
MAX_FAILURES = 3


def config_dir() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME") or "~/.config"
    return Path(base).expanduser() / "qtile-spotify"


def credentials_path() -> Path:
    return config_dir() / "credentials.json"


def token_path() -> Path:
    return config_dir() / "token.json"


@dataclass(frozen=True)
class Track:
    """One line of now-playing, as the widget needs it."""

    title: str
    artist: str
    device: str  # the speaker's name, e.g. "Nick's iPhone"
    device_type: str  # Spotify's own category: Computer, Smartphone, Speaker...
    is_playing: bool

    @property
    def is_local(self) -> bool:
        """Whether this is coming out of the machine the bar is drawn on.

        Spotify names the device but does not say which one is us, so this is
        a hostname match - good enough to spot the common case of the desktop
        client playing here, where MPRIS is the better source anyway.
        """
        return self.device.casefold() == os.uname().nodename.casefold()


def load_credentials() -> dict:
    """The app registration, as written by hand from the Spotify dashboard."""
    with open(credentials_path()) as f:
        creds = json.load(f)
    missing = [
        k for k in ("client_id", "client_secret", "redirect_uri") if not creds.get(k)
    ]
    if missing:
        raise ValueError(f"{credentials_path()} is missing: {', '.join(missing)}")
    if "PASTE" in creds["client_id"] or "PASTE" in creds["client_secret"]:
        raise ValueError(f"{credentials_path()} still holds the placeholder values")
    return creds


def save_token(token: dict) -> None:
    """Write token.json 0600, atomically.

    Atomically because the refresh below rewrites this file while the widget is
    running: a torn write is a lost refresh token, and a lost refresh token
    means going back to the browser.
    """
    path = token_path()
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        json.dump(token, f, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def post_token(payload: dict, creds: dict) -> dict:
    """POST to the token endpoint with the app's basic-auth credentials."""
    secret = f"{creds['client_id']}:{creds['client_secret']}".encode()
    request = urllib.request.Request(
        TOKEN_URL,
        data=urllib.parse.urlencode(payload).encode(),
        headers={
            "Authorization": "Basic " + base64.b64encode(secret).decode(),
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        return json.loads(response.read())


class SpotifyWeb:
    """Polls the account's playback state, holding an access token as it goes.

    Every method here blocks on the network, so the widget runs the whole thing
    in a thread. Nothing locks: the widget schedules one poll at a time and
    waits for it to land before booking the next.
    """

    def __init__(self):
        self._creds: dict | None = None
        self._refresh_token: str | None = None
        self._access_token: str | None = None
        self._expires_at: float = 0.0
        self._retry_after: float = 0.0
        self._failures: int = 0
        self._last: Track | None = None
        # A refresh token the endpoint has already rejected. Kept by value
        # rather than as a flag so that re-running the login recovers on its
        # own: the new token will not match this one, and gets a fair try.
        self._dead_token: str | None = None
        self._complaints: set[str] = set()

    # ─── credentials ──────────────────────────────────────────────────────

    def _complain(self, key: str, message: str) -> None:
        """Log `message` the first time `key` goes wrong, then stay quiet.

        A missing token.json is a standing condition, not an event; without
        this the poll would write the same line to the log every 10 seconds
        for as long as the session lasts.
        """
        if key not in self._complaints:
            from libqtile.log_utils import logger

            logger.warning("Spotify web: %s", message)
            self._complaints.add(key)

    def _load(self) -> bool:
        """Read credentials and the stored refresh token. False if unusable."""
        if self._creds is not None and self._refresh_token is not None:
            return True
        try:
            self._creds = load_credentials()
        except FileNotFoundError:
            self._complain("creds", f"no {credentials_path()}; remote playback off")
            return False
        except (ValueError, json.JSONDecodeError) as e:
            self._complain("creds", f"{e}")
            return False
        try:
            with open(token_path()) as f:
                token = json.load(f)
        except FileNotFoundError:
            self._complain(
                "token", f"no {token_path()}; run qtile/spotify_auth.py once"
            )
            return False
        except json.JSONDecodeError as e:
            self._complain("token", f"{token_path()} is not valid json: {e}")
            return False
        if not token.get("refresh_token"):
            self._complain("token", f"{token_path()} holds no refresh token")
            return False
        if token["refresh_token"] == self._dead_token:
            # Already refused once. Reading it off disk again and retrying is
            # a request every poll, forever, that cannot start working.
            return False
        self._refresh_token = token["refresh_token"]
        self._access_token = token.get("access_token")
        self._expires_at = token.get("expires_at", 0.0)
        return True

    def _refresh(self) -> bool:
        """Trade the refresh token for a fresh access token."""
        assert self._creds is not None and self._refresh_token is not None
        try:
            token = post_token(
                {"grant_type": "refresh_token", "refresh_token": self._refresh_token},
                self._creds,
            )
        except urllib.error.HTTPError as e:
            # 400 here is a revoked or invalidated refresh token, which no
            # amount of retrying fixes - it needs the browser again.
            if e.code == 400:
                self._complain(
                    "revoked",
                    f"refresh token rejected; re-run qtile/spotify_auth.py ({e.read()[:200]!r})",
                )
                self._dead_token = self._refresh_token
                self._refresh_token = None
            return False
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            return False

        self._access_token = token["access_token"]
        self._expires_at = time.time() + token.get("expires_in", 3600)
        # The client-secret flow normally leaves the refresh token alone, but
        # it is allowed to hand back a new one - keep it if it does.
        self._refresh_token = token.get("refresh_token", self._refresh_token)
        save_token(
            {
                "refresh_token": self._refresh_token,
                "access_token": self._access_token,
                "expires_at": self._expires_at,
            }
        )
        self._complaints.discard("revoked")
        return True

    # ─── polling ──────────────────────────────────────────────────────────

    def now_playing(self) -> Track | None:
        """What the account is playing, or None for nothing (or not yet known).

        Blocks. Call it off the event loop.
        """
        if not self._load():
            return None
        if time.time() < self._retry_after:
            return self._last

        # Refresh a minute early: a token that expires mid-flight comes back as
        # a 401 and costs an extra round trip.
        expiring = not self._access_token or time.time() >= self._expires_at - 60
        if expiring and not self._refresh():
            return self._degrade()

        track = self._fetch()
        if track is _UNKNOWN:
            return self._degrade()
        self._failures = 0
        self._last = track
        return track

    def _degrade(self) -> Track | None:
        """Hold the last known track for a few failures, then give up on it."""
        self._failures += 1
        if self._failures >= MAX_FAILURES:
            self._last = None
        return self._last

    def _fetch(self) -> "Track | None":
        """One GET of the player state. `_UNKNOWN` if the answer didn't arrive."""
        # additional_types is what makes podcasts come back as an item at all;
        # without it Spotify reports the episode as a null track.
        url = (
            PLAYER_URL
            + "?"
            + urllib.parse.urlencode({"additional_types": "track,episode"})
        )
        request = urllib.request.Request(
            url, headers={"Authorization": f"Bearer {self._access_token}"}
        )
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
                # 204: nothing is playing anywhere, and there is no body.
                if response.status == 204:
                    return None
                return _parse(json.loads(response.read()))
        except urllib.error.HTTPError as e:
            if e.code == 401:
                # Token died early (password change, scope revoked). One retry
                # on the next poll, via a forced refresh.
                self._expires_at = 0.0
            elif e.code == 429:
                # Spotify's window is rolling and short; honour what it asks
                # for rather than hammering through the ban.
                wait = e.headers.get("Retry-After")
                self._retry_after = time.time() + (
                    int(wait) if wait and wait.isdigit() else 30
                )
                self._complain("429", f"rate limited, backing off {wait or 30}s")
            return _UNKNOWN
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError):
            return _UNKNOWN


# Sentinel for "the request failed", which is not the same answer as None,
# "nothing is playing" - the first keeps the last known track on the bar.
_UNKNOWN: Track = Track("", "", "", "", False)


def _parse(payload: dict) -> Track | None:
    """A player-state response as a Track, or None if there is no track in it."""
    item = payload.get("item")
    if not item:
        # An advert between tracks, or a private session: playing, but with
        # nothing nameable to show.
        return None
    if item.get("type") == "episode":
        # Podcasts have a show where music has artists.
        artist = (item.get("show") or {}).get("name", "")
    else:
        artist = ", ".join(
            a["name"] for a in item.get("artists") or [] if a.get("name")
        )
    device = payload.get("device") or {}
    return Track(
        title=item.get("name", ""),
        artist=artist,
        device=device.get("name", ""),
        device_type=device.get("type", ""),
        is_playing=bool(payload.get("is_playing")),
    )

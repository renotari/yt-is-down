# Review — YouTube Downloader (focused, practical)

Nice work — this is a well thought-out, pragmatic downloader with many realistic fallback strategies and good use of centralized configuration. Below I give actionable, prioritized feedback (critical bugs first), then practical suggestions for robustness, maintainability, security and small cleanups you can apply without overengineering.

---

# Critical issues (fix these first)

## 1. Syntax / packaging mistakes in pasted files

* `downloader.py` starts with `mport yt_dlp` — missing the leading `i`. This will crash immediately.
* `config/download_config.py` has a broken file header (the triple-quote and `python"" "\nDownload...`) — make sure the module has a valid docstring or none. These are blocking.

## 2. Global side-effects: `socket.setdefaulttimeout(self.timeout)`

Setting a global socket default timeout in the constructor modifies global interpreter state and may surprise other parts of the program or third-party libs. Prefer per-call/option timeouts (you already pass `socket_timeout` into yt-dlp). Remove `socket.setdefaulttimeout(...)` or make it opt-in and documented.

## 3. Unsafe filename / path handling (possible directory traversal)

* `outtmpl` uses `%(title)s` and `%(playlist_title)s` directly. Titles/playlist titles can contain path separators or `..`. Although yt-dlp sanitizes filenames, **explicitly** set `restrictfilenames: True` or sanitize fields before using them in templates to avoid directory traversal or creating unexpected directories.
* Example quick mitigation: add `ydl_opts['restrictfilenames'] = True` for any `outtmpl` using user content.

## 4. Overly broad exception handling hides root causes

There are many `except Exception as e: raise YouTubeDownloaderError(...)` or `except Exception` fallbacks across methods. That’s reasonable for a UX layer, but:

* Log the original exception (use `logging.exception`) before wrapping.
* Avoid hiding `KeyboardInterrupt` or `SystemExit` unintentionally (you do handle KeyboardInterrupt in some places but not all).
* Be selective where useful: catch `yt_dlp.DownloadError`, `yt_dlp.utils.ExtractorError` (or the precise exceptions yt-dlp exposes) rather than blanket `Exception`.

## 5. Fragile string matching on exception messages

You repeatedly inspect `str(e).lower()` for `"403"`, `"private"`, `"timeout"`, `"forbidden"`, `"no space left"`, `"ffmpeg"`, etc. This is brittle and fragile to message changes and locales.

* Prefer checking exception types where available or add a small helper `is_http_error(e, code)` using parsed attributes if `yt_dlp` exposes them.
* At minimum, centralize string checks in helper functions and document they are heuristics.

---

# High priority improvements (practical, relatively small)

## 6. Thread safety / multiple downloads

* `self.output_dir` is occasionally re-assigned from `str` to `Path` inside methods. Don't mutate instance state during calls. Convert once in `__init__` and keep immutable. This reduces race conditions if you add parallel downloads.
* If you plan concurrent downloads, `download_stats` and instance-level state must be protected or per-download.

## 7. Move fallback strategies into a configurable list

You currently have many sequential fallback blocks inside `_try_download_with_fallbacks`. Make a list of strategy callables (or small strategy objects) and iterate over them. Advantages:

* Easier to test each strategy separately.
* Able to stop early or limit retries.
* Configurable order/timeouts per user preference.

You don't need to fully refactor now — extract each fallback into its own small method (you already have several) and create a simple ordered list that `_try_download_with_fallbacks` iterates.

## 8. Avoid changing `ydl_opts` in place in fallbacks

You use `.copy()` sometimes but also mutate nested dicts. Use deep-copy or construct new opts to avoid accidentally sharing references between strategies (e.g., postprocessors list mutated will persist).

## 9. Use the logging module, not silent `pass`

There are `except Exception: pass` blocks (e.g., `_get_available_formats`). Replace with `logging.debug` or `logging.exception` so problems can be diagnosed in real runs.

## 10. Protect against empty/partial playlist entries

`get_playlist_info` assumes `entries` is a list and uses `len(entries)`. When `extract_flat` is used entries may contain placeholder dicts or `None`. Validate entries and count only non-None real entries. Example:

```py
entries = [e for e in info.get('entries', []) if e]
video_count = len(entries)
```

---

# Design & architecture

## 11. Single class vs split responsibility

* The single `YouTubeDownloader` class is fine for a small-to-medium desktop app, but it mixes:

  * metadata extraction,
  * download orchestration,
  * fallback strategies,
  * playlist bookkeeping,
  * error types.

**Recommendation (practical):**

* Split into logical modules, not necessarily many classes: e.g.

  * `extractor.py` — methods for getting info (`get_video_info`, `get_playlist_info`, `get_content_info`).
  * `downloader_core.py` — one or two functions that take prepared `ydl_opts` and run downloads + fallback orchestration.
  * `fallbacks.py` — collection of fallback strategies (callables).
  * Keep `YouTubeDownloader` as a thin façade that wires them together and exposes the public API.
    This keeps code navigable and easier to test without heavy redesign.

## 12. Separation of core logic vs UI (GUI/CLI)

You appear to have no GUI code here (good). The core logic uses `progress_callback` to decouple UI — that’s excellent. Ensure the GUI/CLI code only:

* constructs nice `progress_callback` functions,
* calls `YouTubeDownloader` methods,
* handles user confirmation / policy messages.

Avoid embedding UI text inside core; move messages into config/error modules (you already use `ErrorMessages`).

---

# Error handling & messages

## 13. Use custom exceptions consistently

You define several custom exceptions at top — good. But sometimes you raise `yt_dlp.DownloadError` directly from `_raise_fallback_error` and sometimes raise `YouTubeDownloaderError`. Prefer raising your own exceptions so callers don't need to depend on yt-dlp internals. E.g. create `DownloadFailedError` and use it.

## 14. Return values vs exceptions

* `download_video` returns `bool` on success and raises exceptions on failure. That’s acceptable; ensure callers expect exceptions for errors. For playlist downloads you return a result dict. Consider being consistent: either always return a result summary dict or raise on fatal errors.

---

# Performance & reliability

## 15. Performance bottlenecks

* The fallback chain can be long and slow (multiple retries and different clients). That’s expected: fallbacks are expensive. Make them configurable and add an overall fallback timeout or maximum number of strategies to try.
* For playlists, current delays (`DEFAULT_SLEEP_INTERVAL` 15–25s) multiplied by many videos may make downloads extremely slow. You already warn and throw `PlaylistTooLargeError` for >200 items — good. Consider:

  * offering a **concurrency option** for playlist downloads (with `concurrent_fragment_downloads` but be mindful of rate-limiting and politeness).
  * Allow the user to choose conservative vs fast mode (you already have conservative flags).

## 16. Rate limiting values

* The `15–25s` delay is conservative and respectful but may be overkill for small playlists or single videos. Keep these in `DownloadConfig` and make them user-configurable (e.g., a "politeness" slider).
* Provide a short-note in docs: "Defaults favour safety; lower delays in personal use increase speed but may risk throttling."

## 17. Disk space and streaming

* You detect `"no space left"` from exception messages. Consider proactively checking free disk space before starting a download (with `shutil.disk_usage`) if estimated file sizes available from yt-dlp metadata.

---

# Security & ethics

## 18. Client spoofing and ethics

* Changing `User-Agent`, extractor args, and client strings to circumvent restrictions enters an ethical territory. It's common in tools, but you should:

  * Document this behavior clearly for users.
  * Add a user setting to enable/disable aggressive spoofing/fallbacks.
  * Respect robots / TOS considerations — include a short disclaimer.

## 19. Input validation

* `ValidationConfig.MAX_URL_LENGTH` and `MIN_VIDEO_ID_LENGTH` exist but are not used consistently. Validate URL lengths and raise early if too long/too short.
* Sanitize or reject odd characters in video/playlist IDs if you parse them manually.

---

# Maintainability / developer experience

## 20. Tests & dependency injection

* Make yt-dlp usage injectable (pass a yt-dlp wrapper to the class or module) so you can unit test without actually performing network IO.
* Add small unit tests for:

  * `_is_valid_url` / `_is_playlist_url`,
  * parsing of `quality` string into `format_selector`,
  * fallback strategy selection (use a fake `yt_dlp` backend).

## 21. Config cohesion

* `DownloadConfig` is good and centralized. A few minor improvements:

  * Some names are similar (DEFAULT_RETRIES vs EXTRACTOR_RETRIES). Add comments on intended use.
  * Consider grouping playlist-specific settings into a nested structure or class for clarity (not required).
  * `AUDIO_FILE_SIZE_PREFERENCE` and `SMALL_AUDIO_FILE` duplication — keep one source of truth.

## 22. Order-preserving formats list

* `_get_available_formats` returns `list(set(...))`, which loses ordering. If you want a sorted unique list, use `dict.fromkeys()` or `OrderedDict` to preserve discovery order:

```py
formats = list(dict.fromkeys(formats))
```

## 23. Small bugs / logic quibbles

* `get_content_info` sets `video_info['is_playlist'] = False` — but `get_video_info` does not set `is_playlist` key. Be explicit and consistent about keys returned.
* In `download_playlist` the check `if not (playlist_info.get('is_playlist') or 'video_count' in playlist_info):` — the `get_content_info` above sets `is_playlist=False` for videos, so this will pass into the block that assumes "not playlist" and set minimal playlist info. That may be okay but confusing. Use explicit keys from `get_content_info` to represent type.

---

# Practical code snippets / examples

### Sanitize `outtmpl` and use restrictfilenames

```py
base_opts = {
    # ...
    'outtmpl': str(self.output_dir / '%(playlist_title)s/%(title)s.%(ext)s'),
    'restrictfilenames': True,  # avoid problematic characters & directory traversal
}
```

### Safer `socket` usage (remove global default)

Remove `socket.setdefaulttimeout(self.timeout)` from `__init__`. Rely on `'socket_timeout'` per-ydl call.

### better unique formats without losing order

```py
def _get_available_formats(self, info):
    formats = []
    for f in info.get('formats', []) or []:
        if f.get('vcodec') != 'none':
            quality = f.get('height')
            ext = f.get('ext')
            if quality and ext:
                formats.append(f"{quality}p - {ext}")
    # preserve first-seen order
    return list(dict.fromkeys(formats))
```

### Example: centralize error-message heuristics

```py
def _error_contains(self, exc, *tokens):
    s = str(exc).lower()
    return any(tok in s for tok in tokens)
```

Then use `_error_contains(e, "403", "forbidden")` etc.

---

# Prioritized roadmap (concrete, small steps)

1. Fix syntax errors and invalid headers in config file.
2. Remove `socket.setdefaulttimeout` and ensure you pass `socket_timeout` everywhere.
3. Add `restrictfilenames: True` and/or sanitize `outtmpl` templated fields.
4. Replace `list(set(...))` with `dict.fromkeys(...)` to preserve ordering.
5. Replace fragile string matching with helper(s) and log original exceptions.
6. Extract fallback strategies into an ordered list/registry (small refactor).
7. Add logging in all `except Exception` blocks before re-raising.
8. Make fallback aggressiveness configurable and document spoofing behavior.
9. Add unit tests for parsing/URL checks and the `format_selector` logic.
10. Consider splitting extractor vs downloader modules (medium-term).

---

# Final thoughts (practical, non-academic)

This code is close to something that will reliably work for most users. The biggest practical risks are: accidental path issues from unsanitized titles, brittle string-based error handling, and the global socket timeout. Address those and your app will become much more robust. The fallback strategies are thorough and pragmatic — just make them configurable and better isolated for testing.

If you want, I can:

* produce a patch diff for the top 5 fixes (imports, socket removal, restrictfilenames, logging in broad excepts, formats ordering),
* or sketch a small unit-test file and a mock wrapper for yt-dlp so you can start test-driving changes.

Which would you prefer me to do next?

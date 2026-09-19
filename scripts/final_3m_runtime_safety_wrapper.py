#!/usr/bin/env python3
"""RUNTIME SAFETY INSTRUMENTATION WRAPPER for the FINAL 3M validation checker.

Purpose
-------
Run the canonical production CLI (``python -m runner.cli validate ...``) as
``__main__`` inside THIS process with a CPython audit hook installed, recording
every socket / process-exec / filesystem-mutation audit event to a JSON file.

This converts the checker's SAFETY verdict from a static construction argument
("no network by construction") into an actual RUNTIME MEASUREMENT of the
production validation subprocess.  If the engine attempts to open a socket,
spawn a process, or mutate a file outside the repository root during the
validation run, the event is recorded and the checker classifies the run's
safety as FAIL.  If this events file is not produced (process killed, crash
before dump), the checker reports safety as NOT_MEASURED — never PASS.

Mechanism and honest scope
--------------------------
- ``sys.addaudithook`` (CPython >= 3.8).  This is a cooperative observation
  layer INSIDE the engine process — it is NOT a kernel-level sandbox and a
  deliberately adversarial code path could evade it.  The production code
  under test is not adversarial and has no knowledge of this hook; the
  measurement is an observation, not an isolation boundary.
- Captured event names (prefix / exact): ``socket.*``, ``subprocess.*``,
  ``os.exec``, ``os.system``, ``os.posix_spawn``, ``os.spawn``, ``os.fork``,
  ``os.remove``, ``os.rename``, ``os.rmdir``, ``os.truncate``, ``os.link``,
  ``os.symlink``, ``shutil.*``, ``open``, ``ctypes.*``.  All other audit
  events (e.g. per-module ``import``) are ignored.
- ``open`` events carry (path, mode, flags); only write-flagged opens are
  treated as filesystem mutations by the checker.
- The wrapper's OWN write of the events file is excluded from the record
  (recording is disabled during the dump), so it cannot mask engine activity.
- The engine code is executed via ``runpy.run_module("runner.cli",
  run_name="__main__", alter_sys=True)`` with ``sys.argv`` set identically to
  ``python -m runner.cli ...`` — the same entrypoint the canonical CLI
  invocation uses.  No production file is imported or modified by the wrapper
  itself beyond what the CLI itself does.

Usage (invoked by scripts/final_3m_validation.py — not a human entrypoint)
--------------------------------------------------------------------------
    python scripts/final_3m_runtime_safety_wrapper.py \
        --events-out <events.json> [--max-events 50000] [--module runner.cli] -- \
        validate --csv ... --output ... --run-id ... --evidence-dir ...
"""

import argparse
import json
import os
import runpy
import sys
import time

WRAPPER_VERSION = "1.0.0"

# Audit event names/prefixes recorded.  Everything else is ignored.
_RECORD_PREFIXES = (
    "socket.", "subprocess.", "shutil.", "ctypes.",
    "os.exec", "os.system", "os.posix_spawn", "os.spawn", "os.fork",
    "os.remove", "os.rename", "os.rmdir", "os.truncate",
    "os.link", "os.symlink",
)
_RECORD_EXACT = ("open",)

# Module-level recording state (the hook cannot be removed once installed,
# so we gate recording with a flag; the dump phase disables it).
_RECORDING = True
_EVENTS = []
_MAX_EVENTS = 50000


def _event_matches(name):
    if name in _RECORD_EXACT:
        return True
    return name.startswith(_RECORD_PREFIXES)


def _audit_hook(name, args):
    global _RECORDING
    if not _RECORDING:
        return
    if not _event_matches(name):
        return
    if len(_EVENTS) >= _MAX_EVENTS:
        return
    # 'open' carries (path, mode, flags) — keep structured.
    if name == "open" and len(args) >= 3:
        try:
            path, mode, flags = str(args[0]), str(args[1]), args[2]
            _EVENTS.append(
                {"event": "open", "path": path, "mode": mode, "flags": flags})
        except Exception:
            _EVENTS.append({"event": name, "args": repr(args)[:300]})
        return
    _EVENTS.append({"event": name, "args": repr(args)[:300]})


def dump_events(events_out, started_utc, argv, truncated, exit_code,
                error=None):
    """Write the events JSON atomically. Recording is disabled while dumping
    so the dump's own file operations cannot appear in (or be masked from)
    the record."""
    global _RECORDING
    _RECORDING = False
    payload = {
        "wrapper_version": WRAPPER_VERSION,
        "python_version": sys.version.split()[0],
        "started_utc": started_utc,
        "ended_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "module": "runner.cli (executed as __main__ via runpy)",
        "argv": argv,
        "exit_code": exit_code,
        "error": error,
        "max_events": _MAX_EVENTS,
        "truncated": truncated,
        "event_count": len(_EVENTS),
        "events": list(_EVENTS),
    }
    tmp = events_out + ".tmp"
    os.makedirs(os.path.dirname(events_out) or ".", exist_ok=True)
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=1)
    os.replace(tmp, events_out)


def main(argv=None):
    global _MAX_EVENTS
    parser = argparse.ArgumentParser(
        description="Audit-hook runtime safety wrapper for runner.cli")
    parser.add_argument("--events-out", required=True,
                        help="Path for the recorded events JSON")
    parser.add_argument("--max-events", type=int, default=50000)
    parser.add_argument("--module", default="runner.cli",
                        help="Module to execute as __main__ (default: "
                             "runner.cli; the checker always uses the "
                             "default)")
    args, rest = parser.parse_known_args(argv)
    if rest and rest[0] == "--":
        rest = rest[1:]
    _MAX_EVENTS = args.max_events

    started_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    sys.addaudithook(_audit_hook)

    # Make the repo root importable exactly as `python -m` from repo root
    # would (script invocation puts scripts/ at sys.path[0] instead).
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)

    # Mirror `python -m runner.cli ...`: argv[0] is replaced by runpy with the
    # module's real path; argv[1:] is what the CLI's argparse sees.
    sys.argv = ["runner/cli.py"] + list(rest)

    exit_code = 0
    error = None
    try:
        runpy.run_module(args.module, run_name="__main__", alter_sys=True)
    except SystemExit as exc:
        code = exc.code
        if code is None:
            exit_code = 0
        elif isinstance(code, int):
            exit_code = code
        else:
            exit_code = 1
            error = f"SystemExit with non-int code: {code!r}"
    except BaseException as exc:  # engine crash: record and exit non-zero
        exit_code = 1
        error = f"{type(exc).__name__}: {exc}"
    finally:
        truncated = len(_EVENTS) >= _MAX_EVENTS
        try:
            dump_events(args.events_out, started_utc, list(rest), truncated,
                        exit_code, error)
        except Exception as dump_exc:  # pragma: no cover - last-resort guard
            print(f"[safety-wrapper] FATAL: could not dump events: "
                  f"{dump_exc}", file=sys.stderr)
            return 2
    if error:
        print(f"[safety-wrapper] engine raised: {error}", file=sys.stderr)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())

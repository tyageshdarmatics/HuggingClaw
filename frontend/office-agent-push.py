#!/usr/bin/env python3
"""
Helsing's Office - Agent Status active push script

usage:
1. Fill in the following JOIN_KEY(The one-shot you got from Helsing join key)
2. fill in AGENT_NAME(the name you want to be displayed in the office)
3. run:python office-agent-push.py
4. The script will automatically join(first run) and then every 30s Push your current status to Heising's office once
"""

import json
import os
import time
import sys
from datetime import datetime

# === Information you need to fill in ===
JOIN_KEY = ""   # Required: your one-time join key
AGENT_NAME = "" # Required: Your name in the office
OFFICE_URL = "https://office.hyacinth.im"  # Haixin office address (generally no need to change)

# === Push configuration ===
PUSH_INTERVAL_SECONDS = 15  # Push every few seconds (more real-time)
STATUS_ENDPOINT = "/status"
JOIN_ENDPOINT = "/join-agent"
PUSH_ENDPOINT = "/agent-push"

# Automatic status guard: When the local status file does not exist or has not been updated for a long time, it will automatically restore idle,avoid“Fake at work”
STALE_STATE_TTL_SECONDS = int(os.environ.get("OFFICE_STALE_STATE_TTL", "600"))

# Local state storage (remember last join Got it agentId)
STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "office-agent-state.json")

# Read local machine first OpenClaw Workspace status file (more relevant AGENTS.md workflow)
# Supports automatic discovery to reduce the cost of manual configuration of the other party.
DEFAULT_STATE_CANDIDATES = [
    "/root/.openclaw/workspace/Star-Office-UI/state.json",  # Current repository (case accurate)
    "/root/.openclaw/workspace/star-office-ui/state.json",  # history/Compatibility path
    "/root/.openclaw/workspace/state.json",
    os.path.join(os.getcwd(), "state.json"),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "state.json"),
]

# If the other party is local /status Authentication is required, which can be filled in here token(or via environment variables OFFICE_LOCAL_STATUS_TOKEN)
LOCAL_STATUS_TOKEN = os.environ.get("OFFICE_LOCAL_STATUS_TOKEN", "")
LOCAL_STATUS_URL = os.environ.get("OFFICE_LOCAL_STATUS_URL", "http://127.0.0.1:19000/status")
# Optional: Directly specify the local state file path (the simplest solution: bypass /status authentication)
LOCAL_STATE_FILE = os.environ.get("OFFICE_LOCAL_STATE_FILE", "")
VERBOSE = os.environ.get("OFFICE_VERBOSE", "0") in {"1", "true", "TRUE", "yes", "YES"}


def load_local_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "agentId": None,
        "joined": False,
        "joinKey": JOIN_KEY,
        "agentName": AGENT_NAME
    }


def save_local_state(data):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def normalize_state(s):
    """Compatible with different local status words and mapped to office identification status."""
    s = (s or "").strip().lower()
    if s in {"writing", "researching", "executing", "syncing", "error", "idle"}:
        return s
    if s in {"working", "busy", "write"}:
        return "writing"
    if s in {"run", "running", "execute", "exec"}:
        return "executing"
    if s in {"research", "search"}:
        return "researching"
    if s in {"sync"}:
        return "syncing"
    return "idle"


def map_detail_to_state(detail, fallback_state="idle"):
    """when only detail When , use keywords to infer the status (close to AGENTS.md office area logic)."""
    d = (detail or "").lower()
    if any(k in d for k in ["Report an error", "error", "bug", "abnormal", "Call the police"]):
        return "error"
    if any(k in d for k in ["synchronous", "sync", "backup"]):
        return "syncing"
    if any(k in d for k in ["Research", "research", "search", "Check information"]):
        return "researching"
    if any(k in d for k in ["implement", "run", "advance", "processing tasks", "at work", "writing"]):
        return "writing"
    if any(k in d for k in ["Standby", "rest", "idle", "Finish", "done"]):
        return "idle"
    return fallback_state


def _state_age_seconds(data):
    try:
        ts = (data or {}).get("updated_at")
        if not ts:
            return None
        dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        if dt.tzinfo is not None:
            from datetime import timezone
            return (datetime.now(timezone.utc) - dt.astimezone(timezone.utc)).total_seconds()
        return (datetime.now() - dt).total_seconds()
    except Exception:
        return None


def fetch_local_status():
    """Read local status:
    1) priority state.json(conform to AGENTS.md: task forward writing, cut after completion idle)
    2) Secondly try local HTTP /status
    3) at last fallback idle

    Extra anti-shake: If the local status update time exceeds STALE_STATE_TTL_SECONDS, automatically regarded as idle.
    """
    # 1) read local state.json(Read the explicitly specified path first, then automatically discover it)
    candidate_files = []
    if LOCAL_STATE_FILE:
        candidate_files.append(LOCAL_STATE_FILE)
    for fp in DEFAULT_STATE_CANDIDATES:
        if fp not in candidate_files:
            candidate_files.append(fp)

    for fp in candidate_files:
        try:
            if fp and os.path.exists(fp):
                with open(fp, "r", encoding="utf-8") as f:
                    data = json.load(f)

                    # only accept“status file”structure; avoid mistakes office-agent-state.json(caching only agentId) when the status source
                    if not isinstance(data, dict):
                        continue
                    has_state = "state" in data
                    has_detail = "detail" in data
                    if (not has_state) and (not has_detail):
                        continue

                    state = normalize_state(data.get("state", "idle"))
                    detail = data.get("detail", "") or ""
                    # detail Correct the error from the bottom to the bottom to ensure“Work/rest/Call the police”Can land correctly
                    state = map_detail_to_state(detail, fallback_state=state)

                    # Prevent the status file from being stuck in the status file after it has not been updated for a long time working state
                    age = _state_age_seconds(data)
                    if age is not None and age > STALE_STATE_TTL_SECONDS:
                        state = "idle"
                        detail = f"Local status exceeds{STALE_STATE_TTL_SECONDS}sNot updated, will automatically return to standby"

                    if VERBOSE:
                        print(f"[status-source:file] path={fp} state={state} detail={detail[:60]}")
                    return {"state": state, "detail": detail}
        except Exception:
            pass

    # 2) try local /status(Authentication may be required)
    try:
        import requests
        headers = {}
        if LOCAL_STATUS_TOKEN:
            headers["Authorization"] = f"Bearer {LOCAL_STATUS_TOKEN}"
        r = requests.get(LOCAL_STATUS_URL, headers=headers, timeout=5)
        if r.status_code == 200:
            data = r.json()
            state = normalize_state(data.get("state", "idle"))
            detail = data.get("detail", "") or ""
            state = map_detail_to_state(detail, fallback_state=state)

            age = _state_age_seconds(data)
            if age is not None and age > STALE_STATE_TTL_SECONDS:
                state = "idle"
                detail = f"local/status Exceed{STALE_STATE_TTL_SECONDS}sNot updated, will automatically return to standby"

            if VERBOSE:
                print(f"[status-source:http] url={LOCAL_STATUS_URL} state={state} detail={detail[:60]}")
            return {"state": state, "detail": detail}
        # if 401, indicating the need token
        if r.status_code == 401:
            return {"state": "idle", "detail": "local/statusAuthentication required (401), please set OFFICE_LOCAL_STATUS_TOKEN"}
    except Exception:
        pass

    # 3) default fallback
    if VERBOSE:
        print("[status-source:fallback] state=idle detail=On call")
    return {"state": "idle", "detail": "On call"}


def do_join(local):
    import requests
    payload = {
        "name": local.get("agentName", AGENT_NAME),
        "joinKey": local.get("joinKey", JOIN_KEY),
        "state": "idle",
        "detail": "Just joined"
    }
    r = requests.post(f"{OFFICE_URL}{JOIN_ENDPOINT}", json=payload, timeout=10)
    if r.status_code in (200, 201):
        data = r.json()
        if data.get("ok"):
            local["joined"] = True
            local["agentId"] = data.get("agentId")
            save_local_state(local)
            print(f"✅ Has joined Heising's office,agentId={local['agentId']}")
            return True
    print(f"❌ Join failed:{r.text}")
    return False


def do_push(local, status_data):
    import requests
    payload = {
        "agentId": local.get("agentId"),
        "joinKey": local.get("joinKey", JOIN_KEY),
        "state": status_data.get("state", "idle"),
        "detail": status_data.get("detail", ""),
        "name": local.get("agentName", AGENT_NAME)
    }
    r = requests.post(f"{OFFICE_URL}{PUSH_ENDPOINT}", json=payload, timeout=10)
    if r.status_code in (200, 201):
        data = r.json()
        if data.get("ok"):
            area = data.get("area", "breakroom")
            print(f"✅ Status synchronized, current region={area}")
            return True

    # 403/404:reject/Remove → Stop pushing
    if r.status_code in (403, 404):
        msg = ""
        try:
            msg = (r.json() or {}).get("msg", "")
        except Exception:
            msg = r.text
        print(f"⚠️  Access denied or room moved ({r.status_code}), stop pushing:{msg}")
        local["joined"] = False
        local["agentId"] = None
        save_local_state(local)
        sys.exit(1)

    print(f"⚠️  Push failed:{r.text}")
    return False


def main():
    local = load_local_state()

    # First confirm whether the configuration is complete
    if not JOIN_KEY or not AGENT_NAME:
        print("❌ Please fill in at the beginning of the script first JOIN_KEY and AGENT_NAME")
        sys.exit(1)

    # If not before join,First join
    if not local.get("joined") or not local.get("agentId"):
        ok = do_join(local)
        if not ok:
            sys.exit(1)

    # Continuous push
    print(f"🚀 Start continuous push status, interval={PUSH_INTERVAL_SECONDS}Second")
    print("🧭 State logic: on task→work area; standby/Finish→rest area; abnormal→bugdistrict")
    print("🔐 If local /status return Unauthorized(401), please set environment variables:OFFICE_LOCAL_STATUS_TOKEN or OFFICE_LOCAL_STATUS_URL")
    try:
        while True:
            try:
                status_data = fetch_local_status()
                do_push(local, status_data)
            except Exception as e:
                print(f"⚠️  Push exception:{e}")
            time.sleep(PUSH_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        print("\n👋 Stop pushing")
        sys.exit(0)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Lab 4 Starter — Coordinator (2PC/3PC) (HTTP, standard library only)
===================================================================

Endpoints (JSON):
- POST /tx/start   {"txid":"TX1","op":{"type":"SET","key":"x","value":"5"}, "protocol":"2PC"|"3PC"}
- GET  /status

Participants are addressed by base URL (e.g., http://10.0.1.12:8001).

Failure injection:
- Kill the coordinator between phases to demonstrate blocking (2PC).
"""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib import request
import argparse
import json
import os
import threading
import time
from typing import Dict, Any, List, Optional, Tuple

lock = threading.Lock()

NODE_ID: str = ""
PORT: int = 8000
PARTICIPANTS: List[str] = []
TIMEOUT_S: float = 2.0
WAL_PATH: Optional[str] = None
MAX_RETRIES: int = 3

TX: Dict[str, Dict[str, Any]] = {}

def jdump(obj: Any) -> bytes:
    return json.dumps(obj).encode("utf-8")

def jload(b: bytes) -> Any:
    return json.loads(b.decode("utf-8"))

def wal_append(line: str) -> None:
    if not WAL_PATH:
        return
    with open(WAL_PATH, "a", encoding="utf-8") as f:
        f.write(line.rstrip("\n") + "\n")
        f.flush()
        os.fsync(f.fileno())

def retry_post_json(url: str, payload: dict, max_retries: int = MAX_RETRIES, timeout: float = TIMEOUT_S) -> Tuple[bool, Optional[dict]]:
    """Retry POST request with exponential backoff"""
    for attempt in range(max_retries):
        try:
            _, resp = post_json(url, payload, timeout)
            return True, resp
        except Exception:
            if attempt < max_retries - 1:
                time.sleep(0.5 * (attempt + 1))  # Exponential backoff
            else:
                return False, None
    return False, None

def post_json(url: str, payload: dict, timeout: float = TIMEOUT_S) -> Tuple[int, dict]:
    data = jdump(payload)
    req = request.Request(url, data=data, headers={"Content-Type":"application/json"}, method="POST")
    with request.urlopen(req, timeout=timeout) as resp:
        return resp.status, jload(resp.read())

def two_pc(txid: str, op: dict) -> dict:
    print(f"[{NODE_ID}] {txid} PREPARE")
    with lock:
        TX[txid] = {
            "txid": txid, "protocol": "2PC", "state": "PREPARE_SENT",
            "op": op, "votes": {}, "decision": None,
            "participants": list(PARTICIPANTS), "ts": time.time()
        }
    wal_append(f"{txid} PREPARE_SENT {json.dumps(op)}")

    votes = {}
    all_yes = True

    for p in PARTICIPANTS:
        try:
            _, resp = post_json(p.rstrip("/") + "/prepare", {"txid": txid, "op": op})
            vote = str(resp.get("vote", "NO")).upper()
            votes[p] = vote
            if vote != "YES":
                all_yes = False
        except Exception:
            votes[p] = "NO_TIMEOUT"
            all_yes = False

    decision = "COMMIT" if all_yes else "ABORT"
    with lock:
        TX[txid]["votes"] = votes
        TX[txid]["decision"] = decision
        TX[txid]["state"] = f"{decision}_SENT"
    wal_append(f"{txid} DECISION {decision} {json.dumps(votes)}")
    print(f"[{NODE_ID}] {txid} GLOBAL-{decision}")

    endpoint = "/commit" if decision == "COMMIT" else "/abort"
    for p in PARTICIPANTS:
        success, _ = retry_post_json(p.rstrip("/") + endpoint, {"txid": txid})
        if not success:
            print(f"[{NODE_ID}] {txid} Failed to send {decision} to {p} after retries")

    with lock:
        TX[txid]["state"] = "DONE"
    wal_append(f"{txid} DONE")

    return {"ok": True, "txid": txid, "protocol": "2PC", "decision": decision, "votes": votes}

def three_pc(txid: str, op: dict) -> dict:
    print(f"[{NODE_ID}] {txid} CAN_COMMIT")
    with lock:
        TX[txid] = {
            "txid": txid, "protocol": "3PC", "state": "CAN_COMMIT_SENT",
            "op": op, "votes": {}, "decision": None,
            "participants": list(PARTICIPANTS), "ts": time.time()
        }
    wal_append(f"{txid} CAN_COMMIT_SENT {json.dumps(op)}")

    votes = {}
    all_yes = True
    for p in PARTICIPANTS:
        try:
            _, resp = post_json(p.rstrip("/") + "/can_commit", {"txid": txid, "op": op})
            vote = str(resp.get("vote", "NO")).upper()
            votes[p] = vote
            if vote != "YES":
                all_yes = False
        except Exception:
            votes[p] = "NO_TIMEOUT"
            all_yes = False

    with lock:
        TX[txid]["votes"] = votes
    wal_append(f"{txid} CAN_COMMIT_VOTES {json.dumps(votes)}")

    if not all_yes:
        with lock:
            TX[txid]["decision"] = "ABORT"
            TX[txid]["state"] = "ABORT_SENT"
        wal_append(f"{txid} DECISION ABORT")
        print(f"[{NODE_ID}] {txid} GLOBAL-ABORT")
        for p in PARTICIPANTS:
            success, _ = retry_post_json(p.rstrip("/") + "/abort", {"txid": txid})
            if not success:
                print(f"[{NODE_ID}] {txid} Failed to send ABORT to {p} after retries")
        with lock:
            TX[txid]["state"] = "DONE"
        wal_append(f"{txid} DONE")
        return {"ok": True, "txid": txid, "protocol": "3PC", "decision": "ABORT", "votes": votes}

    with lock:
        TX[txid]["decision"] = "PRECOMMIT"
        TX[txid]["state"] = "PRECOMMIT_SENT"
    wal_append(f"{txid} PRECOMMIT_SENT")
    print(f"[{NODE_ID}] {txid} PRECOMMIT")

    # Retry logic for precommit phase
    for p in PARTICIPANTS:
        success, _ = retry_post_json(p.rstrip("/") + "/precommit", {"txid": txid})
        if not success:
            print(f"[{NODE_ID}] {txid} Failed to send PRECOMMIT to {p} after retries")

    with lock:
        TX[txid]["decision"] = "COMMIT"
        TX[txid]["state"] = "DOCOMMIT_SENT"
    wal_append(f"{txid} DOCOMMIT_SENT")
    print(f"[{NODE_ID}] {txid} DOCOMMIT")

    for p in PARTICIPANTS:
        success, _ = retry_post_json(p.rstrip("/") + "/commit", {"txid": txid})
        if not success:
            print(f"[{NODE_ID}] {txid} Failed to send COMMIT to {p} after retries")

    with lock:
        TX[txid]["state"] = "DONE"
    wal_append(f"{txid} DONE")

    return {"ok": True, "txid": txid, "protocol": "3PC", "decision": "COMMIT", "votes": votes}

class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, obj: dict):
        data = jdump(obj)
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path.startswith("/status"):
            with lock:
                self._send(200, {"ok": True, "node": NODE_ID, "port": PORT, "participants": PARTICIPANTS, "tx": TX})
            return
        self._send(404, {"ok": False, "error": "not found"})

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            body = jload(raw)
        except Exception:
            self._send(400, {"ok": False, "error": "invalid json"})
            return

        if self.path == "/tx/start":
            txid = str(body.get("txid", "")).strip()
            op = body.get("op", None)
            protocol = str(body.get("protocol", "2PC")).upper()

            if not txid or not isinstance(op, dict):
                self._send(400, {"ok": False, "error": "txid and op required"})
                return
            if protocol not in ("2PC", "3PC"):
                self._send(400, {"ok": False, "error": "protocol must be 2PC or 3PC"})
                return

            if protocol == "2PC":
                result = two_pc(txid, op)
            else:
                result = three_pc(txid, op)

            self._send(200, result)
            return

        self._send(404, {"ok": False, "error": "not found"})

    def log_message(self, fmt, *args):
        return

def main():
    global NODE_ID, PORT, PARTICIPANTS, WAL_PATH
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", default="COORD")
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--participants", required=True, help="Comma-separated participant base URLs (http://IP:PORT)")
    ap.add_argument("--wal", default="", help="Optional WAL path for coordinator decisions")
    args = ap.parse_args()

    NODE_ID = args.id
    PORT = args.port
    PARTICIPANTS = [p.strip() for p in args.participants.split(",") if p.strip()]
    WAL_PATH = args.wal.strip() or None

    # WAL replay on startup for recovery
    if WAL_PATH and os.path.exists(WAL_PATH):
        print(f"[{NODE_ID}] Replaying coordinator WAL from {WAL_PATH}")
        with open(WAL_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split(" ", 2)
                if len(parts) < 2:
                    continue
                txid = parts[0]
                action = parts[1]
                
                if action == "DECISION":
                    # Parse: TX123 DECISION COMMIT {"http://...": "YES", ...}
                    if len(parts) >= 3:
                        decision_and_votes = parts[2].split(" ", 1)
                        if len(decision_and_votes) >= 1:
                            decision = decision_and_votes[0]
                            with lock:
                                if txid not in TX:
                                    TX[txid] = {
                                        "txid": txid,
                                        "protocol": "2PC",  # Default, could be improved
                                        "state": f"{decision}_SENT",
                                        "decision": decision,
                                        "votes": {},
                                        "ts": time.time()
                                    }
                                else:
                                    TX[txid]["decision"] = decision
                                    TX[txid]["state"] = f"{decision}_SENT"
        print(f"[{NODE_ID}] Coordinator WAL replay complete. Recovered {len(TX)} transactions.")

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"[{NODE_ID}] Coordinator listening on {args.host}:{args.port} participants={PARTICIPANTS}")
    server.serve_forever()

if __name__ == "__main__":
    main()

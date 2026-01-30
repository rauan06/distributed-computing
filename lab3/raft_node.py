#!/usr/bin/env python3
"""
Raft-Lite: Leader Election (Educational)
"""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib import request
import argparse
import json
import threading
import time
import random
from enum import Enum
from typing import List, Optional

# ─────────────────────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────────────────────

ELECTION_TIMEOUT_MIN = 150  # ms
ELECTION_TIMEOUT_MAX = 300  # ms
HEARTBEAT_INTERVAL = 50     # ms

# ─────────────────────────────────────────────────────────────
# State
# ─────────────────────────────────────────────────────────────

class Role(Enum):
    FOLLOWER = "follower"
    CANDIDATE = "candidate"
    LEADER = "leader"

lock = threading.Lock()

NODE_ID: str = ""
PEERS: List[str] = []

current_term: int = 0
voted_for: Optional[str] = None

role: Role = Role.FOLLOWER
current_leader: Optional[str] = None
last_heartbeat: float = 0.0

# ─────────────────────────────────────────────────────────────
# Utils
# ─────────────────────────────────────────────────────────────

def random_timeout() -> float:
    return random.randint(ELECTION_TIMEOUT_MIN, ELECTION_TIMEOUT_MAX) / 1000.0

def log(msg: str):
    print(f"[{NODE_ID}] term={current_term} role={role.value} | {msg}")

# ─────────────────────────────────────────────────────────────
# Transitions
# ─────────────────────────────────────────────────────────────

def become_follower(term: int, leader: Optional[str] = None):
    global current_term, voted_for, role, current_leader, last_heartbeat
    with lock:
        if term > current_term:
            current_term = term
            voted_for = None
        role = Role.FOLLOWER
        current_leader = leader
        last_heartbeat = time.time()
    log(f"became FOLLOWER (leader={leader})")

def become_candidate():
    global current_term, voted_for, role, current_leader, last_heartbeat
    with lock:
        role = Role.CANDIDATE
        current_term += 1
        voted_for = NODE_ID
        current_leader = None
        last_heartbeat = time.time()
    log("became CANDIDATE")

def become_leader():
    global role, current_leader
    with lock:
        role = Role.LEADER
        current_leader = NODE_ID
    log("became LEADER")

# ─────────────────────────────────────────────────────────────
# Vote RPC
# ─────────────────────────────────────────────────────────────

def handle_vote_request(term: int, candidate_id: str) -> dict:
    global current_term, voted_for, role, last_heartbeat, current_leader

    with lock:
        if term < current_term:
            return {"term": current_term, "vote_granted": False}

        if term > current_term:
            current_term = term
            voted_for = None
            role = Role.FOLLOWER
            current_leader = None

        if voted_for is None or voted_for == candidate_id:
            voted_for = candidate_id
            last_heartbeat = time.time()
            return {"term": current_term, "vote_granted": True}

        return {"term": current_term, "vote_granted": False}

def request_votes() -> int:
    global current_term
    votes = 1
    my_term = current_term

    for peer in PEERS:
        try:
            url = peer.rstrip("/") + "/vote"
            payload = json.dumps({
                "term": my_term,
                "candidate_id": NODE_ID
            }).encode()

            req = request.Request(
                url, data=payload,
                headers={"Content-Type": "application/json"},
                method="POST"
            )

            with request.urlopen(req, timeout=0.15) as resp:
                data = json.loads(resp.read())

                if data["term"] > my_term:
                    become_follower(data["term"])
                    return votes

                if data["vote_granted"]:
                    votes += 1

        except Exception:
            pass

    return votes

# ─────────────────────────────────────────────────────────────
# Heartbeat RPC
# ─────────────────────────────────────────────────────────────

def handle_heartbeat(term: int, leader_id: str) -> dict:
    global current_term, role, current_leader, last_heartbeat, voted_for

    with lock:
        if term < current_term:
            return {"term": current_term, "success": False}

        if term > current_term:
            current_term = term
            voted_for = None

        role = Role.FOLLOWER
        current_leader = leader_id
        last_heartbeat = time.time()
        return {"term": current_term, "success": True}

def send_heartbeats():
    my_term = current_term
    for peer in PEERS:
        try:
            url = peer.rstrip("/") + "/heartbeat"
            payload = json.dumps({
                "term": my_term,
                "leader_id": NODE_ID
            }).encode()

            req = request.Request(
                url, data=payload,
                headers={"Content-Type": "application/json"},
                method="POST"
            )

            with request.urlopen(req, timeout=0.1) as resp:
                data = json.loads(resp.read())
                if data["term"] > my_term:
                    become_follower(data["term"])
                    return
        except Exception:
            pass

# ─────────────────────────────────────────────────────────────
# Background loops
# ─────────────────────────────────────────────────────────────

def election_loop():
    global last_heartbeat
    timeout = random_timeout()
    last_heartbeat = time.time()

    while True:
        time.sleep(0.01)

        with lock:
            r = role
            elapsed = time.time() - last_heartbeat

        if r == Role.LEADER:
            continue

        if r == Role.FOLLOWER and elapsed > timeout:
            become_candidate()
            timeout = random_timeout()

        if r == Role.CANDIDATE:
            votes = request_votes()
            majority = (len(PEERS) + 1) // 2 + 1

            log(f"got {votes}/{len(PEERS)+1} votes (need {majority})")

            if votes >= majority:
                become_leader()
            else:
                time.sleep(random_timeout())
                with lock:
                    if role == Role.CANDIDATE:
                        become_candidate()

def leader_loop():
    while True:
        time.sleep(HEARTBEAT_INTERVAL / 1000)
        with lock:
            if role != Role.LEADER:
                continue
        send_heartbeats()

# ─────────────────────────────────────────────────────────────
# HTTP
# ─────────────────────────────────────────────────────────────

class Handler(BaseHTTPRequestHandler):

    def _send(self, code: int, obj: dict):
        data = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/status":
            with lock:
                self._send(200, {
                    "node": NODE_ID,
                    "term": current_term,
                    "role": role.value,
                    "leader": current_leader,
                    "voted_for": voted_for,
                    "peers": PEERS
                })
            return
        self._send(404, {"error": "not found"})

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length) or "{}")

        if self.path == "/vote":
            res = handle_vote_request(body["term"], body["candidate_id"])
            self._send(200, res)
            return

        if self.path == "/heartbeat":
            res = handle_heartbeat(body["term"], body["leader_id"])
            self._send(200, res)
            return

        self._send(404, {"error": "not found"})

    def log_message(self, *_):
        pass

# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────

def main():
    global NODE_ID, PEERS, last_heartbeat

    p = argparse.ArgumentParser()
    p.add_argument("--id", required=True)
    p.add_argument("--host", default="0.0.0.0")
    p.add_argument("--port", type=int, required=True)
    p.add_argument("--peers", default="")
    args = p.parse_args()

    NODE_ID = args.id
    PEERS = [p for p in args.peers.split(",") if p]
    last_heartbeat = time.time()

    threading.Thread(target=election_loop, daemon=True).start()
    threading.Thread(target=leader_loop, daemon=True).start()

    log(f"starting on {args.host}:{args.port} peers={PEERS}")

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    server.serve_forever()

if __name__ == "__main__":
    main()

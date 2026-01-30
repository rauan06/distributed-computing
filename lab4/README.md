## Lab 4 – Distributed Transactions (2PC / 3PC)

This lab implements a simple distributed transaction system using a **Coordinator** and multiple **Participants**, supporting both **Two-Phase Commit (2PC)** and **Three-Phase Commit (3PC)** protocols.

All source code is in `Distributed_Transactions_2PC_3PC_Starter_Python/`.

### 1. Environment

- **Language**: Python 3
- **Dependencies**: standard library only (no external packages)

### 2. Files

- `coordinator.py` – Coordinator HTTP server (2PC + 3PC, WAL, retries)
- `participant.py` – Participant HTTP server (WAL, recovery)
- `client.py` – Simple CLI client to start transactions and query status

### 3. How to Run (Single Machine Example)

From the `Distributed_Transactions_2PC_3PC_Starter_Python/` directory:

```bash
# Terminal 1 – Participant B
python3 participant.py --id B --port 8001 --wal /tmp/participant_B.wal

# Terminal 2 – Participant C
python3 participant.py --id C --port 8002 --wal /tmp/participant_C.wal

# Terminal 3 – Coordinator
python3 coordinator.py \
  --id COORD \
  --port 8002 \
  --participants http://127.0.0.1:8001,http://127.0.0.1:8002 \
  --wal /tmp/coordinator.wal
```

### 4. Starting Transactions

From any terminal:

```bash
cd Distributed_Transactions_2PC_3PC_Starter_Python

# 2PC transaction
python3 client.py --coord http://127.0.0.1:8002 start TX1 2PC SET x 5

# 3PC transaction
python3 client.py --coord http://127.0.0.1:8002 start TX2 3PC SET y 9

# Coordinator status
python3 client.py --coord http://127.0.0.1:8002 status
```

### 5. Failure Scenarios to Demonstrate

- **2PC blocking**:  
  After `PREPARE` (participants in `READY`), kill the coordinator process.  
  Participants block waiting for a decision.

- **Participant crash before vote**:  
  Kill one participant before it replies to `PREPARE`.  
  Coordinator times out and aborts the transaction.

- **3PC non-blocking**:  
  After `PRECOMMIT` (participants in `PRECOMMIT`), kill the coordinator.  
  Participants can safely complete the commit based on their state.


# DRUNIX Pay — Resilient Payments for Low-Connectivity India
**DRUNIX Hackathon in collaboration with Citi | Domain: Financial Inclusion**
*Built on the DRUNIX Platform*

---

## 1. Executive Summary & Problem Statement
In tier-2/3 Indian cities, rural agricultural mandis, and deep underground transport corridors (e.g. metro stations, basements), digital payments frequently encounter network degradation:
- **Payment Failures & Double Debits**: Customers retry stalled payments, resulting in duplicate withdrawals.
- **Transaction Uncertainty**: Neither customer nor merchant knows whether funds were debited or credited.
- **Merchant Reluctance**: Merchants revert to cash due to unreliable payment confirmation.

### The Innovation:
DRUNIX Pay does **not** treat offline mode as an emergency toggle. Instead, it introduces an end-to-end **resilience layer**:
```
PAY NOW  →  SECURELY STORE  →  VERIFY  →  SYNC  →  RECONCILE
```
> *"Offline is not the feature. Resilience is the feature."*

---

## 2. Core Architecture & Components

```
+-----------------------------------------------------------------------------------+
|                              CUSTOMER MOBILE APP                                  |
|   [₹1,850 Offline Balance] [Scan & Pay] [Tap & Pay] [Offline Mode Active]         |
+----------------------------------------+------------------------------------------+
                                         |
                       +-----------------+-----------------+
                       | (Online)                          | (Offline / Limited)
                       v                                   v
             [ Standard Direct UPI ]             [ OFFLINE RESILIENCE ENGINE ]
                       |                                   |
                       |                     +-------------+-------------+
                       |                     | Local Secure Vault        |
                       |                     | Nonce + HMAC-SHA256 Hash  |
                       |                     | 8-Factor Risk Scoring     |
                       |                     | Duplicate Detection Radar |
                       |                     +-------------+-------------+
                       |                                   |
                       |                                   v
                       |                     [ QUEUED FOR BACKGROUND SYNC ]
                       |                                   |
                       +-----------------+-----------------+
                                         |
                                         v (When Connectivity Restored)
                      [ DRUNIX AUTO-SYNC ENGINE ]
                      (Exponential Backoff: Retry 1 -> Retry 2 -> Retry 3)
                                         |
                                         v
                    [ SERVER RECONCILIATION ENGINE ]
                    - Local Digest vs Server Digest
                    - MATCH -> SETTLED
                    - MISMATCH -> FRAUD INVESTIGATION
                    - DUPLICATE -> REJECT SECOND TXN
                                         |
                                         v
                     [ MOCK BANKING & NPCI SWITCH ]
```

### Key Pillars:
1. **Customer App (Mobile Experience)**:
   - Available Offline Balance: ₹1,850 (out of ₹5,000 regulatory capacity)
   - Dynamic Connectivity Badge: 🟢 ONLINE, 🟠 LIMITED (780ms, 34% packet loss), 🔴 OFFLINE
   - Transparent feature disabling (e.g. wire transfers requiring live core banking are disabled offline; eligible micro-payments ≤ ₹2,000 continue seamlessly)
2. **Local Cryptographic Vault**:
   - Hardware-backed Android Keystore / iOS Secure Enclave simulation
   - Nonce generation + deterministic HMAC-SHA256 tamper-evident digest
   - Zero storage of raw banking PINs or credentials
3. **Duplicate Payment Protection**:
   - Multi-variable interception: Same merchant + Same amount + Same device + Under 180s interval
   - Contextual modal: *“We found a recent offline payment with the same merchant and amount”* with `[VIEW EXISTING]` and `[CONTINUE ANYWAY]`
4. **Merchant POS Terminal & Digital Receipt**:
   - Real-time sales telemetry: Today's Sales (₹24,850), Offline Sales (₹8,450), Pending Sync (3), Duplicates Blocked (2)
   - Instant cryptographic offline receipt with tokenized QR validation
5. **Reconciliation Engine**:
   - Compares client vault record vs central server ledger
   - Categorizes outcomes into: `MATCH`, `MISMATCH`, `DUPLICATE`, and `UNKNOWN`
6. **Judge Simulation Control Panel**:
   - 1-click execution for Internet Loss, Internet Restore, Duplicate Payment, Sync Failure with Backoff, Timeout, and Hash Mismatch

---

## 3. The 3-Minute Scripted Demo (8 Scenes)

| Scene | Action | Observed Result |
|---|---|---|
| **Scene 1: Customer Online** | Initialize app | Balance shows ₹1,850 on 4G network |
| **Scene 2: Switch to Offline** | Click `[🔴 OFFLINE]` | Status updates to Offline Mode Active; eligible payments stay enabled |
| **Scene 3: Pay ₹450 to Sharma Store** | Scan QR & confirm | Risk engine outputs LOW RISK (12/100); records Txn `DRX-2026-001284` in vault; balance updates to ₹1,400 |
| **Scene 4: Duplicate Attempt** | Click Pay again | Warning modal intercepts: *“⚠ POSSIBLE DUPLICATE PAYMENT: Existing txn ₹450 waiting for sync”* |
| **Scene 5: Restore Connectivity** | Click `[🟢 ONLINE]` | Auto-sync triggers; verifies HMAC-SHA256 token against server ledger |
| **Scene 6: Merchant Dashboard** | Switch to Merchant Tab | Sharma General Store terminal marks ₹450 as Reconciled; total sales updated |
| **Scene 7: Transaction Audit** | View State Machine | Lifecycle audited: `CREATED → QUEUED → SYNCED → RECONCILED → SETTLED` |
| **Scene 8: Architecture Proof** | View Architecture Tab | Demonstrates resilience shim integration with mock Citi/NPCI switch |

---

## 4. API Reference

- `GET /connectivity/status`: Returns current network telemetry (latency, packet loss, operational recommendation).
- `POST /connectivity/set`: Switches connectivity state between `ONLINE`, `LIMITED`, and `OFFLINE`.
- `POST /risk/evaluate`: Runs 8 pre-authorization risk checks and outputs risk score (0-100).
- `POST /payment/offline`: Stores transaction in local vault, deducts offline balance, and queues for sync.
- `POST /payment/initiate`: Standard online gateway routing.
- `GET /payment/{transaction_id}`: Retrieves transaction details with cryptographic hash proofs.
- `POST /sync`: Executes batch synchronization of queued transactions with exponential backoff handling.
- `POST /reconcile`: Runs backend ledger matching (MATCH, MISMATCH, DUPLICATE).
- `GET /merchant/dashboard`: Returns real-time POS metrics and transaction stream for merchants.
- `GET /vault/records`: Inspects client-side secure enclave metadata and integrity checks.
- `GET /metrics/observability`: Returns prototype impact metrics and chart data.
- `POST /demo/action`: Triggers 1-click judge simulation scenarios.

---

## 5. Prototype Impact Metrics
*(Prototype simulation metrics — for demonstration only)*
- **Offline Transaction Continuity**: 98%
- **Duplicate Prevention Rate**: 94%
- **Automatic Reconciliation Rate**: 97%
- **Average Sync Time**: < 5 seconds
- **Exception Detection Rate**: 99%

---

## 6. Regulatory & Production Positioning
> *This prototype demonstrates a simulated resilience layer for low-connectivity payments. Actual deployment would require integration with authorized payment system participants, applicable RBI/NPCI requirements, security certification, transaction limits, authentication requirements, and production-grade reconciliation. Built on the DRUNIX Platform in collaboration with Citi for the DRUNIX Hackathon.*

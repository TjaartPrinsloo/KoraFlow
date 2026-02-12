# SOP: Change Management & Deployment

## 1. Purpose
To ensure all changes to the production environment are assessed, approved, and deployed safely to maintain system integrity and validation status (SAHPRA).

## 2. Change Categories

### A. Standard Change (Low Risk)
*   *Examples*: Frontend UI text changes, Report format updates.
*   *Approval*: Peer Review (GitHub Pull Request).
*   *Deployment*: Automated via CI/CD (Pipeline 1).

### B. Normal Change (Medium/High Risk)
*   *Examples*: Database Schema changes, New workflow logic, Permission updates.
*   *Approval*: Change Advisory Board (CAB) / System Owner.
*   *Deployment*: Scheduled maintenance window (Pipeline 2).

### C. Emergency Change
*   *Examples*: Fixing a P1 outage or security breach.
*   *Approval*: Incident Commander / Emergency Approver.
*   *Deployment*: Expedited, with retroactive paperwork file within 24 hours.

---

## 3. The Process (Normal Change)

1.  **RFC (Request for Change)**: Developer creates a ticket describing the change.
2.  **Development**: Code written in a branch.
3.  **Testing**:
    *   Deployed to `Staging`.
    *   QA / User Acceptance Testing (UAT) performed.
    *   Evidence attached to ticket (Screenshots / Logs).
4.  **Approval**: System Owner reviews UAT evidence and approves deployment.
5.  **Deployment**:
    *   Set `ALLOW_PROD_MIGRATE=true` (if DB change).
    *   Trigger Release Pipeline.
    *   Verify Production health.
6.  **Closure**: Ticket closed as "Successful".

---

## 4. Evidence Requirements
For every Normal/Emergency change, we must support:
*   **Traceability**: Git Commit -> Ticket -> Approval.
*   **Validation**: Proof that it worked in Staging.

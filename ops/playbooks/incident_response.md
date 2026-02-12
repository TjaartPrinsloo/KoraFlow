# Incident Response Playbook

## 1. Incident Severity Matrix

| Severity | Definition                           | Response Time (SLA) | Notification |
| :--- | :--- | :--- | :--- |
| **P1 - Critical** | Full system outage OR Potential Data Breach (POPIA). | 15 Minutes | CIO, Compliance Officer |
| **P2 - High** | Core functionality degraded. Workarounds exist. | 1 Hour | Product Owner |
| **P3 - Medium** | Minor bugs, aesthetic issues. | 4 Hours | Lead Developer |

## 2. Core Response Team
*   **Incident Commander (IC)**: [Name/Role] - Makes final decisions.
*   **Tech Lead**: [Name/Role] - Runs technical remediation.
*   **Communications Lead**: [Name/Role] - Handles internal/external comms.

---

## Playbook A: Potential Data Breach (POPIA Alert)
**Trigger**: Unusual data export, leaked credential, public report.

1.  **Stop the Bleeding (Containment)**:
    *   Identify compromised account/service.
    *   IMMEDIATE: Revoke access / disable account.
    *   IMMEDIATE: Isolate affected service (e.g., stop Cloud Run revision).
2.  **Preserve Evidence**:
    *   Do NOT reboot compromised servers if possible (Cloud Run is stateless, so check logs FIRST).
    *   Export Cloud Audit Logs for the timeframe.
    *   Snapshot database.
3.  **Assess Scope**:
    *   Which data subjects were exposed?
    *   Volume of data?
4.  **Notify**:
    *   Notify Responsible Officer (POPIA).
    *   Draft notification to Regulator (must be done "as soon as reasonably possible").

---

## Playbook B: System Outage (Production Down)
**Trigger**: 500 Errors, Monitoring Alerts.

1.  **Check Recent Changes**:
    *   Was code deployed recently? -> **Rollback**.
    *   Was config changed? -> **Revert**.
2.  **Check Infrastructure**:
    *   Cloud SQL status? (CPU, Connections).
    *   Cloud Run status? (Errors, Latency).
3.  **Check Database**:
    *   Is database accessible?
    *   If corrupted -> **Execute PITR (See DR Strategy)**.
4.  **Communicate**:
    *   Update Status Page.
    *   Notify Support Team.

---

## Playbook C: Unauthorized Access Attempt
**Trigger**: Multiple failed logins, API scanning.

1.  **Block Source**:
    *   Add IP to Cloud Armor Denylist (if applicable) or WAF rules.
2.  **Audit User**:
    *   Check `Access Log` in Frappe for user activity.
    *   Check `Audit Log` for any changes made.
3.  **Rotate Credentials**:
    *   Force password reset involved users.
    *   Rotate API Keys if service account compromised.

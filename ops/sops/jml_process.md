# SOP: Joiners, Movers, Leavers (JML) Process

## 1. Purpose
To ensure that access to KoraFlow and related infrastructure is granted, modified, and revoked in a controlled, auditable manner. This SOP is critical for POPIA and SAHPRA compliance.

## 2. Scope
Applies to all employees, contractors, and third parties requiring access to:
*   KoraFlow (Frappe)
*   Google Cloud Platform (GCP)
*   Source Code Repositories

## 3. Roles
*   **Hiring Manager / Supervisor**: Requests access.
*   **System Owner**: Approves access based on role.
*   **IT Administrator**: Executes the technical changes.

---

## 4. Joiners Process (New Access)

1.  **Request**: Manager submits a "New User Request" ticket.
    *   *Required info*: Name, Email, Role (e.g., Medical Practitioner), Start Date.
2.  **Approval**: System Owner approves the request, verifying the role is appropriate (`Least Privilege`).
3.  **Provisioning**:
    *   IT Admin creates User in Frappe.
    *   Assigns **ONLY** the approved Role.
    *   Enforce "Change Password on First Login".
4.  **Notification**: Credentials sent securely to user (e.g., via password manager invite).
5.  **Evidence**: Ticket linked to user profile creation date.

---

## 5. Movers Process (Role Change)

1.  **Request**: Manager submits "Access Change Request".
2.  **Approval**: System Owner approves.
3.  **Execution**:
    *   **REVOKE** old permissions first (if no longer needed).
    *   **GRANT** new permissions.
4.  **Evidence**: Ticket showing the transition.

---

## 6. Leavers Process (Offboarding) - CRITICAL

**Timing**: Must be executed **on or before** the effective termination time.

1.  **Trigger**: HR notifies IT of termination.
2.  **Immediate Action**:
    *   **Frappe**: Set `Enabled` = 0.
    *   **GCP**: Remove IAM bindings.
    *   **Sessions**: Clear all active sessions for the user.
3.  **Verification**: IT Admin replies to HR confirming "All access revoked".
4.  **Evidence**: Ticket closed with timestamp of revocation.

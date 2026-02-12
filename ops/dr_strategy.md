# Backup & Disaster Recovery Strategy

## 1. Objectives (SAHPRA Aligned)
*   **Recovery Point Objective (RPO)**: <= 24 Hours (Maximum data loss acceptable in worst case).
*   **Recovery Time Objective (RTO)**: <= 4 Hours (Maximum downtime acceptable).

## 2. Backup Configuration

### A. Database (Cloud SQL)
*   **Automated Daily Backups**: Enabled. Retained for 35 days.
    *   Window: 02:00 - 06:00 SAST.
    *   Location: Multi-region (EU/US) for durability.
*   **Point-in-Time Recovery (PITR)**: Enabled.
    *   Allows restoring to any second within the retention window (7 days log retention).
    *   Uses Write-Ahead Logs (WAL).
*   **Deletion Protection**: ENABLED on Production. Prevents accidental `terraform destroy`.

### B. File Storage (Google Cloud Storage)
*   **Versioning**: Enabled on all buckets.
*   **Soft Delete**: 7-day retention for deleted objects.

## 3. Disaster Recovery Scenarios

### Scenario 1: Data Corruption (e.g., Bad Migration)
**Action**: Point-in-Time Recovery (PITR).
1.  **Identify Timestamp**: Determine exact time $T$ before corruption.
2.  **Clone Instance**: Create a *new* Cloud SQL instance from the backup at time $T$.
3.  **Verify**: Connect staging app to new instance to verify data.
4.  **Switchover**: Update Application Secrets to point to new DB IP.
5.  **Downtime**: ~20-40 minutes (depends on DB size).

### Scenario 2: Accidental Table Drop / Deletion
**Action**: Restore from Daily Backup.
1.  **Select Backup**: Choose last successful nightly backup.
2.  **Restore**: Restore to a fresh instance.
3.  **Recover Data**: Export missing data and import to Prod (if partial) OR switchover (if full loss).

### Scenario 3: Application Failure (Cloud Run)
**Action**: Rollback Revision.
1.  **Identify**: Check Cloud Run revisions list.
2.  **Rollback**: Click "Manage Traffic" -> Route 100% to previous healthy revision.
3.  **Downtime**: < 1 minute.

## 4. DR Drills
*   **Frequency**: Quarterly.
*   **Method**: In `staging` environment, simulate a data corruption event and perform a PITR restore.
*   **Evidence**: Log the start time, end time, and result for SAHPRA inspection.

# SAHPRA Inspection Pack: Readiness Guide

## 1. Introduction
This document serves as an index for a Regulatory Inspection (SAHPRA/POPIA). When an auditor asks for evidence, refer to the sections below to retrieve it quickly.

**Golden Rule**: Answer only what is asked. Provide evidence, not opinions.

## 2. System Overview
| Item | Evidence Location | Description |
| :--- | :--- | :--- |
| **Architecture** | `infra/` (Terraform) | Infrastructure as Code proves the design is strict. |
| **Network Diagram** | *[To be generated from Terraform]* | Visual representation of VPCs and Subnets. |
| **Data Flow** | `docs/data_flow.md` | (Create if missing) Shows how PHI moves. |

## 3. Access Control (RBAC)
| Item | Evidence |
| :--- | :--- |
| **Policy** | `ops/sops/jml_process.md` | The JML SOP. |
| **Role Matrix** | `apps/koraflow_core/setup/roles.py` | Code definition of roles & permissions. |
| **Active Users** | `Frappe > User Report` | Export list of active users & roles. |
| **Review Proof** | `ops/sops/access_review.md` | Signed quarterly review sheets. |

## 4. Change Management
| Item | Evidence |
| :--- | :--- |
| **Policy** | `ops/sops/change_management.md` | The Change Management SOP. |
| **Traceability** | `git log` | Commit history linked to tickets. |
| **Approval** | GitHub PRs / Jira | Proof of code review and UAT sign-off. |
| **No-Go Zone** | `deploy/safe_migrate.sh` | Proof that Production cannot be migrated easily. |

## 5. Deployment & Operations
| Item | Evidence |
| :--- | :--- |
| **Pipelines** | `.github/workflows/` | CI/CD YAML files showing separation of duties. |
| **Audit Logs** | Google Cloud Logging | Admin Activity + Data Access Logs. |
| **App Logs** | Frappe `Access Log` | View logs for sensitive DocTypes. |

## 6. Business Continuity (DR)
| Item | Evidence |
| :--- | :--- |
| **Policy** | `ops/dr_strategy.md` | RPO/RTO definitions and backup policy. |
| **Backups** | GCP Console Snapshot | Screenshot of automated backup list. |
| **Restores** | *[Drill Report]* | Log of the last quarterly DR drill. |

## 7. Incident Response
| Item | Evidence |
| :--- | :--- |
| **Playbooks** | `ops/playbooks/` | Incident Response plans. |
| **Incidents** | Incident Report Log | List of past P1/P2 incidents and RCAs. |

---

## 8. Auditor Q&A Cheat Sheet

**Q: "How do you ensure developers don't access patient data?"**
A: "Developers have no access to the Production Project. They deploy via CI/CD pipelines (`.github/workflows`), and database access is restricted to the Application Service Account (`infra/modules/iam`)."

**Q: "Show me proof of your backups."**
A: *Open Google Cloud Console -> SQL -> Backups. Show the list of daily backups retained for 35 days.*

**Q: "What happens if an admin leaves?"**
A: "We follow the JML Leavers process (`ops/sops/jml_process.md`). Access is revoked immediately on termination, sessions are cleared, and the change is logged."

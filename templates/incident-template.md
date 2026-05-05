# Security Incident Response Template

**Incident ID:** INC-[YYYY-MM-DD]-[###]
**Reported By:** [Name/Agent]
**Date/Time:** [YYYY-MM-DD HH:MM:SS UTC]
**Severity:** [CRITICAL / HIGH / MEDIUM / LOW]
**Status:** [OPEN / INVESTIGATING / CONTAINED / RESOLVED / CLOSED]

---

## Incident Summary

**Type:** [Data Breach / Unauthorized Access / Prompt Injection / Service Disruption / Other]

**Brief Description:**
[One paragraph summary of what happened]

**Affected Systems/Zones:**
- [ ] PUBLIC
- [ ] WORKSPACE
- [ ] FAMILY_PRIVATE
- [ ] QUARANTINE
- [ ] SACRED

**Impact Assessment:**
- **Data Confidentiality:** [None / Low / Medium / High / Critical]
- **Data Integrity:** [None / Low / Medium / High / Critical]
- **System Availability:** [None / Low / Medium / High / Critical]
- **Privacy Impact:** [None / Low / Medium / High / Critical]

---

## Timeline

| Time | Event | Actor |
|------|-------|-------|
| [HH:MM] | Incident occurred | [Agent/User/System] |
| [HH:MM] | Incident detected | [Detection method] |
| [HH:MM] | Response initiated | [Responder] |
| [HH:MM] | Containment achieved | [Responder] |
| [HH:MM] | Investigation complete | [Investigator] |
| [HH:MM] | Remediation complete | [Remediator] |
| [HH:MM] | Incident closed | [Closer] |

---

## Detailed Description

### What Happened?
[Detailed narrative of the incident]

### How Was It Detected?
[Detection mechanism, alerts, logs, user report, etc.]

### Root Cause
[Technical root cause analysis]

### Attack Vector (if applicable)
[How did the attacker/vulnerability manifest?]

---

## Evidence Collected

### Logs
```
[Relevant log entries from /kirobi-core/core-events.log]
```

### Files Affected
- `/path/to/file1.ext` - [Description of impact]
- `/path/to/file2.ext` - [Description of impact]

### Network Activity
[Any external connections, API calls, unusual traffic]

### Agent Behavior
[Unusual agent actions or responses]

### Screenshots/Artifacts
[Link to evidence files in /experiences/learnings/security-incidents/[incident-id]/]

---

## Containment Actions

**Immediate Actions Taken:**
- [ ] Stopped affected services
- [ ] Isolated affected systems
- [ ] Disabled compromised accounts
- [ ] Blocked malicious IPs/domains
- [ ] Revoked compromised credentials
- [ ] Created backups of evidence
- [ ] Other: [Specify]

**Commands Executed:**
```bash
# Document exact commands used for containment
docker compose stop [service]
# etc.
```

---

## Impact Assessment

### Data Exposure
**Was sensitive data accessed?**
- [ ] Yes - [Specify what data]
- [ ] No
- [ ] Unknown

**Was data exfiltrated?**
- [ ] Yes - [Specify what and where]
- [ ] No
- [ ] Unknown

### System Compromise
**Were any systems compromised?**
- [ ] Yes - [List systems]
- [ ] No
- [ ] Unknown

**Was code or configuration modified?**
- [ ] Yes - [List changes]
- [ ] No
- [ ] Unknown

### User/Family Impact
**Were family members affected?**
- [ ] Yes - [Describe impact]
- [ ] No
- [ ] Unknown

### Business Impact
**Was business data or operations affected?**
- [ ] Yes - [Describe impact]
- [ ] No
- [ ] Unknown

---

## Investigation Findings

### Vulnerabilities Exploited
1. [Vulnerability description]
2. [Vulnerability description]

### Indicators of Compromise (IoCs)
- File hashes: [List]
- IP addresses: [List]
- Domains: [List]
- User agents: [List]
- Patterns: [Describe]

### Attribution (if known)
[External attacker / Internal user error / System bug / etc.]

---

## Remediation Actions

### Immediate Fixes
- [ ] Patched vulnerability: [Description]
- [ ] Updated configurations: [What changed]
- [ ] Rotated credentials: [Which ones]
- [ ] Restored from backup: [What was restored]
- [ ] Other: [Specify]

### Long-Term Improvements
- [ ] Code changes: [PR link or description]
- [ ] Policy updates: [Which policies]
- [ ] Process improvements: [What changed]
- [ ] Training/awareness: [Who needs training]
- [ ] Monitoring enhancements: [What was added]

---

## Lessons Learned

### What Went Well?
1. [Success point]
2. [Success point]

### What Went Wrong?
1. [Failure point]
2. [Failure point]

### What Could Be Improved?
1. [Improvement opportunity]
2. [Improvement opportunity]

### Preventive Measures
1. [Specific action to prevent recurrence]
2. [Specific action to prevent recurrence]

---

## Follow-Up Actions

| Action | Owner | Due Date | Status |
|--------|-------|----------|--------|
| [Action description] | [Name] | [Date] | [ ] Open / [x] Done |
| [Action description] | [Name] | [Date] | [ ] Open / [x] Done |

---

## Notifications

### Internal Notifications
- [ ] Sven (System Owner) - [Date/Time]
- [ ] Family Members (if affected) - [Date/Time]
- [ ] Other: [Specify]

### External Notifications
- [ ] Customers/Clients (if affected) - [Date/Time]
- [ ] Authorities (if required by law) - [Date/Time]
- [ ] Service Providers - [Date/Time]
- [ ] Other: [Specify]

---

## Post-Incident Review

**Review Date:** [YYYY-MM-DD]
**Participants:** [Names]

**Key Takeaways:**
1. [Takeaway]
2. [Takeaway]

**Documentation Updated:**
- [ ] /CLAUDE.md
- [ ] /metadata/SECURITY-CLASSIFICATION.md
- [ ] /metadata/ZONE-POLICY-MATRIX.md
- [ ] /prompts/safety/[relevant-files]
- [ ] /experiences/learnings/security-incidents.md
- [ ] Other: [Specify]

**Tests Added:**
- [ ] /tests/security/test_[vulnerability].py
- [ ] Other: [Specify]

---

## Closure

**Resolved By:** [Name]
**Resolution Date:** [YYYY-MM-DD]
**Final Status:** [RESOLVED / FALSE POSITIVE / UNABLE TO RESOLVE]

**Sign-Off:**
- [ ] Technical resolution verified
- [ ] All follow-up actions completed
- [ ] Documentation updated
- [ ] Lessons learned recorded
- [ ] Preventive measures implemented

**Approved By:** [Name] - [Date]

---

## Appendix

### Related Incidents
- [Link to related incident reports]

### External References
- [Links to CVEs, security advisories, etc.]

### Additional Notes
[Any other relevant information]

---

**Template Version:** 1.0
**Last Updated:** 2026-05-05
**Location:** /templates/incident-template.md

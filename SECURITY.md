# SECURITY.md - Security Policy

**Repository:** Kirobi / Disruptive OS
**Version:** 1.0
**Last Updated:** 2026-05-05
**Classification:** PUBLIC (this file) / WORKSPACE (internal docs)

---

## Security Overview

Kirobi / Disruptive OS is a local-first, privacy-focused personal AI ecosystem. Security is paramount because this system handles:
- Personal and family data
- Business information
- Sensitive experiences and values
- Credentials and system access

---

## Reporting Security Vulnerabilities

### For External Contributors

If you discover a security vulnerability, please **DO NOT** create a public issue.

**Instead, report privately to:**
- Email: [To be configured - use GitHub Security Advisories]
- GitHub: Use the "Security" tab → "Report a vulnerability"

**What to include:**
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if you have one)
- Your contact information

**Response Timeline:**
- Initial response: Within 48 hours
- Status update: Within 7 days
- Resolution target: 30 days (depending on severity)

### For Internal Users (Sven/Family)

Report security concerns to:
- Log in `/kirobi-core/core-events.log`
- Create incident report in `/experiences/learnings/security-incidents/`
- Use template: `/templates/incident-template.md`

---

## Security Model

### Five-Zone Security Architecture

This system uses a **zone-based security model** where all data is classified into one of five zones:

| Zone | Symbol | Sensitivity | External API Access | Description |
|------|--------|-------------|---------------------|-------------|
| PUBLIC | 🌍 | Low | ✅ Allowed | Publicly shareable content |
| WORKSPACE | 💼 | Medium | ⚠️ With approval | Work/technical, not personal |
| FAMILY_PRIVATE | 👨‍👩‍👦 | High | ❌ Forbidden | Family experiences, personal data |
| QUARANTINE | ⚠️ | Untrusted | ❌ Forbidden | Unverified, potentially unsafe |
| SACRED | 🔐 | Critical | ❌ Forbidden | Highest confidentiality |

**Key Principle:** Data never flows from a higher sensitivity zone to a lower one or to external services without explicit approval.

See `/metadata/ZONE-POLICY-MATRIX.md` for detailed access control.

---

## Threat Model

### Threats We Protect Against

1. **Prompt Injection Attacks**
   - Malicious instructions embedded in user input
   - Adversarial content in RAG-retrieved data
   - **Mitigation:** Input sanitization, content isolation, output filtering
   - **Reference:** `/prompts/safety/injection-detection.md`

2. **Data Exfiltration**
   - Unauthorized sending of sensitive data to external services
   - Accidental exposure via cloud APIs
   - **Mitigation:** Zone enforcement, API call logging, human approval gates
   - **Reference:** `/metadata/ZONE-POLICY-MATRIX.md`

3. **Privilege Escalation**
   - Agents attempting to access zones beyond their permissions
   - Users or agents modifying security policies
   - **Mitigation:** Role-based access control, immutable security configs
   - **Reference:** `/CLAUDE.md` section 5

4. **Unauthorized Data Access**
   - Accessing SACRED or FAMILY_PRIVATE without permission
   - Reading sensitive files without audit logging
   - **Mitigation:** Zone-based access control, comprehensive logging
   - **Reference:** `/kirobi-core/core-policies.md`

5. **Supply Chain Attacks**
   - Malicious dependencies or Docker images
   - Compromised external integrations
   - **Mitigation:** Dependency pinning, image verification, minimal external dependencies
   - **Reference:** `/infra/` documentation

6. **Social Engineering**
   - Tricking agents into bypassing security controls
   - Fake emergency scenarios
   - **Mitigation:** Agent training, suspicious pattern detection
   - **Reference:** `/prompts/safety/` (all files)

7. **Insider Threats**
   - Accidental data exposure by authorized users
   - Misconfiguration leading to vulnerabilities
   - **Mitigation:** Principle of least privilege, configuration validation, backup/restore
   - **Reference:** `/CLAUDE.md`

### Threats Currently Out of Scope

- Nation-state adversaries
- Hardware-level attacks
- Physical security of devices
- DDoS attacks (system is local-first)
- Zero-day OS exploits

---

## Security Controls

### Administrative Controls

- **Security Policies:** Documented in `/metadata/` and `/kirobi-core/core-policies.md`
- **Access Control:** Zone-based permissions in `/metadata/ZONE-POLICY-MATRIX.md`
- **Incident Response:** Template at `/templates/incident-template.md`
- **Security Training:** AI agents trained via `/CLAUDE.md` and `/prompts/safety/`

### Technical Controls

- **Input Validation:** All user input treated as untrusted
- **Output Filtering:** Prevents sensitive data leakage
- **Audit Logging:** All security-relevant events logged to `/kirobi-core/core-events.log`
- **Encryption:** SACRED data encrypted at rest (planned)
- **Network Segmentation:** Docker network isolation
- **Secrets Management:** Environment variables, never committed to git
- **Backup & Recovery:** Automated backups with encryption

### Physical Controls

- **Local-First Architecture:** Sensitive data never leaves local hardware
- **Air-Gap Option:** SACRED data can be stored offline
- **Device Security:** Responsibility of system owner (disk encryption, physical access control)

---

## Security Assumptions

### What We Assume is Secure

1. **Host Operating System:** Assumed to be patched and secured by system owner
2. **Docker Runtime:** Assumed to be up-to-date and properly configured
3. **Local Network:** Assumed to be trustworthy (home network)
4. **Physical Access:** Assumed to be controlled by authorized users only
5. **Backup Storage:** Assumed to be physically and cryptographically secured

### What We Do NOT Assume

1. **User Input:** Always treated as untrusted
2. **RAG-Retrieved Content:** Always treated as untrusted
3. **External APIs:** Assumed to be potentially malicious or compromised
4. **Web-Scraped Content:** Assumed to be untrusted
5. **Imported Files:** Assumed to be potentially malicious (quarantined first)

---

## Secure Development Practices

### For Contributors

1. **Never Commit Secrets**
   - Use `.env` (gitignored), never `.env.example` for real values
   - Use placeholders in example files
   - Scan commits for secrets before pushing

2. **Follow Zone Rules**
   - Understand zone classifications before reading/writing files
   - Respect access control matrix
   - Get approval for cross-zone operations

3. **Input Validation**
   - Validate all user input
   - Sanitize before processing
   - Never execute user-provided code

4. **Error Handling**
   - Don't leak sensitive info in error messages
   - Log errors appropriately for debugging
   - Use generic error messages for users

5. **Dependencies**
   - Pin versions in requirements/package files
   - Review dependencies for known vulnerabilities
   - Minimize external dependencies

6. **Code Review**
   - Security-sensitive changes require review
   - Check for zone violations
   - Verify no secrets committed

### Testing Requirements

- **Security Tests:** Required for all PRs touching sensitive areas
- **Prompt Injection Tests:** Test new agent prompts against adversarial inputs
- **Zone Enforcement Tests:** Verify access control works as expected
- **Regression Tests:** Ensure previous vulnerabilities don't reappear

---

## Compliance & Privacy

### Data Protection Principles

1. **Data Minimization:** Only collect necessary data
2. **Purpose Limitation:** Use data only for intended purpose
3. **Storage Limitation:** Retain data according to `/metadata/RETENTION-POLICY.md`
4. **Integrity & Confidentiality:** Protect data via zones and encryption
5. **Accountability:** Log all data access and modifications

### GDPR Considerations

While this is a personal system, we follow GDPR principles:
- **Right to Access:** System owner has full access
- **Right to Rectification:** Data can be corrected
- **Right to Erasure:** Data can be deleted (with soft-delete for backups)
- **Right to Portability:** Data is in open formats
- **Right to Object:** Human has final say on all processing

---

## Encryption

### Data at Rest

- **SACRED Zone:** Encrypted with key stored securely offline (planned)
- **Backups:** Encrypted with strong passphrase
- **Credentials:** Stored in `.env` (file-system permissions protect)
- **Other Zones:** Rely on disk encryption (system owner's responsibility)

### Data in Transit

- **Internal (Docker network):** Plaintext (local only)
- **External APIs:** TLS/HTTPS (when used)
- **Backup Transport:** Encrypted before transport

---

## Monitoring & Alerting

### What We Monitor

- Agent actions in protected zones (FAMILY_PRIVATE, SACRED)
- External API calls with data classification
- Failed authentication attempts
- Suspicious input patterns (injection attempts)
- System health and resource usage

### Alert Conditions

- SACRED zone access by non-authorized agent
- FAMILY_PRIVATE data sent to external API (blocked + alert)
- High-confidence prompt injection detection
- Multiple failed operations in succession
- Resource exhaustion (disk, memory, CPU)

### Log Locations

- **Security Events:** `/kirobi-core/core-events.log`
- **System Logs:** Docker logs (`docker compose logs`)
- **Incident Reports:** `/experiences/learnings/security-incidents/`
- **Agent Errors:** `/experiences/learnings/agent-errors.md`

---

## Incident Response

### Severity Levels

- **CRITICAL:** SACRED data exposed, system compromise
- **HIGH:** FAMILY_PRIVATE data exposed, privilege escalation
- **MEDIUM:** WORKSPACE data exposed, service disruption
- **LOW:** Minor security policy violation, non-exploitable vulnerability

### Response Process

1. **Detection:** Via monitoring, alert, or manual discovery
2. **Containment:** Isolate affected systems, stop malicious activity
3. **Investigation:** Determine scope, impact, root cause
4. **Eradication:** Remove vulnerability, patch systems
5. **Recovery:** Restore services, verify integrity
6. **Lessons Learned:** Document and improve

**Template:** `/templates/incident-template.md`

---

## Known Limitations

1. **No Active Intrusion Detection:** No real-time IDS/IPS (planned)
2. **Limited Encryption:** Not all data encrypted at rest (except SACRED)
3. **No Multi-User Auth:** Single-user system (Sven), family has implicit trust
4. **No Rate Limiting:** No protection against local resource exhaustion via API spam
5. **Prompt Injection:** Defense-in-depth, but not foolproof (ongoing research)

---

## Security Roadmap

### Short-Term (Q2 2025)

- [ ] Implement automated security testing
- [ ] Add real-time injection detection
- [ ] Enhance audit logging with structured events
- [ ] Create security dashboard

### Medium-Term (Q3-Q4 2025)

- [ ] Full encryption for SACRED zone
- [ ] Multi-factor authentication for sensitive operations
- [ ] Intrusion detection system
- [ ] Automated vulnerability scanning

### Long-Term (2026+)

- [ ] Zero-trust architecture
- [ ] Hardware-backed secrets (TPM/HSM)
- [ ] Advanced threat intelligence integration
- [ ] Continuous security testing

---

## Security Contacts

**System Owner:** Sven Kirchner
**Primary Contact:** [To be configured]
**GitHub Security:** Use repository security tab

---

## Acknowledgments

We thank the security research community for their work on LLM security, particularly:
- OWASP LLM Top 10 Project
- Prompt injection research by Simon Willison and others
- AI safety researchers at Anthropic, OpenAI, and academic institutions

---

## Version History

```
v1.0 - 2026-05-05 - Initial security policy creation
```

---

**This security policy is a living document and will be updated as threats evolve and the system matures.**

For detailed implementation guidance, see:
- `/CLAUDE.md` - AI agent operating instructions
- `/metadata/SECURITY-CLASSIFICATION.md` - Zone classification guide
- `/metadata/ZONE-POLICY-MATRIX.md` - Access control matrix
- `/prompts/safety/` - Safety prompt implementations

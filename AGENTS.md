# AGENTS.md — wp-memlog Project

This file applies to all AI agents (데우스, 맥거핀, 휴브리스) working on this project.

---

## 🚨 Security Absolute Rules (Immediate Work Stop on Violation)

**These rules apply without exception in any situation.**

1. **NEVER Hardcode API Keys/Tokens/Passwords**
   - Never write `sk-or-`, `Bearer`, API keys, passwords directly in code
   - Always use environment variables (`os.getenv()`, `${VAR}`) or `.env` file
   - Example: `sk-or-v1-...` ← ❌ NEVER | `os.getenv("OPENROUTER_API_KEY")` ← ✅

2. **NEVER Commit `.env` file**
   - Always verify `.env` is in `.gitignore`
   - If accidentally staged, remove immediately: `git reset HEAD .env`

3. **Mandatory Self-Check Before git push**
   - Before pushing, always run:
     ```bash
     git diff --cached | grep -iE "sk-or|Bearer|api_key|token|password|secret"
     ```
   - If ANY result appears, **DO NOT push.** Remove hardcoded secrets first, then re-verify.

4. **NEVER Create/Change Public Repo**
   - This project is managed as **private repo only**
   - To create new repo or change visibility, must get david's advance approval

5. **Database Password Masking**
   - In `docker-compose.yml`, config files, etc., passwords must use `${MYSQL_PASSWORD}` format
   - `password: "actualpassword"` ← ❌ | `password: ${MYSQL_PASSWORD}` ← ✅

---

## Violation Handling

- 1st violation: Immediate code fix + report to david
- 2nd violation: Project access permission review for that agent
- API key exposure confirmed externally: Immediate key rotation + report to david

---

## General Work Rules

- Korean first, English technical terms allowed
- Always report verification results after work completion
- Don't guess uncertain matters — check with david
- Always read and understand existing code before modifying
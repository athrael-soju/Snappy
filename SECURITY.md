# Security Policy 🔒

We take the security of Snappy seriously. This document outlines our security policies, supported versions, and how to report vulnerabilities.

---

## 📋 Table of Contents

- [Supported Versions](#supported-versions)
- [Reporting a Vulnerability](#reporting-a-vulnerability)
- [Security Best Practices](#security-best-practices)
- [Known Security Considerations](#known-security-considerations)
- [Security Updates](#security-updates)
- [Disclosure Policy](#disclosure-policy)

---

## Supported Versions

We provide security updates for the following versions:

| Version | Supported          | Status |
| ------- | ------------------ | ------ |
| 0.4.x   | :white_check_mark: | Current stable release |
| 0.3.x   | :warning:          | Security fixes only |
| < 0.3   | :x:                | No longer supported |

**Recommendation:** Always use the latest stable version to ensure you have the most recent security patches and improvements.

---

## Reporting a Vulnerability

### How to Report

If you discover a security vulnerability, please **do not** open a public GitHub issue. Instead:

1. **Use GitHub Security Advisories**: Navigate to the [Security tab](https://github.com/athrael-soju/Snappy/security/advisories) and click "Report a vulnerability"
2. **Contact the maintainers** directly via GitHub or create a private security advisory

### What to Include

Please provide as much information as possible:

- **Description** of the vulnerability
- **Steps to reproduce** the issue
- **Potential impact** and attack scenarios
- **Affected versions** (if known)
- **Suggested fix** (if you have one)
- **Your contact information** for follow-up

### Example Report

```
Subject: [SECURITY] Potential SQL Injection in Search Endpoint

Description:
The /search endpoint may be vulnerable to SQL injection when handling
special characters in the query parameter.

Steps to Reproduce:
1. Send GET request to /search?q=' OR 1=1--
2. Observe unexpected behavior in results

Impact:
- Potential unauthorized data access
- Database manipulation risk

Affected Versions: 0.1.x, 0.2.x

Environment:
- OS: Ubuntu 22.04
- Docker version: 24.0.6
- Python version: 3.11.5
```

### Response Timeline

- **Initial Response**: Within 48 hours
- **Status Update**: Within 7 days
- **Fix Timeline**: Depends on severity
  - **Critical**: 1-7 days
  - **High**: 7-30 days
  - **Medium**: 30-90 days
  - **Low**: Next planned release

### What to Expect

1. **Acknowledgment** - We'll confirm receipt of your report
2. **Investigation** - We'll validate and assess the vulnerability
3. **Fix Development** - We'll develop and test a fix
4. **Disclosure Coordination** - We'll work with you on disclosure timing
5. **Release** - We'll release the fix and publish a security advisory
6. **Credit** - We'll publicly credit you (unless you prefer anonymity)

---

## Security Best Practices

### For Deployment

#### Environment Variables

**Never commit sensitive credentials to version control:**

```bash
# ✅ Good - Use environment files (gitignored)
OPENAI_API_KEY=sk-...

# ❌ Bad - Hardcoded credentials
OPENAI_API_KEY="sk-proj-1234567890"  # In committed code
```

**Use strong, unique passwords:**
- Qdrant: Use API keys in production
- OpenAI: Rotate keys periodically

#### CORS Configuration

**Set explicit allowed origins:**

```bash
# ❌ Development only - Too permissive
ALLOWED_ORIGINS=*

# ✅ Production - Explicit domains
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

#### HTTPS/TLS

**Always use HTTPS in production:**
- Use SSL certificates (Let's Encrypt, CloudFlare, etc.)
- Use HTTPS in production
- Configure Next.js behind a reverse proxy (nginx, Traefik)
- Enable HSTS headers

#### File Uploads

**Validate and sanitize uploads:**
- Enforce file type restrictions (PDF only by default)
- Set maximum file sizes (`UPLOAD_MAX_FILE_SIZE`)
- Limit concurrent uploads (`UPLOAD_MAX_FILES`)
- Scan uploaded files for malware (recommended in production)

#### API Rate Limiting

**Implement rate limiting for production:**

```python
# backend/api/app.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

# Apply to expensive endpoints
@app.get("/search")
@limiter.limit("60/minute")
async def search_documents(...):
    ...
```

### For Development

#### Dependency Management

**Keep dependencies updated:**

```bash
# Backend
cd backend
uv pip list --outdated
uv pip install -U package-name

# Frontend
cd frontend
yarn upgrade-interactive
```

**Audit for vulnerabilities:**

```bash
# Backend
pip-audit  # Install: pip install pip-audit

# Frontend
yarn audit
yarn audit fix
```

#### Secrets Management

**Use `.env` files (never commit them):**

```bash
# .env.example - Commit this
OPENAI_API_KEY=your_openai_key_here

# .env - Gitignored, contains real secrets
OPENAI_API_KEY=sk-proj-actual-key-123
```

**Rotate secrets regularly:**
- OpenAI API keys: Every 90 days
- Database passwords: Every 180 days

#### Code Security

**Input Validation:**

```python
# ✅ Good - Pydantic validation
from pydantic import BaseModel, Field, validator

class SearchRequest(BaseModel):
    query: str = Field(..., max_length=500)
    k: int = Field(default=10, ge=1, le=100)
    
    @validator('query')
    def sanitize_query(cls, v):
        # Remove potentially dangerous characters
        return v.strip()
```

**SQL Injection Prevention:**
- Use parameterized queries (SQLAlchemy, asyncpg)
- Never interpolate user input into SQL strings
- Qdrant uses its own query language (safe by design)

**XSS Prevention:**
- React escapes output by default (safe)
- Sanitize HTML if using `dangerouslySetInnerHTML`
- Use CSP headers in production

---

## Known Security Considerations

### Current Architecture

#### 1. API Key Exposure (Frontend)

**Issue:**  
The frontend chat route requires `OPENAI_API_KEY` in the Next.js environment. This is intentional for edge runtime but means the key is exposed server-side.

**Mitigation:**
- Key is in `.env.local` (server-side only, not exposed to browser)
- Use API key restrictions (OpenAI dashboard)
- Consider backend proxy for production deployments

**Production Recommendation:**
```typescript
// Option 1: Backend proxy (recommended)
// Move chat logic to backend/api/routers/chat.py

// Option 2: API key per user
// Implement user authentication and per-user API keys
```

#### 2. Local Storage Public Access

**Issue:**
Page images are served from local storage with public read access for simplicity.

**Mitigation:**
- Images are stored in dedicated storage folder
- No sensitive metadata in image URLs
- Access control can be implemented at the web server level if needed

#### 3. No Authentication/Authorization

**Issue:**  
The application currently has no user authentication or role-based access control.

**Impact:**
- Anyone with network access can use the API
- Suitable for internal deployments, demos, or behind VPN
- Not suitable for public internet without additional security

**Production Recommendation:**
- Implement authentication (JWT, OAuth, API keys)
- Add role-based access control (RBAC)
- Use a reverse proxy with authentication (OAuth2 Proxy, Authelia)
- Consider managed solutions (Auth0, Clerk, NextAuth.js)

#### 4. Docker Security

**Issue:**  
Default Docker Compose setup may run containers as root.

**Mitigation:**
- Use non-root users in production Dockerfiles
- Apply security contexts in docker-compose.yml
- Use Docker secrets for sensitive data

**Enhanced docker-compose.yml:**
```yaml
services:
  backend:
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
    user: "1000:1000"
```

---

## Security Updates

### Staying Informed

- **GitHub Watch**: Enable notifications for security advisories
- **Dependency Alerts**: Review Dependabot alerts
- **Release Notes**: Check `CHANGELOG.md` for security fixes

### Automated Updates

**Dependabot Configuration** (`.github/dependabot.yml`):

```yaml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/backend"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10
    labels:
      - "dependencies"
      - "security"
    
  - package-ecosystem: "npm"
    directory: "/frontend"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10
    labels:
      - "dependencies"
      - "security"
```

### Security Checklist

Before deploying to production:

- [ ] All secrets in environment files (not committed)
- [ ] HTTPS/TLS enabled
- [ ] CORS set to explicit origins
- [ ] Rate limiting implemented
- [ ] File upload validation configured
- [ ] Dependencies audited and updated
- [ ] Docker containers run as non-root users
- [ ] Firewall rules configured
- [ ] Monitoring and logging enabled
- [ ] Backup strategy in place
- [ ] Authentication implemented (if needed)
- [ ] API keys rotated and restricted

---

## Disclosure Policy

### Our Commitment

- We will respond to security reports within 48 hours
- We will keep you informed of our progress
- We will credit researchers who report vulnerabilities (unless anonymity is requested)
- We will not pursue legal action against researchers who follow responsible disclosure

### Responsible Disclosure

We ask that you:

- **Give us reasonable time** to fix the issue before public disclosure (typically 90 days)
- **Avoid privacy violations**, data destruction, or service disruption during research
- **Do not exploit** the vulnerability beyond what's necessary to demonstrate it
- **Act in good faith** to avoid harming our users or systems

### Public Disclosure

Once a fix is released:

1. We'll publish a **GitHub Security Advisory**
2. Update the **CHANGELOG.md** with security notes
3. Credit the reporter (if they agree)
4. Provide **migration guidance** if needed

---

## Security Features

### Current Implementation

✅ **Input Validation** - Pydantic models for all API inputs  
✅ **Type Safety** - Python type hints + TypeScript strict mode  
✅ **Dependency Scanning** - Pre-commit hooks and linters  
✅ **Error Handling** - No sensitive data in error messages  
✅ **File Type Validation** - PDF-only uploads by default  
✅ **Size Limits** - Configurable upload limits  
✅ **CORS Configuration** - Environment-based origins  

### Planned Enhancements

🔜 **Authentication** - JWT or OAuth2 support  
🔜 **Rate Limiting** - Request throttling  
🔜 **Audit Logging** - Security event tracking  
🔜 **API Keys** - Per-user API key management  
🔜 **Content Security Policy** - Enhanced XSS protection  
🔜 **Malware Scanning** - Upload file scanning  

---

## Additional Resources

### Security Tools

- [pip-audit](https://github.com/pypa/pip-audit) - Python dependency vulnerability scanner
- [Bandit](https://github.com/PyCQA/bandit) - Python security linter
- [Trivy](https://github.com/aquasecurity/trivy) - Container vulnerability scanner
- [OWASP ZAP](https://www.zaproxy.org/) - Web application security scanner

### Security Guidelines

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CWE Top 25](https://cwe.mitre.org/top25/)
- [Docker Security Best Practices](https://docs.docker.com/develop/security-best-practices/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [Next.js Security](https://nextjs.org/docs/app/building-your-application/configuring/content-security-policy)

### Related Documentation

- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines
- [VERSIONING.md](VERSIONING.md) - Version management
- [backend/docs/configuration.md](backend/docs/configuration.md) - Configuration reference

---

## Contact

For security-related inquiries:

- **Security Reports**: Use GitHub Security Advisories, or email athrael.soju@gmail.com
- **General Questions**: Open a GitHub Discussion
- **Non-Security Issues**: Create a GitHub Issue

---

## Acknowledgments

We thank the security researchers and community members who help keep Snappy secure. Responsible disclosure helps protect all users.

---

**Last Updated:** November 13, 2025
**Next Review:** TBA
**License:** [MIT](LICENSE)

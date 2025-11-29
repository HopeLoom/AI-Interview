# Security Policy

## Supported Versions

We release patches for security vulnerabilities. Which versions are eligible for receiving such patches depends on the CVSS v3.0 Rating:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via one of the following methods:

- **Email**: security@hopeloom.com
- **Private Security Advisory**: [Create a private security advisory](https://github.com/HopeLoom/AI-Interview/security/advisories/new)

Please include the following information:

- Type of vulnerability
- Full paths of source file(s) related to the vulnerability
- The location of the affected source code (tag/branch/commit or direct URL)
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit the issue

You should receive a response within 48 hours. If you haven't heard back by then, please follow up via email to ensure we received your message.

## Security Best Practices

This project is currently a **prototype/starter project**. Before deploying to production:

1. **Implement proper authentication**: Replace placeholder authentication with secure password hashing (bcrypt/argon2) and JWT tokens
2. **Add authorization**: Implement proper role-based access control (RBAC)
3. **Secure API endpoints**: Add rate limiting, input validation, and CORS configuration
4. **Environment variables**: Never commit API keys or secrets to the repository
5. **Database security**: Use connection pooling and parameterized queries
6. **HTTPS only**: Enforce HTTPS in production
7. **Dependency updates**: Regularly update dependencies to patch vulnerabilities

See [ISSUES_AND_RECOMMENDATIONS.md](./ISSUES_AND_RECOMMENDATIONS.md) for detailed security recommendations.

## Known Security Limitations

- Authentication is simplified for development (password verification not implemented)
- No JWT token implementation (placeholder tokens in use)
- No rate limiting on API endpoints
- No input sanitization on all endpoints

These are intentional limitations for the prototype/starter project. Implement proper security before production use.


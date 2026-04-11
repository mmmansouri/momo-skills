# Secrets Management Guide

## Overview

Best practices for handling sensitive data securely throughout the development lifecycle.

---

## Types of Secrets

| Type | Examples | Sensitivity | Rotation Frequency |
|------|----------|-------------|-------------------|
| API Keys | Stripe, Twilio, AWS | High | Quarterly |
| Database Credentials | Connection strings | Critical | On incident |
| Encryption Keys | JWT secrets, AES keys | Critical | Annually |
| Service Tokens | Inter-service auth | Medium | Monthly |
| SSH Keys | Deploy keys | High | Annually |
| TLS Certificates | HTTPS certs | Medium | Before expiry |

---

## 🔴 BLOCKING Rules

### 1. Never Commit Secrets

```bash
# .gitignore - ALWAYS include these
.env
.env.*
!.env.example
*.pem
*.key
*_rsa
*.p12
secrets/
credentials/
```

### 2. Never Log Secrets

```typescript
// 🔴 WRONG
console.log('Connecting with:', connectionString);
logger.info(`API Key: ${apiKey}`);

// ✅ CORRECT
console.log('Connecting to database...');
logger.info('API request authenticated');

// ✅ BETTER: Mask in logging config
const maskedString = connectionString.replace(/password=([^&]+)/, 'password=***');
```

### 3. Never Hardcode Secrets

```typescript
// 🔴 WRONG
const apiKey = 'sk_live_abc123xyz789';
const dbPassword = 'supersecret';

// ✅ CORRECT
const apiKey = process.env.API_KEY;
const dbPassword = process.env.DB_PASSWORD;

// ✅ BETTER: Validate at startup
const apiKey = process.env.API_KEY;
if (!apiKey) {
  throw new Error('API_KEY environment variable is required');
}
```

### 4. Least Privilege Access

```yaml
# ✅ CORRECT: Scoped permissions
aws:
  - Effect: Allow
    Action:
      - s3:GetObject
      - s3:PutObject
    Resource: arn:aws:s3:::my-bucket/*

# 🔴 WRONG: Overly permissive
aws:
  - Effect: Allow
    Action: s3:*
    Resource: '*'
```

---

## Secret Storage Solutions

### Environment Variables

**Use for:** Simple deployments, local development

```bash
# .env.example (commit this)
DATABASE_URL=postgres://user:password@host:5432/db
API_KEY=your-key-here

# .env (DO NOT commit)
DATABASE_URL=postgres://prod:realpass@db.example.com:5432/prod
API_KEY=sk_live_realkey123
```

**Pros:** Simple, universal support
**Cons:** Visible in process listings, no audit trail

### CI/CD Secrets

**Use for:** Build-time and deploy-time secrets

```yaml
# GitHub Actions
jobs:
  deploy:
    steps:
      - name: Deploy
        env:
          API_KEY: ${{ secrets.API_KEY }}
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
        run: ./deploy.sh
```

### HashiCorp Vault

**Use for:** Enterprise, complex secret management

```bash
# Store secret
vault kv put secret/myapp/database \
  username=admin \
  password=supersecret

# Retrieve secret
vault kv get -field=password secret/myapp/database
```

```typescript
// Application integration
const vault = require('node-vault')({ endpoint: 'https://vault.example.com' });
const secret = await vault.read('secret/data/myapp/database');
const password = secret.data.data.password;
```

### AWS Secrets Manager

**Use for:** AWS workloads

```typescript
import { SecretsManagerClient, GetSecretValueCommand } from '@aws-sdk/client-secrets-manager';

const client = new SecretsManagerClient({ region: 'us-east-1' });
const response = await client.send(
  new GetSecretValueCommand({ SecretId: 'prod/myapp/database' })
);
const secret = JSON.parse(response.SecretString);
```

---

## Secret Rotation

### Why Rotate?

- Limits exposure window if compromised
- Compliance requirements
- Employee offboarding

### Rotation Strategy

```
┌─────────────────────────────────────────────────────────────┐
│                    Secret Rotation                           │
│                                                              │
│  1. Generate new secret                                      │
│  2. Add new secret (both valid)                             │
│  3. Update all consumers to use new                         │
│  4. Verify new secret is working                            │
│  5. Revoke old secret                                       │
│                                                              │
│  Timeline:                                                   │
│  ──────────────────────────────────────────────────────►    │
│  │ New created │ Both valid │ New only │ Old revoked │      │
└─────────────────────────────────────────────────────────────┘
```

### Automated Rotation (AWS Example)

```python
# Lambda function for rotation
def lambda_handler(event, context):
    secret_id = event['SecretId']
    step = event['Step']
    
    if step == 'createSecret':
        # Generate new password
        new_password = generate_secure_password()
        secrets_client.put_secret_value(
            SecretId=secret_id,
            SecretString=json.dumps({'password': new_password}),
            VersionStage='AWSPENDING'
        )
    
    elif step == 'setSecret':
        # Update the actual service (e.g., database)
        update_database_password(new_password)
    
    elif step == 'testSecret':
        # Verify new secret works
        test_connection(new_password)
    
    elif step == 'finishSecret':
        # Mark as current version
        secrets_client.update_secret_version_stage(
            SecretId=secret_id,
            VersionStage='AWSCURRENT',
            MoveToVersionId=pending_version
        )
```

---

## Pre-Commit Secret Scanning

### Git Secrets

```bash
# Install
brew install git-secrets

# Setup for repo
cd myrepo
git secrets --install
git secrets --register-aws

# Add custom patterns
git secrets --add 'password\s*=\s*.+'
git secrets --add 'api[_-]?key\s*=\s*.+'

# Scan existing commits
git secrets --scan-history
```

### Gitleaks

```yaml
# .github/workflows/security.yml
name: Secret Scan
on: [push, pull_request]

jobs:
  gitleaks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### TruffleHog

```bash
# Scan repo
trufflehog git file://. --only-verified

# Scan in CI
trufflehog git https://github.com/org/repo --branch main --only-verified
```

---

## Secret in Docker

### 🔴 WRONG Ways

```dockerfile
# 🔴 WRONG: In Dockerfile
ENV API_KEY=sk_live_abc123

# 🔴 WRONG: Build arg persists in layers
ARG DB_PASSWORD
ENV DB_PASSWORD=$DB_PASSWORD

# 🔴 WRONG: Copy secret file
COPY .env /app/
```

### ✅ CORRECT Ways

```dockerfile
# ✅ Runtime injection
# Dockerfile has no secrets
CMD ["node", "app.js"]

# docker run -e API_KEY=sk_live_abc123 myapp
```

```dockerfile
# ✅ BuildKit secret mounts (not persisted)
# syntax=docker/dockerfile:1.4
RUN --mount=type=secret,id=npmrc,target=/root/.npmrc \
    npm ci
```

```yaml
# ✅ Docker Compose with env_file
services:
  app:
    env_file:
      - .env
```

---

## Kubernetes Secrets

### Basic Secret

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: db-credentials
type: Opaque
data:
  username: YWRtaW4=      # base64 encoded
  password: cGFzc3dvcmQ=  # base64 encoded
```

### Using Secrets

```yaml
apiVersion: v1
kind: Pod
spec:
  containers:
    - name: app
      env:
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: password
```

### External Secrets Operator

```yaml
# Sync from AWS Secrets Manager to K8s Secret
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: db-credentials
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secrets-manager
    kind: ClusterSecretStore
  target:
    name: db-credentials
  data:
    - secretKey: password
      remoteRef:
        key: prod/database
        property: password
```

---

## Incident Response

### If a Secret is Exposed

```markdown
## Immediate Actions (within minutes)
1. [ ] Rotate the secret immediately
2. [ ] Revoke the exposed secret
3. [ ] Check audit logs for unauthorized usage
4. [ ] Notify security team

## Investigation (within hours)
5. [ ] Determine exposure scope (git history, logs, etc.)
6. [ ] Identify how it was exposed
7. [ ] Check for unauthorized access/data breach

## Remediation (within days)
8. [ ] Remove secret from git history if committed
9. [ ] Update processes to prevent recurrence
10. [ ] Document incident
```

### Removing Secrets from Git History

```bash
# Using git-filter-repo (recommended)
git filter-repo --invert-paths --path secret-file.txt

# Force push (coordinate with team!)
git push --force --all
git push --force --tags

# All developers must re-clone
```

---

## Audit Checklist

```markdown
## Weekly
- [ ] Review access logs for secret stores
- [ ] Check for secrets in recent commits

## Monthly  
- [ ] Review who has access to production secrets
- [ ] Rotate service account tokens
- [ ] Update secrets nearing expiration

## Quarterly
- [ ] Rotate API keys
- [ ] Review and prune unused secrets
- [ ] Security awareness training

## Annually
- [ ] Full secret inventory audit
- [ ] Rotate encryption keys
- [ ] Update secret management procedures
```

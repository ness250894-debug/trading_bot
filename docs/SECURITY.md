# Security Guidelines

## 🔐 API Key Rotation Procedures

If you suspect your API keys have been compromised, follow these steps immediately:

### 1. Bybit API Keys
1. Log into [Bybit Account](https://www.bybit.com/)
2. Navigate to API Management
3. Delete the compromised API key
4. Create a new API key with the same permissions
5. Update `BYBIT_API_KEY` and `BYBIT_API_SECRET` in your `.env` file
6. Restart the application

### 2. Telegram Bot Token
1. Open Telegram and message [@BotFather](https://t.me/botfather)
2. Send `/revoke` and select your bot
3. Send `/newbot` or use the revoked bot to get a new token
4. Update `TELEGRAM_BOT_TOKEN` in your `.env` file
5. Update `TELEGRAM_CHAT_ID` if needed (get from [@userinfobot](https://t.me/userinfobot))

### 3. JWT Secret Key
```bash
# Generate new JWT secret
python generate_jwt_secret.py

# Update .env with the new key
# IMPORTANT: This will invalidate all existing user sessions
```

### 4. Encryption Key
```bash
# Generate new encryption key
python generate_encryption_key.py

# IMPORTANT: Before rotating encryption key:
# 1. Set ENCRYPTION_KEY_OLD to current key
# 2. Set ENCRYPTION_KEY to new key
# 3. Run key rotation script
python key_rotation.py
```

### 5. Coinbase Commerce
1. Log into [Coinbase Commerce Dashboard](https://commerce.coinbase.com/)
2. Go to Settings → API Keys
3. Delete old API key
4. Create new API key
5. Update `COINBASE_COMMERCE_API_KEY` in `.env`
6. Go to Settings → Webhook subscriptions
7. Update webhook secret
8. Update `COINBASE_COMMERCE_WEBHOOK_SECRET` in `.env`

### 6. Google Gemini API Key
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Delete compromised key
3. Create new API key
4. Update `GEMINI_API_KEY` in `.env`

### 7. CryptoPanic API Key
1. Visit [CryptoPanic API Settings](https://cryptopanic.com/developers/api/)
2. Regenerate API key
3. Update `CRYPTOPANIC_API_KEY` in `.env`

## 🛡️ Security Best Practices

### Environment Variables
- **NEVER** commit `.env` files to version control
- Use `.env.example` as a template with placeholder values
- Rotate all keys if `.env` is accidentally committed
- Use different keys for development and production

### Git Security
```bash
# Check if .env is properly ignored
git check-ignore -v .env

# Check Git history for .env
git log --all --full-history -- .env

# If .env was committed, remove from history
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch .env" \
  --prune-empty --tag-name-filter cat -- --all

# Force push (ONLY if repository is private and you control all clones)
git push origin --force --all
```

### Password Security
- Minimum 8 characters
- Must contain uppercase, lowercase, and numbers
- Consider using special characters
- Use a password manager
- Never reuse passwords across services

### Database Security
- Regularly backup the database
- Encrypt sensitive data at rest
- Use parameterized queries (never string interpolation)
- Implement proper access controls

### API Security
- Always use HTTPS in production
- Implement rate limiting on all endpoints
- Validate all input data
- Use strong authentication (JWT with reasonable expiry)
- Enable CORS only for trusted domains

### Webhook Security
- Always validate webhook signatures
- Implement timestamp validation (reject old requests)
- Use HTTPS for webhook endpoints
- Log all webhook attempts for auditing

## 🚨 Incident Response

If you detect a security breach:

1. **Immediate Actions**:
   - Rotate ALL API keys immediately
   - Review application logs for suspicious activity
   - Check database for unauthorized access
   - Disable affected user accounts if necessary

2. **Investigation**:
   - Determine scope of breach
   - Identify compromised data
   - Review access logs
   - Check for backdoors or malware

3. **Remediation**:
   - Apply security patches
   - Update dependencies
   - Strengthen access controls
   - Implement additional monitoring

4. **Communication**:
   - Notify affected users if personal data was compromised
   - Document the incident
   - Update security procedures

## 📞 Security Contacts

- Report security vulnerabilities: [Your security email]
- Emergency contact: [Your contact info]

## 🔄 Regular Security Maintenance

- [ ] Review and rotate API keys quarterly
- [ ] Update dependencies monthly
- [ ] Review access logs weekly
- [ ] Test backup restoration quarterly
- [ ] Security audit annually

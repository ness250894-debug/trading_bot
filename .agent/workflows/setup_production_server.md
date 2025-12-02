---
description: Setup HTTPS with Let's Encrypt and Enable Gzip Compression on Nginx
---

# Setup HTTPS and Gzip Compression

Follow these steps on your AWS server to secure your application and optimize performance.

## Prerequisites
- Ensure your domain name (e.g., `yourdomain.com`) is pointing to your server's IP address (`13.51.150.6`).
- You must have SSH access to your server.

## Step 1: Install Certbot
Certbot is the tool used to obtain SSL certificates from Let's Encrypt.

```bash
sudo apt update
sudo apt install -y certbot python3-certbot-nginx
```

## Step 2: Obtain SSL Certificate
Run the following command to obtain a certificate and automatically configure Nginx. Replace `yourdomain.com` with your actual domain.

```bash
# If you have a domain
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# If you only have the IP (Note: Let's Encrypt requires a domain name. 
# If you only have an IP, you can use a self-signed cert, but it will show a warning in browsers.
# For production, get a domain name.)
```

Follow the interactive prompts. When asked about redirecting HTTP traffic to HTTPS, choose **Option 2: Redirect** (this is crucial for the "Best Practices" score).

## Step 3: Enable Gzip Compression
Edit your Nginx configuration file to enable Gzip compression.

1. Open the Nginx config file (usually `/etc/nginx/nginx.conf` or your site-specific config in `/etc/nginx/sites-available/default`).

```bash
sudo nano /etc/nginx/nginx.conf
```

2. Locate the `http { ... }` block and add or uncomment the following lines:

```nginx
http {
    # ... existing config ...

    ##
    # Gzip Settings
    ##

    gzip on;
    gzip_disable "msie6";

    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_buffers 16 8k;
    gzip_http_version 1.1;
    gzip_min_length 256;
    gzip_types
        text/plain
        text/css
        text/javascript
        application/javascript
        application/json
        application/x-javascript
        application/xml
        application/xml+rss
        image/svg+xml;

    # ... existing config ...
}
```

3. Save and exit (`Ctrl+O`, `Enter`, `Ctrl+X`).

## Step 4: Verify and Restart Nginx
Test your configuration for syntax errors and then restart Nginx.

```bash
sudo nginx -t
sudo systemctl restart nginx
```

## Step 5: Verify Changes
1. **HTTPS**: Visit `https://yourdomain.com`. You should see the padlock icon.
2. **Compression**: Open Chrome DevTools -> Network tab. Reload the page. Click on a text resource (like `.js` or `.css`). Look at the "Response Headers". You should see `content-encoding: gzip`.

## Troubleshooting
- **Firewall**: Ensure port 443 (HTTPS) is open in your AWS Security Group.
- **Nginx Errors**: Check logs with `sudo tail -f /var/log/nginx/error.log`.

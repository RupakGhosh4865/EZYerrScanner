# 🚀 EZYerrScanner Deployment Guide

This document provides step-by-step instructions for deploying the EZYerrScanner to various production environments.

---

## 🏗️ Method 1: Docker Compose (Self-Hosted/VPS)
This is the recommended method for maximum control and performance.

### 1. Prerequisites
- Docker & Docker Compose installed on your server (Ubuntu/Debian recommended).
- A domain name pointing to your server IP (optional but recommended).

### 2. Deployment Steps
```bash
# 1. Clone your repository
git clone https://github.com/RupakGhosh4865/EZYerrScanner.git
cd EZYerrScanner

# 2. Configure Environment Variables
# Create backend/.env
echo "GROQ_API_KEY=your_key_here" >> backend/.env
echo "GROQ_MODEL=llama-3.1-8b-instant" >> backend/.env

# 3. Build and Start
docker-compose up -d --build
```
Your application will be live at `http://your-server-ip:80`.

---

## ☁️ Method 2: Render.com (Easiest)
Render is perfect for zero-config deployments directly from GitHub.

### **Backend (Web Service)**
1.  **New** -> **Web Service**.
2.  Connect your GitHub repo.
3.  **Root Directory**: `backend`
4.  **Runtime**: `Python`
5.  **Build Command**: `pip install -r requirements.txt`
6.  **Start Command**: `gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:$PORT`
7.  **Environment Variables**: Add `GROQ_API_KEY`.

### **Frontend (Static Site)**
1.  **New** -> **Static Site**.
2.  Connect your GitHub repo.
3.  **Root Directory**: `frontend`
4.  **Build Command**: `npm run build`
5.  **Publish Directory**: `dist`
6.  **Redirects**: Add a "Rewrite" rule from `/*` to `/index.html` (Status 200).

---

## 🚂 Method 3: Railway.app
Railway is extremely fast and handles monorepos beautifully.

1.  **New Project** -> **GitHub Repo**.
2.  Railway will automatically detect the `docker-compose.yml`.
3.  Go to the **Variables** tab for the backend service and add your `GROQ_API_KEY`.
4.  Expose the frontend service to a public domain in the **Settings** tab.

---

## 🛡️ Security Best Practices
- **API Keys**: Never commit your `.env` files to GitHub. Use the platform's "Secrets" or "Variables" UI.
- **HTTPS**: Use Cloudflare or Nginx (with Certbot) to enable SSL/TLS on port 443.
- **Rate Limiting**: For public instances, consider adding a rate-limiter to the `/api/analyze` endpoints to prevent API credit exhaustion.

---

**Happy Deploying!** 🦾🌐🚀🦾🦾🦾

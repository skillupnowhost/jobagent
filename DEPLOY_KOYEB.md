# Deploy to Koyeb — Free, Always-On, 5 Minutes

## Step 1: Push to GitHub

```bash
cd "e:\Resume Agent"
git init
git add .
git commit -m "AI Job Application Agent"
```

Go to https://github.com/new → create a repo → push:

```bash
git remote add origin https://github.com/YOUR_USERNAME/job-agent.git
git branch -M main
git push -u origin main
```

## Step 2: Deploy on Koyeb

1. Go to https://www.koyeb.com → Sign up (free, no credit card)
2. Click **"Create App"**
3. Select **GitHub** → connect your repo
4. Settings:
   - **Builder**: Dockerfile
   - **Instance type**: Free
   - **Port**: 8000
5. Add environment variables (click "Add Variable"):
   - `ADZUNA_APP_ID` = your key (get free at https://developer.adzuna.com)
   - `ADZUNA_APP_KEY` = your key
   - `RAPIDAPI_KEY` = your key (get free at https://rapidapi.com → subscribe to JSearch)
   - `SMTP_USER` = your Gmail
   - `SMTP_PASSWORD` = your Gmail app password
   - `FROM_EMAIL` = your Gmail
   - `FROM_NAME` = Your Name
   - `USER_NAME` = Your Name
   - `USER_EMAIL` = your email
6. Click **"Deploy"**

Wait 3-5 minutes. Done. Your URL will be:
```
https://job-agent-YOUR_USERNAME.koyeb.app
```

## Step 3: Access Your Dashboard

Open the Koyeb URL on any browser (phone or laptop). That's it.

## Free API Keys (all free tier)

| Service | Sign Up | What You Get |
|---------|---------|-------------|
| Adzuna | https://developer.adzuna.com/signup | 250 requests/day, job search |
| RapidAPI JSearch | https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch | 100 requests/day, LinkedIn/Glassdoor/Indeed |
| Gmail App Password | Google Account > Security > App Passwords | Email automation |

## Auto-Deploy on Every Push

Koyeb auto-deploys when you push to GitHub. Just:
```bash
git add . && git commit -m "update" && git push
```

## Limitations of Free Tier

- 1 app, 1 instance
- 512MB RAM, shared CPU
- Sleeps never (always on!)
- Custom domain supported
- HTTPS included automatically

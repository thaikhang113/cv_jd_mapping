# Deployment Guide

## MongoDB Atlas

1. Create M0 cluster.
2. Create DB user.
3. Network Access: add current Azure outbound IPs or `0.0.0.0/0` for demo.
4. Copy `mongodb+srv://...` connection string.
5. Store it only as environment variable, never commit `.env`.

## Azure App Service Backend

```powershell
az group create --name rg-cv-match-platform --location southeastasia
az appservice plan create --name asp-cv-match-platform --resource-group rg-cv-match-platform --sku B1 --is-linux
az webapp create --resource-group rg-cv-match-platform --plan asp-cv-match-platform --name cv-match-platform-api --runtime "PYTHON:3.12"
az webapp config appsettings set --resource-group rg-cv-match-platform --name cv-match-platform-api --settings MONGO_URI="<atlas-uri>" DATABASE_NAME="cv_match_platform" JWT_SECRET_KEY="<generated>" JWT_ALGORITHM="HS256" ACCESS_TOKEN_EXPIRE_MINUTES="1440" FRONTEND_URL="http://localhost:5173" UPLOAD_DIR="uploads"
az webapp config set --resource-group rg-cv-match-platform --name cv-match-platform-api --startup-file "gunicorn app.main:app -k uvicorn.workers.UvicornWorker --bind=0.0.0.0:8000"
```

Deploy from `backend` using zip deploy or `az webapp up`.

Health checks:

```powershell
curl https://cv-match-platform-api.azurewebsites.net/health
curl https://cv-match-platform-api.azurewebsites.net/docs
```

## Vercel Frontend

```powershell
cd frontend
vercel env add VITE_API_BASE_URL production
vercel --prod
```

Set `VITE_API_BASE_URL` to Azure backend URL.

## CORS Fix

After Vercel deploy:

```powershell
az webapp config appsettings set --resource-group rg-cv-match-platform --name cv-match-platform-api --settings FRONTEND_URL="https://<project>.vercel.app"
az webapp restart --resource-group rg-cv-match-platform --name cv-match-platform-api
```

## Common Issues

- 401: expired token or bad JWT secret between deploys.
- CORS: `FRONTEND_URL` missing exact Vercel URL.
- Upload fail: App Service filesystem is ephemeral; OK for demo, use Blob Storage for production.
- Atlas timeout: Network Access IP not allowed.
- scikit install fail locally: use Python 3.12 or Docker image.

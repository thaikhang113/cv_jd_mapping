# GitHub Actions CI/CD

## Workflows

- `ci.yml`: runs backend tests and frontend build on pull requests and pushes to `main`.
- `deploy.yml`: on `main` push, builds backend Docker image, updates Azure App Service, then deploys frontend to Vercel.

## Required GitHub Secrets

Azure:

- `AZURE_CREDENTIALS`: output from `az ad sp create-for-rbac --sdk-auth ...`
- `AZURE_RESOURCE_GROUP`: `rg-cv-match-platform`
- `AZURE_WEBAPP_NAME`: `cv-match-platform-api-tk2`
- `AZURE_ACR_NAME`: `cvmatchacrthaikhang`
- `AZURE_ACR_LOGIN_SERVER`: `cvmatchacrthaikhang.azurecr.io`

Vercel:

- `VERCEL_TOKEN`
- `VERCEL_ORG_ID`
- `VERCEL_PROJECT_ID`
- `VITE_API_BASE_URL`: `https://cv-match-platform-api-tk2.azurewebsites.net`

## Create Azure Secret

```powershell
az ad sp create-for-rbac `
  --name "cv-match-platform-github-actions" `
  --role contributor `
  --scopes /subscriptions/<subscription-id>/resourceGroups/rg-cv-match-platform `
  --sdk-auth
```

Paste the JSON output into `AZURE_CREDENTIALS`.

## Vercel IDs

From `frontend/`:

```powershell
vercel link
Get-Content .vercel/project.json
```

Use `orgId` as `VERCEL_ORG_ID`, `projectId` as `VERCEL_PROJECT_ID`.

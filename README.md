# Deployment to Google Cloud Run via Docker Hub

This document outlines the steps to deploy this service to Google Cloud Run using Docker Hub as the container registry.

---
## 1. Prerequisites

- Google Cloud SDK (`gcloud` CLI)
- Docker
- A Docker Hub account with an existing repository

---
## 2. One-Time Setup

### A. Log In to Google Cloud Account  
Required for the `gcloud run deploy` command
```
gcloud auth login
```

### B. Set Active Project ID
```
gcloud config set project [YOUR_PROJECT_ID]
```

### C. Log In to Docker Hub  
Required for the `docker push` command
```
docker login
```

---
## 3. Manual Deployment Process

### A. Set Shell Variables  
Replace the values according to your project and Docker Hub account.

#### REPLACE THE VALUES BELOW
```
export DOCKER_USERNAME="[YOUR_DOCKER_HUB_USERNAME]"
export SERVICE_NAME="your-service" # Match your Docker Hub repo name
export TAG="latest" # or v1.0.1

export PROJECT_ID="[YOUR_PROJECT_ID]" # For gcloud
export REGION="asia-southeast2"       # For gcloud
```

#### THIS WILL BE AUTOMATICALLY FILLED
```
export IMAGE_NAME="${DOCKER_USERNAME}/${SERVICE_NAME}:${TAG}"
```

### B. Build the Docker Image
```
docker build -t $IMAGE_NAME .
```

### C. Push Image to Docker Hub
```
docker push $IMAGE_NAME
```

### D. Deploy to Cloud Run  
Note that `--image` now points to the image on Docker Hub.
```
gcloud run deploy $SERVICE_NAME --image $IMAGE_NAME --platform managed --region $REGION --allow-unauthenticated --port 8080 --memory 2Gi --cpu 1 --min-instances 0 --max-instances 10 --concurrency 80 --timeout 300s --env-vars-file .env.yaml
```

---
## 4. Sample `.env.yaml` File  
Make sure your `.env.yaml` file follows the format below. **DO NOT commit this file to Git if it contains secrets!** Use `.gitignore`.

```yaml
# Format: KEY: "VALUE" (values in quotation marks)
DATABASE_URL: "your-database-connection-string"
API_KEY: "your-secret-api-key"
```

#Deploy to GCP Cloud Run 
##1. Build docker image
docker build -t gcr.io/project-id/your-service:[tag] .

##2. Push ke GCP
docker push gcr.io/project-id/your-service:[tag]

##3. Deploy ke Cloud RUn 
gcloud run deploy your-service --image gcr.io/project-id/your-service:[tag] --platform managed --region asia-southeast2 --allow-unauthenticated --port 8080 --memory 2Gi --cpu 1 --min-instances 0 --max-instances 10 --concurrency 80 --timeout 300s --env-vars-file .env.yaml

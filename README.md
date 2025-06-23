# Deployment ke Google Cloud Run via Docker Hub

Dokumen ini menjelaskan langkah-langkah untuk melakukan deployment layanan ini ke Google Cloud Run menggunakan Docker Hub sebagai container registry.

---
## 1. Prasyarat (Prerequisites)

- Google Cloud SDK (`gcloud` CLI)
- Docker
- Akun Docker Hub dengan sebuah repository yang sudah dibuat.

---
## 2. Konfigurasi Awal (One-Time Setup)

### A. Login ke Akun Google Cloud
Diperlukan untuk perintah `gcloud run deploy`
```
gcloud auth login
```

### B. Set Project ID Aktif
```
gcloud config set project [YOUR_PROJECT_ID]
```

### C. Login ke Docker Hub
Diperlukan untuk perintah `docker push`
```
docker login
```

---
## 3. Proses Deployment Manual

### A. Set Shell Variables
Ganti nilainya sesuai dengan proyek dan akun Docker Hub Anda.

#### GANTI NILAI DI BAWAH INI
```
export DOCKER_USERNAME="[YOUR_DOCKER_HUB_USERNAME]"
export SERVICE_NAME="your-service" # Sesuaikan dengan nama repo di Docker Hub
export TAG="latest" # atau v1.0.1

export PROJECT_ID="[YOUR_PROJECT_ID]" # Untuk gcloud
export REGION="asia-southeast2"      # Untuk gcloud
```
#### INI AKAN OTOMATIS TERISI
```
export IMAGE_NAME="${DOCKER_USERNAME}/${SERVICE_NAME}:${TAG}"
```

### B. Build Docker Image
```
docker build -t $IMAGE_NAME .
```

### C. Push Image ke Docker Hub
```
docker push $IMAGE_NAME
```

### D. Deploy ke Cloud Run
Perhatikan bahwa `--image` sekarang menunjuk ke image di Docker Hub.
```
gcloud run deploy $SERVICE_NAME --image $IMAGE_NAME --platform managed --region $REGION --allow-unauthenticated --port 8080 --memory 2Gi --cpu 1 --min-instances 0 --max-instances 10 --concurrency 80 --timeout 300s --env-vars-file .env.yaml
```

---
## 4. Contoh File `.env.yaml`
Pastikan file `.env.yaml` Anda mengikuti format berikut. **JANGAN masukkan file ini ke Git jika berisi rahasia!** Gunakan `.gitignore`.

```yaml
# Format: KEY: "VALUE" (nilai dalam tanda kutip)
DATABASE_URL: "your-database-connection-string"
API_KEY: "your-secret-api-key"

# Deployment ke Google Cloud Run

Dokumen ini menjelaskan langkah-langkah untuk melakukan deployment layanan ini ke Google Cloud Run.

## 1. Prasyarat (Prerequisites)

Pastikan hal-hal berikut sudah terpasang dan terkonfigurasi di komputer Anda:
- **Google Cloud SDK (`gcloud` CLI):** [Link Instalasi](https://cloud.google.com/sdk/docs/install)
- **Docker:** [Link Instalasi](https://docs.docker.com/engine/install/)
- **File di Repositori:**
    - `Dockerfile`: Diperlukan untuk membangun image layanan.
    - `.env.yaml`: File yang berisi environment variables untuk Cloud Run. Lihat contoh format di bawah.

## 2. Konfigurasi Awal (One-Time Setup)

Langkah-langkah ini hanya perlu dilakukan sekali untuk mengautentikasi dan mengonfigurasi lingkungan lokal Anda.

### a. Login ke Akun Google Cloud
gcloud auth login

### b. Set Project ID Aktif
gcloud config set project [YOUR_PROJECT_ID]

### c. Konfigurasi Docker untuk GCP
Perintah ini mengizinkan Docker untuk melakukan push ke Artifact Registry (layanan penerus GCR) di region Anda.
gcloud auth configure-docker asia-southeast2-docker.pkg.dev

## 3. Proses Deployment Manual

Untuk mempermudah dan mengurangi kesalahan, mari kita set variabel terlebih dahulu.

### a. Set Shell Variables
Salin dan tempel blok ini di terminal Anda. Ganti nilainya sesuai dengan proyek Anda.

# --- GANTI NILAI DI BAWAH INI ---
export PROJECT_ID="[YOUR_PROJECT_ID]"
export SERVICE_NAME="your-service"
export REGION="asia-southeast2"
export TAG="latest" # atau gunakan versi spesifik, misal: v1.0.1
# --- Variabel di bawah ini akan otomatis terisi ---
export IMAGE_NAME="${REGION}-docker.pkg.dev/${PROJECT_ID}/${SERVICE_NAME}:${TAG}"

### b. Build Docker Image
Membangun image Docker dari source code dengan tag yang sudah ditentukan.
docker build -t $IMAGE_NAME .

### c. Push Image ke Artifact Registry
Mengunggah image yang sudah di-build ke container registry GCP.
docker push $IMAGE_NAME

### d. Deploy ke Cloud Run
Menerapkan image baru sebagai versi aktif di Cloud Run dengan konfigurasi yang ditentukan.
gcloud run deploy $SERVICE_NAME \
  --image $IMAGE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --port 8080 \
  --memory 2Gi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 10 \
  --concurrency 80 \
  --timeout 300s \
  --env-vars-file .env.yaml

---
## 4. Contoh File `.env.yaml`
Pastikan file `.env.yaml` Anda mengikuti format berikut. **JANGAN masukkan file ini ke Git jika berisi rahasia!** Gunakan `.gitignore`.

```yaml
# Format: KEY: "VALUE" (nilai dalam tanda kutip)
DATABASE_URL: "your-database-connection-string"
API_KEY: "your-secret-api-key"

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from api.endpoints import router as api_router


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Tambahkan endpoint untuk root "/"
@app.get("/", response_class=HTMLResponse)
def read_root():
    return """
    <h2>✅ RAG API is Running!</h2>
    <p>Gunakan endpoint <code>/docs</code> untuk mencoba API.</p>
    """


app.include_router(api_router)

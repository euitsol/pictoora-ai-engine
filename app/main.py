from fastapi import FastAPI
from app.routers import images, processing
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(images.router)
app.include_router(processing.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to Taleified AI Engine. Use /docs to explore the API documentation."}
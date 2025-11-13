from fastapi import FastAPI

app = FastAPI(
    title="Sales Angel Production",
    version="1.0.0",
    description="Sales Angel Production API"
)

@app.get("/")
async def root():
    return {"message": "Sales Angel Production API", "status": "operational"}

@app.get("/health")
async def health():
    return {"status": "healthy", "version": "1.0.0"}

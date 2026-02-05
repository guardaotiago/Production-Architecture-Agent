from fastapi import FastAPI

app = FastAPI(
    title="My FastAPI App",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "healthy"}


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Hello, World!"}

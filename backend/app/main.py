from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="AI Indian Stock Market Analyzer",
    version="0.1.0",
    description="Research and educational market-analysis API.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root() -> dict[str, str]:
    return {"service": "AI Indian Stock Market Analyzer", "status": "ok"}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


# Future routers should be included here, for example:
# app.include_router(stock_router, prefix="/api/stocks", tags=["stocks"])

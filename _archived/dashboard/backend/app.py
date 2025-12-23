"""
Trading Dashboard Backend
FastAPI server for real-time stock tracking, risk analysis, and portfolio management
"""

from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from datetime import datetime
import logging

from api.stocks import router as stocks_router
from api.risk import router as risk_router
from api.portfolio import router as portfolio_router
from api.analysis import router as analysis_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Adaptron Trading Dashboard",
    description="Real-time stock tracking, risk analysis, and portfolio management",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(stocks_router, prefix="/api/stocks", tags=["Stocks"])
app.include_router(risk_router, prefix="/api/risk", tags=["Risk Management"])
app.include_router(portfolio_router, prefix="/api/portfolio", tags=["Portfolio"])
app.include_router(analysis_router, prefix="/api/analysis", tags=["Analysis"])

@app.get("/")
async def root():
    return {
        "name": "Adaptron Trading Dashboard API",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

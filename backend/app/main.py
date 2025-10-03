from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from backend.app.routers import fantasyHback

app = FastAPI(
    title="Walmart AI Starter",
    description="Enhanced AI platform with Supply-Demand Mapping and Fantasy Cricket Predictor",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Include routers
app.include_router(fantasyHback.router)

# Serve static files (CSS, JS, images)
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

# Add middleware for CORS
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint that shows available endpoints
@app.get("/")
async def root():
    return {
        "message": "Walmart AI Starter API",
        "endpoints": {
            "docs": "/docs",
            "fantasy_home": "/api/fantasy/home",
            "fantasy_predict": "/api/fantasy/predict",
        }
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "walmart-ai-starter"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
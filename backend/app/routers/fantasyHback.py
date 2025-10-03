from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request
from pydantic import BaseModel
from typing import List
from catboost import CatBoostRegressor
import pandas as pd
import os

class PlayerDetailResponse(BaseModel):
    player_name: str
    message: str
    stats: dict
router = APIRouter(prefix="/api/fantasy", tags=["fantasy"])

# Load the trained model
MODEL_PATH = "ml_models/catboost_fantasy_points_model.cbm"

# Add this line:
templates = Jinja2Templates(directory="frontend/templates")

try:
    model = CatBoostRegressor()
    model.load_model(MODEL_PATH)
    print(f"✓ Model loaded successfully from {MODEL_PATH}")
except Exception as e:
    print(f"✗ Error loading model: {e}")
    model = None


class PredictionRequest(BaseModel):
    players: List[str]
    date: str
    format: str


class PlayerPrediction(BaseModel):
    player_name: str
    predicted_points: float


class PredictionResponse(BaseModel):
    top_players: List[PlayerPrediction]


@router.post("/predict", response_model=PredictionResponse)
async def predict_fantasy_points(request: PredictionRequest):
    """
    Predict fantasy points for selected players and return top 5
    """
    if model is None:
        raise HTTPException(
            status_code=500,
            detail="Model not loaded. Please ensure the model file exists at ml_models/catboost_fantasy_points_model.cbm"
        )
    
    if len(request.players) != 10:
        raise HTTPException(
            status_code=400,
            detail="Please select exactly 10 players"
        )
    
    if request.format not in ["Test", "ODI", "T20"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid format. Must be Test, ODI, or T20"
        )
    
    try:
        # Create prediction dataframe
        prediction_data = []
        for player in request.players:
            prediction_data.append({
                'player_name': player,
                'date': request.date,
                'format': request.format
            })
        
        df = pd.DataFrame(prediction_data)
        
        # Make predictions
        predictions = model.predict(df)
        
        # Combine players with their predictions
        results = []
        for i, player in enumerate(request.players):
            results.append({
                'player_name': player,
                'predicted_points': float(predictions[i])
            })
        
        # Sort by predicted points (descending) and get top 5
        results.sort(key=lambda x: x['predicted_points'], reverse=True)
        top_5 = results[:5]
        
        return PredictionResponse(top_players=top_5)
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Prediction error: {str(e)}"
        )


# Serve the fantasy home page
@router.get("/home", response_class=HTMLResponse)
async def fantasy_home():
    """
    Serve the fantasy cricket predictor page
    """
    try:
        with open("frontend/templates/fantasyhome.html", "r") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="fantasyhome.html not found"
        )


@router.get("/health")
async def fantasy_health():
    """
    Check if the fantasy prediction service is healthy
    """
    model_loaded = model is not None
    return {
        "status": "healthy" if model_loaded else "unhealthy",
        "model_loaded": model_loaded,
        "model_path": MODEL_PATH
    }

@router.get("/player-info/{player_name}", response_model=PlayerDetailResponse)
async def get_player_info(player_name: str):
    """
    Get player information and return a message
    This is a proper backend API that returns JSON data
    """
    # You can add database queries here, ML predictions, etc.
    # For now, returning a simple response
    
    # Example: You could query your database or calculate stats
    player_stats = {
        "total_matches": 250,
        "average_points": 85.5,
        "best_score": 150,
        "format_preference": "T20"
    }
    
    # Generate the message
    message = f"{player_name} is the greatest player of all time"
    
    return PlayerDetailResponse(
        player_name=player_name,
        message=message,
        stats=player_stats
    )


@router.get("/player/{player_name}", response_class=HTMLResponse)
async def player_detail_page(request: Request, player_name: str):
    """
    Serve the player detail HTML page
    The page will fetch data from /player-info/{player_name} API
    """
    return templates.TemplateResponse(
        "player_detail.html",
        {"request": request, "player_name": player_name}
    )
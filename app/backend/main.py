import os
import sys
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Add backend directory to Python path
sys.path.insert(0, os.path.dirname(__file__))
from player_data import PLAYER_DATABASE, POSITION_WEIGHTS, ROLE_REQUIREMENTS

# Initialize the FastAPI app
app = FastAPI()

# --- Configuration for separate folders ---
# Define the paths to the frontend directory
backend_dir = os.path.abspath(os.path.dirname(__file__))
frontend_dir = os.path.join(os.path.dirname(backend_dir), 'frontend')
static_dir = os.path.join(frontend_dir, "static")
templates_dir = os.path.join(frontend_dir, "templates")

# --- DEBUGGING: Print the calculated paths to the terminal ---
print("="*50)
print(f"Backend directory is: {backend_dir}")
print(f"Frontend directory is: {frontend_dir}")
print(f"Attempting to mount static files from: {static_dir}")
print(f"Attempting to load templates from: {templates_dir}")
print("="*50)
# --- END DEBUGGING ---

# 1. Mount the 'static' folder to serve CSS, JS, and images
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# 2. Set up the Jinja2 templates directory
templates = Jinja2Templates(directory=os.path.join(frontend_dir, "templates"))


# --- Routes for Each Page ---

@app.get("/", response_class=HTMLResponse)
async def login(request: Request):
    """Renders the login page."""
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/index", response_class=HTMLResponse)
async def read_index(request: Request):
    """Renders the main page on a GET request."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/index", response_class=HTMLResponse)
async def post_index(request: Request, team1: str = Form(...), team2: str = Form(...), venue: str = Form(...)):
    """Handles the form submission from the main page and redirects to player selection."""
    
    # Store the selections in session or pass as query params
    print(f"Team 1: {team1}, Team 2: {team2}, Venue: {venue}")
    
    # Get comprehensive player data from database
    team1_data = PLAYER_DATABASE.get(team1, {"players": []})
    team2_data = PLAYER_DATABASE.get(team2, {"players": []})
    
    players1 = team1_data["players"]
    players2 = team2_data["players"]
    
    # Pass to player selection template
    return templates.TemplateResponse("player.html", {
        "request": request,
        "team1": team1,
        "team2": team2,
        "venue": venue,
        "players1": players1,
        "players2": players2
    })

@app.get("/contact", response_class=HTMLResponse)
async def contact(request: Request):
    """Renders the contact page."""
    return templates.TemplateResponse("contact.html", {"request": request})

@app.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    """Renders the about page."""
    return templates.TemplateResponse("about.html", {"request": request})

def select_dream_team(selected_players_data):
    """Algorithm to select the best 11 players from 22 selected players."""
    # Sort players by weighted score (points * position weight)
    for player in selected_players_data:
        weight = POSITION_WEIGHTS.get(player["position"], 1.0)
        player["weighted_score"] = player["points"] * weight
    
    # Sort by weighted score (descending)
    sorted_players = sorted(selected_players_data, key=lambda x: x["weighted_score"], reverse=True)
    
    # Initialize counters for position requirements
    selected_team = []
    position_counts = {
        "Batsman": 0,
        "Bowler": 0,
        "All-Rounder": 0,
        "Wicket-Keeper": 0
    }
    
    # First, ensure we have at least 1 wicket-keeper
    for player in sorted_players:
        if player["position"] == "Wicket-Keeper" and position_counts["Wicket-Keeper"] == 0:
            selected_team.append(player)
            position_counts["Wicket-Keeper"] += 1
            if len(selected_team) == 11:
                break
    
    # Then add players based on requirements and scores
    for player in sorted_players:
        if player in selected_team:
            continue
            
        position = player["position"]
        
        # Check if we can add this position type
        can_add = False
        
        if position == "Wicket-Keeper":
            can_add = False  # Already have required WK
        elif position == "Batsman":
            can_add = position_counts["Batsman"] < ROLE_REQUIREMENTS["max_batsmen"]
        elif position == "Bowler":
            can_add = position_counts["Bowler"] < ROLE_REQUIREMENTS["max_bowlers"]
        elif position == "All-Rounder":
            can_add = position_counts["All-Rounder"] < ROLE_REQUIREMENTS["max_all_rounders"]
        
        if can_add and len(selected_team) < 11:
            selected_team.append(player)
            position_counts[position] += 1
            
        if len(selected_team) == 11:
            break
    
    # If we still need players, fill with highest scoring remaining players
    while len(selected_team) < 11:
        for player in sorted_players:
            if player not in selected_team:
                selected_team.append(player)
                break
        if len(selected_team) == 11:
            break
    
    return selected_team

@app.post("/player", response_class=HTMLResponse)
async def process_players(request: Request):
    """Handles the player selection and shows results."""
    form_data = await request.form()
    
    # Get selected players from both teams
    selected_players1 = form_data.getlist("player1")
    selected_players2 = form_data.getlist("player2")
    team1_name = form_data.get("team1_name")
    team2_name = form_data.get("team2_name")
    venue = form_data.get("venue")
    
    # Combine selected players
    all_selected_players = selected_players1 + selected_players2
    
    # Check if between 11 and 22 players are selected
    if len(all_selected_players) < 11 or len(all_selected_players) > 22:
        # Get original player data to restore the form
        team1_data = PLAYER_DATABASE.get(team1_name, {"players": []})
        team2_data = PLAYER_DATABASE.get(team2_name, {"players": []})
        
        return templates.TemplateResponse("player.html", {
            "request": request,
            "error_message": f"Please select between 11 and 22 players. You selected {len(all_selected_players)} players.",
            "players1": team1_data["players"],
            "players2": team2_data["players"],
            "team1": team1_name,
            "team2": team2_name,
            "venue": venue
        })
    
    # Get detailed player data for selected players
    selected_players_data = []
    team1_data = PLAYER_DATABASE.get(team1_name, {"players": []})
    team2_data = PLAYER_DATABASE.get(team2_name, {"players": []})
    
    # Find player details for team 1 selections
    for player_name in selected_players1:
        for player in team1_data["players"]:
            if player["name"] == player_name:
                player_copy = player.copy()
                player_copy["team"] = team1_name
                selected_players_data.append(player_copy)
                break
    
    # Find player details for team 2 selections
    for player_name in selected_players2:
        for player in team2_data["players"]:
            if player["name"] == player_name:
                player_copy = player.copy()
                player_copy["team"] = team2_name
                selected_players_data.append(player_copy)
                break
    
    # If exactly 11 players selected, use them as is
    if len(selected_players_data) == 11:
        final_team = selected_players_data
    else:
        # Use algorithm to select best 11 from the selected players
        final_team = select_dream_team(selected_players_data)
    
    # Create the predicted team HTML with enhanced details
    predicted_team_html = "<div class='team-overview'>"
    predicted_team_html += f"<h3>Your Dream11 Team ({len(final_team)} players)</h3>"
    predicted_team_html += "<div class='team-composition'>"
    
    # Count positions
    position_counts = {}
    for player in final_team:
        pos = player["position"]
        position_counts[pos] = position_counts.get(pos, 0) + 1
    
    predicted_team_html += "<div class='composition-summary'>"
    for pos, count in position_counts.items():
        pos_class = pos.lower().replace('-', '')
        predicted_team_html += f"<span class='pos-badge {pos_class}'>{pos}: {count}</span>"
    predicted_team_html += "</div></div>"
    
    # Wrap table in scrollable container
    predicted_team_html += "<div class='table-wrapper'>"
    predicted_team_html += "<table class='result-table'>"
    predicted_team_html += "<tr><th>Player</th><th>Team</th><th>Points</th></tr>"
    
    # Sort final team by position priority for display
    position_order = ["Wicket-Keeper", "Batsman", "All-Rounder", "Bowler"]
    final_team.sort(key=lambda x: (position_order.index(x["position"]) if x["position"] in position_order else 4, -x["points"]))
    
    for player in final_team:
        predicted_team_html += f"<tr>"
        predicted_team_html += f"<td class='player-name'>{player['name']}</td>"
        predicted_team_html += f"<td class='team-name'>{player['team']}</td>"
        predicted_team_html += f"<td class='points'>{player['points']}</td>"
        predicted_team_html += f"</tr>"
    
    predicted_team_html += "</table></div></div>"
    
    # Show results
    return templates.TemplateResponse("result.html", {
        "request": request,
        "predicted_team": predicted_team_html,
        "team1": team1_name,
        "team2": team2_name,
        "venue": venue
    })

import os
import requests
import json
from datetime import datetime

# CONFIGURATION SECTION
DEBUG_MODE = True 

headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:131.0) Gecko/20100101 Firefox/131.0",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.5",
    "x-api-key": "CHi8Hy5CEE4khd46XNYL23dCFX96oUdw6qOt1Dnh",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site"
}

api_config = {
    "base_url": "https://api.bettingpros.com/v3",
    "location": "OH",
    "sport": "NFL",
    "limit": 16,
    "season": 2024,
    "week": 6
}

bookie_map = {
    0: "BettingPros", 
    12: "DraftKings", 
    10: "FanDuel", 
    19: "BetMGM", 
    13: "Caesars", 
    33: "ESPNBet", 
    24: "Bet365", 
    18: "BetRivers"
}

prop_market_map = {
    103: {"name": "Passing Yards", "directory": "passing"},
    100: {"name": "Completions", "directory": "passing"},
    333: {"name": "Passing Attempts", "directory": "passing"},
    101: {"name": "Interceptions", "directory": "passing"},
    106: {"name": "Rushing Attempts", "directory": "rushing"},
    107: {"name": "Rushing Yards", "directory": "rushing"},
    105: {"name": "Receiving Yards", "directory": "receiving"},
    104: {"name": "Receptions", "directory": "receiving"},
    253: {"name": "Fantasy Points", "directory": "fantasy"},
    78:  {"name": "Anytime TD", "directory": "anytime_td"}
}

markets = [
    {"market_id": 3, "name": "Spreads"},   
    {"market_id": 2, "name": "Totals"},    
    {"market_id": 1, "name": "Moneylines"}
]

event_statuses_to_skip = {"closed", "complete"}

data_base_dir = "data/betting_mkt/"  # Unified base directory

# Ensure base directory exists
os.makedirs(data_base_dir, exist_ok=True)

# COMMON FUNCTIONS
def debug_log(message):
    if DEBUG_MODE:
        print(f"[DEBUG] {message}")

def log_run_status(status, game_count):
    log_file_path = os.path.join(data_base_dir, "run_log.txt")
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"{current_time} - {status} - Fetched betting data for {game_count} games\n"
    
    with open(log_file_path, "a") as file:
        file.write(log_entry)
    
    debug_log(f"Run status logged: {status}, games fetched: {game_count}")

def clean_stadium_type(stadium_type):
    return stadium_type.replace("_", " ")

# MAIN FUNCTIONS
def save_game_info(event_id, home_team, away_team, stadium_type, weather, scheduled_date):
    event_dir_name = f"{away_team} @ {home_team} - {scheduled_date.strftime('%m-%d-%Y')}"
    game_info_path = os.path.join(data_base_dir, event_dir_name, "game_info.json")
    os.makedirs(os.path.dirname(game_info_path), exist_ok=True)

    game_info_data = {
        "home_team": home_team,
        "away_team": away_team,
        "stadium_type": clean_stadium_type(stadium_type),
        "weather": weather,
        "scheduled_date": scheduled_date.strftime("%Y-%m-%d %H:%M:%S")
    }

    with open(game_info_path, "w") as file:
        json.dump(game_info_data, file, indent=4)
    
    debug_log(f"Game info saved for event {event_id}.")

def save_bookie_data(data, directory, event_id, home_team, away_team, scheduled_date):
    event_dir_name = f"{away_team} @ {home_team} - {scheduled_date.strftime('%m-%d-%Y')}"
    file_path = os.path.join(data_base_dir, directory, event_dir_name, f"{data['bookie']}.json")
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    file_data = []

    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            file_data = json.load(file)

    file_data.append({
        "timestamp": current_time,
        "data": data
    })

    with open(file_path, "w") as file:
        json.dump(file_data, file, indent=4)

    debug_log(f"Bookie data saved for {data['bookie']} in event {event_id}.")

def process_offers_data(offers_data, directory, event_info):
    if 'offers' not in offers_data or len(offers_data['offers']) == 0:
        print(f"No offers found for {directory}.")
        return
    debug_log(f"Processing offers for {directory}.")
    for offer in offers_data['offers']:
        event_id = str(offer.get('event_id', 'Unknown'))
        if event_id not in event_info:
            print(f"Warning: Event ID {event_id} not found in event_info. Skipping this event.")
            continue
        
        home_team = event_info[event_id]['home']
        away_team = event_info[event_id]['away']
        stadium_type = event_info[event_id]['stadium_type']
        weather = event_info[event_id]['weather']
        scheduled_date = event_info[event_id]['scheduled']

        save_game_info(event_id, home_team, away_team, stadium_type, weather, scheduled_date)

        selections = offer.get('selections', [])
        for selection in selections:
            team_label = selection.get('label', 'Unknown Team')
            books = selection.get('books', [])
            for book in books:
                lines = book.get('lines', [])
                for line in lines:
                    book_id = book.get('id', 'Unknown')
                    cost = line.get('cost', 'N/A')
                    betting_line = line.get('line', 'N/A')
                    
                    bookie_name = bookie_map.get(book_id, "Unknown Bookie")
                    data = {
                        "team_label": team_label,
                        "betting_line": betting_line,
                        "cost": cost,
                        "bookie": bookie_name
                    }
                    save_bookie_data(data, directory, event_id, home_team, away_team, scheduled_date)
    debug_log(f"Offers processed for {directory}.")

def fetch_all_offers(market_id, event_id_string):
    base_url = api_config['base_url'].rstrip("/")
    url = f"{base_url}/offers?sport={api_config['sport']}&market_id={market_id}&event_id={event_id_string}&location={api_config['location']}&limit={api_config['limit']}&page=1"
    debug_log(f"Fetching URL: {url}")

    offers_data = {"offers": []}
    
    while url:
        try:
            response_offers = requests.get(url, headers=headers)
            response_offers.raise_for_status()
            data = response_offers.json()

            if "offers" in data:
                offers_data["offers"].extend(data["offers"])

            next_url = data.get("_pagination", {}).get("next")
            url = f"{base_url}{next_url}" if next_url else None
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data: {e}")
            break

    debug_log(f"Offers fetched for market {market_id}.")
    return offers_data

def fetch_events(week, season):
    url_events = f"{api_config['base_url']}/events?sport={api_config['sport']}&week={week}&season={season}"

    response_events = requests.get(url_events, headers=headers)
    events_data = response_events.json()

    event_info = {}
    event_ids = []

    for event in events_data['events']:
        status = event.get('status', '').strip().lower()
        if status not in event_statuses_to_skip:
            event_id = str(event['id'])
            event_ids.append(event_id)

            participants = event.get('participants', [])
            home_team = participants[1]['name'] if len(participants) > 1 else "Unknown"
            away_team = participants[0]['name'] if len(participants) > 0 else "Unknown"
            scheduled_date = datetime.strptime(event['scheduled'], "%Y-%m-%d %H:%M:%S")

            event_info[event_id] = {
                "home": home_team,
                "away": away_team,
                "stadium_type": event.get("venue", {}).get("stadium_type", "Unknown"),
                "weather": event.get("weather", {}),
                "scheduled": scheduled_date
            }

    event_id_string = ":".join(event_ids)
    
    if not event_id_string:
        print("No valid events found.")
        exit()

    debug_log(f"Fetched events for week {week}, season {season}.")
    return event_info, event_id_string


# MAIN EXECUTION SECTION
week = api_config["week"]
season = api_config["season"]

event_info, event_id_string = fetch_events(week, season)

if not event_id_string:
    print("No valid events found.")
    log_run_status("Failure", 0)
    exit()

for market in markets:
    market_id = market['market_id']
    all_offers = fetch_all_offers(market_id, event_id_string)
    process_offers_data(all_offers, market['name'], event_info)

for market_id, market_data in prop_market_map.items():
    directory = market_data["directory"]
    all_offers = fetch_all_offers(market_id, event_id_string)
    process_offers_data(all_offers, directory, event_info)

log_run_status("Success", len(event_info))



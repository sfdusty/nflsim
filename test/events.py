# functions/format_games.py

def format_games(data):
    events = data.get("events", [])
    
    if not events:
        print("No game information available.")
        return
    
    for event in events:
        # Basic game info
        home_team = event.get('home')
        visitor_team = event.get('visitor')
        scheduled_time = event.get('scheduled')
        venue_info = event.get('venue', {})
        broadcasts = event.get('broadcasts', [])
        
        # Venue
        venue_name = venue_info.get('name')
        venue_city = venue_info.get('city')
        venue_state = venue_info.get('state', '')
        
        # Weather (optional - placeholder in this case)
        weather_info = event.get('weather', {})
        forecast_temp = weather_info.get('forecast_temp', 'N/A')
        forecast_rain_chance = weather_info.get('forecast_rain_chance', 'N/A')
        
        # Home and visitor records
        home_record = None
        visitor_record = None
        for participant in event.get('participants', []):
            if participant.get('id') == home_team:
                home_record = participant['team']['record']
            elif participant.get('id') == visitor_team:
                visitor_record = participant['team']['record']
        
        print("=" * 40)
        print(f"{home_team} vs {visitor_team}")
        print(f"Scheduled: {scheduled_time}")
        print(f"Venue: {venue_name}, {venue_city}, {venue_state}")
        print(f"Home Record: {home_record['W']}-{home_record['L']}-{home_record['T']}")
        print(f"Visitor Record: {visitor_record['W']}-{visitor_record['L']}-{visitor_record['T']}")
        
        # Broadcast info
        if broadcasts:
            for broadcast in broadcasts:
                print(f"Broadcast on: {broadcast.get('network')} ({broadcast.get('type')})")
        
        # Weather info
        print(f"Weather Forecast: Temp {forecast_temp}°F, Rain Chance {forecast_rain_chance}%")
        print("=" * 40)
        print("\n")


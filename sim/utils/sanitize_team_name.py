# sim/utils/sanitize_team_name.py

import re

def sanitize_team_name(team_name: str) -> str:
    """
    Sanitizes team names to be filesystem-friendly by replacing spaces and removing special characters.
    
    Args:
        team_name (str): The team name to sanitize.
    
    Returns:
        str: Sanitized team name.
    """
    # Replace spaces with underscores
    sanitized = team_name.replace(' ', '_')
    # Remove any character that is not alphanumeric or underscore
    sanitized = re.sub(r'[^\w]', '', sanitized)
    return sanitized


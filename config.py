"""
Configuration settings for the Travel Planner application.
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
API_TIMEOUT = int(os.getenv("API_TIMEOUT", "120"))  # seconds

# Application Settings
APP_TITLE = "🌍 AI-Powered Travel Itinerary Planner"
APP_ICON = "🧳"
DEFAULT_LAYOUT = "wide"

# Cache Settings
CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))  # 1 hour in seconds

# Default Values
DEFAULT_TRIP_DAYS = 7
DEFAULT_TRAVELERS = 2
DEFAULT_TRIP_TYPE = "Leisure"

# Feature Flags
ENABLE_ANALYTICS = os.getenv("ENABLE_ANALYTICS", "false").lower() == "true"
ENABLE_FEEDBACK = os.getenv("ENABLE_FEEDBACK", "true").lower() == "true"
ENABLE_CACHING = os.getenv("ENABLE_CACHING", "true").lower() == "true"

# Error Messages
ERROR_MESSAGES = {
    "api_connection": "Unable to connect to the planning service. Please try again later.",
    "invalid_response": "Received an invalid response from the planning service.",
    "timeout": "The request timed out. Please try again or simplify your search criteria.",
    "no_results": "No results found for your search criteria. Please try different parameters."
}

# UI Settings
THEME_PRIMARY_COLOR = "#4CAF50"
THEME_SECONDARY_COLOR = "#2196F3"
THEME_WARNING_COLOR = "#FFC107"
THEME_ERROR_COLOR = "#F44336"
THEME_SUCCESS_COLOR = "#4CAF50"

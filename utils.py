"""
Utility functions for the Travel Planner application.
"""
import re
import json
import time
import logging
import requests
from datetime import datetime, timedelta
import streamlit as st
from typing import Dict, List, Any, Optional, Union, Tuple

import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Cache decorator for expensive operations
def st_cache_with_ttl(ttl_seconds=config.CACHE_TTL):
    """
    Custom cache decorator with time-to-live (TTL)
    """
    def decorator(func):
        # Use streamlit's cache mechanism
        cached_func = st.cache_data(ttl=ttl_seconds)(func)
        return cached_func
    return decorator

# Price extraction and formatting
def extract_price(price_str: Union[str, float, int, None]) -> float:
    """
    Extract numeric value from price string.
    
    Args:
        price_str: Price string or numeric value
        
    Returns:
        Extracted price as float
    """
    if not price_str:  # Handle None or empty string
        return 0.0
    
    if isinstance(price_str, (int, float)):
        return float(price_str)
    
    # Check for non-numeric indicators
    if isinstance(price_str, str) and price_str.upper() in ['NA', 'N/A', 'NONE', 'NULL', '-']:
        return 0.0
    
    try:
        # Remove currency symbols and commas
        cleaned_price = str(price_str)
        for symbol in ['₹', '$', '€', '£', '¥']:
            cleaned_price = cleaned_price.replace(symbol, '')
        
        # Remove commas and spaces
        cleaned_price = cleaned_price.replace(',', '').replace(' ', '')
        
        # Extract numeric part using regex
        match = re.search(r'(\d+(\.\d+)?)', cleaned_price)
        if match:
            return float(match.group(1))
        
        # If no match found, try direct conversion
        return float(cleaned_price) if cleaned_price else 0.0
    except (ValueError, TypeError):
        logger.warning(f"Could not extract price from: {price_str}")
        return 0.0

def format_price(price: float, currency: str = "$") -> str:
    """
    Format price with currency symbol.
    
    Args:
        price: Price value
        currency: Currency symbol
        
    Returns:
        Formatted price string
    """
    return f"{currency}{price:,.2f}"

# Time and duration calculations
def calculate_duration_estimate(departure_time: str, arrival_time: str) -> str:
    """
    Estimate the duration between departure and arrival times.
    
    Args:
        departure_time: Departure time string
        arrival_time: Arrival time string
        
    Returns:
        Duration string (e.g., "2h 30m")
    """
    try:
        # Try to parse times in common formats
        dep_formats = ['%H:%M', '%I:%M %p', '%H:%M:%S', '%I:%M:%S %p']
        arr_formats = ['%H:%M', '%I:%M %p', '%H:%M:%S', '%I:%M:%S %p']
        
        # Extract time using regex if it's part of a more complex string
        dep_time_match = re.search(r'(\d{1,2}:\d{2}(?::\d{2})?(?: ?[AP]M)?)', departure_time)
        arr_time_match = re.search(r'(\d{1,2}:\d{2}(?::\d{2})?(?: ?[AP]M)?)', arrival_time)
        
        dep_time_str = dep_time_match.group(1) if dep_time_match else departure_time
        arr_time_str = arr_time_match.group(1) if arr_time_match else arrival_time
        
        # Try different formats
        dep_dt = None
        arr_dt = None
        
        for fmt in dep_formats:
            try:
                dep_dt = datetime.strptime(dep_time_str, fmt)
                break
            except ValueError:
                continue
                
        for fmt in arr_formats:
            try:
                arr_dt = datetime.strptime(arr_time_str, fmt)
                break
            except ValueError:
                continue
        
        if dep_dt and arr_dt:
            # Handle overnight flights (where arrival is earlier than departure)
            if arr_dt < dep_dt:
                arr_dt = arr_dt.replace(day=dep_dt.day + 1)
            
            # Calculate duration
            duration = arr_dt - dep_dt
            hours, remainder = divmod(duration.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            
            if hours > 0 and minutes > 0:
                return f"{hours}h {minutes}m"
            elif hours > 0:
                return f"{hours}h"
            else:
                return f"{minutes}m"
    except Exception as e:
        logger.warning(f"Error calculating duration: {str(e)}")
    
    # If anything goes wrong, return a generic message
    return "Duration information not available"

# API interaction
@st_cache_with_ttl(ttl_seconds=300)  # Cache for 5 minutes
def fetch_itinerary_data(
    origin: str, 
    destination: str, 
    trip_type: str, 
    num_days: int, 
    people: int, 
    start_date: datetime.date, 
    end_date: datetime.date
) -> Optional[Dict[str, Any]]:
    """
    Fetch itinerary data from the API with error handling and retries.
    
    Args:
        origin: Origin location
        destination: Destination location
        trip_type: Type of trip (e.g., Leisure, Business)
        num_days: Number of days for the trip
        people: Number of travelers
        start_date: Start date
        end_date: End date
        
    Returns:
        Itinerary data dictionary or None if failed
    """
    max_retries = 2
    retry_delay = 2  # seconds
    
    payload = {
        "current_location": origin,
        "destination": destination,
        "trip_type": trip_type,
        "num_days": num_days,
        "people": people,
        "start_date": start_date.strftime("%Y/%m/%d"),
        "end_date": end_date.strftime("%Y/%m/%d")
    }
    
    url = f"{config.API_BASE_URL}/plan"
    
    for attempt in range(max_retries + 1):
        try:
            response = requests.post(
                url, 
                json=payload,
                timeout=config.API_TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if the expected keys exist
                if "data" in data and "trip" in data["data"] and "itinerary" in data["data"]["trip"]:
                    return data["data"]["trip"]["itinerary"]
                else:
                    logger.error(f"API response missing expected structure: {data}")
                    if attempt < max_retries:
                        time.sleep(retry_delay)
                        continue
                    return None
            else:
                logger.error(f"API error: {response.status_code} - {response.text}")
                if attempt < max_retries:
                    time.sleep(retry_delay)
                    continue
                return None
                
        except requests.exceptions.Timeout:
            logger.error(f"API request timed out (attempt {attempt + 1}/{max_retries + 1})")
            if attempt < max_retries:
                time.sleep(retry_delay)
                continue
            return None
            
        except Exception as e:
            logger.error(f"Error fetching itinerary data: {str(e)}")
            if attempt < max_retries:
                time.sleep(retry_delay)
                continue
            return None
    
    return None

# Data validation
def is_valid_date_range(start_date: datetime.date, end_date: datetime.date) -> bool:
    """
    Check if date range is valid.
    
    Args:
        start_date: Start date
        end_date: End date
        
    Returns:
        True if valid, False otherwise
    """
    today = datetime.now().date()
    max_future_date = today + timedelta(days=365)  # Max 1 year in future
    
    return (
        start_date >= today and
        end_date >= start_date and
        end_date <= max_future_date and
        (end_date - start_date).days <= 30  # Max 30 days trip
    )

def is_valid_location(location: str) -> bool:
    """
    Basic validation for location strings.
    
    Args:
        location: Location string
        
    Returns:
        True if valid, False otherwise
    """
    if not location or len(location.strip()) < 2:
        return False
    
    # Check for invalid characters
    invalid_chars = re.findall(r'[^a-zA-Z0-9\s\-\',.]', location)
    if invalid_chars:
        return False
    
    return True

# UI helpers
def show_error(message: str, icon: str = "❌"):
    """
    Display a styled error message.
    
    Args:
        message: Error message
        icon: Icon to display
    """
    st.error(f"{icon} {message}")

def show_success(message: str, icon: str = "✅"):
    """
    Display a styled success message.
    
    Args:
        message: Success message
        icon: Icon to display
    """
    st.success(f"{icon} {message}")

def show_info(message: str, icon: str = "ℹ️"):
    """
    Display a styled info message.
    
    Args:
        message: Info message
        icon: Icon to display
    """
    st.info(f"{icon} {message}")

def show_warning(message: str, icon: str = "⚠️"):
    """
    Display a styled warning message.
    
    Args:
        message: Warning message
        icon: Icon to display
    """
    st.warning(f"{icon} {message}")

def create_progress_bar(total_steps: int) -> Tuple[st.progress, st.empty]:
    """
    Create a progress bar with a status message.
    
    Args:
        total_steps: Total number of steps
        
    Returns:
        Tuple of progress bar and status message placeholder
    """
    progress_bar = st.progress(0)
    status_message = st.empty()
    return progress_bar, status_message

def update_progress(
    progress_bar: st.progress, 
    status_message: st.empty, 
    step: int, 
    total_steps: int, 
    message: str
):
    """
    Update progress bar and status message.
    
    Args:
        progress_bar: Streamlit progress bar
        status_message: Streamlit empty placeholder for status message
        step: Current step
        total_steps: Total number of steps
        message: Status message
    """
    progress_value = min(step / total_steps, 1.0)
    progress_bar.progress(progress_value)
    status_message.text(message)

# Analytics helpers
def log_user_action(action: str, metadata: Dict[str, Any] = None):
    """
    Log user action for analytics if enabled.
    
    Args:
        action: Action name
        metadata: Additional metadata
    """
    if not config.ENABLE_ANALYTICS:
        return
    
    if metadata is None:
        metadata = {}
    
    try:
        logger.info(f"USER_ACTION: {action} - {json.dumps(metadata)}")
        # In a production app, you might send this to an analytics service
    except Exception as e:
        logger.error(f"Error logging user action: {str(e)}")

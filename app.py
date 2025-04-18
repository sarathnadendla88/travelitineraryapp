import streamlit as st
import requests
import json
from datetime import date, timedelta, datetime
import re

# Set page configuration
st.set_page_config(page_title="🌍 Travel Planner", layout="wide")
st.title("🧳 AI-Powered Travel Itinerary Planner")

# Function to fetch data from API
def fetch_itinerary_data(origin, destination, trip_type, num_days, people, start_date, end_date):
    try:
        url = "http://127.0.0.1:8000/plan"

        payload = {
            "current_location": origin,
            "destination": destination,
            "trip_type": trip_type,
            "num_days": num_days,
            "people": people,
            "start_date": start_date.strftime("%Y/%m/%d"),
            "end_date": end_date.strftime("%Y/%m/%d")
        }

        # Show a spinner while waiting for the API response
        with st.spinner(f"Planning your {num_days}-day trip to {destination}..."):
            pass

        response = requests.post(url, json=payload)

        if response.status_code == 200:
            data = response.json()

            # Check if the expected keys exist
            if "data" in data and "trip" in data["data"] and "itinerary" in data["data"]["trip"]:
                return data["data"]["trip"]["itinerary"]
            else:
                st.error("API response does not contain the expected data structure.")
                st.write("Expected path: data -> trip -> itinerary")
                st.write("Actual response structure:")
                st.json(data)
                return None
        else:
            st.error(f"Error: API returned status code {response.status_code}")
            st.code(response.text)
            return None
    except Exception as e:
        st.error(f"Error connecting to API: {str(e)}")
        st.write(f"Exception details: {type(e).__name__}")
        import traceback
        st.code(traceback.format_exc())
        return None

# Trip information display has been removed

# Display trip summary with cheapest flight and hotel prices
def display_trip_summary(itinerary_data):
    # Create a container with a light background and compact design
    with st.container():
        st.markdown("""
        <style>
        .summary-box {
            background-color: #f8f9fa;
            padding: 8px;
            border-radius: 8px;
            margin-bottom: 15px;
            border-left: 3px solid #4CAF50;
            font-size: 0.9em;
        }
        .summary-title {
            font-size: 0.85em;
            font-weight: bold;
            margin-bottom: 3px;
            color: #555;
        }
        .price-highlight {
            color: #2E7D32;
            font-weight: bold;
        }
        .total-price {
            color: #1565C0;
            font-weight: bold;
            font-size: 1.1em;
        }
        .summary-item {
            margin-bottom: 2px;
        }
        </style>
        """, unsafe_allow_html=True)

        # Find cheapest flight
        cheapest_flight = None
        cheapest_flight_price = float('inf')
        flights = itinerary_data.get("flights", [])

        if flights:
            for flight in flights:
                price_str = flight.get("price", "")
                if price_str:
                    # Extract numeric value from price string
                    try:
                        price_value = ''.join(filter(lambda x: x.isdigit() or x == '.', str(price_str)))
                        if price_value:
                            price = float(price_value)
                            if price < cheapest_flight_price:
                                cheapest_flight_price = price
                                cheapest_flight = flight
                    except:
                        pass

        # Find cheapest hotel
        cheapest_hotel = None
        cheapest_hotel_price = float('inf')
        hotels = itinerary_data.get("hotels", [])

        if hotels:
            for hotel in hotels:
                price_str = hotel.get("price_per_night", "")
                if price_str:
                    # Extract numeric value from price string
                    try:
                        price_value = ''.join(filter(lambda x: x.isdigit() or x == '.', str(price_str)))
                        if price_value:
                            price = float(price_value)
                            if price < cheapest_hotel_price:
                                cheapest_hotel_price = price
                                cheapest_hotel = hotel
                    except:
                        pass

        # Calculate total cost
        total_cost = 0
        currency_symbol = "$"  # Default

        # Add flight cost
        flight_cost = 0
        if cheapest_flight:
            try:
                price_value = ''.join(filter(lambda x: x.isdigit() or x == '.', str(cheapest_flight.get("price", "0"))))
                if price_value:
                    flight_cost = float(price_value)
                    total_cost += flight_cost

                    # Try to detect currency
                    price_str = cheapest_flight.get("price", "")
                    if isinstance(price_str, str):
                        if "$" in price_str:
                            currency_symbol = "$"
                        elif "€" in price_str:
                            currency_symbol = "€"
                        elif "£" in price_str:
                            currency_symbol = "£"
                        elif "₹" in price_str:
                            currency_symbol = "₹"
            except:
                pass

        # Add hotel cost
        hotel_cost = 0
        num_days = len(itinerary_data.get("daily_plan", {}))
        if num_days == 0:
            num_days = 3  # Default if no daily plan

        if cheapest_hotel:
            try:
                price_value = ''.join(filter(lambda x: x.isdigit() or x == '.', str(cheapest_hotel.get("price_per_night", "0"))))
                if price_value:
                    hotel_cost_per_night = float(price_value)
                    hotel_cost = hotel_cost_per_night * num_days
                    total_cost += hotel_cost
            except:
                pass

        # Create a compact summary box
        html = '<div class="summary-box">'
        html += '<div style="display: flex; justify-content: space-between; align-items: center;">'  # Flex container

        # Left section - Flight
        html += '<div style="flex: 1; padding-right: 10px;">'  # Flight section
        html += '<div class="summary-title">✈️ CHEAPEST FLIGHT</div>'
        if cheapest_flight:
            airline = cheapest_flight.get("airline", "Airline")
            flight_number = cheapest_flight.get("flight_number", "")
            price = cheapest_flight.get("price", "Price not available")
            html += f'<div class="summary-item">{airline} {flight_number}</div>'
            html += f'<div class="summary-item price-highlight">{price}</div>'
        else:
            html += '<div class="summary-item">No flight info available</div>'
        html += '</div>'  # End flight section

        # Middle section - Hotel
        html += '<div style="flex: 1; padding-right: 10px; border-left: 1px solid #ddd; padding-left: 10px;">'  # Hotel section
        html += '<div class="summary-title">🏨 CHEAPEST HOTEL</div>'
        if cheapest_hotel:
            name = cheapest_hotel.get("name", "Hotel")
            price = cheapest_hotel.get("price_per_night", "Price not available")
            html += f'<div class="summary-item">{name}</div>'
            html += f'<div class="summary-item price-highlight">{price}/night</div>'
        else:
            html += '<div class="summary-item">No hotel info available</div>'
        html += '</div>'  # End hotel section

        # Right section - Total Cost
        html += '<div style="flex: 1; border-left: 1px solid #ddd; padding-left: 10px;">'  # Total cost section
        html += '<div class="summary-title">💰 ESTIMATED COST</div>'
        if total_cost > 0:
            html += f'<div class="summary-item total-price">{currency_symbol}{total_cost:.2f}</div>'
            html += f'<div class="summary-item" style="font-size: 0.8em;">Flight: {currency_symbol}{flight_cost:.2f}</div>'
            html += f'<div class="summary-item" style="font-size: 0.8em;">Hotel ({num_days} nights): {currency_symbol}{hotel_cost:.2f}</div>'
        else:
            html += '<div class="summary-item">Cost info not available</div>'
        html += '</div>'  # End total cost section

        html += '</div>'  # End flex container
        html += '</div>'  # End summary box

        st.markdown(html, unsafe_allow_html=True)

# Function to extract numeric value from price string
def extract_price(price_str):
    if not price_str:  # Handle None or empty string
        return float(0)
    if not isinstance(price_str, str):
        return float(price_str)
    # Check for non-numeric indicators
    if price_str.upper() in ['NA', 'N/A', 'NONE', 'NULL', '-']:
        return float(0)
    # Remove currency symbols and commas
    cleaned_price = price_str
    for symbol in ['₹', '$', '€', '£', '¥']:
        cleaned_price = cleaned_price.replace(symbol, '')
    # Remove commas and spaces
    cleaned_price = cleaned_price.replace(',', '').replace(' ', '')
    # Convert to float, default to 0 if empty
    return float(cleaned_price) if cleaned_price else float(0)

# Function to estimate duration between two time strings
def calculate_duration_estimate(departure_time, arrival_time):
    """Estimate the duration between departure and arrival times.
    This is a simplified calculation and may not be accurate for all formats.
    """
    try:
        # Try to parse times in common formats
        dep_formats = ['%H:%M', '%I:%M %p', '%H:%M:%S', '%I:%M:%S %p']
        arr_formats = ['%H:%M', '%I:%M %p', '%H:%M:%S', '%I:%M:%S %p']

        # Extract time using regex if it's part of a more complex string
        dep_time_match = re.search(r'(\d{1,2}:\d{2}(?::\d{2})?(?: ?[AP]M)?)', departure_time)
        arr_time_match = re.search(r'(\d{1,2}:\d{2}(?::\d{2})?(?: ?[AP]M)?)', arrival_time)

        if dep_time_match:
            dep_time_str = dep_time_match.group(1)
        else:
            dep_time_str = departure_time

        if arr_time_match:
            arr_time_str = arr_time_match.group(1)
        else:
            arr_time_str = arrival_time

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
        # If anything goes wrong, return a generic message
        return "Duration information not available"

# Display flights
def display_flights(flights):
    st.header("✈️ Available Flights")

    if not flights or len(flights) == 0:
        st.warning("No flights available for this route.")
        return

    # Sort flights by price for better display
    try:
        sorted_flights = sorted(flights, key=lambda x: extract_price(x.get("price", 0)))
    except Exception as e:
        st.warning(f"Could not sort flights by price: {e}")
        sorted_flights = flights

    # Display flights in a grid
    for i, flight in enumerate(sorted_flights):
        with st.expander(f"{flight.get('airline', 'Airline')} - {flight.get('from', 'Origin')} to {flight.get('to', 'Destination')} - {flight.get('price', 'Price')}" + (" 🏆 Best Value!" if i == 0 else ""), expanded=True):
            # Flight details in a single column layout (no images)
            st.markdown(f"**Route:** {flight.get('from', 'Origin')} → {flight.get('to', 'Destination')}")

            # Flight number if available
            if 'flight_number' in flight:
                st.markdown(f"**Flight Number:** {flight.get('flight_number')}")

            # Departure and arrival information
            if 'departure_time' in flight or 'departure_date' in flight:
                dep_date = flight.get('departure_date', '')
                dep_time = flight.get('departure_time', '')
                if dep_date or dep_time:
                    st.markdown(f"**Departure:** {dep_date}{' at ' if dep_date and dep_time else ''}{dep_time}")

            if 'arrival_time' in flight or 'arrival_date' in flight:
                arr_date = flight.get('arrival_date', '')
                arr_time = flight.get('arrival_time', '')
                if arr_date or arr_time:
                    st.markdown(f"**Arrival:** {arr_date}{' at ' if arr_date and arr_time else ''}{arr_time}")

            # Display journey duration
            if 'duration' in flight and flight['duration']:
                st.markdown(f"**⏱️ Journey Duration:** {flight['duration']}")
            # Calculate duration if not provided but we have departure and arrival times
            elif 'departure_time' in flight and 'arrival_time' in flight and not ('duration' in flight):
                try:
                    # This is a simplified calculation and may not be accurate for all formats
                    # A more robust implementation would parse the times properly
                    st.markdown(f"**⏱️ Journey Duration:** Approximately {calculate_duration_estimate(flight.get('departure_time', ''), flight.get('arrival_time', ''))}")
                except:
                    pass

            # Layover information - moved here to display right after arrival information
            if 'layover_details' in flight and flight['layover_details']:
                layover_details = flight['layover_details']
                if not layover_details or len(layover_details) == 0:
                    st.markdown("**✅ Direct Flight**")
                else:
                    st.markdown(f"**🛑 Stops:** {len(layover_details)}")

                    # Display detailed layover information
                    st.markdown("**Layover Details:**")
                    for layover in layover_details:
                        city = layover.get('city', 'N/A')
                        duration = layover.get('duration', 'N/A')
                        arrival = layover.get('arrival_time', 'N/A')
                        departure = layover.get('departure_time', 'N/A')
                        terminal_change = layover.get('terminal_change', 'No')

                        # Create a formatted layover display
                        st.markdown(f"""<div style='background-color: #f8f9fa; padding: 10px; border-radius: 5px; margin-bottom: 5px;'>
                            <strong>🌆 {city}</strong> - ⏱️ {duration}<br>
                            🛬 Arrival: {arrival} | 🛫 Departure: {departure}<br>
                            {'🚶 Terminal change required' if terminal_change.lower() == 'yes' else '✓ No terminal change'}
                        </div>""", unsafe_allow_html=True)
            elif 'stops' in flight:
                stops = flight.get('stops', 0)
                if stops == 0:
                    st.markdown("**✅ Direct Flight**")
                else:
                    st.markdown(f"**🛑 Stops:** {stops}")
            elif 'layover' in flight and flight['layover']:
                if flight['layover'].lower() == 'direct flight' or flight['layover'] == '':
                    st.markdown("**✅ Direct Flight**")
                else:
                    st.markdown(f"**🛑 Layover:** {flight['layover']}")
            elif 'layovers' in flight and flight['layovers']:
                st.markdown(f"**🛑 Layover:** {flight['layovers']}")
            else:
                st.markdown("**✅ Direct Flight**")

            # Book now button for flight
            st.markdown(f"[Book Now]({flight.get('url', '#')})")

            # Create a styled box for fare class information
            st.markdown("### Fare Class Options")

            # Get the current fare class
            current_fare_class = flight.get('class', 'Economy')

            # Get price and baggage information for the current fare class
            current_price = flight.get('price', 'N/A')

            # Set default baggage allowances based on airline standards if not provided
            current_fare_class_lower = current_fare_class.lower()

            # Default baggage allowances by class
            if 'economy' in current_fare_class_lower or 'standard' in current_fare_class_lower:
                default_check_in = '20 kg'
                default_hand = '7 kg'
            elif 'premium' in current_fare_class_lower:
                default_check_in = '25 kg'
                default_hand = '10 kg'
            elif 'business' in current_fare_class_lower or 'first' in current_fare_class_lower:
                default_check_in = '32 kg'
                default_hand = '14 kg'
            else:  # Default to economy if class is unknown
                default_check_in = '20 kg'
                default_hand = '7 kg'

            # Use provided values or defaults
            current_check_in = flight.get('check_in_baggage', default_check_in)
            current_hand = flight.get('hand_baggage', default_hand)

            # If values are empty or N/A, use defaults
            if current_check_in == 'N/A' or not current_check_in:
                current_check_in = default_check_in
            if current_hand == 'N/A' or not current_hand:
                current_hand = default_hand

            # Create a container with three columns for the three fare classes
            col_eco, col_premium, col_business = st.columns(3)

            # Economy Class
            with col_eco:
                # Determine if this is the current fare class
                is_current = 'economy' in current_fare_class.lower() or 'standard' in current_fare_class.lower()
                border_style = "border: 2px solid #4CAF50;" if is_current else ""

                # Display Economy class details
                st.markdown(f"""
                <div style="background-color: #f0f0f0; padding: 10px; border-radius: 5px; margin-bottom: 10px; {border_style}">
                    <h4 style="margin-top: 0;">🔵 Economy</h4>
                    <p><strong>Price:</strong> {current_price if is_current else 'Available'}</p>
                    <p><strong>Check-in Baggage:</strong> {current_check_in if is_current else '15-20 kg (33-44 lbs)'}</p>
                    <p><strong>Hand Baggage:</strong> {current_hand if is_current else '7-8 kg (15-18 lbs)'}</p>
                </div>
                """, unsafe_allow_html=True)

            # Premium Economy Class
            with col_premium:
                # Determine if this is the current fare class
                is_current = 'premium' in current_fare_class.lower()
                border_style = "border: 2px solid #4CAF50;" if is_current else ""

                # Calculate premium economy price (typically 30-50% more than economy)
                if is_current:
                    premium_price = current_price
                    premium_check_in = current_check_in
                    premium_hand = current_hand
                else:
                    # If the current class is economy, estimate premium price
                    if 'economy' in current_fare_class.lower() or 'standard' in current_fare_class.lower():
                        try:
                            # Try to extract numeric value from price
                            price_value = ''.join(filter(lambda x: x.isdigit() or x == '.', str(current_price)))
                            if price_value:
                                base_price = float(price_value)
                                premium_price = f"~${int(base_price * 1.4)}" if '$' in str(current_price) else f"~{int(base_price * 1.4)}"
                            else:
                                premium_price = 'Available (30-50% more)'
                        except:
                            premium_price = 'Available (30-50% more)'
                        premium_check_in = '25-30 kg (55-66 lbs)'
                        premium_hand = '10-12 kg (22-26 lbs)'
                    else:  # If current class is business, estimate premium price
                        premium_price = 'Available (30-40% less than Business)'
                        premium_check_in = '25-30 kg (55-66 lbs)'
                        premium_hand = '10-12 kg (22-26 lbs)'

                # Display Premium Economy class details
                st.markdown(f"""
                <div style="background-color: #fff2e6; padding: 10px; border-radius: 5px; margin-bottom: 10px; {border_style}">
                    <h4 style="margin-top: 0;">⭐ Premium Economy</h4>
                    <p><strong>Price:</strong> {premium_price}</p>
                    <p><strong>Check-in Baggage:</strong> {premium_check_in}</p>
                    <p><strong>Hand Baggage:</strong> {premium_hand}</p>
                </div>
                """, unsafe_allow_html=True)

            # Business Class
            with col_business:
                # Determine if this is the current fare class
                is_current = 'business' in current_fare_class.lower() or 'first' in current_fare_class.lower()
                border_style = "border: 2px solid #4CAF50;" if is_current else ""

                # Calculate business price (typically 2-3x more than economy)
                if is_current:
                    business_price = current_price
                    business_check_in = current_check_in
                    business_hand = current_hand
                else:
                    # If the current class is economy, estimate business price
                    if 'economy' in current_fare_class.lower() or 'standard' in current_fare_class.lower():
                        try:
                            # Try to extract numeric value from price
                            price_value = ''.join(filter(lambda x: x.isdigit() or x == '.', str(current_price)))
                            if price_value:
                                base_price = float(price_value)
                                business_price = f"~${int(base_price * 2.5)}" if '$' in str(current_price) else f"~{int(base_price * 2.5)}"
                            else:
                                business_price = 'Available (2-3x more)'
                        except:
                            business_price = 'Available (2-3x more)'
                        business_check_in = '30-40 kg (66-88 lbs)'
                        business_hand = '14-18 kg (31-40 lbs)'
                    else:  # If current class is premium, estimate business price
                        try:
                            # Try to extract numeric value from price
                            price_value = ''.join(filter(lambda x: x.isdigit() or x == '.', str(current_price)))
                            if price_value:
                                base_price = float(price_value)
                                business_price = f"~${int(base_price * 1.8)}" if '$' in str(current_price) else f"~{int(base_price * 1.8)}"
                            else:
                                business_price = 'Available (70-100% more)'
                        except:
                            business_price = 'Available (70-100% more)'
                        business_check_in = '30-40 kg (66-88 lbs)'
                        business_hand = '14-18 kg (31-40 lbs)'

                # Display Business class details
                st.markdown(f"""
                <div style="background-color: #e6f7ff; padding: 10px; border-radius: 5px; margin-bottom: 10px; {border_style}">
                    <h4 style="margin-top: 0;">✨ Business</h4>
                    <p><strong>Price:</strong> {business_price}</p>
                    <p><strong>Check-in Baggage:</strong> {business_check_in}</p>
                    <p><strong>Hand Baggage:</strong> {business_hand}</p>
                </div>
                """, unsafe_allow_html=True)





                # Note: Layover information is already displayed above after arrival information

                # Book now button
                st.markdown(f"[Book Now]({flight.get('url', '#')})")

# Display hotels
def display_hotels(hotels):
    st.header("🏨 Recommended Hotels")

    if not hotels or len(hotels) == 0:
        st.warning("No hotels available for this destination.")
        return

    # Sort hotels by price for better display
    try:
        sorted_hotels = sorted(hotels, key=lambda x: extract_price(x.get("price_per_night", 0)))
    except Exception as e:
        st.warning(f"Could not sort hotels by price: {e}")
        sorted_hotels = hotels

    # Display hotels in a grid
    cols = st.columns(3)
    for i, hotel in enumerate(sorted_hotels):
        with cols[i % 3]:
            with st.container():
                # Add a 'Best Value' indicator for the cheapest hotels
                if i < 3:  # Mark the top 3 best value hotels
                    st.subheader(f"{hotel['name']} 🏆")
                    if i == 0:
                        st.markdown("<span style='color:green; font-weight:bold'>Best Value!</span>", unsafe_allow_html=True)
                    elif i == 1:
                        st.markdown("<span style='color:green'>Great Deal</span>", unsafe_allow_html=True)
                    elif i == 2:
                        st.markdown("<span style='color:green'>Good Price</span>", unsafe_allow_html=True)
                else:
                    st.subheader(f"{hotel['name']}")
                # No images for hotels
                st.write(f"**Location:** {hotel['location']}")
                st.write(f"**Price per night:** {hotel['price_per_night']}")

                # Display check-in and check-out times if available
                if 'check_in_time' in hotel:
                    st.write(f"**Check-in time:** {hotel.get('check_in_time', 'Not specified')}")
                if 'check_out_time' in hotel:
                    st.write(f"**Check-out time:** {hotel.get('check_out_time', 'Not specified')}")

                # Display availability information if available
                if 'availability' in hotel:
                    availability = hotel.get('availability', 'Available')
                    if 'limited' in availability.lower():
                        st.write(f"**Availability:** 🟠 {availability}")
                    elif 'full' in availability.lower() or 'few' in availability.lower():
                        st.write(f"**Availability:** 🔴 {availability}")
                    else:
                        st.write(f"**Availability:** 🟢 {availability}")

                # Display available dates if provided
                if 'available_dates' in hotel:
                    st.write(f"**Available dates:** {hotel.get('available_dates', 'Not specified')}")

                st.markdown(f"[Book Now]({hotel['url']})")
                st.divider()

# Display trains
def display_trains(trains):
    st.header("🚆 Trains")

    if not trains or len(trains) == 0:
        st.warning("No trains available for this route. For long-distance or international travel, consider flights instead.")
        return

    # Add radio button to filter trains by availability
    train_filter = st.radio(
        "Show trains:",
        ["Available Trains Only", "All Trains"],
        key="train_filter"
    )

    # Sort trains by departure time for better display
    try:
        # Sort by departure date and time
        sorted_trains = sorted(trains, key=lambda x: (x.get('departure_date', ''), x.get('departure_time', '')))
    except Exception as e:
        st.warning(f"Could not sort trains by departure time: {e}")
        sorted_trains = trains

    # Filter trains based on radio button selection
    if train_filter == "Available Trains Only":
        filtered_trains = [train for train in sorted_trains if
                          not ('availability' in train and
                               ('sold out' in train['availability'].lower() or
                                'not available' in train['availability'].lower()))]
        if not filtered_trains:
            st.info("No available trains found. Showing all trains instead.")
            filtered_trains = sorted_trains
    else:
        filtered_trains = sorted_trains

    # Display trains in a grid
    for i, train in enumerate(filtered_trains):
        with st.expander(f"{train.get('train_name', 'Train')} ({train.get('train_number', '')}) - {train.get('departure_time', '')} to {train.get('arrival_time', '')} - {train.get('price', 'Price not available')}", expanded=True):
            col1, col2 = st.columns([1, 3])

            with col1:
                # Display availability with color coding
                availability = train.get('availability', 'Available')
                if 'waitlist' in availability.lower() or 'wait list' in availability.lower():
                    st.markdown(f"<span style='color:orange; font-weight:bold'>🕖 **Availability:** {availability}</span>", unsafe_allow_html=True)
                elif 'sold out' in availability.lower() or 'not available' in availability.lower():
                    st.markdown(f"<span style='color:red; font-weight:bold'>❌ **Availability:** {availability}</span>", unsafe_allow_html=True)
                elif 'limited' in availability.lower() or 'few' in availability.lower():
                    st.markdown(f"<span style='color:orange; font-weight:bold'>⚠️ **Availability:** {availability}</span>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<span style='color:green; font-weight:bold'>✅ **Availability:** {availability}</span>", unsafe_allow_html=True)

            with col2:
                # Train details
                st.subheader(f"{train.get('train_name', 'Train')}")
                st.write(f"**Train Number:** {train.get('train_number', 'Not specified')}")
                st.write(f"**Operator:** {train.get('operator', 'Not specified')}")
                st.write(f"**Route:** {train.get('from', 'Origin')} → {train.get('to', 'Destination')}")

                # Display departure and arrival information with dates
                dep_date = train.get('departure_date', '')
                dep_time = train.get('departure_time', '')
                if dep_date or dep_time:
                    st.write(f"📅 ⏰ **Departure:** {dep_date}{' at ' if dep_date and dep_time else ''}{dep_time}")

                arr_date = train.get('arrival_date', '')
                arr_time = train.get('arrival_time', '')
                if arr_date or arr_time:
                    st.write(f"📅 ⏰ **Arrival:** {arr_date}{' at ' if arr_date and arr_time else ''}{arr_time}")

                # Display duration if available
                if 'duration' in train and train['duration']:
                    st.write(f"⏱️ **Journey Duration:** {train['duration']}")
                # Calculate duration if not provided but we have departure and arrival times
                elif 'departure_time' in train and 'arrival_time' in train and not ('duration' in train):
                    try:
                        # This is a simplified calculation and may not be accurate for all formats
                        st.write(f"⏱️ **Journey Duration:** Approximately {calculate_duration_estimate(train.get('departure_time', ''), train.get('arrival_time', ''))}")
                    except:
                        pass

                # Display stops if available
                if 'stops' in train and train['stops']:
                    if isinstance(train['stops'], list) and len(train['stops']) > 0:
                        st.write(f"🚏 **Stops:** {len(train['stops'])}")

                        # Create a table for stops
                        st.markdown("<div style='background-color: #f8f9fa; padding: 10px; border-radius: 5px;'>", unsafe_allow_html=True)
                        st.markdown("<strong>Stop Details:</strong>", unsafe_allow_html=True)

                        for stop in train['stops']:
                            station = stop.get('station', 'N/A')
                            arr_time = stop.get('arrival_time', 'N/A')
                            dep_time = stop.get('departure_time', 'N/A')
                            platform = stop.get('platform', 'N/A')

                            st.markdown(f"""<div style='margin-bottom: 8px; padding: 5px; border-left: 3px solid #4285f4;'>
                                <strong>🚉 {station}</strong><br>
                                🛬 Arrival: {arr_time} | 🛫 Departure: {dep_time}<br>
                                🚧 Platform: {platform}
                            </div>""", unsafe_allow_html=True)

                        st.markdown("</div>", unsafe_allow_html=True)
                    else:
                        st.write(f"🚏 **Stops:** {train['stops']}")

                # Display class information
                st.write(f"💺 **Class:** {train.get('class', 'Not specified')}")

                # Display price
                st.write(f"💰 **Price:** {train.get('price', 'Not specified')}")

                # Book now button
                if 'url' in train and train['url']:
                    st.markdown(f"[Book Now]({train['url']})")

# Display buses
def display_buses(buses):
    st.header("🚌 Buses")

    if not buses or len(buses) == 0:
        st.warning("No buses available for this route. For long-distance or international travel, consider flights instead.")
        return

    # Add radio button to filter buses by availability
    bus_filter = st.radio(
        "Show buses:",
        ["Available Buses Only", "All Buses"],
        key="bus_filter"
    )

    # Sort buses by departure time for better display
    try:
        # Sort by departure date and time
        sorted_buses = sorted(buses, key=lambda x: (x.get('departure_date', ''), x.get('departure_time', '')))
    except Exception as e:
        st.warning(f"Could not sort buses by departure time: {e}")
        sorted_buses = buses

    # Filter buses based on radio button selection
    if bus_filter == "Available Buses Only":
        filtered_buses = [bus for bus in sorted_buses if
                         not ('availability' in bus and
                              ('sold out' in bus['availability'].lower() or
                               'not available' in bus['availability'].lower()))]
        if not filtered_buses:
            st.info("No available buses found. Showing all buses instead.")
            filtered_buses = sorted_buses
    else:
        filtered_buses = sorted_buses

    # Display buses in a grid
    for i, bus in enumerate(filtered_buses):
        with st.expander(f"{bus.get('operator', 'Bus Operator')} - {bus.get('departure_time', '')} to {bus.get('arrival_time', '')} - {bus.get('price', 'Price not available')}", expanded=True):
            col1, col2 = st.columns([1, 3])

            with col1:
                # Display availability with color coding
                availability = bus.get('availability', 'Available')
                if 'sold out' in availability.lower() or 'not available' in availability.lower():
                    st.markdown(f"<span style='color:red; font-weight:bold'>❌ **Availability:** {availability}</span>", unsafe_allow_html=True)
                elif 'limited' in availability.lower() or 'few' in availability.lower():
                    st.markdown(f"<span style='color:orange; font-weight:bold'>⚠️ **Availability:** {availability}</span>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<span style='color:green; font-weight:bold'>✅ **Availability:** {availability}</span>", unsafe_allow_html=True)

            with col2:
                # Bus details
                st.subheader(f"{bus.get('operator', 'Bus Operator')}")
                st.write(f"**Bus Type:** {bus.get('bus_type', 'Not specified')}")
                st.write(f"**Route:** {bus.get('from', 'Origin')} → {bus.get('to', 'Destination')}")

                # Display departure and arrival information with dates
                dep_date = bus.get('departure_date', '')
                dep_time = bus.get('departure_time', '')
                if dep_date or dep_time:
                    st.write(f"📅 ⏰ **Departure:** {dep_date}{' at ' if dep_date and dep_time else ''}{dep_time}")

                arr_date = bus.get('arrival_date', '')
                arr_time = bus.get('arrival_time', '')
                if arr_date or arr_time:
                    st.write(f"📅 ⏰ **Arrival:** {arr_date}{' at ' if arr_date and arr_time else ''}{arr_time}")

                # Display duration if available
                if 'duration' in bus and bus['duration']:
                    st.write(f"⏱️ **Journey Duration:** {bus['duration']}")
                # Calculate duration if not provided but we have departure and arrival times
                elif 'departure_time' in bus and 'arrival_time' in bus and not ('duration' in bus):
                    try:
                        # This is a simplified calculation and may not be accurate for all formats
                        st.write(f"⏱️ **Journey Duration:** Approximately {calculate_duration_estimate(bus.get('departure_time', ''), bus.get('arrival_time', ''))}")
                    except:
                        pass

                # Display stops if available
                if 'stops' in bus and bus['stops']:
                    if isinstance(bus['stops'], list) and len(bus['stops']) > 0:
                        st.write(f"🚏 **Stops:** {len(bus['stops'])}")

                        # Create a table for stops
                        st.markdown("<div style='background-color: #f8f9fa; padding: 10px; border-radius: 5px;'>", unsafe_allow_html=True)
                        st.markdown("<strong>Stop Details:</strong>", unsafe_allow_html=True)

                        for stop in bus['stops']:
                            location = stop.get('location', 'N/A')
                            arr_time = stop.get('arrival_time', 'N/A')
                            dep_time = stop.get('departure_time', 'N/A')
                            duration = stop.get('duration', 'N/A')

                            st.markdown(f"""<div style='margin-bottom: 8px; padding: 5px; border-left: 3px solid #4CAF50;'>
                                <strong>🚏 {location}</strong><br>
                                🛬 Arrival: {arr_time} | 🛫 Departure: {dep_time}<br>
                                ⏳ Stop Duration: {duration}
                            </div>""", unsafe_allow_html=True)

                        st.markdown("</div>", unsafe_allow_html=True)
                    else:
                        st.write(f"🚏 **Stops:** {bus['stops']}")

                # Display price
                st.write(f"💰 **Price:** {bus.get('price', 'Not specified')}")

                # Book now button
                if 'url' in bus and bus['url']:
                    st.markdown(f"[Book Now]({bus['url']})")

# Display daily plan
def display_daily_plan(daily_plan):
    if not daily_plan or len(daily_plan) == 0:
        st.warning("No daily plan information available.")
        return

    st.header("📅 Daily Itinerary")

    # Create tabs only if there are days in the plan
    day_labels = [day.replace("_", " ").title() for day in daily_plan.keys()]
    if not day_labels:
        st.warning("Daily plan data is empty.")
        return

    tabs = st.tabs(day_labels)

    for i, (day, activities) in enumerate(daily_plan.items()):
        with tabs[i]:
            if not activities:
                st.write("No activities planned for this day.")
                continue

            for activity in activities:
                with st.container():
                    col1, col2, col3, col4 = st.columns([1, 1, 2, 1])
                    with col1:
                        st.write(f"**{activity.get('time', 'Time not specified')}**")
                    with col2:
                        st.write(f"*{activity.get('type', 'Type not specified')}*")
                    with col3:
                        st.write(f"{activity.get('activity', 'Activity not specified')}")
                    with col4:
                        # Display transport information if available
                        transport = activity.get('transport', '')
                        transport_fare = activity.get('transport_fare', '')

                        if transport:
                            # Add appropriate emoji based on transport mode
                            if 'metro' in transport.lower() or 'subway' in transport.lower():
                                emoji = '🚇'  # Metro emoji
                            elif 'bus' in transport.lower():
                                emoji = '🚌'  # Bus emoji
                            elif 'cab' in transport.lower() or 'taxi' in transport.lower():
                                emoji = '🚕'  # Taxi emoji
                            elif 'train' in transport.lower():
                                emoji = '🚆'  # Train emoji
                            elif 'walk' in transport.lower() or 'foot' in transport.lower():
                                emoji = '🚶'  # Walking person emoji
                            elif 'bike' in transport.lower() or 'cycle' in transport.lower():
                                emoji = '🚴'  # Cyclist emoji
                            elif 'boat' in transport.lower() or 'ferry' in transport.lower():
                                emoji = '⛵'  # Boat emoji
                            else:
                                emoji = '🚗'  # Car emoji

                            st.write(f"{emoji} **{transport}**")
                            if transport_fare:
                                st.write(f"💰 {transport_fare}")
                    st.divider()

# Display sightseeing spots
def display_sightseeing(sightseeing):
    if not sightseeing or len(sightseeing) == 0:
        st.warning("No sightseeing information available.")
        return

    st.header("📸 Must-Visit Sightseeing Spots")

    # Display in a grid
    cols = st.columns(3)
    for i, spot in enumerate(sightseeing):
        with cols[i % 3]:
            st.write(f"• {spot}")

# Display food recommendations
def display_food(food):
    if not food or len(food) == 0:
        st.warning("No food recommendations available.")
        return

    st.header("🍽️ Local Cuisine to Try")

    # Display in a grid
    cols = st.columns(3)
    for i, dish in enumerate(food):
        with cols[i % 3]:
            st.write(f"• {dish}")

# Display shopping recommendations
def display_shopping(items):
    if not items or len(items) == 0:
        st.warning("No shopping recommendations available.")
        return

    st.header("🛍️ Shopping Recommendations")

    # Display in a grid
    cols = st.columns(3)
    for i, item in enumerate(items):
        with cols[i % 3]:
            st.write(f"• {item}")

# Display events
def display_events(events):
    if not events or len(events) == 0:
        st.warning("No events found during your trip dates.")
        return

    st.header("🎭 Events & Happenings")

    # Group events by type
    event_types = {}
    for event in events:
        event_type = event.get('type', 'Other')
        if event_type not in event_types:
            event_types[event_type] = []
        event_types[event_type].append(event)

    # Create tabs for different event types if there are multiple types
    if len(event_types) > 1:
        event_tabs = st.tabs(list(event_types.keys()))

        for i, (event_type, type_events) in enumerate(event_types.items()):
            with event_tabs[i]:
                display_event_cards(type_events)
    else:
        # If there's only one type, display without tabs
        display_event_cards(events)

# Display pilgrimages
def display_pilgrimages(pilgrimages):
    if not pilgrimages or len(pilgrimages) == 0:
        st.warning("No pilgrimages or religious events found during your trip dates.")
        return

    st.header("🙏 Pilgrimages & Religious Events")

    # Sort pilgrimages by date
    try:
        sorted_pilgrimages = sorted(pilgrimages, key=lambda x: x.get('date', ''))
    except:
        sorted_pilgrimages = pilgrimages

    # Display pilgrimages in a grid
    for pilgrimage in sorted_pilgrimages:
        with st.expander(f"{pilgrimage.get('name', 'Pilgrimage')} - {pilgrimage.get('date', 'Date not specified')}", expanded=True):
            col1, col2 = st.columns([1, 3])

            with col1:
                # Use a default pilgrimage image if none is available
                default_image = "https://dummyimage.com/600x400/cccccc/000000&text=Pilgrimage+Image"
                image_url = pilgrimage.get("image", default_image)
                if not image_url or image_url.strip() == "":
                    image_url = default_image
                st.image(image_url, use_column_width=True)

            with col2:
                # Pilgrimage details
                st.subheader(pilgrimage.get('name', 'Pilgrimage'))

                st.write(f"🙏 **Religious Event**")
                st.write(f"📍 **Location:** {pilgrimage.get('location', 'Not specified')}")
                st.write(f"📅 **Date:** {pilgrimage.get('date', 'Not specified')}")
                st.write(f"⏰ **Time:** {pilgrimage.get('time', 'Not specified')}")

                # Display price if available
                if 'price' in pilgrimage and pilgrimage['price']:
                    st.write(f"💰 **Price:** {pilgrimage['price']}")

                # Display description if available
                if 'description' in pilgrimage and pilgrimage['description']:
                    st.write(f"**Description:** {pilgrimage['description']}")

                # Display religious significance
                if 'religious_significance' in pilgrimage:
                    st.write(f"**Religious Significance:** {pilgrimage.get('religious_significance', 'Not specified')}")

                # Display crowd expectations
                if 'crowd_expectations' in pilgrimage:
                    st.write(f"**Crowd Expectations:** {pilgrimage.get('crowd_expectations', 'Not specified')}")

                # Display rituals
                if 'rituals' in pilgrimage:
                    st.write(f"**Special Rituals:** {pilgrimage.get('rituals', 'Not specified')}")

                # Display ticket URL if available
                if 'ticket_url' in pilgrimage and pilgrimage['ticket_url']:
                    st.markdown(f"[More Information]({pilgrimage['ticket_url']})")

# Display news
def display_news(news):
    if not news or len(news) == 0:
        st.warning("No news or current events found for your destination.")
        return

    st.header("📰 Local News & Current Events")

    # Sort news by date
    try:
        sorted_news = sorted(news, key=lambda x: x.get('date', ''), reverse=True)  # Most recent first
    except:
        sorted_news = news

    # Display news in a grid
    for news_item in sorted_news:
        with st.expander(f"{news_item.get('title', 'News')} - {news_item.get('date', 'Date not specified')}", expanded=True):
            col1, col2 = st.columns([1, 3])

            with col1:
                # Use a default news image if none is available
                default_image = "https://dummyimage.com/600x400/cccccc/000000&text=News+Image"
                image_url = news_item.get("image", default_image)
                if not image_url or image_url.strip() == "":
                    image_url = default_image
                st.image(image_url, use_column_width=True)

            with col2:
                # News details
                st.subheader(news_item.get('title', 'News'))

                st.write(f"📰 **Current News**")
                st.write(f"📅 **Date:** {news_item.get('date', 'Not specified')}")

                # Display description if available
                if 'description' in news_item and news_item['description']:
                    st.write(f"**Description:** {news_item['description']}")

                # Display impact on travel
                if 'impact_on_travel' in news_item:
                    impact = news_item.get('impact_on_travel', 'Not specified')

                    # Add color coding based on impact severity
                    if any(word in impact.lower() for word in ['severe', 'major', 'significant', 'avoid', 'cancel', 'dangerous']):
                        st.markdown(f"<span style='color:red; font-weight:bold'>⚠️ **Impact on Travel:** {impact}</span>", unsafe_allow_html=True)
                    elif any(word in impact.lower() for word in ['moderate', 'caution', 'delay', 'prepare', 'aware']):
                        st.markdown(f"<span style='color:orange; font-weight:bold'>⚠️ **Impact on Travel:** {impact}</span>", unsafe_allow_html=True)
                    elif any(word in impact.lower() for word in ['minor', 'minimal', 'slight', 'small', 'limited']):
                        st.markdown(f"<span style='color:blue; font-weight:bold'>ℹ️ **Impact on Travel:** {impact}</span>", unsafe_allow_html=True)
                    elif any(word in impact.lower() for word in ['no impact', 'none', 'not affected', 'normal']):
                        st.markdown(f"<span style='color:green; font-weight:bold'>✓ **Impact on Travel:** {impact}</span>", unsafe_allow_html=True)
                    else:
                        st.write(f"**Impact on Travel:** {impact}")

                # Display source
                if 'source' in news_item:
                    st.write(f"**Source:** {news_item.get('source', 'Not specified')}")

                # Display URL if available
                if 'url' in news_item and news_item['url']:
                    st.markdown(f"[Read More]({news_item['url']})")

def display_event_cards(events):
    # Sort events by date
    try:
        sorted_events = sorted(events, key=lambda x: x.get('date', ''))
    except:
        sorted_events = events

    # Display events in a grid
    for i, event in enumerate(sorted_events):
        with st.expander(f"{event.get('name', 'Event')} - {event.get('date', 'Date not specified')}", expanded=True):
            col1, col2 = st.columns([1, 3])

            with col1:
                # Use a default event image if none is available
                default_event_image = "https://dummyimage.com/600x400/cccccc/000000&text=Event+Image"
                image_url = event.get("image", default_event_image)
                if not image_url or image_url.strip() == "":
                    image_url = default_event_image
                st.image(image_url, use_column_width=True)

            with col2:
                # Event details
                st.subheader(event.get('name', 'Event'))

                # Add emoji based on event type
                event_type = event.get('type', '').lower()
                if 'festival' in event_type:
                    type_emoji = '🎭'  # Festival emoji
                elif 'sport' in event_type or 'match' in event_type or 'game' in event_type:
                    if 'cricket' in event_type:
                        type_emoji = '🏏'  # Cricket emoji
                    elif 'football' in event_type or 'soccer' in event_type:
                        type_emoji = '⚽'  # Football emoji
                    elif 'basketball' in event_type:
                        type_emoji = '🏀'  # Basketball emoji
                    elif 'tennis' in event_type:
                        type_emoji = '🎾'  # Tennis emoji
                    else:
                        type_emoji = '🏆'  # Trophy emoji for other sports
                elif 'concert' in event_type or 'music' in event_type:
                    type_emoji = '🎵'  # Music emoji
                elif 'parade' in event_type:
                    type_emoji = '🎪'  # Circus tent emoji
                elif 'exhibition' in event_type or 'museum' in event_type or 'gallery' in event_type:
                    type_emoji = '🖼️'  # Picture frame emoji
                elif 'theater' in event_type or 'theatre' in event_type or 'show' in event_type:
                    type_emoji = '🎭'  # Performing arts emoji
                elif 'cultural' in event_type or 'tradition' in event_type:
                    type_emoji = '🌈'  # Rainbow emoji for cultural events
                else:
                    type_emoji = '📅'  # Calendar emoji for other events

                st.write(f"{type_emoji} **Type:** {event.get('type', 'Not specified')}")
                st.write(f"📍 **Location:** {event.get('location', 'Not specified')}")
                st.write(f"📅 **Date:** {event.get('date', 'Not specified')}")
                st.write(f"⏰ **Time:** {event.get('time', 'Not specified')}")

                # Display price if available
                if 'price' in event and event['price']:
                    st.write(f"💰 **Price:** {event['price']}")
                else:
                    st.write("💰 **Price:** Not specified")

                # Display description if available
                if 'description' in event and event['description']:
                    st.write(f"**Description:** {event['description']}")

                # Display ticket URL if available
                if 'ticket_url' in event and event['ticket_url']:
                    st.markdown(f"[Buy Tickets]({event['ticket_url']})")

# Display local transport
def display_transport(transport):
    if not transport or len(transport) == 0:
        st.warning("No transportation information available.")
        return

    st.header("🚇 Local Transportation")

    for option in transport:
        try:
            st.write(f"**{option.get('mode', 'Transport')}** - {option.get('pass_type', 'Pass')} ({option.get('price', 'Price not available')})")
        except Exception as e:
            st.write(f"Transport option: {option}")

# Display weather forecast
def display_weather(weather):
    if not weather or len(weather) == 0:
        st.warning("No weather forecast available.")
        return

    st.header("🌤️ Weather Forecast")

    # Create tabs only if there are days in the forecast
    day_labels = [day.replace("_", " ").title() for day in weather.keys()]
    if not day_labels:
        st.warning("Weather forecast data is empty.")
        return

    tabs = st.tabs(day_labels)

    for i, (day, forecast) in enumerate(weather.items()):
        with tabs[i]:
            if not forecast:
                st.write("No weather data for this day.")
                continue

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Morning", forecast.get("morning", "N/A"))
            with col2:
                st.metric("Afternoon", forecast.get("afternoon", "N/A"))
            with col3:
                st.metric("Evening", forecast.get("evening", "N/A"))

# Display emergency contacts
def display_emergency(contacts):
    if not contacts:
        st.warning("No emergency contact information available.")
        return

    st.header("🚨 Emergency Contacts")

    st.write(f"**Local Police:** {contacts.get('local_police', 'Not available')}")
    st.write(f"**Nearest Embassy:** {contacts.get('nearest_embassy', 'Not available')}")
    st.write(f"**Hospital:** {contacts.get('hospital', 'Not available')}")

# Display travel tips
def display_tips(tips):
    if not tips:
        st.warning("No travel tips available.")
        return

    st.header("✈️ Travel Tips")

    st.write(f"**Currency:** {tips.get('currency', 'Not available')}")
    st.write(f"**Language:** {tips.get('language', 'Not available')}")

    if 'common_phrases' in tips and tips['common_phrases']:
        st.subheader("Useful Phrases")
        for phrase in tips['common_phrases']:
            st.write(f"**{phrase.get('phrase', '')}** - {phrase.get('meaning', '')}")

# Display country culture and do's/don'ts
def display_country_culture(culture):
    if not culture:
        st.warning("No cultural information available for this destination.")
        return

    st.header("🌍 Country Culture & Etiquette")

    # Create tabs for different sections of cultural guidelines
    tab1, tab2, tab3 = st.tabs(["Do's & Don'ts", "Cultural Norms", "Local Customs & Taboos"])

    with tab1:
        # Display Do's
        if 'dos' in culture and culture['dos']:
            st.subheader("✅ Do's")
            for item in culture['dos']:
                with st.container():
                    st.markdown(f"**{item.get('title', '')}**")
                    st.markdown(f"{item.get('description', '')}")
                    st.divider()
        else:
            st.info("No specific do's available for this destination.")

        # Display Don'ts
        if 'donts' in culture and culture['donts']:
            st.subheader("❌ Don'ts")
            for item in culture['donts']:
                with st.container():
                    st.markdown(f"**{item.get('title', '')}**")
                    st.markdown(f"{item.get('description', '')}")
                    st.divider()
        else:
            st.info("No specific don'ts available for this destination.")

    with tab2:
        # Display Cultural Norms
        if 'cultural_norms' in culture and culture['cultural_norms']:
            for norm in culture['cultural_norms']:
                aspect = norm.get('aspect', '')
                description = norm.get('description', '')

                # Add appropriate emoji based on the aspect
                if 'greet' in aspect.lower():
                    emoji = '👋'  # Waving hand
                elif 'dress' in aspect.lower() or 'cloth' in aspect.lower() or 'attire' in aspect.lower():
                    emoji = '👗'  # Dress
                elif 'din' in aspect.lower() or 'eat' in aspect.lower() or 'food' in aspect.lower() or 'meal' in aspect.lower():
                    emoji = '🍴'  # Fork and knife
                elif 'relig' in aspect.lower() or 'pray' in aspect.lower() or 'worship' in aspect.lower() or 'sacred' in aspect.lower():
                    emoji = '🙏'  # Praying hands
                elif 'social' in aspect.lower() or 'interact' in aspect.lower() or 'talk' in aspect.lower() or 'convers' in aspect.lower():
                    emoji = '💬'  # Speech bubble
                elif 'gift' in aspect.lower() or 'present' in aspect.lower():
                    emoji = '🎁'  # Gift
                elif 'business' in aspect.lower() or 'work' in aspect.lower() or 'meeting' in aspect.lower():
                    emoji = '💼'  # Briefcase
                elif 'photo' in aspect.lower() or 'picture' in aspect.lower() or 'camera' in aspect.lower():
                    emoji = '📷'  # Camera
                elif 'tip' in aspect.lower() or 'money' in aspect.lower() or 'payment' in aspect.lower():
                    emoji = '💸'  # Money with wings
                else:
                    emoji = '🌍'  # Globe

                st.subheader(f"{emoji} {aspect}")
                st.write(description)
                st.divider()
        else:
            st.info("No specific cultural norms available for this destination.")

    with tab3:
        # Display Local Customs
        if 'local_customs' in culture and culture['local_customs']:
            st.subheader("🎐 Local Customs")
            st.write(culture['local_customs'])
            st.divider()
        else:
            st.info("No specific local customs available for this destination.")

        # Display Taboos
        if 'taboos' in culture and culture['taboos']:
            st.subheader("⛔ Taboos & Sensitive Topics")
            st.write(culture['taboos'])
        else:
            st.info("No specific taboos available for this destination.")

# Main app
def main():
    # Form to collect trip info
    with st.form("trip_form"):
        st.subheader("Enter Your Trip Details")

        col1, col2 = st.columns(2)
        with col1:
            origin = st.text_input("Current Location", "Hyderabad")
            destination = st.text_input("Destination", "Paris")
            trip_type = st.selectbox("Trip Type", ["Leisure", "Adventure", "Romantic", "Business", "Pilgrimage", "Family", "Wellness"])

        with col2:
            people = st.number_input("Number of Travelers", min_value=1, value=2)
            # Set default dates to current date and one week later
            today = date.today()
            one_week_later = today + timedelta(days=7)

            # Format for display: yyyy/mm/dd
            start_date = st.date_input("Start Date", today, format="YYYY/MM/DD")
            end_date = st.date_input("End Date", one_week_later, format="YYYY/MM/DD")
            # Calculate number of days from date range
            num_days = (end_date - start_date).days + 1

        submit = st.form_submit_button("Generate Itinerary")

    if submit:
        # Fetch data from API
        itinerary_data = fetch_itinerary_data(origin, destination, trip_type, num_days, people, start_date, end_date)

        if itinerary_data:
            # Add Trip Information heading
            st.header("Trip Information")

            # Display trip summary with cheapest flight and hotel prices
            display_trip_summary(itinerary_data)

            # Create tabs for different sections
            tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs(["Transportation", "Hotels", "Daily Plan", "Events", "News", "Attractions & Food", "Country Culture", "Weather & Transport", "Tips & Emergency"])

            with tab1:
                # Transportation tab with subtabs for flights, trains, and buses
                transport_tabs = st.tabs(["Flights", "Trains", "Buses"])
                with transport_tabs[0]:
                    display_flights(itinerary_data.get("flights", []))
                with transport_tabs[1]:
                    display_trains(itinerary_data.get("trains", []))
                with transport_tabs[2]:
                    display_buses(itinerary_data.get("buses", []))

            with tab2:
                display_hotels(itinerary_data.get("hotels", []))

            with tab3:
                display_daily_plan(itinerary_data.get("daily_plan", {}))

                # If trip_type is Pilgrimage, show pilgrimages in the daily plan tab
                if trip_type.lower() == "pilgrimage":
                    st.markdown("---")
                    display_pilgrimages(itinerary_data.get("pilgrimages", []))

            with tab4:
                display_events(itinerary_data.get("events", []))

            with tab5:
                display_news(itinerary_data.get("news", []))

            with tab6:
                display_sightseeing(itinerary_data.get("sightseeing", []))
                display_food(itinerary_data.get("famous_food", []))
                display_shopping(itinerary_data.get("local_items_to_buy", []))

            with tab7:
                display_country_culture(itinerary_data.get("country_culture", {}))

            with tab8:
                display_weather(itinerary_data.get("weather_forecast", {}))
                display_transport(itinerary_data.get("local_transport", []))

            with tab9:
                display_tips(itinerary_data.get("travel_tips", {}))
                display_emergency(itinerary_data.get("emergency_contacts", {}))
        else:
            st.error("Failed to fetch itinerary data from API. Please try again later.")

if __name__ == "__main__":
    main()

import streamlit as st
import requests
import json
from datetime import date

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

        st.info(f"Sending request to itinerary planner API for a {num_days}-day trip...")

        response = requests.post(url, json=payload)

        if response.status_code == 200:
            data = response.json()
            return data["data"]["trip"]["itinerary"]
        else:
            st.error(f"Error: API returned status code {response.status_code}")
            st.code(response.text)
            return None
    except Exception as e:
        st.error(f"Error connecting to API: {str(e)}")
        return None

# Display trip information
def display_trip_info(origin, destination, start_date, end_date, people, trip_type):
    st.header("Trip Information")
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"**From:** {origin}")
    with col2:
        st.info(f"**To:** {destination}")

    num_days = (end_date - start_date).days + 1
    st.info(f"**Dates:** {start_date.strftime('%B %d, %Y')} - {end_date.strftime('%B %d, %Y')} ({num_days} days)")
    st.info(f"**Travelers:** {people}")
    st.info(f"**Trip Type:** {trip_type}")

# Display flights
def display_flights(flights):
    st.header("✈️ Available Flights")

    # Sort flights by price for better display
    try:
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

        sorted_flights = sorted(flights, key=lambda x: extract_price(x.get("price", 0)))
    except Exception as e:
        st.warning(f"Could not sort flights by price: {e}")
        sorted_flights = flights

    # Display flights in a grid
    cols = st.columns(3)
    for i, flight in enumerate(sorted_flights):
        with cols[i % 3]:
            with st.container():
                # Add a 'Best Value' indicator for the cheapest flights
                if i < 3:  # Mark the top 3 cheapest flights
                    st.subheader(f"{flight['airline']} 🏆")
                    if i == 0:
                        st.markdown("<span style='color:green; font-weight:bold'>Best Value!</span>", unsafe_allow_html=True)
                    elif i == 1:
                        st.markdown("<span style='color:green'>Great Deal</span>", unsafe_allow_html=True)
                    elif i == 2:
                        st.markdown("<span style='color:green'>Good Price</span>", unsafe_allow_html=True)
                else:
                    st.subheader(f"{flight['airline']}")
                # Use a default flight image if none is available
                default_flight_image = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR7KqiRxGHCiV_DsPk7amCKfe0BPRQNhH6yFA&s"
                image_url = flight.get("imag", default_flight_image)
                if not image_url or image_url.strip() == "":
                    image_url = default_flight_image
                st.image(image_url, use_container_width=True)
                st.write(f"**Route:** {flight['from']} → {flight['to']}")
                st.write(f"**Price:** {flight['price']}")

                # Display layover information if available
                if 'layover' in flight and flight['layover']:
                    if flight['layover'].lower() == 'direct flight' or flight['layover'] == '':
                        st.write("**✅ Direct Flight**")
                    else:
                        st.write(f"**🛑 Layover:** {flight['layover']}")
                elif 'layovers' in flight and flight['layovers']:
                    st.write(f"**🛑 Layover:** {flight['layovers']}")
                elif 'stops' in flight and flight['stops']:
                    st.write(f"**🛑 Stops:** {flight['stops']}")
                else:
                    st.write("**✅ Direct Flight**")

                st.markdown(f"[Book Now]({flight['url']})")
                st.divider()

# Display hotels
def display_hotels(hotels):
    st.header("🏨 Recommended Hotels")

    # Sort hotels by price for better display
    try:
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
                # Use a default hotel image if none is available
                default_hotel_image = "https://img.freepik.com/free-photo/type-entertainment-complex-popular-resort-with-pools-water-parks-turkey-with-more-than-5-million-visitors-year-amara-dolce-vita-luxury-hotel-resort-tekirova-kemer_146671-18728.jpg?semt=ais_hybrid&w=740"
                image_url = hotel.get("imag", default_hotel_image)
                if not image_url or image_url.strip() == "":
                    image_url = default_hotel_image
                st.image(image_url, use_container_width=True)
                st.write(f"**Location:** {hotel['location']}")
                st.write(f"**Price per night:** {hotel['price_per_night']}")
                st.markdown(f"[Book Now]({hotel['url']})")
                st.divider()

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
                    col1, col2, col3 = st.columns([1, 1, 3])
                    with col1:
                        st.write(f"**{activity.get('time', 'Time not specified')}**")
                    with col2:
                        st.write(f"*{activity.get('type', 'Type not specified')}*")
                    with col3:
                        st.write(f"{activity.get('activity', 'Activity not specified')}")
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

# Main app
def main():
    # Form to collect trip info
    with st.form("trip_form"):
        st.subheader("Enter Your Trip Details")

        col1, col2 = st.columns(2)
        with col1:
            origin = st.text_input("Current Location", "Hyderabad")
            destination = st.text_input("Destination", "Paris")
            trip_type = st.selectbox("Trip Type", ["Leisure", "Adventure", "Romantic", "Business"])

        with col2:
            people = st.number_input("Number of Travelers", min_value=1, value=2)
            start_date = st.date_input("Start Date", date(2025, 4, 16))
            end_date = st.date_input("End Date", date(2025, 4, 21))
            # Calculate number of days from date range
            num_days = (end_date - start_date).days + 1

        submit = st.form_submit_button("Generate Itinerary")

    if submit:
        # Display trip information
        display_trip_info(origin, destination, start_date, end_date, people, trip_type)

        # Fetch data from API
        itinerary_data = fetch_itinerary_data(origin, destination, trip_type, num_days, people, start_date, end_date)

        if itinerary_data:
            # Create tabs for different sections
            tab1, tab2, tab3, tab4, tab5 = st.tabs(["Flights & Hotels", "Daily Plan", "Attractions & Food", "Weather & Transport", "Tips & Emergency"])

            with tab1:
                display_flights(itinerary_data.get("flights", []))
                display_hotels(itinerary_data.get("hotels", []))

            with tab2:
                display_daily_plan(itinerary_data.get("daily_plan", {}))

            with tab3:
                display_sightseeing(itinerary_data.get("sightseeing", []))
                display_food(itinerary_data.get("famous_food", []))
                display_shopping(itinerary_data.get("local_items_to_buy", []))

            with tab4:
                display_weather(itinerary_data.get("weather_forecast", {}))
                display_transport(itinerary_data.get("local_transport", []))

            with tab5:
                display_tips(itinerary_data.get("travel_tips", {}))
                display_emergency(itinerary_data.get("emergency_contacts", {}))
        else:
            st.error("Failed to fetch itinerary data from API. Please try again later.")

if __name__ == "__main__":
    main()

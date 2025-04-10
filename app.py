import streamlit as st
import requests
from datetime import date
import json

st.set_page_config(page_title="🌍 Travel Planner via API", layout="centered")
st.title("🧳 AI-Powered Travel Itinerary Planner")
st.markdown("Plan a personalized itinerary using the FastAPI backend.")

# ---- Form to collect trip info ----
with st.form("trip_form"):
    origin = st.text_input("Current Location", "Hyderabad")
    destination = st.text_input("Destination", "Paris")
    trip_type = st.selectbox("Trip Type", ["Leisure", "Adventure", "Romantic", "Business"])
    num_days = st.number_input("Number of Days", min_value=1, value=5)
    people = st.number_input("Number of Travelers", min_value=1, value=2)
    start_date = st.date_input("Start Date", date(2025, 4, 10))
    end_date = st.date_input("End Date", date(2025, 4, 15))
    submit = st.form_submit_button("Generate Itinerary")

# ---- On Submit ----
if submit:
    st.info("Sending request to itinerary planner...")
    try:
        url = "http://127.0.0.1:8000/plan"  # Change this to your actual API endpoint

        payload = {
            "current_location": origin,
            "destination": destination,
            "trip_type": trip_type,
            "num_days": num_days,
            "people": people,
            "start_date": start_date.strftime("%Y/%m/%d"),
            "end_date": end_date.strftime("%Y/%m/%d")
        }

        response = requests.post(url, json=payload)
        if response.status_code == 200:
            data = response.json()["data"]
            trip = data["trip"]
            traveler = data["traveler"]
            itinerary = trip["itinerary"]

            st.success(f"Trip from {trip['origin']} to {trip['destination']} for {traveler['count']} traveler(s)")
            st.write(f"📅 {trip['startDate']} to {trip['endDate']}")

            st.subheader("✈️ Flights")
            for flight in itinerary.get("flights", []):
                st.markdown(f"- **{flight['from']} → {flight['to']}** | {flight['airline']} | {flight['price']}")

            st.subheader("🏨 Hotels")
            for hotel in itinerary.get("hotels", []):
                st.markdown(f"- **{hotel['name']}** in *{hotel['location']}* — {hotel['price_per_night']}")

            st.subheader("📅 Daily Plan")
            for day, activities in itinerary["daily_plan"].items():
                st.markdown(f"**{day.replace('_', ' ').title()}**")
                for act in activities:
                    st.markdown(f"- ⏰ {act['time']} | *{act['type']}* — **{act['activity']}**")

            st.subheader("📸 Sightseeing Spots")
            st.markdown(", ".join(itinerary.get("sightseeing", [])))

            st.subheader("🍽️ Foods to Try")
            st.markdown(", ".join(itinerary.get("famous_food", [])))

            st.subheader("🛍️ Local Items to Buy")
            st.markdown(", ".join(itinerary.get("local_items_to_buy", [])))

        else:
            st.error(f"🚫 Failed to get response: {response.status_code}")
            st.code(response.text)

    except Exception as e:
        st.error(f"❌ Error occurred: {e}")

def build_prompt(data: dict) -> str:
    return f"""
Generate a detailed JSON itinerary for a {data['trip_type']} trip from {data['current_location']} to {data['destination']} for {data['num_days']} days.
Include:
- Transportation (flight details with dates, times, flight numbers)
- Hotel info (name, check-in/out, room type)
- Daily plans (keyed by date with activities)

Start date: {data['start_date']}, End date: {data['end_date']}, Travelers: {data['people']}.

Respond with ONLY valid JSON. No markdown or explanation.
"""

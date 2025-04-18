from typing_extensions import TypedDict, Annotated
from langchain_groq import ChatGroq
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langchain_core.messages import BaseMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
import os
from dotenv import load_dotenv

load_dotenv()
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
os.environ["LANGSMITH_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")

class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

# Using a more capable model for better flight and cost information
model = ChatGroq(model="meta-llama/llama-4-scout-17b-16e-instruct")

def create_langgraph_agent():
    @tool
    def travel_serper_search(query: str):
        """Use Serper to search for real-time travel information with accurate flight and cost details."""
        import requests
        import json

        url = "https://google.serper.dev/search"

        payload = json.dumps({
            "q": query,
            "num": 10
        })

        headers = {
            'X-API-KEY': os.getenv("SERPER_API_KEY"),
            'Content-Type': 'application/json'
        }

        try:
            response = requests.request("POST", url, headers=headers, data=payload)
            result = response.json()
            return result
        except Exception as e:
            return {"error": str(e)}

    # Tavily search tool
    @tool
    def tavily_search(query: str):
        """Use Tavily to search for travel information with accurate details about flights, hotels, and destinations."""
        try:
            from tavily import TavilyClient
            client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
            result = client.search(query=query, search_depth="advanced", include_domains=["booking.com", "expedia.com", "tripadvisor.com", "kayak.com", "hotels.com", "airbnb.com", "skyscanner.com", "makemytrip.com", "cleartrip.com", "yatra.com", "goibibo.com", "irctc.co.in", "redbus.in"])
            return result
        except Exception as e:
            print(f"Tavily search error: {str(e)}")
            return {"error": str(e)}

    # DuckDuckGo search tool
    @tool
    def duckduckgo_search(query: str):
        """Use DuckDuckGo to search for travel information with accurate details about flights, hotels, and destinations."""
        try:
            from duckduckgo_search import DDGS
            ddgs = DDGS()
            results = list(ddgs.text(query, max_results=10))
            return {"results": results}
        except Exception as e:
            print(f"DuckDuckGo search error: {str(e)}")
            return {"error": str(e)}

    # Create a more robust version of the search tool with retry logic and multiple search engines
    @tool
    def multi_search(query: str):
        """Use multiple search engines (Serper, Tavily, DuckDuckGo) to find accurate travel information. This tool combines results from different sources for better accuracy."""
        import requests
        import json
        import time

        max_retries = 3
        retry_delay = 2  # seconds
        results = {}

        # Try Serper first
        for attempt in range(max_retries):
            try:
                url = "https://google.serper.dev/search"

                payload = json.dumps({
                    "q": query,
                    "num": 10
                })

                headers = {
                    'X-API-KEY': os.getenv("SERPER_API_KEY"),
                    'Content-Type': 'application/json'
                }

                response = requests.request("POST", url, headers=headers, data=payload)
                serper_result = response.json()

                # Check if the result contains meaningful data
                if serper_result and 'organic' in serper_result and len(serper_result['organic']) > 0:
                    print(f"Serper search successful on attempt {attempt + 1}")
                    results["serper"] = serper_result
                    break
                else:
                    print(f"Serper search returned empty results on attempt {attempt + 1}, retrying...")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                    else:
                        results["serper"] = {"error": "No meaningful results found after multiple attempts"}
            except Exception as e:
                print(f"Serper search error on attempt {attempt + 1}: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    results["serper"] = {"error": f"Failed after {max_retries} attempts: {str(e)}"}

        # Try Tavily
        try:
            tavily_result = tavily_search(query)
            results["tavily"] = tavily_result
        except Exception as e:
            results["tavily"] = {"error": str(e)}

        # Try DuckDuckGo
        try:
            duckduckgo_result = duckduckgo_search(query)
            results["duckduckgo"] = duckduckgo_result
        except Exception as e:
            results["duckduckgo"] = {"error": str(e)}

        return results

    # Create a tool node with all search tools
    tool_node = ToolNode([travel_serper_search, tavily_search, duckduckgo_search, multi_search])
    model_with_tools = model.bind_tools([travel_serper_search, tavily_search, duckduckgo_search, multi_search])

    def call_model(state: State):
        return {
            "messages": [
                model_with_tools.invoke([
                    SystemMessage(content=(
                        "You are a professional travel itinerary planner assistant with expertise in providing accurate flight and cost information. You have access to multiple search tools (Serper, Tavily, DuckDuckGo) that you should use to find the most accurate and up-to-date travel information. Use these tools to cross-verify information from multiple sources for better accuracy. "
                        "Your task is to return a well-structured JSON object based on user trip details. "
                        "Always respond ONLY with JSON. DO NOT include any explanation or apologies.\n\n"
                        "Use the following strict format:\n\n"
                        "{\n"
                        "  \"flights\": [\n"
                        "    {\"from\": \"...\", \"to\": \"...\", \"airline\": \"...\", \"flight_number\": \"...\", \"price\": \"...\", \"departure_date\": \"...\", \"departure_time\": \"...\", \"arrival_date\": \"...\", \"arrival_time\": \"...\", \"layover_details\": [{\"city\": \"City name\", \"duration\": \"Duration\", \"arrival_time\": \"Time of arrival\", \"departure_time\": \"Time of next flight\", \"terminal_change\": \"Yes/No\"}], \"url\": \"...\", \"class\": \"Economy/Premium Economy/Business\", \"check_in_baggage\": \"20 kg (44 lbs)\", \"hand_baggage\": \"7 kg (15 lbs)\"},\n"
                        "    ... (8 total realistic and diverse flight options, sorted by price from cheapest to most expensive)\n"
                        "  ],\n"
                        "  \"trains\": [\n"
                        "    {\"from\": \"...\", \"to\": \"...\", \"train_name\": \"...\", \"train_number\": \"...\", \"operator\": \"...\", \"price\": \"...\", \"departure_date\": \"...\", \"departure_time\": \"...\", \"arrival_date\": \"...\", \"arrival_time\": \"...\", \"duration\": \"...\", \"class\": \"...\", \"availability\": \"Available/Limited/Waitlist\", \"stops\": [{\"station\": \"Station name\", \"arrival_time\": \"Time of arrival\", \"departure_time\": \"Time of departure\", \"platform\": \"Platform number\"}], \"url\": \"...\"},\n"
                        "    ... (5 train options if available for the route)\n"
                        "  ],\n"
                        "  \"buses\": [\n"
                        "    {\"from\": \"...\", \"to\": \"...\", \"operator\": \"...\", \"bus_type\": \"...\", \"price\": \"...\", \"departure_date\": \"...\", \"departure_time\": \"...\", \"arrival_date\": \"...\", \"arrival_time\": \"...\", \"duration\": \"...\", \"availability\": \"Available/Limited/Sold Out\", \"stops\": [{\"location\": \"Stop name\", \"arrival_time\": \"Time of arrival\", \"departure_time\": \"Time of departure\", \"duration\": \"Stop duration\"}], \"url\": \"...\"},\n"
                        "    ... (5 bus options if available for the route)\n"
                        "  ],\n"
                        "  \"hotels\": [\n"
                        "    {\"name\": \"...\", \"location\": \"...\", \"price_per_night\": \"...\", \"availability\": \"Available/Limited/Almost Full\", \"check_in_time\": \"...\", \"check_out_time\": \"...\", \"available_dates\": \"From ... to ...\", \"url\": \"...\", \"image\": \"...\"},\n"
                        "    ... (8 total real and well-reviewed hotels, sorted by price from cheapest to most expensive)\n"
                        "  ],\n"
                        "  \"daily_plan\": {\n"
                        "    \"day_1\": [\n"
                        "      {\"time\": \"Morning\", \"type\": \"Sightseeing\", \"activity\": \"...\", \"transport\": \"Metro/Bus/Cab/Train\", \"transport_fare\": \"...\"},\n"
                        "      {\"time\": \"Late Morning\", \"type\": \"Cultural\", \"activity\": \"...\", \"transport\": \"Metro/Bus/Cab/Train\", \"transport_fare\": \"...\"},\n"
                        "      {\"time\": \"Afternoon\", \"type\": \"Dining\", \"activity\": \"...\", \"transport\": \"Metro/Bus/Cab/Train\", \"transport_fare\": \"...\"},\n"
                        "      {\"time\": \"Evening\", \"type\": \"Leisure\", \"activity\": \"...\", \"transport\": \"Metro/Bus/Cab/Train\", \"transport_fare\": \"...\"},\n"
                        "      {\"time\": \"Night\", \"type\": \"Entertainment\", \"activity\": \"...\", \"transport\": \"Metro/Bus/Cab/Train\", \"transport_fare\": \"...\"}\n"
                        "    ],\n"
                        "    ... (Repeat for each day based on trip duration from start_date to end_date)\n"
                        "  },\n"
                        "  \"events\": [\n"
                        "    {\"name\": \"...\", \"type\": \"Festival/Sports/Concert/Parade/Exhibition/Cultural\", \"date\": \"...\", \"time\": \"...\", \"location\": \"...\", \"description\": \"...\", \"price\": \"...\", \"ticket_url\": \"...\", \"image\": \"...\"},\n"
                        "    ... (All events happening during the trip dates)\n"
                        "  ],\n"
                        "  \"pilgrimages\": [\n"
                        "    {\"name\": \"...\", \"date\": \"...\", \"time\": \"...\", \"location\": \"...\", \"description\": \"...\", \"religious_significance\": \"...\", \"crowd_expectations\": \"...\", \"rituals\": \"...\", \"price\": \"...\", \"ticket_url\": \"...\", \"image\": \"...\"},\n"
                        "    ... (All pilgrimages and religious events happening during the trip dates)\n"
                        "  ],\n"
                        "  \"news\": [\n"
                        "    {\"title\": \"...\", \"date\": \"...\", \"description\": \"...\", \"impact_on_travel\": \"...\", \"source\": \"...\", \"url\": \"...\", \"image\": \"...\"},\n"
                        "    ... (Current news and happenings that might affect the trip)\n"
                        "  ],\n"
                        "  \"country_culture\": {\n"
                        "    \"dos\": [\n"
                        "      {\"title\": \"...\", \"description\": \"...\"},\n"
                        "      ... (At least 5 important things to do at the destination)\n"
                        "    ],\n"
                        "    \"donts\": [\n"
                        "      {\"title\": \"...\", \"description\": \"...\"},\n"
                        "      ... (At least 5 important things to avoid at the destination)\n"
                        "    ],\n"
                        "    \"cultural_norms\": [\n"
                        "      {\"aspect\": \"Greetings\", \"description\": \"...\"},\n"
                        "      {\"aspect\": \"Dress Code\", \"description\": \"...\"},\n"
                        "      {\"aspect\": \"Dining Etiquette\", \"description\": \"...\"},\n"
                        "      {\"aspect\": \"Religious Customs\", \"description\": \"...\"},\n"
                        "      {\"aspect\": \"Social Interactions\", \"description\": \"...\"}\n"
                        "    ],\n"
                        "    \"local_customs\": \"...\",\n"
                        "    \"taboos\": \"...\"\n"
                        "  },\n"
                        "  \"sightseeing\": [\n"
                        "    \"...\", \"...\", \"...\", \"...\", \"...\", \"...\", \"...\", \"...\", \"...\", \"...\"\n"
                        "  ],\n"
                        "  \"famous_food\": [\"...\", \"...\", \"...\", \"...\", \"...\"],\n"
                        "  \"local_items_to_buy\": [\"...\", \"...\", \"...\", \"...\", \"...\"],\n"
                        "  \"local_transport\": [\n"
                        "    {\"mode\": \"...\", \"pass_type\": \"...\", \"price\": \"...\"}\n"
                        "  ],\n"
                        "  \"weather_forecast\": {\n"
                        "    \"day_1\": {\"morning\": \"...\", \"afternoon\": \"...\", \"evening\": \"...\"},\n"
                        "    ... (per day, for each day of the trip from start_date to end_date)\n"
                        "  },\n"
                        "  \"emergency_contacts\": {\n"
                        "    \"local_police\": \"...\",\n"
                        "    \"nearest_embassy\": \"...\",\n"
                        "    \"hospital\": \"...\"\n"
                        "  },\n"
                        "  \"travel_tips\": {\n"
                        "    \"currency\": \"...\",\n"
                        "    \"language\": \"...\",\n"
                        "    \"common_phrases\": [\n"
                        "      {\"phrase\": \"...\", \"meaning\": \"...\"},\n"
                        "      {\"phrase\": \"...\", \"meaning\": \"...\"}\n"
                        "    ]\n"
                        "  }\n"
                        "}\n\n"
                        "Requirements:\n"
                        "- Use multiple search tools (travel_serper_search, tavily_search, duckduckgo_search, or multi_search) to find and cross-verify accurate and up-to-date flight prices, schedules, and availability.\n"
                        "- When searching for flight information, use specific queries like 'flights from [origin] to [destination] on [date]' to get accurate results.\n"
                        "- When searching for hotel information, use specific queries like 'hotels in [destination] with prices' to get accurate results.\n"
                        "- Use the multi_search tool for important information that requires verification from multiple sources.\n"
                        "- Include at least 8 diverse and realistic flight options (varied airlines, times, prices).\n"
                        "- For flights, always include detailed layover information in the layover_details array with city name, duration, arrival time at the layover city, departure time of the next flight, and whether a terminal change is required.\n"
                        "- If it's a direct flight, provide an empty array for layover_details.\n"
                        "- Sort flights by price from cheapest to most expensive.\n"
                        "- For each flight, include fare class information (Economy, Premium Economy, Business).\n"
                        "- For each flight, include check-in baggage allowance in both kg and lbs (e.g., '20 kg (44 lbs)', '30 kg (66 lbs)') and hand baggage allowance in both kg and lbs (e.g., '7 kg (15 lbs)', '10 kg (22 lbs)').\n"
                        "- For each flight, include departure and arrival dates and times (e.g., departure_date: '2023-12-15', departure_time: '08:30 AM', arrival_date: '2023-12-15', arrival_time: '11:45 AM').\n"
                        "- Include flight number for each flight option.\n"
                        "- If trains are available for the route between the user's specified origin and destination, include at least 5 train options with detailed information.\n"
                        "- For trains, include train number, name, operator, class options, departure and arrival times, duration, availability status, and detailed stops information.\n"
                        "- For train stops, include the station name, arrival time, departure time, and platform number for each stop.\n"
                        "- If buses are available for the route between the user's specified origin and destination, include at least 5 bus options with detailed information.\n"
                        "- For buses, include operator, bus type, departure and arrival times, duration, availability status, and detailed stops information.\n"
                        "- For bus stops, include the location name, arrival time, departure time, and duration of the stop.\n"
                        "- Include 8 real and well-known hotels (across luxury, mid-range, budget categories).\n"
                        "- Sort hotels by price from cheapest to most expensive.\n"
                        "- For each hotel, include check-in and check-out times (e.g., check_in_time: '3:00 PM', check_out_time: '11:00 AM').\n"
                        "- For each hotel, include availability status (e.g., 'Available', 'Limited Rooms', 'Almost Full') and available dates that align with the trip duration.\n"
                        "- Create a daily plan for each day of the trip, from start_date to end_date.\n"
                        "- Each day should have 5 daily activities (e.g., sightseeing, cultural, dining, shopping, nightlife).\n"
                        "- For each activity in the daily plan, include the mode of transport (Metro, Bus, Cab, Train, Walk) and the transport fare.\n"
                        "- Research and include special events (festivals, sports matches, concerts, parades, exhibitions, cultural events) happening during the trip dates.\n"
                        "- Research and include pilgrimages and religious events happening at the destination during the trip dates.\n"
                        "- For pilgrimages, include religious significance, crowd expectations, and any special rituals or customs.\n"
                        "- Research and include current news and happenings at the destination that might affect the trip.\n"
                        "- For news events, include current happenings, local news, and any events that might affect travel plans (e.g., political rallies, strikes, special celebrations).\n"
                        "- Research and include detailed country culture information, including do's and don'ts, cultural norms, local customs, and taboos specific to the destination.\n"
                        "- For cultural norms, include information about greetings, dress code, dining etiquette, religious customs, and social interactions specific to the destination.\n"
                        "- For each event, include the name, type, date, time, location, description, price (if applicable), and ticket URL (if available).\n"
                        "- Provide at least 10 sightseeing places, relevant to the destination.\n"
                        "- Use real names for hotels, flights, trains, buses, locations, and events (no placeholders).\n"
                        "- All values must be realistic for the destination and trip duration (calculated from start_date to end_date).\n"
                        "- Adjust daily activities based on optional user preferences:\n"
                        "   - trip_theme (romantic, adventure, family, wellness, pilgrimage)\n"
                        "   - pace (relaxed = 3/day, moderate = 4/day, packed = 5+/day)\n"
                        "   - meal_preferences (vegetarian, halal, local-only)\n"
                        "- Price values can be numbers or strings with currency (e.g., \"$150\", 120).\n"
                        "- You must ONLY respond with JSON. Do NOT include any explanation, greeting, or apology.\n"
                        "- For each hotel and event, include a URL for booking and an image link.\n"
                        "- For each flight, train, and bus, include only a URL for booking (no image needed).\n"
                        "- If no image available, use a fallback dummy image: https://dummyimage.com/600x400/cccccc/000000&text=Image+Not+Available\n"
                    )),
                    *state["messages"]
                ])
            ]
        }

    def should_continue(state: State):
        last = state["messages"][-1]
        return "tools" if last.tool_calls else END

    graph = StateGraph(State)
    graph.add_node("agent", call_model)
    graph.add_node("tools", tool_node)
    graph.add_edge("tools", "agent")
    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", should_continue)

    return graph.compile()

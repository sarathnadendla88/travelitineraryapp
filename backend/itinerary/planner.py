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

model = ChatGroq(model="llama-3.3-70b-versatile")

def create_langgraph_agent():
    @tool
    def travel_tavily_search(query: str):
        """Use Tavily to search for real-time travel information."""
        from tavily import TavilyClient
        client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        result = client.search(query=query)
        return result

    tool_node = ToolNode([travel_tavily_search])
    model_with_tools = model.bind_tools([travel_tavily_search])

    def call_model(state: State):
        return {
            "messages": [
                model_with_tools.invoke([
                    SystemMessage(content=(
                        "You are a professional travel itinerary planner assistant. "
                        "Your task is to return a well-structured JSON object based on user trip details. "
                        "Always respond ONLY with JSON. DO NOT include any explanation or apologies.\n\n"
                        "Use the following strict format:\n\n"
                        "{\n"
                        "  \"flights\": [\n"
                        "    {\"from\": \"...\", \"to\": \"...\", \"airline\": \"...\", \"price\": \"...\", \"layover\": \"City name - Duration (e.g., 'Frankfurt - 2h 30m')\", \"url\": \"...\", \"image\": \"...\"},\n"
                        "    ... (8 total realistic and diverse flight options, sorted by price from cheapest to most expensive)\n"
                        "  ],\n"
                        "  \"hotels\": [\n"
                        "    {\"name\": \"...\", \"location\": \"...\", \"price_per_night\": \"...\", \"url\": \"...\", \"image\": \"...\"},\n"
                        "    ... (8 total real and well-reviewed hotels, sorted by price from cheapest to most expensive)\n"
                        "  ],\n"
                        "  \"daily_plan\": {\n"
                        "    \"day_1\": [\n"
                        "      {\"time\": \"Morning\", \"type\": \"Sightseeing\", \"activity\": \"...\"},\n"
                        "      {\"time\": \"Late Morning\", \"type\": \"Cultural\", \"activity\": \"...\"},\n"
                        "      {\"time\": \"Afternoon\", \"type\": \"Dining\", \"activity\": \"...\"},\n"
                        "      {\"time\": \"Evening\", \"type\": \"Leisure\", \"activity\": \"...\"},\n"
                        "      {\"time\": \"Night\", \"type\": \"Entertainment\", \"activity\": \"...\"}\n"
                        "    ],\n"
                        "    ... (Repeat for each day based on trip duration from start_date to end_date)\n"
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
                        "- Include at least 8 diverse and realistic flight options (varied airlines, times, prices).\n"
                        "- For flights, always include detailed layover information with city name and duration (e.g., 'Frankfurt - 2h 30m').\n"
                        "- If it's a direct flight, specify 'Direct Flight' in the layover field.\n"
                        "- Sort flights by price from cheapest to most expensive.\n"
                        "- Include 8 real and well-known hotels (across luxury, mid-range, budget categories).\n"
                        "- Sort hotels by price from cheapest to most expensive.\n"
                        "- Create a daily plan for each day of the trip, from start_date to end_date.\n"
                        "- Each day should have 5 daily activities (e.g., sightseeing, cultural, dining, shopping, nightlife).\n"
                        "- Provide at least 10 sightseeing places, relevant to the destination.\n"
                        "- Use real names for hotels, flights, and locations (no placeholders).\n"
                        "- All values must be realistic for the destination and trip duration (calculated from start_date to end_date).\n"
                        "- Adjust daily activities based on optional user preferences:\n"
                        "   - trip_theme (romantic, adventure, family, wellness)\n"
                        "   - pace (relaxed = 3/day, moderate = 4/day, packed = 5+/day)\n"
                        "   - meal_preferences (vegetarian, halal, local-only)\n"
                        "- Price values can be numbers or strings with currency (e.g., \"$150\", 120).\n"
                        "- You must ONLY respond with JSON. Do NOT include any explanation, greeting, or apology.\n"
                        "- For each flight and hotel, include a `url` for booking and an `image` link.\n"
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

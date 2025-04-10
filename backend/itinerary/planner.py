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

model = ChatGroq(model="llama3-70b-8192")

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
                        "    {\"from\": \"...\", \"to\": \"...\", \"airline\": \"...\", \"price\": \"...\"}\n"
                        "  ],\n"
                        "  \"hotels\": [\n"
                        "    {\"name\": \"...\", \"location\": \"...\", \"price_per_night\": \"...\"}\n"
                        "  ],\n"
                        "  \"daily_plan\": {\n"
                        "    \"day_1\": [\n"
                        "      {\"time\": \"Morning\", \"type\": \"Sightseeing\", \"activity\": \"Visit the Eiffel Tower\"},\n"
                        "      {\"time\": \"Afternoon\", \"type\": \"Dining\", \"activity\": \"Lunch at a riverside café\"},\n"
                        "      {\"time\": \"Evening\", \"type\": \"Cruise\", \"activity\": \"Seine River boat cruise\"}\n"
                        "    ],\n"
                        "    \"day_2\": [\n"
                        "      {\"time\": \"Morning\", \"type\": \"Museum\", \"activity\": \"Tour the Louvre Museum\"},\n"
                        "      {\"time\": \"Afternoon\", \"type\": \"Shopping\", \"activity\": \"Shop on Champs-Élysées\"},\n"
                        "      {\"time\": \"Evening\", \"type\": \"Dining\", \"activity\": \"Dinner at Le Cinq\"}\n"
                        "    ]\n"
                        "  },\n"
                        "  \"sightseeing\": [\n"
                        "    \"Eiffel Tower\", \"Louvre Museum\", \"Notre-Dame Cathedral\", \"Champs-Élysées\", \"Montmartre\"\n"
                        "  ],\n"
                        "  \"famous_food\": [\n"
                        "    \"Croissant\", \"Escargot\", \"Coq au Vin\", \"Crêpes\", \"Macarons\"\n"
                        "  ],\n"
                        "  \"local_items_to_buy\": [\n"
                        "    \"French wine\", \"Perfume\", \"Designer fashion\", \"Cheese\", \"Handmade soaps\"\n"
                        "  ]\n"
                        "}\n\n"
                        "Ensure your response strictly follows this format and includes realistic values for the selected destination and trip duration. "
                        "DO NOT return any text outside the JSON block."
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

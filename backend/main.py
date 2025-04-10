from fastapi import FastAPI
from backend.itinerary.schema import ItineraryRequest, ItineraryResponse
from backend.itinerary.planner import create_langgraph_agent
from langchain_core.messages import HumanMessage
import json

app = FastAPI()
agent_executor = create_langgraph_agent()

@app.post("/plan", response_model=ItineraryResponse)
async def generate_itinerary(payload: ItineraryRequest):
    user_prompt = HumanMessage(content=json.dumps(payload.dict()))

    result = agent_executor.invoke({"messages": [user_prompt]})
    final_message = result["messages"][-1]

    print("🧪 LLM Output:\n", final_message.content)

    try:
        itinerary_data = json.loads(final_message.content)
    except Exception as e:
        itinerary_data = {
            "error": "Failed to parse JSON from model",
            "raw_output": final_message.content,
            "exception": str(e),
        }

    return {
        "status": "success",
        "data": {
            "traveler": {
                "name": "",
                "count": payload.people,
            },
            "trip": {
                "startDate": payload.start_date,
                "endDate": payload.end_date,
                "origin": payload.current_location,
                "destination": payload.destination,
                "itinerary": itinerary_data,
            }
        }
    }

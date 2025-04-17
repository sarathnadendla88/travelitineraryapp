from fastapi import FastAPI
from backend.itinerary.schema import ItineraryRequest, ItineraryResponse
from backend.itinerary.planner import create_langgraph_agent
from langchain_core.messages import HumanMessage
import json

app = FastAPI()
agent_executor = create_langgraph_agent()

@app.post("/plan", response_model=ItineraryResponse)
async def generate_itinerary(payload: ItineraryRequest):
    # Maximum number of retries for the LLM call
    max_retries = 3

    # Use model_dump instead of dict (which is deprecated)
    try:
        user_prompt_content = json.dumps(payload.model_dump())
    except AttributeError:
        # Fallback for older versions of Pydantic
        user_prompt_content = json.dumps(payload.dict())

    user_prompt = HumanMessage(content=user_prompt_content)

    # Initialize variables
    final_message = None
    itinerary_data = None
    success = False
    attempt = 0

    while not success and attempt < max_retries:
        attempt += 1
        print(f"\n🔄 Attempt {attempt} of {max_retries}")

        try:
            # Invoke the agent
            result = agent_executor.invoke({"messages": [user_prompt]})
            final_message = result["messages"][-1]

            # Try to parse the response
            content = final_message.content

            # Check if content is valid
            if content and len(content.strip()) > 0:
                try:
                    # Try direct parsing first
                    itinerary_data = json.loads(content)

                    # Validate that the response has the required fields
                    required_fields = ["flights", "hotels", "daily_plan"]
                    if all(field in itinerary_data for field in required_fields):
                        print(f"✅ Attempt {attempt}: Valid response received with all required fields")
                        success = True
                    else:
                        missing_fields = [field for field in required_fields if field not in itinerary_data]
                        print(f"⚠️ Attempt {attempt}: Response missing required fields: {missing_fields}")

                        # Add a more specific prompt for the retry
                        retry_prompt = f"""Your previous response was missing these required fields: {missing_fields}.
                        Please provide a complete response with ALL required fields according to the schema.
                        Original request: {user_prompt_content}"""

                        user_prompt = HumanMessage(content=retry_prompt)
                except json.JSONDecodeError:
                    print(f"⚠️ Attempt {attempt}: JSON parsing failed, retrying...")
            else:
                print(f"⚠️ Attempt {attempt}: Empty response received, retrying...")
        except Exception as e:
            print(f"❌ Attempt {attempt}: Error: {str(e)}")

        # If we're still not successful and have more attempts, wait briefly before retrying
        if not success and attempt < max_retries:
            import time
            time.sleep(2)  # Wait 2 seconds between attempts

    # If we still don't have a valid response after all retries, use the last response
    if not success and final_message is not None:
        print("❌ All retry attempts failed. Using last response.")

    print("🧪 LLM Output:\n", final_message.content)

    # If we already have valid itinerary_data from our retry loop, use that
    if success and itinerary_data:
        print("Using successfully parsed itinerary data from retry loop")
    else:
        # Otherwise, try to parse the content again or use fallback
        # Check if content is empty or whitespace
        if not final_message.content or final_message.content.strip() == "":
            print("Warning: Empty content received from LLM")
            # Provide a minimal valid JSON as fallback
            itinerary_data = {
                "error": "Empty response from model",
                "flights": [],
                "hotels": [],
                "trains": [],
                "buses": [],
                "daily_plan": {}
            }
            return {
                "status": "partial_success",
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

    # If we don't already have valid itinerary_data from our retry loop, try to parse it now
    if not (success and itinerary_data):
        try:
            # First, try to parse the content directly
            content = final_message.content

            # Function to attempt to fix common JSON syntax errors
            def fix_json(json_str):
                # Replace single quotes with double quotes (but not inside strings)
                import re
                # Fix trailing commas in arrays and objects
                json_str = re.sub(r',\s*([\]\}])', r'\1', json_str)
                # Fix missing quotes around keys
                json_str = re.sub(r'([{,])\s*(\w+)\s*:', r'\1"\2":', json_str)
                # Fix unquoted values that should be strings
                # This is a simplistic approach and might not catch all cases
                return json_str

            try:
                # Try to parse directly
                print(f"Attempting to parse content of length {len(content)}")
                print(f"First 100 characters: {content[:100]}")
                itinerary_data = json.loads(content)
            except json.JSONDecodeError as e:
                print(f"Initial JSON parsing failed: {str(e)}")
                print(f"Content type: {type(content)}")

                # Try to fix common JSON errors
                try:
                    fixed_content = fix_json(content)
                    print(f"Attempting to parse fixed content of length {len(fixed_content)}")
                    print(f"First 100 characters of fixed content: {fixed_content[:100]}")
                    itinerary_data = json.loads(fixed_content)
                    print("JSON fixed and parsed successfully")
                except json.JSONDecodeError:
                    # If direct parsing fails, check if the content is wrapped in markdown code blocks
                    if "```json" in content or "```" in content:
                        # Extract JSON from markdown code blocks
                        import re
                        json_match = re.search(r'```(?:json)?\n(.+?)\n```', content, re.DOTALL)
                        if json_match:
                            json_str = json_match.group(1)
                            try:
                                itinerary_data = json.loads(json_str)
                            except json.JSONDecodeError:
                                # Try to fix the extracted JSON
                                fixed_json = fix_json(json_str)
                                itinerary_data = json.loads(fixed_json)
                        else:
                            # Try another approach - find content between triple backticks
                            parts = content.split('```')
                            if len(parts) >= 3:  # At least one code block
                                # The content between the first and second ``` is our JSON
                                json_str = parts[1]
                                # Remove 'json' if it's the language specifier
                                if json_str.startswith('json'):
                                    json_str = json_str[4:]
                                try:
                                    itinerary_data = json.loads(json_str.strip())
                                except json.JSONDecodeError:
                                    # Try to fix the extracted JSON
                                    fixed_json = fix_json(json_str.strip())
                                    itinerary_data = json.loads(fixed_json)
                            else:
                                # Last resort: try to find anything that looks like JSON
                                import re
                                # Look for content between curly braces
                                json_match = re.search(r'(\{.*\})', content, re.DOTALL)
                                if json_match:
                                    json_str = json_match.group(1)
                                    try:
                                        itinerary_data = json.loads(json_str)
                                    except json.JSONDecodeError:
                                        # Try to fix the extracted JSON
                                        fixed_json = fix_json(json_str)
                                        itinerary_data = json.loads(fixed_json)
                                else:
                                    raise ValueError("Could not extract JSON from content")
                    else:
                        raise
        except Exception as e:
            print(f"Error parsing JSON: {str(e)}")
            # Create a minimal valid structure with the error information
            itinerary_data = {
                "error": "Failed to parse JSON from model",
                "raw_output": final_message.content[:500] + "..." if len(final_message.content) > 500 else final_message.content,
                "exception": str(e),
                # Add minimal required fields to prevent UI errors
                "flights": [],
                "trains": [],
                "buses": [],
                "hotels": [],
                "daily_plan": {},
                "events": [],
                "news": [],
                "sightseeing": [],
                "famous_food": [],
                "local_items_to_buy": [],
                "local_transport": [],
                "weather_forecast": {},
                "emergency_contacts": {},
                "travel_tips": {},
                "country_culture": {"dos": [], "donts": []}
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

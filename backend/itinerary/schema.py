from typing_extensions import TypedDict
from pydantic import BaseModel

class ItineraryRequest(BaseModel):
    current_location: str
    destination: str
    trip_type: str
    num_days: int
    people: int
    start_date: str  # YYYY/MM/DD
    end_date: str    # YYYY/MM/DD

class ItineraryResponse(BaseModel):
    status: str
    data: dict

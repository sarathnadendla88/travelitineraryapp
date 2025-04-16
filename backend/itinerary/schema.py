from typing_extensions import TypedDict, Optional
from pydantic import BaseModel
from datetime import datetime

class ItineraryRequest(BaseModel):
    current_location: str
    destination: str
    trip_type: str
    num_days: Optional[int] = None
    people: int
    start_date: str  # YYYY/MM/DD
    end_date: str    # YYYY/MM/DD

    def __init__(self, **data):
        super().__init__(**data)
        # Calculate num_days from start_date and end_date if not provided
        if self.num_days is None and self.start_date and self.end_date:
            try:
                start = datetime.strptime(self.start_date, "%Y/%m/%d")
                end = datetime.strptime(self.end_date, "%Y/%m/%d")
                self.num_days = (end - start).days + 1
            except Exception:
                # Default to 1 day if date parsing fails
                self.num_days = 1

class ItineraryResponse(BaseModel):
    status: str
    data: dict

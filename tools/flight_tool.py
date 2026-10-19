import os
import certifi
import airportsdata
import requests
from typing import Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator
from langchain.tools import tool

load_dotenv()

os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

API_KEY = os.getenv("AVIATIONSTACK_API_KEY")


BASE_URL = "https://api.aviationstack.com/v1/flights"


AIRPORTS = airportsdata.load("IATA")

class FlightSearchRequest(BaseModel):
    origin: Optional[str] = Field(
        default = None,
        description = (
            "The IATA code of the origin airport, e.g. DAC for Dhaka. "
            "Resolve cities and countries to their main international airport "
            "yourself. Omit to search by destination only."
        )
    )
    destination: Optional[str] = Field(
        default = None,
        description = (
            "The IATA code of the destination airport, e.g. NRT for Tokyo. "
            "Resolve cities and countries to their main international airport "
            "yourself. Omit to search by origin only."
        )
    )
    limit: int = Field(
        default = 5,
        ge = 1,
        le = 100,
        description = "The maximum number of flight results to return."
    )

    @field_validator("origin", "destination", mode = "before")
    @classmethod
    def normalize_iata(cls, value):
        if value is None:
            return None
        return str(value).strip().upper() or None


def format_flight(flight: dict) -> str:
    airline = flight.get("airline", {}).get("name") or "Unknown airline"
    number = flight.get("flight", {}).get("iata") or "Unknown flight number"
    status = flight.get("flight_status") or "Unknown"

    dep = flight.get("departure") or {}
    arr = flight.get("arrival") or {}

    return (
        f"Airline: {airline} | Flight: {number} | Status: {status}\n"
        f"From: {dep.get('airport') or 'Unknown'} ({dep.get('iata') or '???'}) "
        f"at {dep.get('scheduled') or 'Unknown'}\n"
        f"To: {arr.get('airport') or 'Unknown'} ({arr.get('iata') or '???'}) "
        f"at {arr.get('scheduled') or 'Unknown'}"
    )


@tool("search_flights", args_schema = FlightSearchRequest)
def search_flights(
    origin: Optional[str] = None,
    destination: Optional[str] = None,
    limit: int = 5,
) -> str:
    """
    Tool to search live and scheduled flights between two airports using the
    AviationStack API.

    Resolve cities and countries to IATA airport codes before calling: Dhaka or
    Bangladesh is DAC, Tokyo or Japan is NRT, London is LHR. Both origin and
    destination are optional. Returns airline, flight number, status and
    scheduled times. It does NOT return ticket prices.
    """
    if not API_KEY:
        return "Flight API error: AVIATIONSTACK_API_KEY is missing from the .env file."

    if origin and origin not in AIRPORTS:
        return f"Invalid origin airport code '{origin}'. Retry with a valid 3-letter IATA code."

    if destination and destination not in AIRPORTS:
        return f"Invalid destination airport code '{destination}'. Retry with a valid 3-letter IATA code."

    params = {
        "access_key": API_KEY,
        "limit": limit,
    }

    if origin:
        params["dep_iata"] = origin

    if destination:
        params["arr_iata"] = destination

    try:
        response = requests.get(BASE_URL, params=params, timeout=60)
        payload = response.json()
    except requests.exceptions.RequestException as e:
        return f"Error occurred while making the API request: {e}"
    except ValueError:
        return f"Error occurred while parsing the API response (HTTP {response.status_code})."

    if "error" in payload:
        error = payload["error"] or {}
        return (
            "Flight API error:\n"
            f"Code: {error.get('code', 'Unknown')}\n"
            f"Message: {error.get('message', 'Unknown error')}"
        )

    data = payload.get("data") or []

    if not data:
        return (
            "No live flight data found for that search.\n"
            "Note: AviationStack serves live status data, not ticket prices."
        )

    return "\n\n---\n\n".join(format_flight(flight) for flight in data[:limit])

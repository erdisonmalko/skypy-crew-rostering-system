from app.models.models import Flight

def required_rest_minutes(flight: Flight) -> int:
      """Calculate required rest time based on flight duration."""
      return 60 if flight.duration_minutes < 180 else 120
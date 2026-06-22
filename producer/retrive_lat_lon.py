from geopy.geocoders import Nominatim

def get_city_coordinates(city_name):
    """
    Retrieves the latitude and longitude of a city.

    Args:
        city_name (str): The name of the city

    Returns:
        tuple: (latitude, longitude) or None if the city is not found
    """
    geolocator = Nominatim(user_agent="city_locator")
    try:
        location = geolocator.geocode(city_name)
        if location:
            return (location.latitude, location.longitude)
        else:
            return None
    except Exception as e:
        print(f"Error retrieving coordinates for {city_name}: {e}")
        return None

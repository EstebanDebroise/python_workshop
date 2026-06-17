from geopy.geocoders import Nominatim

def get_city_coordinates(city_name):
    """
    Récupère la latitude et la longitude d'une ville.

    Args:
        city_name (str): Le nom de la ville

    Returns:
        tuple: (latitude, longitude) ou None si la ville n'est pas trouvée
    """
    geolocator = Nominatim(user_agent="city_locator")
    try:
        location = geolocator.geocode(city_name)
        if location:
            return (location.latitude, location.longitude)
        else:
            return None
    except Exception as e:
        print(f"Erreur lors de la recherche de la ville: {e}")
        return None


if __name__ == "__main__":
    # Exemple d'utilisation
    city = "Montpinchon"
    coords = get_city_coordinates(city)
    if coords:
        print(f"Coordonnées de {city}: Latitude {coords[0]}, Longitude {coords[1]}")
    else:
        print(f"Ville '{city}' non trouvée")

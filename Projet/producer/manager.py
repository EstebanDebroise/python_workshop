import time
import sys
from weather_collector import fetch_kafka_topics, fetch_weather, send_to_kafka, format_message
from retrive_lat_lon import get_city_coordinates

def main():
    topics = fetch_kafka_topics()
    if len(topics) > 10:
        print("[ALERT] Number of topics exceeds 10. Please check the configuration.", file=sys.stderr)

    for topic in topics:
        cordonnee = get_city_coordinates(topic)
        if cordonnee is not None:
            lat, lon = cordonnee
            if lat is not None and lon is not None:
                weather_data = fetch_weather(lat, lon)
                weather_data_formatted = format_message(weather_data, lat, lon)
                send_to_kafka(topic, weather_data_formatted)
        else:
            print(f"[ERROR] Unable to retrieve coordinates for {topic}.", file=sys.stderr)

if __name__ == "__main__":    
    main()
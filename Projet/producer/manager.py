import sys
from weather_collector import fetch_kafka_topics, fetch_weather, send_to_kafka, format_message
from retrive_lat_lon import get_city_coordinates

def main():
    print("[INFO] ========================================", file=sys.stderr)
    print("[INFO]  Weather Producer starting up...", file=sys.stderr)
    print("[INFO] ========================================", file=sys.stderr)

    print("[INFO] Fetching topic list from API...", file=sys.stderr)
    topics = fetch_kafka_topics()

    if not topics:
        print("[WARN] No topics found. Nothing to collect.", file=sys.stderr)
        return

    print(f"[INFO] Found {len(topics)} topic(s): {', '.join(topics)}", file=sys.stderr)

    if len(topics) > 10:
        print("[ALERT] Number of topics exceeds 10. Please check the configuration.", file=sys.stderr)

    for topic in topics:
        print(f"[INFO] Processing topic '{topic}'...", file=sys.stderr)
        cordonnee = get_city_coordinates(topic)
        if cordonnee is not None:
            lat, lon = cordonnee
            if lat is not None and lon is not None:
                print(f"[INFO] Fetching weather for {topic} (lat={lat}, lon={lon})...", file=sys.stderr)
                weather_data = fetch_weather(lat, lon)
                weather_data_formatted = format_message(weather_data, lat, lon)
                send_to_kafka(topic, weather_data_formatted)
                print(f"[INFO] Done for '{topic}'.", file=sys.stderr)
        else:
            print(f"[ERROR] Unable to retrieve coordinates for '{topic}'.", file=sys.stderr)

    print("[INFO] All topics processed. Producer shutting down.", file=sys.stderr)

if __name__ == "__main__":
    main()
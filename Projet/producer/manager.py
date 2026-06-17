#this programme feth the number of topic and manage to update each topic at least 1 time per 10 minutes but don't ask the api more than 1 time per minute if the number of topic is more than 10 send a alert but continue to update the topic with the api
import time
import sys
from weather_collector import fetch_kafka_topics, fetch_weather_mock, send_to_kafka
from retrive_lat_lon import get_city_coordinates

def main():
    while True:
        topics = fetch_kafka_topics()
        if len(topics) > 10:
            print("[ALERTE] Nombre de topics supérieur à 10. Veuillez vérifier la configuration.", file=sys.stderr)

        for topic in topics:
            cordonnee = get_city_coordinates(topic)
            if cordonnee is not None:
                lat, lon = cordonnee
                if lat is not None and lon is not None:
                    weather_data = fetch_weather_mock(lat, lon)
                    send_to_kafka(topic, weather_data)
            else:
                print(f"[ERREUR] Impossible de récupérer les coordonnées pour {topic}.", file=sys.stderr)

        time.sleep(600)  # Attendre 10 minutes avant la prochaine mise à jour

if __name__ == "__main__":    
    main()
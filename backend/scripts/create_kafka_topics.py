"""
Étape 10 — Collecte des données (Kafka)

Script one-shot pour créer explicitement les topics métier avec un nombre
de partitions défini, plutôt que de laisser Kafka les créer implicitement
au premier message (souvent avec 1 seule partition, ce qui limite le
parallélisme de lecture pour Spark à l'étape 11).

Utilisation (une fois Docker/Kafka lancé) :

    cd backend
    python scripts/create_kafka_topics.py
"""
import sys
from pathlib import Path

# Permet d'exécuter le script directement (python scripts/create_kafka_topics.py)
# sans avoir à installer le package.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError

from app.config import settings
from app.kafka_topics import ALL_TOPICS


def main():
    admin = KafkaAdminClient(
        bootstrap_servers=settings.kafka_bootstrap_servers,
        client_id="smartrent-topic-setup",
    )

    topics = [
        NewTopic(name=name, num_partitions=3, replication_factor=1)
        for name in ALL_TOPICS
    ]

    try:
        admin.create_topics(new_topics=topics, validate_only=False)
        print(f"Topics créés : {ALL_TOPICS}")
    except TopicAlreadyExistsError:
        print("Certains topics existent déjà — c'est normal si le script a déjà été exécuté.")
    finally:
        admin.close()


if __name__ == "__main__":
    main()

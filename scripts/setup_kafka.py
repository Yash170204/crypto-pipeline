from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC_RAW

admin_client = KafkaAdminClient(
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    client_id='setup'
)

topic = NewTopic(
    name=KAFKA_TOPIC_RAW,
    num_partitions=3,
    replication_factor=1
)

try:
    admin_client.create_topics(new_topics=[topic], validate_only=False)
    print(f"Topic '{KAFKA_TOPIC_RAW}' created successfully")
except TopicAlreadyExistsError:
    print(f"Topic '{KAFKA_TOPIC_RAW}' already exists")

admin_client.close()

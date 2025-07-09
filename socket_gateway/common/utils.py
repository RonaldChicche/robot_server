from kafka import KafkaProducer, KafkaConsumer

import redis, yaml, json, os


def load_keys(path="redis_keys.yaml"):
    with open(path, "r") as f:
        return yaml.safe_load(f)
    
def create_kafka_consumer(topic, broker, group_id):
    consumer = KafkaConsumer(
        topic, 
        bootstrap_servers=[broker], 
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        group_id=group_id,
        auto_offset_reset='latest',
        enable_auto_commit=True
        )
    return consumer

def create_kafka_producer(broker):
    producer = KafkaProducer(
        bootstrap_servers=[broker],
        value_serializer=lambda v: json.dumps(v).encode("utf-8")
        )
    return producer

def create_redis_client(host="localhost", port=6379):
    return redis.Redis(host=host, port=port, decode_responses=True)

import time
from confluent_kafka import Consumer, Producer, KafkaError
from json import dumps, loads

class PackageDataProcessor:
    def __init__(self, consumer_config, producer_config, topic_consumer, topic_producer, cities_file_path):
        self.consumer = Consumer(consumer_config)
        self.producer = Producer(producer_config)
        self.topic_consumer = topic_consumer
        self.topic_producer = topic_producer
        self.desired_cities = self.load_desired_cities(cities_file_path)

    def load_desired_cities(self, file_path):
        with open(file_path, 'r') as file:
            return [line.strip().lower() for line in file]

    def city_is_desired(self, city_name):
        return city_name.lower() in self.desired_cities

    def process_message(self, msg_json):
        if 'destination_city' in msg_json and self.city_is_desired(msg_json['destination_city']):
            filtered_msg_str = dumps(msg_json)
            filtered_msg_bytes = filtered_msg_str.encode('utf-8')
            self.producer.produce(topic=self.topic_producer, value=filtered_msg_bytes)
            print("Enviando datos a {} al tópico {}".format(filtered_msg_str, self.topic_producer))

    def consume_messages(self):
        self.consumer.subscribe([self.topic_consumer])

        try:
            while True:
                msg = self.consumer.poll(1.0)  # Lee nuevos mensajes cada 1 segundo

                if msg is not None:
                    if msg.error():
                        if msg.error().code() == KafkaError._PARTITION_EOF:
                            print("No hay más mensajes en esta partición.")
                        else:
                            print("Error al recibir mensaje: {}".format(msg.error()))
                    else:
                        # Procesar el mensaje recibido.
                        msg_value_str = msg.value().decode('utf-8')
                        msg_json = loads(msg_value_str)
                        self.process_message(msg_json)

        except KeyboardInterrupt:
            pass
        finally:
            self.consumer.close()

if __name__ == "__main__":
    # Configuración del consumidor
    consumer_config = {
        'bootstrap.servers': 'localhost:9092',
        'group.id': 'python-consumer-group',
        'auto.offset.reset': 'earliest'
    }

    # Configuración del productor
    producer_config = {
        'bootstrap.servers': 'localhost:9092',
        'client.id': 'python-producer'
    }

    topic_consumer = 'package_delivery'
    topic_producer = 'package_delivery_madrid'
    cities_file_path = 'destinatios_filtered.txt'

    data_processor = PackageDataProcessor(consumer_config, producer_config, topic_consumer, topic_producer, cities_file_path)

    try:
        data_processor.consume_messages()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Cerrar el consumidor al detener la aplicación Python
        data_processor.consumer.close()

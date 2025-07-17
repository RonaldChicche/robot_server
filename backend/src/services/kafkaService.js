const { Kafka } = require("kafkajs");

const kafka = new Kafka({
  clientId: "robot-backend",
  brokers: [process.env.KAFKA_BROKER],
});

const producer = kafka.producer();

(async () => {
  await producer.connect();
})();

exports.produceKafkaMessage = async (message) => {
  await producer.send({
    topic: process.env.KAFKA_TOPIC_COMMANDS,
    messages: [{ value: JSON.stringify(message) }],
  });
};


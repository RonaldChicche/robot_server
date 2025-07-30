const { Kafka, logLevel } = require("kafkajs");

const kafka = new Kafka({
  clientId: "robot-backend",
  brokers: [process.env.KAFKA_BROKER],
  retry: {
    retries: 10,
    initialRetryTime: 300,
    factor: 0.2,
    multiplier: 2,
  },
  logLevel: logLevel.ERROR,
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


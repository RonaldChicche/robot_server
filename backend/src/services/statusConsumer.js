const { Kafka } = require("kafkajs");

const kafka = new Kafka({
  clientId: "backend-status-consumer",
  brokers: [process.env.KAFKA_BROKER],
});

const consumer = kafka.consumer({ groupId: "status-consumers" });

async function startStatusConsumer(onMessage) {
  await consumer.connect();
  await consumer.subscribe({ topic: process.env.KAFKA_TOPIC_STATUS, fromBeginning: false });

  await consumer.run({
    eachMessage: async ({ topic, partition, message }) => {
      try {
        const payload = JSON.parse(message.value.toString());
        onMessage(payload); // callback que definimos afuera
      } catch (err) {
        console.error("❌ Error parsing status:", err);
      }
    },
  });
}

module.exports = { startStatusConsumer };

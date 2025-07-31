const { Kafka } = require("kafkajs");

const kafka = new Kafka({
  clientId: "backend-status-consumer",
  brokers: [process.env.KAFKA_BROKER],
});

const consumer = kafka.consumer({ groupId: "status-consumers" });

async function waitForTopic(admin, topicName, maxTries = 10) {
  for (let i = 0; i < maxTries; i++) {
    const topics = await admin.listTopics();
    if (topics.includes(topicName)) return true;
    console.log(`⏳ Esperando a que Kafka propague el topic "${topicName}"...`);
    await new Promise((res) => setTimeout(res, 1000));
  }
  throw new Error(`❌ Timeout esperando el topic ${topicName}`);
}

async function startStatusConsumer(onMessage) {
  const topic = process.env.KAFKA_TOPIC_STATUS;

  const admin = kafka.admin();
  await admin.connect();
  await waitForTopic(admin, topic);
  await admin.disconnect();

  await consumer.connect();
  await consumer.subscribe({ topic, fromBeginning: false });

  await consumer.run({
    eachMessage: async ({ topic, partition, message }) => {
      try {
        const payload = JSON.parse(message.value.toString());
        onMessage(payload);
      } catch (err) {
        console.error("❌ Error parsing status:", err);
      }
    },
  });
}

module.exports = { startStatusConsumer };

const { produceKafkaMessage } = require("../services/kafkaService");
const { getPickAndPutFromRedis } = require("../services/redisService");

exports.sendKafkaMessage = async (req, res) => {
  try {
    const {
      robot_id = process.env.DEFAULT_ROBOT_ID,
      type = "method",
      name,
      params = {},
    } = req.body;

    const timestamp = new Date().toISOString();
    const order_id = `ORD_${timestamp.replace(/[-:.TZ]/g, "")}_${name}_${robot_id}`;

    const { pick, put } = await getPickAndPutFromRedis(robot_id);

    const data_msg = {
      order_id,
      robot_id,
      type,
      name,
      params: {
        ...params
      },
      timestamp,
    };

    await produceKafkaMessage(data_msg);

    res.status(200).json({ success: true, data: data_msg });
  } catch (err) {
    console.error("❌ Error al enviar mensaje a Kafka:", err);
    res.status(500).json({ success: false, error: err.message });
  }
};


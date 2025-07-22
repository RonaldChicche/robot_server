const { produceKafkaMessage } = require("../services/kafkaService");
const {
  buildMethodPayload,
  buildProcessPayload,
} = require("../services/kafkaPayloadBuilder");

exports.sendMethodMessage = async (req, res) => {
  try {
    const {
      robot_id = process.env.DEFAULT_ROBOT_ID,
      name,
      params = {},
    } = req.body;

    const data_msg = buildMethodPayload({ robot_id, name, params });
    await produceKafkaMessage(data_msg);

    res.status(200).json({ success: true, data: data_msg });
  } catch (err) {
    console.error("❌ Error al enviar mensaje tipo method a Kafka:", err);
    res.status(500).json({ success: false, error: err.message });
  }
};

exports.sendProcessMessage = async (req, res) => {
  try {
    const {
      name,
      params = {},
    } = req.body;

    const data_msg = buildProcessPayload({ name, params });
    await produceKafkaMessage(data_msg);

    res.status(200).json({ success: true, data: data_msg });
  } catch (err) {
    console.error("❌ Error al enviar mensaje tipo process a Kafka:", err);
    res.status(500).json({ success: false, error: err.message });
  }
};

exports.sendStartButtonMessage = async (req, res) => {
  try {
    const { id } = req.params;
    const data_msg = buildMethodPayload({ robot_id: id, name: "start_button", params: {} });
    await produceKafkaMessage(data_msg);
    res.status(200).json({ success: true, data: data_msg });
  } catch (err) {
    console.error("❌ Error al enviar mensaje start_button a Kafka:", err);
    res.status(500).json({ success: false, error: err.message });
  }
}

exports.sendPauseButtonMessage = async (req, res) => {
  try {
    const { id } = req.params;
    const data_msg = buildMethodPayload({ robot_id: id, name: "pause_button", params: {} });
    await produceKafkaMessage(data_msg);
    res.status(200).json({ success: true, data: data_msg });
  } catch (err) {
    console.error("❌ Error al enviar mensaje pause_button a Kafka:", err);
    res.status(500).json({ success: false, error: err.message });
  }
}

exports.sendStopButtonMessage = async (req, res) => {
  try {
    const { id } = req.params;
    const data_msg = buildMethodPayload({ robot_id: id, name: "stop_button", params: {} });
    await produceKafkaMessage(data_msg);
    res.status(200).json({ success: true, data: data_msg });
  } catch (err) {
    console.error("❌ Error al enviar mensaje stop_button a Kafka:", err);
    res.status(500).json({ success: false, error: err.message });
  }
}

exports.sendClearAlarmButtonMessage = async (req, res) => {
  try {
    const { id } = req.params;
    const data_msg = buildMethodPayload({ robot_id: id, name: "clear_alarm_button", params: {} });
    await produceKafkaMessage(data_msg);
    res.status(200).json({ success: true, data: data_msg });
  } catch (err) {
    console.error("❌ Error al enviar mensaje clear_alarm a Kafka:", err);
    res.status(500).json({ success: false, error: err.message });
  }
}

exports.sendToggleStackBitMessage = async (req, res) => {
  try {
    const { id } = req.params;
    const { value } = req.body;

    params = { 
      "output_id": 42,
      value 
    };
    const data_msg = buildMethodPayload({ robot_id: id, name: "modify_output_y", params});
    await produceKafkaMessage(data_msg);
    res.status(200).json({ success: true, data: data_msg });
  } catch (err) {
    console.error("❌ Error al enviar mensaje toggle_bit a Kafka:", err);
    res.status(500).json({ success: false, error: err.message });
  }
}

exports.sendToggleCoordBitMessage = async (req, res) => {
  try {
    const { id } = req.params;
    const { value } = req.body;
    params = { 
      "output_id": 41,
      value
    };
    const data_msg = buildMethodPayload({ robot_id: id, name: "modify_output_y", params});
    await produceKafkaMessage(data_msg);
    res.status(200).json({ success: true, data: data_msg });
  } catch (err) {
    console.error("❌ Error al enviar mensaje toggle_bit a Kafka:", err);
    res.status(500).json({ success: false, error: err.message });
  }
}
const express = require("express");
const router = express.Router();
const { sendKafkaMessage } = require("../controllers/kafkaController");

router.post("/send", sendKafkaMessage);

module.exports = router;


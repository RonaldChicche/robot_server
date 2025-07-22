const express = require("express");
const router = express.Router();
const { 
    sendMethodMessage, 
    sendProcessMessage, 
    sendStartButtonMessage, 
    sendPauseButtonMessage, 
    sendStopButtonMessage, 
    sendClearAlarmButtonMessage, 
    sendToggleStackBitMessage, 
    sendToggleCoordBitMessage } = require("../controllers/kafkaController");

router.post("/send-method", sendMethodMessage);
router.post("/send-process", sendProcessMessage);

// control routes
router.post("/:id/start_button", sendStartButtonMessage);
router.post("/:id/pause_button", sendPauseButtonMessage);
router.post("/:id/stop_button", sendStopButtonMessage);
router.post("/:id/clear_alarm_button", sendClearAlarmButtonMessage);
router.post("/:id/toggle-stack-bit", sendToggleStackBitMessage);
router.post("/:id/toggle-coord-bit", sendToggleCoordBitMessage);

module.exports = router;


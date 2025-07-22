const express = require("express");
const dotenv = require("dotenv");
const cors = require("cors");
const http = require("http");

const pool = require("./config/db");
const kafkaRoutes = require("./routes/kafkaRoutes");
const methodsRoutes = require("./routes/methodsRoutes");

const { initSocketServer } = require("./websockets/socketServer");
const { startStatusConsumer } = require("./services/statusConsumer");

dotenv.config();
const app = express();
const server = http.createServer(app);
const io = initSocketServer(server);

app.use(cors());
app.use(express.json());

app.use("/api/kafka", kafkaRoutes);
app.use("/api/methods", methodsRoutes);

app.get("/", async (req, res) => {
  const result = await pool.query("SELECT current_database()");
  res.send(`The data base is YARA: ${result.rows[0].current_database}`);
});

// Kafka + WebSocket bridge
startStatusConsumer((payload) => {
  const { robot_id, status, outputs, counters, timestamp } = payload;
  const filteredData = {
    robot_id,
    timestamp,
    status: {
      alarm_code: status.alarm_code,
      movement_status: status.movement_status,
      cur_mode: status.cur_mode,
      axis_position: status.axis_position,
    },
    outputs: outputs.y,
    counters,
  };

  io.emit(`status:${robot_id}`, filteredData);
  io.emit("status:update", filteredData);
});

const PORT = process.env.PORT || 5000;
server.listen(PORT, () => {
  console.log(`🚀 Servidor backend + WebSocket escuchando en puerto ${PORT}`);
});

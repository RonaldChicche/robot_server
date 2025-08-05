const express = require("express");
const dotenv = require("dotenv");
const cors = require("cors");
const http = require("http");

const pool = require("./config/db");
const kafkaRoutes = require("./routes/kafkaRoutes");
const methodsRoutes = require("./routes/methodsRoutes");
const recetasRoutes = require("./routes/recetasRoutes");
const alarmasRoutes = require("./routes/alarmasRoutes");

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
app.use("/api/recetas", recetasRoutes);
app.use("/api/alarmas", alarmasRoutes);

app.get("/", async (req, res) => {
  const result = await pool.query("SELECT current_database()");
  res.send(`The data base is YARA: ${result.rows[0].current_database}`);
});

// Kafka + WebSocket bridge
startStatusConsumer((payload) => {
  const { robot_id, ip, status, online, timestamp, process_status } = payload;
  const filteredData = {
    robot_id,
    ip,
    online,
    timestamp,
    process_status: process_status.state,
    status: {
      alarm_code: status.status.alarm_code[0],
      movement_status: status.status.movement_status[0],
      cur_mode: status.status.cur_mode[0],
      process_status: process_status.state,
      outputs: status.outputs.y,
    },
    axis_position: status.status.axis_position,
    axis_torque: status.status.axis_torque,
    axis_velocity: status.status.axis_velocity,
    world_position: status.status.world_position,
    counters: status.counters,
  };

  //console.log(filteredData);

  io.emit(`status:${robot_id}`, filteredData);
  io.emit("status:update", filteredData);
});

const PORT = process.env.PORT || 5000;
server.listen(PORT, () => {
  console.log(`🚀 Servidor backend + WebSocket escuchando en puerto ${PORT}`);
});

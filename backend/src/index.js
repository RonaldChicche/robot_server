const express = require("express");
const dotenv = require("dotenv");
const cors = require('cors');
const pool = require("./config/db");
const kafkaRoutes = require("./routes/kafkaRoutes");
// const redisRoutes = require("./routes/redisRoutes");
const methodsRoutes = require("./routes/methodsRoutes");


dotenv.config();

const app = express();

app.use(cors());

// Middlewares
app.use(express.json());

// Rutas
app.use("/api/kafka", kafkaRoutes);
// app.use("/api/redis", redisRoutes);
app.use("/api/methods", methodsRoutes);

// Puerto
const PORT = process.env.PORT || 5000;

app.get("/", async(req, res) => {
  console.log("🚀 Start DB connection");
  const result = await pool.query("SELECT current_database()");
  res.send(`The data base is YARA: ${result.rows[0].current_database}`);
});

app.listen(PORT, () => {
  console.log(`🚀 Servidor backend escuchando en el puerto ${PORT}`);
});

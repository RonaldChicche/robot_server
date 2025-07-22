const { Server } = require("socket.io");

function initSocketServer(httpServer) {
  const io = new Server(httpServer, {
    cors: {
      origin: "*", // ajusta según tu frontend
    },
  });

  io.on("connection", (socket) => {
    console.log("🔌 Cliente conectado:", socket.id);
  });

  return io;
}

module.exports = { initSocketServer };

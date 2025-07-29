// src/lib/socket.js
import { io } from "socket.io-client"

const socket = io("http://190.168.10.102:5000", {
  transports: ["websocket"], // opcional, fuerza websocket
  autoConnect: true,
})

export default socket

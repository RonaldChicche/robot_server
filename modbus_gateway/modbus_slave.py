# modbus_static_server.py
import asyncio, logging, signal
from datetime import datetime
from pymodbus.server import StartAsyncTcpServer
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSlaveContext, ModbusServerContext

logging.basicConfig(level=logging.INFO)
ts = lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

def trace_pdu(is_rx, pdu):
    kind = "RX" if is_rx else "TX"
    data = getattr(pdu, "registers", getattr(pdu, "bits", None))
    logging.info(f"[{ts()}] {kind} fc={pdu.function_code} data={data}")
    return pdu

def build_context():
    # Estático: valores iniciales fijos
    return ModbusServerContext(
        slaves=ModbusSlaveContext(
            di=ModbusSequentialDataBlock(0, [0]*100),
            co=ModbusSequentialDataBlock(0, [0]*100),
            hr=ModbusSequentialDataBlock(0, [0]*1000),  # HR[0]=1234, HR[1]=5678
            ir=ModbusSequentialDataBlock(0, [0]*100),
        ),
        single=True
    )

async def main(host="0.0.0.0", port=5020):
    context = build_context()
    stop = asyncio.Event()

    # Señales para shutdown limpio
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop.set)
        except Exception:
            pass  # Windows no soporta bien add_signal_handler

    logging.info(f"🟢 Modbus TCP esclavo estático en {host}:{port}")
    server_task = asyncio.create_task(
        StartAsyncTcpServer(context, address=(host, port), framer="socket", trace_pdu=trace_pdu)
    )

    # 🔴 IMPORTANTE: esperar hasta Ctrl+C / SIGTERM
    await stop.wait()

    # Cierre limpio
    server_task.cancel()
    try:
        await server_task
    except asyncio.CancelledError:
        pass
    logging.info("🛑 Server stopped")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass

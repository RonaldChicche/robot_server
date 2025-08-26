import asyncio, logging, signal
from datetime import datetime
from pymodbus.server import StartAsyncTcpServer
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSlaveContext, ModbusServerContext

logging.basicConfig(level=logging.INFO)
def ts(): return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

def trace_pdu(is_rx: bool, pdu):
    kind = "RX" if is_rx else "TX"
    data = getattr(pdu, "registers", getattr(pdu, "bits", None))
    logging.info(f"[{ts()}] {kind} fc={pdu.function_code} data={data}")
    return pdu

def build_context():
    store = ModbusSlaveContext(
        di=ModbusSequentialDataBlock(0, [0]*100),
        co=ModbusSequentialDataBlock(0, [0]*100),
        hr=ModbusSequentialDataBlock(0, [0]*1000),
        ir=ModbusSequentialDataBlock(0, [0]*100),
    )
    return ModbusServerContext(slaves=store, single=True)

async def main(host="0.0.0.0", port=5020):
    context = build_context()
    stop = asyncio.Event()

    for s in (signal.SIGINT, signal.SIGTERM):
        try:
            asyncio.get_running_loop().add_signal_handler(s, stop.set)
        except Exception:
            logging.warning(f"Error adding signal handler: {s}", exc_info=True)

    logging.info(f"🟢 Modbus TCP esclavo en {host}:{port}")
    server_task = asyncio.create_task(StartAsyncTcpServer(
        context, address=(host, port), framer="socket", trace_pdu=trace_pdu
    ))

    # ejemplo: tarea opcional que actualiza un registro para pruebas
    async def ticker():
        i = 0
        while not stop.is_set():
            context[0x00].setValues(3, 0, [i])   # FC03/HR addr 0 := i
            i = (i + 1) & 0xFFFF
            await asyncio.sleep(0.1)
    tick_task = asyncio.create_task(ticker())

    await stop.wait()
    for t in (tick_task, server_task):
        t.cancel()
    logging.info("🛑 Server stopped")

if __name__ == "__main__":
    try: 
        asyncio.run(main())
    except KeyboardInterrupt:
        pass

import asyncio
import logging
import time
from datetime import datetime
from pymodbus.server import StartAsyncTcpServer
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSlaveContext, ModbusServerContext
from pymodbus.pdu import ModbusPDU


def timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

logging.basicConfig(level=logging.INFO)

def trace_pdu_hook(is_receive: bool, pdu: ModbusPDU) -> ModbusPDU:
    t = timestamp()
    direction = "RX" if is_receive else "TX"
    logging.info(f"[{t}] {direction}: Func={pdu.function_code} Data={getattr(pdu, 'registers', getattr(pdu, 'bits', None))}")
    return pdu 

async def run_server(context: ModbusServerContext, port: int = 5020):
    await StartAsyncTcpServer(
        context,
        address=("0.0.0.0", port),
        framer="socket",
        trace_pdu=trace_pdu_hook
    )


if __name__ == "__main__":
    try:
        store = ModbusSlaveContext(
            di=ModbusSequentialDataBlock(0, [0]*100),
            co=ModbusSequentialDataBlock(0, [0]*100),
            hr=ModbusSequentialDataBlock(0, [0]*1000),
            ir=ModbusSequentialDataBlock(0, [0]*100),
        )
        context = ModbusServerContext(slaves=store, single=True)
        store = ModbusSlaveContext(
            di=ModbusSequentialDataBlock(0, [0]*100),
            co=ModbusSequentialDataBlock(0, [0]*100),
            hr=ModbusSequentialDataBlock(0, [0]*1000),
            ir=ModbusSequentialDataBlock(0, [0]*100),
        )
        context = ModbusServerContext(slaves=store, single=True)
        logging.info("🟢 Servidor Modbus TCP activo en 0.0.0.0:5020")
        asyncio.run(run_server(context))
    except Exception as e:
        logging.error(f"Error: {e}")
    finally:
        logging.info("🛑 Server stopped ...")

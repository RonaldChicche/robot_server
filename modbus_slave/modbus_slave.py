import os, asyncio, logging, signal
from datetime import datetime
from typing import Dict
from pymodbus.server import StartAsyncTcpServer
from pymodbus.datastore import (
    ModbusSequentialDataBlock, ModbusSlaveContext, ModbusServerContext
)

APP_LOGGER = logging.getLogger("modbus_server")
ts = lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

def configure_logging() -> bool:
    lvl = getattr(logging, os.getenv("LOG_LEVEL", "ERROR").upper(), logging.ERROR)
    logging.basicConfig(level=lvl, format="%(asctime)s %(levelname)s [%(name)s] %(message)s")
    if lvl >= logging.ERROR:
        logging.getLogger("pymodbus").setLevel(logging.ERROR)
        logging.getLogger("asyncio").setLevel(logging.ERROR)
    APP_LOGGER.setLevel(min(logging.INFO, lvl))
    return os.getenv("LOG_DATA", "0").strip().lower() in ("1", "true", "yes")

def parse_inits(s: str) -> Dict[int, int]:
    out = {}
    for token in s.split(","):
        token = token.strip()
        if not token: continue
        k, v = token.split("=", 1)
        k, v = int(k), int(v)
        if not (0 <= v <= 0xFFFF): raise ValueError("HR value must be 0..65535")
        out[k] = v
    return out

def build_context() -> ModbusServerContext:
    di, co, ir, hr = (
        [0]*int(os.getenv("DI_SIZE", "100")),
        [0]*int(os.getenv("CO_SIZE", "100")),
        [0]*int(os.getenv("IR_SIZE", "100")),
        [0]*int(os.getenv("HR_SIZE", "1000")),
    )
    init = os.getenv("HR_INIT", "").strip()
    if init:
        m = parse_inits(init)
        for i, v in m.items():
            if i < 0 or i >= len(hr): raise IndexError(f"HR index {i} out of range")
            hr[i] = v
    return ModbusServerContext(
        slaves=ModbusSlaveContext(
            di=ModbusSequentialDataBlock(0, di),
            co=ModbusSequentialDataBlock(0, co),
            hr=ModbusSequentialDataBlock(0, hr),
            ir=ModbusSequentialDataBlock(0, ir),
        ),
        single=True,
    )

def make_trace(enabled: bool):
    if not enabled:
        return None
    def _trace(is_rx, pdu):
        data = getattr(pdu, "registers", getattr(pdu, "bits", None))
        preview = list(data)[:32] + (["…"] if data and len(data) > 32 else []) if data else "-"
        logging.info(f"[{ts()}] {'RX' if is_rx else 'TX'} fc={getattr(pdu,'function_code','?')} data={preview}")
        return pdu
    return _trace

async def main():
    log_data = configure_logging()
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "5020"))
    ctx = build_context()
    trace = make_trace(log_data)

    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (getattr(signal, "SIGINT", None), getattr(signal, "SIGTERM", None)):
        if sig:
            try: loop.add_signal_handler(sig, stop.set)
            except NotImplementedError: pass

    APP_LOGGER.info(f"🟢 Modbus TCP estático en {host}:{port}")
    server_task = asyncio.create_task(StartAsyncTcpServer(ctx, address=(host, port), **({"trace_pdu": trace} if trace else {})))

    await stop.wait()
    server_task.cancel()
    try: await server_task
    except asyncio.CancelledError: pass
    APP_LOGGER.info("🛑 Server detenido limpiamente")

if __name__ == "__main__":
    try: asyncio.run(main())
    except KeyboardInterrupt: pass

import asyncio
import json
import os
import logging

from pymodbus.datastore import (
    ModbusSequentialDataBlock,
    ModbusSlaveContext,
    ModbusServerContext,
)
from pymodbus.server import StartAsyncTcpServer

MODBUS_ADDRESS = 254

# Configure logging
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.INFO)

# Load config file
script_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(script_dir, "scada_config", "config.json")

with open(config_path, "r") as f:
    config = json.load(f)

# Extract data points
data_points = config["data_points"]
binary_inputs = data_points["binary_inputs"]
analog_inputs = data_points["analog_inputs"]
counters = data_points["counters"]
binary_outputs = data_points["binary_outputs"]
analog_outputs = data_points["analog_outputs"]

# Modbus Data Blocks
store = ModbusSlaveContext(
    di=ModbusSequentialDataBlock(0, binary_inputs),          # Discrete Inputs (1xxxx)
    co=ModbusSequentialDataBlock(0, binary_outputs),         # Coils (0xxxx)
    hr=ModbusSequentialDataBlock(0, analog_outputs),         # Holding Registers (4xxxx)
    ir=ModbusSequentialDataBlock(0, analog_inputs + counters), # Input Registers (3xxxx)
    unit=MODBUS_ADDRESS
)

context = ModbusServerContext(slaves=store, single=True)

ip = config["ip"]
port = config["port"]


async def run_modbus_server():
    print(f"Starting Modbus TCP Server on {ip}:{port}")
    await StartAsyncTcpServer(context=context, address=(ip, port))


if __name__ == "__main__":
    asyncio.run(run_modbus_server())

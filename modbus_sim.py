import asyncio
import json
import os

from pymodbus.datastore import (
    ModbusSequentialDataBlock,
    ModbusSlaveContext,
    ModbusServerContext,
)
from pymodbus.server import ModbusTcpServer
from pymodbus import pymodbus_apply_logging_config


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
    ir=ModbusSequentialDataBlock(0, analog_inputs + counters) # Input Registers (3xxxx)
)

context = ModbusServerContext(slaves=store, single=True)

ip = config["ip"]
port = config["port"]


async def run_modbus_server():
    pymodbus_apply_logging_config()
    print(f"Starting Modbus TCP Server on {ip}:{port}")
    server = ModbusTcpServer(context=context, address=(ip, port))
    await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(run_modbus_server())

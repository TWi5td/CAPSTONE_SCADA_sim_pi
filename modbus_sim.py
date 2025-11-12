import asyncio
import json
import os

from pymodbus.datastore.context import ModbusServerContext
from pymodbus.datastore import ModbusSlaveContext, ModbusSequentialDataBlock

from pymodbus.server import ModbusTcpServer
from pymodbus import pymodbus_apply_logging_config


# Load config file
script_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(script_dir, "scada_config", "config.json")

# Fallback to current directory if scada_config doesn't exist
if not os.path.exists(config_path):
    config_path = "config.json"

with open(config_path, "r") as f:
    config = json.load(f)

# Extract data points
data_points = config["data_points"]
binary_inputs = data_points["binary_inputs"]
analog_inputs = data_points["analog_inputs"]
counters = data_points["counters"]
binary_outputs = data_points["binary_outputs"]
analog_outputs = data_points["analog_outputs"]

# Modbus Data Blocks for Unit ID 254 (RTAC requirement)
slave_context = ModbusSlaveContext(
    di=ModbusSequentialDataBlock(0, binary_inputs),          # Discrete Inputs (1xxxx)
    co=ModbusSequentialDataBlock(0, binary_outputs),         # Coils (0xxxx)
    hr=ModbusSequentialDataBlock(0, analog_outputs),         # Holding Registers (4xxxx)
    ir=ModbusSequentialDataBlock(0, analog_inputs + counters) # Input Registers (3xxxx)
)

# Create context with Unit ID 254 for RTAC
# The RTAC will poll this specific unit ID
slaves = {254: slave_context}  # Unit ID 254 as required by RTAC
context = ModbusServerContext(slaves=slaves, single=False)

ip = config["ip"]
port = config["port"]


async def run_modbus_server():
    pymodbus_apply_logging_config()
    print(f"Starting Modbus TCP Server on {ip}:{port}")
    print(f"Configured for RTAC with Unit ID: 254")
    print(f"Data Points Available:")
    print(f"  - Discrete Inputs (addresses 0-{len(binary_inputs)-1}): {binary_inputs}")
    print(f"  - Coils (addresses 0-{len(binary_outputs)-1}): {binary_outputs}")
    print(f"  - Input Registers (addresses 0-{len(analog_inputs + counters)-1}): {analog_inputs + counters}")
    print(f"  - Holding Registers (addresses 0-{len(analog_outputs)-1}): {analog_outputs}")
    
    server = ModbusTcpServer(context=context, address=(ip, port))
    await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(run_modbus_server())

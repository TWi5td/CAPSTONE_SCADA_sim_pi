from pymodbus.server import StartTcpServer
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSlaveContext, ModbusServerContext
import json
import os

# Load config
script_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(script_dir, 'scada_config', 'config.json')
with open(config_path, 'r') as f:
    config = json.load(f)

# Extract data points
data_points = config["data_points"]
binary_inputs = data_points["binary_inputs"]
analog_inputs = data_points["analog_inputs"]
counters = data_points["counters"]
binary_outputs = data_points["binary_outputs"]
analog_outputs = data_points["analog_outputs"]

# Set up Modbus datastore
store = ModbusSlaveContext(
    di=ModbusSequentialDataBlock(0, binary_inputs),  # Discrete Inputs
    co=ModbusSequentialDataBlock(0, binary_outputs),  # Coils
    hr=ModbusSequentialDataBlock(0, analog_outputs),  # Holding Registers
    ir=ModbusSequentialDataBlock(0, analog_inputs + counters)  # Input Registers (combine analogs and counters)
)
context = ModbusServerContext(slaves=store, single=True)

# Start Modbus TCP server
ip = config["ip"]
port = config["port"]
print("Input Registers:", context[0].getValues(4, 0, count=3))
StartTcpServer(context=context, address=(ip, port))

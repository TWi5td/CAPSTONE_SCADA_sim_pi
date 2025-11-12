"""
IED Simulator for SEL 3530 RTAC
Simulates a Modbus TCP server that the RTAC can poll
"""

from pymodbus.server.sync import StartTcpServer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSlaveContext, ModbusServerContext
from flask import Flask, render_template, request, jsonify
from threading import Thread
import logging

# Configuration from RTAC settings
MODBUS_ADDRESS = 254
SERVER_IP = "0.0.0.0"
SERVER_PORT = 5002

# Flask app for web interface
app = Flask(__name__)

# Global datastore reference
server_context = None

class IEDSimulator:
    def __init__(self):
        # Initialize data blocks based on RTAC configuration
        # Coils (0x): Read/Write - Digital Outputs
        self.coils = ModbusSequentialDataBlock(0, [0] * 100)
        
        # Discrete Inputs (1x): Read Only - Digital Inputs
        self.discrete_inputs = ModbusSequentialDataBlock(0, [0, 0] + [0] * 98)
        
        # Holding Registers (4x): Read/Write - Analog Outputs
        self.holding_registers = ModbusSequentialDataBlock(0, [0] * 100)
        
        # Input Registers (3x): Read Only - Analog Inputs
        # Initialize with default values from your config
        input_reg_defaults = [100, 200, 0] + [0] * 97  # SIM_AI_00=100, SIM_AI_01=200, IREG_00002=0
        self.input_registers = ModbusSequentialDataBlock(0, input_reg_defaults)
        
        # Create slave context
        self.slave_context = ModbusSlaveContext(
            di=self.discrete_inputs,
            co=self.coils,
            hr=self.holding_registers,
            ir=self.input_registers
        )
        
        # Create server context
        self.server_context = ModbusServerContext(
            slaves={MODBUS_ADDRESS: self.slave_context},
            single=False
        )

    def get_coil(self, address):
        """Read coil value"""
        values = self.slave_context.getValues(1, address, 1)
        return values[0]
    
    def set_coil(self, address, value):
        """Write coil value"""
        self.slave_context.setValues(1, address, [value])
    
    def get_discrete_input(self, address):
        """Read discrete input value"""
        values = self.slave_context.getValues(2, address, 1)
        return values[0]
    
    def set_discrete_input(self, address, value):
        """Write discrete input value"""
        self.slave_context.setValues(2, address, [value])
    
    def get_holding_register(self, address):
        """Read holding register value"""
        values = self.slave_context.getValues(3, address, 1)
        return values[0]
    
    def set_holding_register(self, address, value):
        """Write holding register value"""
        # Handle signed 16-bit values
        if value < 0:
            value = 0xFFFF + value + 1
        self.slave_context.setValues(3, address, [value])
    
    def get_input_register(self, address):
        """Read input register value"""
        values = self.slave_context.getValues(4, address, 1)
        return values[0]
    
    def set_input_register(self, address, value):
        """Write input register value"""
        # Handle signed 16-bit values
        if value < 0:
            value = 0xFFFF + value + 1
        self.slave_context.setValues(4, address, [value])

# Initialize simulator
simulator = IEDSimulator()
server_context = simulator.server_context

# Flask Web Interface
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    """Get current status of all registers"""
    return jsonify({
        'coils': {
            'COIL_00000': simulator.get_coil(0)
        },
        'discrete_inputs': {
            'DI_00000': simulator.get_discrete_input(0),
            'DI_00001': simulator.get_discrete_input(1)
        },
        'holding_registers': {
            'SIM_AO_00': simulator.get_holding_register(0)
        },
        'input_registers': {
            'SIM_AI_00': simulator.get_input_register(0),
            'SIM_AI_01': simulator.get_input_register(1),
            'IREG_00002': simulator.get_input_register(2)
        }
    })

@app.route('/api/set_coil', methods=['POST'])
def set_coil():
    """Set coil value"""
    data = request.json
    address = data.get('address', 0)
    value = data.get('value', 0)
    simulator.set_coil(address, value)
    return jsonify({'success': True, 'address': address, 'value': value})

@app.route('/api/set_discrete_input', methods=['POST'])
def set_discrete_input():
    """Set discrete input value"""
    data = request.json
    address = data.get('address', 0)
    value = data.get('value', 0)
    simulator.set_discrete_input(address, value)
    return jsonify({'success': True, 'address': address, 'value': value})

@app.route('/api/set_holding_register', methods=['POST'])
def set_holding_register():
    """Set holding register value"""
    data = request.json
    address = data.get('address', 0)
    value = data.get('value', 0)
    simulator.set_holding_register(address, value)
    return jsonify({'success': True, 'address': address, 'value': value})

@app.route('/api/set_input_register', methods=['POST'])
def set_input_register():
    """Set input register value"""
    data = request.json
    address = data.get('address', 0)
    value = data.get('value', 0)
    simulator.set_input_register(address, value)
    return jsonify({'success': True, 'address': address, 'value': value})

def run_modbus_server():
    """Run Modbus TCP server"""
    logging.basicConfig()
    log = logging.getLogger()
    log.setLevel(logging.INFO)
    
    # Device identification
    identity = ModbusDeviceIdentification()
    identity.VendorName = 'IED Simulator'
    identity.ProductCode = 'IED-SIM'
    identity.VendorUrl = 'http://localhost:5000'
    identity.ProductName = 'IED Simulator for SEL RTAC'
    identity.ModelName = 'Raspberry Pi Simulator'
    identity.MajorMinorRevision = '1.0.0'
    
    print(f"Starting Modbus TCP Server on {SERVER_IP}:{SERVER_PORT}")
    print(f"Modbus Address: {MODBUS_ADDRESS}")
    
    StartTcpServer(
        server_context,
        identity=identity,
        address=(SERVER_IP, SERVER_PORT)
    )

def run_flask_app():
    """Run Flask web server"""
    print("Starting Flask Web Interface on http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

if __name__ == '__main__':
    # Start Modbus server in a separate thread
    modbus_thread = Thread(target=run_modbus_server, daemon=True)
    modbus_thread.start()
    
    # Start Flask web interface
    run_flask_app()

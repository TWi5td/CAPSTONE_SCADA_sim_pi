"""
Enhanced SCADA IED Simulator with Advanced HMI
Real-time monitoring, connection tracking, and comprehensive web interface
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
from pymodbus.server import StartTcpServer
from pymodbus import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusDeviceContext, ModbusServerContext
from threading import Thread, Lock
from datetime import datetime
import logging
import json
import os
import time
import asyncio

# Configuration
MODBUS_ADDRESS = 254
SERVER_IP = "0.0.0.0"
SERVER_PORT = 5002
FLASK_PORT = 5000

app = Flask(__name__)

# Global state management
class SystemState:
    def __init__(self):
        self.lock = Lock()
        self.connections = []
        self.last_request_time = None
        self.request_count = 0
        self.server_start_time = datetime.now()
        self.modbus_running = False
        self.flask_running = False
        
    def add_connection(self, remote_addr):
        with self.lock:
            self.connections.append({
                'address': remote_addr,
                'timestamp': datetime.now().isoformat(),
                'request_count': 1
            })
            self.request_count += 1
            self.last_request_time = datetime.now()
    
    def get_stats(self):
        with self.lock:
            uptime = (datetime.now() - self.server_start_time).total_seconds()
            return {
                'uptime_seconds': uptime,
                'total_requests': self.request_count,
                'recent_connections': self.connections[-10:],
                'last_request': self.last_request_time.isoformat() if self.last_request_time else None,
                'modbus_running': self.modbus_running,
                'flask_running': self.flask_running
            }

state = SystemState()

class IEDSimulator:
    def __init__(self):
        # Initialize data blocks
        self.coils = ModbusSequentialDataBlock(0, [0] * 100)
        self.discrete_inputs = ModbusSequentialDataBlock(0, [0] * 100)
        self.holding_registers = ModbusSequentialDataBlock(0, [0] * 100)
        self.input_registers = ModbusSequentialDataBlock(0, [100, 200, 0] + [0] * 97)
        
        # Custom variables storage
        self.custom_variables = {}
        self.load_custom_variables()
        
        # Create device context
        self.device_context = ModbusDeviceContext(
            di=self.discrete_inputs,
            co=self.coils,
            hr=self.holding_registers,
            ir=self.input_registers
        )
        
        self.server_context = ModbusServerContext(
            devices={MODBUS_ADDRESS: self.device_context},
            single=False
        )
        
        # Change tracking
        self.last_changes = []
        self.lock = Lock()
    
    def load_custom_variables(self):
        """Load custom variables from config file"""
        try:
            if os.path.exists('custom_variables.json'):
                with open('custom_variables.json', 'r') as f:
                    self.custom_variables = json.load(f)
        except Exception as e:
            print(f"Error loading custom variables: {e}")
            self.custom_variables = {}
    
    def save_custom_variables(self):
        """Save custom variables to config file"""
        try:
            with open('custom_variables.json', 'w') as f:
                json.dump(self.custom_variables, f, indent=2)
        except Exception as e:
            print(f"Error saving custom variables: {e}")
    
    def track_change(self, register_type, address, old_value, new_value):
        """Track changes to registers"""
        with self.lock:
            change = {
                'timestamp': datetime.now().isoformat(),
                'type': register_type,
                'address': address,
                'old_value': old_value,
                'new_value': new_value
            }
            self.last_changes.append(change)
            if len(self.last_changes) > 50:
                self.last_changes.pop(0)
    
    def get_coil(self, address):
        values = self.coils.getValues(address, 1)
        return values[0]
    
    def set_coil(self, address, value):
        old_value = self.get_coil(address)
        self.coils.setValues(address, [value])
        self.track_change('coil', address, old_value, value)
    
    def get_discrete_input(self, address):
        values = self.discrete_inputs.getValues(address, 1)
        return values[0]
    
    def set_discrete_input(self, address, value):
        old_value = self.get_discrete_input(address)
        self.discrete_inputs.setValues(address, [value])
        self.track_change('discrete_input', address, old_value, value)
    
    def get_holding_register(self, address):
        values = self.holding_registers.getValues(address, 1)
        return values[0]
    
    def set_holding_register(self, address, value):
        old_value = self.get_holding_register(address)
        if value < 0:
            value = 0xFFFF + value + 1
        self.holding_registers.setValues(address, [value])
        self.track_change('holding_register', address, old_value, value)
    
    def get_input_register(self, address):
        values = self.input_registers.getValues(address, 1)
        return values[0]
    
    def set_input_register(self, address, value):
        old_value = self.get_input_register(address)
        if value < 0:
            value = 0xFFFF + value + 1
        self.input_registers.setValues(address, [value])
        self.track_change('input_register', address, old_value, value)
    
    def get_recent_changes(self):
        with self.lock:
            return self.last_changes[-20:]

# Initialize simulator
simulator = IEDSimulator()
server_context = simulator.server_context

# Flask Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/simulation')
def simulation_page():
    return render_template('simulation.html')

@app.route('/variables')
def variables_page():
    return render_template('variables.html')

@app.route('/api/system_status')
def system_status():
    """Get comprehensive system status"""
    stats = state.get_stats()
    return jsonify({
        'system': stats,
        'modbus': {
            'address': MODBUS_ADDRESS,
            'ip': SERVER_IP,
            'port': SERVER_PORT,
            'protocol': 'Modbus TCP'
        },
        'recent_changes': simulator.get_recent_changes()
    })

@app.route('/api/status')
def get_status():
    """Get current status of all registers"""
    state.add_connection(request.remote_addr)
    
    return jsonify({
        'coils': {f'COIL_{i:05d}': simulator.get_coil(i) for i in range(10)},
        'discrete_inputs': {f'DI_{i:05d}': simulator.get_discrete_input(i) for i in range(10)},
        'holding_registers': {f'HR_{i:05d}': simulator.get_holding_register(i) for i in range(10)},
        'input_registers': {f'IR_{i:05d}': simulator.get_input_register(i) for i in range(10)}
    })

@app.route('/api/get_register', methods=['POST'])
def get_register():
    """Get specific register value"""
    data = request.json
    reg_type = data.get('type')
    address = data.get('address', 0)
    
    value = None
    if reg_type == 'coil':
        value = simulator.get_coil(address)
    elif reg_type == 'discrete_input':
        value = simulator.get_discrete_input(address)
    elif reg_type == 'holding_register':
        value = simulator.get_holding_register(address)
    elif reg_type == 'input_register':
        value = simulator.get_input_register(address)
    
    return jsonify({'success': True, 'value': value})

@app.route('/api/set_coil', methods=['POST'])
def set_coil():
    data = request.json
    address = data.get('address', 0)
    value = data.get('value', 0)
    simulator.set_coil(address, value)
    return jsonify({'success': True, 'address': address, 'value': value})

@app.route('/api/set_discrete_input', methods=['POST'])
def set_discrete_input():
    data = request.json
    address = data.get('address', 0)
    value = data.get('value', 0)
    simulator.set_discrete_input(address, value)
    return jsonify({'success': True, 'address': address, 'value': value})

@app.route('/api/set_holding_register', methods=['POST'])
def set_holding_register():
    data = request.json
    address = data.get('address', 0)
    value = data.get('value', 0)
    simulator.set_holding_register(address, value)
    return jsonify({'success': True, 'address': address, 'value': value})

@app.route('/api/set_input_register', methods=['POST'])
def set_input_register():
    data = request.json
    address = data.get('address', 0)
    value = data.get('value', 0)
    simulator.set_input_register(address, value)
    return jsonify({'success': True, 'address': address, 'value': value})

@app.route('/api/custom_variables', methods=['GET'])
def get_custom_variables():
    """Get all custom variables"""
    return jsonify(simulator.custom_variables)

@app.route('/api/custom_variables', methods=['POST'])
def save_custom_variable():
    """Save a custom variable"""
    data = request.json
    var_name = data.get('name')
    var_config = data.get('config')
    
    simulator.custom_variables[var_name] = var_config
    simulator.save_custom_variables()
    
    return jsonify({'success': True, 'message': f'Variable {var_name} saved'})

@app.route('/api/custom_variables/<var_name>', methods=['DELETE'])
def delete_custom_variable(var_name):
    """Delete a custom variable"""
    if var_name in simulator.custom_variables:
        del simulator.custom_variables[var_name]
        simulator.save_custom_variables()
        return jsonify({'success': True, 'message': f'Variable {var_name} deleted'})
    return jsonify({'success': False, 'message': 'Variable not found'}), 404

@app.route('/api/export_config', methods=['GET'])
def export_config():
    """Export current configuration"""
    config = {
        'timestamp': datetime.now().isoformat(),
        'modbus_config': {
            'address': MODBUS_ADDRESS,
            'ip': SERVER_IP,
            'port': SERVER_PORT
        },
        'custom_variables': simulator.custom_variables,
        'current_values': {
            'coils': {i: simulator.get_coil(i) for i in range(100)},
            'discrete_inputs': {i: simulator.get_discrete_input(i) for i in range(100)},
            'holding_registers': {i: simulator.get_holding_register(i) for i in range(100)},
            'input_registers': {i: simulator.get_input_register(i) for i in range(100)}
        }
    }
    return jsonify(config)

@app.route('/api/import_config', methods=['POST'])
def import_config():
    """Import configuration"""
    try:
        config = request.json
        
        # Import custom variables
        if 'custom_variables' in config:
            simulator.custom_variables = config['custom_variables']
            simulator.save_custom_variables()
        
        # Import register values if present
        if 'current_values' in config:
            values = config['current_values']
            
            # Import coils
            if 'coils' in values:
                for addr, val in values['coils'].items():
                    simulator.set_coil(int(addr), val)
            
            # Import discrete inputs
            if 'discrete_inputs' in values:
                for addr, val in values['discrete_inputs'].items():
                    simulator.set_discrete_input(int(addr), val)
            
            # Import holding registers
            if 'holding_registers' in values:
                for addr, val in values['holding_registers'].items():
                    simulator.set_holding_register(int(addr), val)
            
            # Import input registers
            if 'input_registers' in values:
                for addr, val in values['input_registers'].items():
                    simulator.set_input_register(int(addr), val)
        
        return jsonify({'success': True, 'message': 'Configuration imported successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

def run_modbus_server():
    """Run Modbus TCP server"""
    logging.basicConfig()
    log = logging.getLogger()
    log.setLevel(logging.INFO)
    
    identity = ModbusDeviceIdentification()
    identity.VendorName = 'IED Simulator'
    identity.ProductCode = 'IED-SIM'
    identity.VendorUrl = 'http://localhost:5000'
    identity.ProductName = 'IED Simulator for SEL RTAC'
    identity.ModelName = 'Raspberry Pi Simulator'
    identity.MajorMinorRevision = '2.0.0'
    
    state.modbus_running = True
    print(f"[MODBUS] Starting Modbus TCP Server on {SERVER_IP}:{SERVER_PORT}")
    print(f"[MODBUS] Modbus Address: {MODBUS_ADDRESS}")
    print(f"[MODBUS] Waiting for connections...")
    
    # Run the async server in a new event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(
        StartTcpServer(
            context=server_context,
            identity=identity,
            address=(SERVER_IP, SERVER_PORT)
        )
    )

def run_flask_app():
    """Run Flask web server"""
    state.flask_running = True
    print(f"[FLASK] Starting Web Interface on http://0.0.0.0:{FLASK_PORT}")
    print(f"[FLASK] Access the interface at http://<your-pi-ip>:{FLASK_PORT}")
    app.run(host='0.0.0.0', port=FLASK_PORT, debug=False, use_reloader=False)

def print_startup_banner():
    """Print startup information"""
    print("=" * 70)
    print("SCADA IED SIMULATOR - Enhanced Edition")
    print("=" * 70)
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Modbus TCP: {SERVER_IP}:{SERVER_PORT} (Unit ID: {MODBUS_ADDRESS})")
    print(f"Web Interface: http://0.0.0.0:{FLASK_PORT}")
    print("=" * 70)
    print()

if __name__ == '__main__':
    print_startup_banner()
    
    # Start Modbus server in a separate thread
    modbus_thread = Thread(target=run_modbus_server, daemon=True)
    modbus_thread.start()
    
    # Small delay to let Modbus server start
    time.sleep(1)
    
    # Start Flask web interface
    run_flask_app()
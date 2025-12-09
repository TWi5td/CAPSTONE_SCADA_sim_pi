"""
Enhanced SCADA IED Simulator with Advanced HMI
Power Industry Edition - Comprehensive Modbus TCP Server
Real-time monitoring, connection tracking, and professional web interface
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
import math
import random

# Configuration
MODBUS_ADDRESS = 254
SERVER_IP = "0.0.0.0"
SERVER_PORT = 5002
FLASK_PORT = 5000

# Expanded register counts for power industry applications
REGISTER_COUNT = 500  # Expanded from 100 to accommodate all power variables

app = Flask(__name__)

# =============================================================================
# POWER INDUSTRY REGISTER MAPPING
# =============================================================================
# This defines the standard Modbus register layout for power industry IEDs

POWER_REGISTER_MAP = {
    # =========================================================================
    # INPUT REGISTERS (Read-Only Analog Values) - Function Code 04
    # =========================================================================
    'input_registers': {
        # --- Three-Phase Voltage Measurements (0-19) ---
        0: {'name': 'V_L1_N', 'description': 'Phase L1-N Voltage', 'unit': 'V', 'scale': 0.1, 'default': 1200},
        1: {'name': 'V_L2_N', 'description': 'Phase L2-N Voltage', 'unit': 'V', 'scale': 0.1, 'default': 1200},
        2: {'name': 'V_L3_N', 'description': 'Phase L3-N Voltage', 'unit': 'V', 'scale': 0.1, 'default': 1200},
        3: {'name': 'V_L1_L2', 'description': 'Phase L1-L2 Voltage', 'unit': 'V', 'scale': 0.1, 'default': 2078},
        4: {'name': 'V_L2_L3', 'description': 'Phase L2-L3 Voltage', 'unit': 'V', 'scale': 0.1, 'default': 2078},
        5: {'name': 'V_L3_L1', 'description': 'Phase L3-L1 Voltage', 'unit': 'V', 'scale': 0.1, 'default': 2078},
        6: {'name': 'V_AVG_LN', 'description': 'Average L-N Voltage', 'unit': 'V', 'scale': 0.1, 'default': 1200},
        7: {'name': 'V_AVG_LL', 'description': 'Average L-L Voltage', 'unit': 'V', 'scale': 0.1, 'default': 2078},
        8: {'name': 'V_UNBAL', 'description': 'Voltage Unbalance', 'unit': '%', 'scale': 0.01, 'default': 50},
        9: {'name': 'V_ZERO_SEQ', 'description': 'Zero Sequence Voltage', 'unit': 'V', 'scale': 0.1, 'default': 0},
        
        # --- Three-Phase Current Measurements (20-39) ---
        20: {'name': 'I_L1', 'description': 'Phase L1 Current', 'unit': 'A', 'scale': 0.01, 'default': 10000},
        21: {'name': 'I_L2', 'description': 'Phase L2 Current', 'unit': 'A', 'scale': 0.01, 'default': 10000},
        22: {'name': 'I_L3', 'description': 'Phase L3 Current', 'unit': 'A', 'scale': 0.01, 'default': 10000},
        23: {'name': 'I_N', 'description': 'Neutral Current', 'unit': 'A', 'scale': 0.01, 'default': 100},
        24: {'name': 'I_G', 'description': 'Ground Current', 'unit': 'A', 'scale': 0.01, 'default': 0},
        25: {'name': 'I_AVG', 'description': 'Average Phase Current', 'unit': 'A', 'scale': 0.01, 'default': 10000},
        26: {'name': 'I_UNBAL', 'description': 'Current Unbalance', 'unit': '%', 'scale': 0.01, 'default': 50},
        27: {'name': 'I_ZERO_SEQ', 'description': 'Zero Sequence Current', 'unit': 'A', 'scale': 0.01, 'default': 0},
        28: {'name': 'I_POS_SEQ', 'description': 'Positive Sequence Current', 'unit': 'A', 'scale': 0.01, 'default': 10000},
        29: {'name': 'I_NEG_SEQ', 'description': 'Negative Sequence Current', 'unit': 'A', 'scale': 0.01, 'default': 0},
        
        # --- Power Measurements (40-69) ---
        40: {'name': 'P_L1', 'description': 'Phase L1 Active Power', 'unit': 'kW', 'scale': 0.1, 'default': 400},
        41: {'name': 'P_L2', 'description': 'Phase L2 Active Power', 'unit': 'kW', 'scale': 0.1, 'default': 400},
        42: {'name': 'P_L3', 'description': 'Phase L3 Active Power', 'unit': 'kW', 'scale': 0.1, 'default': 400},
        43: {'name': 'P_TOTAL', 'description': 'Total Active Power', 'unit': 'kW', 'scale': 0.1, 'default': 1200},
        44: {'name': 'Q_L1', 'description': 'Phase L1 Reactive Power', 'unit': 'kVAR', 'scale': 0.1, 'default': 100},
        45: {'name': 'Q_L2', 'description': 'Phase L2 Reactive Power', 'unit': 'kVAR', 'scale': 0.1, 'default': 100},
        46: {'name': 'Q_L3', 'description': 'Phase L3 Reactive Power', 'unit': 'kVAR', 'scale': 0.1, 'default': 100},
        47: {'name': 'Q_TOTAL', 'description': 'Total Reactive Power', 'unit': 'kVAR', 'scale': 0.1, 'default': 300},
        48: {'name': 'S_L1', 'description': 'Phase L1 Apparent Power', 'unit': 'kVA', 'scale': 0.1, 'default': 412},
        49: {'name': 'S_L2', 'description': 'Phase L2 Apparent Power', 'unit': 'kVA', 'scale': 0.1, 'default': 412},
        50: {'name': 'S_L3', 'description': 'Phase L3 Apparent Power', 'unit': 'kVA', 'scale': 0.1, 'default': 412},
        51: {'name': 'S_TOTAL', 'description': 'Total Apparent Power', 'unit': 'kVA', 'scale': 0.1, 'default': 1237},
        52: {'name': 'PF_L1', 'description': 'Phase L1 Power Factor', 'unit': '', 'scale': 0.001, 'default': 970},
        53: {'name': 'PF_L2', 'description': 'Phase L2 Power Factor', 'unit': '', 'scale': 0.001, 'default': 970},
        54: {'name': 'PF_L3', 'description': 'Phase L3 Power Factor', 'unit': '', 'scale': 0.001, 'default': 970},
        55: {'name': 'PF_TOTAL', 'description': 'Total Power Factor', 'unit': '', 'scale': 0.001, 'default': 970},
        
        # --- Frequency Measurements (70-79) ---
        70: {'name': 'FREQ', 'description': 'System Frequency', 'unit': 'Hz', 'scale': 0.01, 'default': 6000},
        71: {'name': 'FREQ_DEV', 'description': 'Frequency Deviation', 'unit': 'Hz', 'scale': 0.001, 'default': 0},
        72: {'name': 'ROCOF', 'description': 'Rate of Change of Frequency', 'unit': 'Hz/s', 'scale': 0.001, 'default': 0},
        
        # --- Energy Measurements (80-99) ---
        80: {'name': 'WH_IMP_HI', 'description': 'Import Wh (High Word)', 'unit': 'kWh', 'scale': 1, 'default': 0},
        81: {'name': 'WH_IMP_LO', 'description': 'Import Wh (Low Word)', 'unit': 'kWh', 'scale': 1, 'default': 12500},
        82: {'name': 'WH_EXP_HI', 'description': 'Export Wh (High Word)', 'unit': 'kWh', 'scale': 1, 'default': 0},
        83: {'name': 'WH_EXP_LO', 'description': 'Export Wh (Low Word)', 'unit': 'kWh', 'scale': 1, 'default': 500},
        84: {'name': 'VARH_IMP_HI', 'description': 'Import VARh (High Word)', 'unit': 'kVARh', 'scale': 1, 'default': 0},
        85: {'name': 'VARH_IMP_LO', 'description': 'Import VARh (Low Word)', 'unit': 'kVARh', 'scale': 1, 'default': 3200},
        86: {'name': 'VARH_EXP_HI', 'description': 'Export VARh (High Word)', 'unit': 'kVARh', 'scale': 1, 'default': 0},
        87: {'name': 'VARH_EXP_LO', 'description': 'Export VARh (Low Word)', 'unit': 'kVARh', 'scale': 1, 'default': 100},
        88: {'name': 'VAH_HI', 'description': 'Total VAh (High Word)', 'unit': 'kVAh', 'scale': 1, 'default': 0},
        89: {'name': 'VAH_LO', 'description': 'Total VAh (Low Word)', 'unit': 'kVAh', 'scale': 1, 'default': 13000},
        
        # --- Transformer Measurements (100-129) ---
        100: {'name': 'XFMR_OIL_TEMP', 'description': 'Transformer Oil Temperature', 'unit': '°C', 'scale': 0.1, 'default': 450},
        101: {'name': 'XFMR_WNDG_TEMP', 'description': 'Transformer Winding Temperature', 'unit': '°C', 'scale': 0.1, 'default': 550},
        102: {'name': 'XFMR_AMB_TEMP', 'description': 'Ambient Temperature', 'unit': '°C', 'scale': 0.1, 'default': 250},
        103: {'name': 'XFMR_LOAD_PCT', 'description': 'Transformer Load Percent', 'unit': '%', 'scale': 0.1, 'default': 650},
        104: {'name': 'XFMR_OIL_LEVEL', 'description': 'Oil Level', 'unit': '%', 'scale': 0.1, 'default': 950},
        105: {'name': 'XFMR_PRESS', 'description': 'Tank Pressure', 'unit': 'kPa', 'scale': 0.1, 'default': 150},
        106: {'name': 'XFMR_TAP_POS', 'description': 'Tap Changer Position', 'unit': '', 'scale': 1, 'default': 8},
        107: {'name': 'XFMR_FAN_STATUS', 'description': 'Cooling Fan Status', 'unit': '', 'scale': 1, 'default': 1},
        108: {'name': 'XFMR_H2_PPM', 'description': 'Dissolved H2 Gas', 'unit': 'ppm', 'scale': 1, 'default': 25},
        109: {'name': 'XFMR_CH4_PPM', 'description': 'Dissolved CH4 Gas', 'unit': 'ppm', 'scale': 1, 'default': 10},
        110: {'name': 'XFMR_C2H2_PPM', 'description': 'Dissolved C2H2 Gas', 'unit': 'ppm', 'scale': 1, 'default': 2},
        111: {'name': 'XFMR_C2H4_PPM', 'description': 'Dissolved C2H4 Gas', 'unit': 'ppm', 'scale': 1, 'default': 15},
        112: {'name': 'XFMR_CO_PPM', 'description': 'Dissolved CO Gas', 'unit': 'ppm', 'scale': 1, 'default': 200},
        113: {'name': 'XFMR_CO2_PPM', 'description': 'Dissolved CO2 Gas', 'unit': 'ppm', 'scale': 1, 'default': 2500},
        114: {'name': 'XFMR_MOIST_PPM', 'description': 'Oil Moisture Content', 'unit': 'ppm', 'scale': 1, 'default': 15},
        
        # --- Breaker/Switch Measurements (130-149) ---
        130: {'name': 'BKR_OPS_TOTAL', 'description': 'Total Breaker Operations', 'unit': '', 'scale': 1, 'default': 1250},
        131: {'name': 'BKR_FAULT_OPS', 'description': 'Fault Operations Count', 'unit': '', 'scale': 1, 'default': 45},
        132: {'name': 'BKR_CLOSE_TIME', 'description': 'Last Close Time', 'unit': 'ms', 'scale': 0.1, 'default': 650},
        133: {'name': 'BKR_TRIP_TIME', 'description': 'Last Trip Time', 'unit': 'ms', 'scale': 0.1, 'default': 480},
        134: {'name': 'BKR_COIL_I', 'description': 'Trip Coil Current', 'unit': 'A', 'scale': 0.01, 'default': 250},
        135: {'name': 'BKR_SPRING_CHRG', 'description': 'Spring Charge Status', 'unit': '', 'scale': 1, 'default': 1},
        136: {'name': 'BKR_SF6_PRESS', 'description': 'SF6 Gas Pressure', 'unit': 'bar', 'scale': 0.01, 'default': 650},
        137: {'name': 'BKR_CONTACT_WEAR', 'description': 'Contact Wear Index', 'unit': '%', 'scale': 0.1, 'default': 250},
        
        # --- Protection Relay Measurements (150-179) ---
        150: {'name': 'PROT_50_PICKUP', 'description': '50 Element Pickup Level', 'unit': 'A', 'scale': 0.01, 'default': 50000},
        151: {'name': 'PROT_51_PICKUP', 'description': '51 Element Pickup Level', 'unit': 'A', 'scale': 0.01, 'default': 12000},
        152: {'name': 'PROT_51_TD', 'description': '51 Time Dial Setting', 'unit': '', 'scale': 0.01, 'default': 300},
        153: {'name': 'PROT_50N_PICKUP', 'description': '50N Element Pickup', 'unit': 'A', 'scale': 0.01, 'default': 5000},
        154: {'name': 'PROT_51N_PICKUP', 'description': '51N Element Pickup', 'unit': 'A', 'scale': 0.01, 'default': 1200},
        155: {'name': 'PROT_27_PICKUP', 'description': '27 Undervoltage Pickup', 'unit': 'V', 'scale': 0.1, 'default': 900},
        156: {'name': 'PROT_59_PICKUP', 'description': '59 Overvoltage Pickup', 'unit': 'V', 'scale': 0.1, 'default': 1320},
        157: {'name': 'PROT_81U_PICKUP', 'description': '81U Underfrequency Pickup', 'unit': 'Hz', 'scale': 0.01, 'default': 5950},
        158: {'name': 'PROT_81O_PICKUP', 'description': '81O Overfrequency Pickup', 'unit': 'Hz', 'scale': 0.01, 'default': 6050},
        159: {'name': 'PROT_LAST_FAULT_I', 'description': 'Last Fault Current', 'unit': 'A', 'scale': 0.01, 'default': 0},
        160: {'name': 'PROT_LAST_FAULT_T', 'description': 'Last Fault Duration', 'unit': 'ms', 'scale': 1, 'default': 0},
        
        # --- Generator Measurements (180-209) ---
        180: {'name': 'GEN_MW', 'description': 'Generator MW Output', 'unit': 'MW', 'scale': 0.1, 'default': 750},
        181: {'name': 'GEN_MVAR', 'description': 'Generator MVAR Output', 'unit': 'MVAR', 'scale': 0.1, 'default': 200},
        182: {'name': 'GEN_MVA', 'description': 'Generator MVA Output', 'unit': 'MVA', 'scale': 0.1, 'default': 776},
        183: {'name': 'GEN_PF', 'description': 'Generator Power Factor', 'unit': '', 'scale': 0.001, 'default': 966},
        184: {'name': 'GEN_SPEED_RPM', 'description': 'Generator Speed', 'unit': 'RPM', 'scale': 1, 'default': 3600},
        185: {'name': 'GEN_FREQ', 'description': 'Generator Frequency', 'unit': 'Hz', 'scale': 0.01, 'default': 6000},
        186: {'name': 'GEN_EXCITER_V', 'description': 'Exciter Voltage', 'unit': 'V', 'scale': 0.1, 'default': 1250},
        187: {'name': 'GEN_EXCITER_I', 'description': 'Exciter Current', 'unit': 'A', 'scale': 0.1, 'default': 450},
        188: {'name': 'GEN_STATOR_TEMP', 'description': 'Stator Temperature', 'unit': '°C', 'scale': 0.1, 'default': 850},
        189: {'name': 'GEN_ROTOR_TEMP', 'description': 'Rotor Temperature', 'unit': '°C', 'scale': 0.1, 'default': 750},
        190: {'name': 'GEN_BEARING_TEMP', 'description': 'Bearing Temperature', 'unit': '°C', 'scale': 0.1, 'default': 550},
        191: {'name': 'GEN_VIBRATION', 'description': 'Vibration Level', 'unit': 'mm/s', 'scale': 0.01, 'default': 150},
        
        # --- Capacitor Bank Measurements (210-229) ---
        210: {'name': 'CAP_BANK_MVAR', 'description': 'Capacitor Bank MVAR', 'unit': 'MVAR', 'scale': 0.1, 'default': 100},
        211: {'name': 'CAP_BANK_V', 'description': 'Capacitor Bank Voltage', 'unit': 'V', 'scale': 0.1, 'default': 1200},
        212: {'name': 'CAP_BANK_I', 'description': 'Capacitor Bank Current', 'unit': 'A', 'scale': 0.01, 'default': 8500},
        213: {'name': 'CAP_UNBAL_I', 'description': 'Unbalance Current', 'unit': 'A', 'scale': 0.01, 'default': 50},
        214: {'name': 'CAP_STEPS_ON', 'description': 'Steps Energized', 'unit': '', 'scale': 1, 'default': 3},
        215: {'name': 'CAP_OPS_TODAY', 'description': 'Operations Today', 'unit': '', 'scale': 1, 'default': 2},
        
        # --- Battery/DC System Measurements (230-249) ---
        230: {'name': 'DC_BUS_V', 'description': 'DC Bus Voltage', 'unit': 'V', 'scale': 0.1, 'default': 1250},
        231: {'name': 'DC_BATT_V', 'description': 'Battery Voltage', 'unit': 'V', 'scale': 0.1, 'default': 1300},
        232: {'name': 'DC_CHARGER_I', 'description': 'Charger Current', 'unit': 'A', 'scale': 0.1, 'default': 50},
        233: {'name': 'DC_LOAD_I', 'description': 'DC Load Current', 'unit': 'A', 'scale': 0.1, 'default': 25},
        234: {'name': 'DC_BATT_TEMP', 'description': 'Battery Temperature', 'unit': '°C', 'scale': 0.1, 'default': 250},
        235: {'name': 'DC_BATT_SOC', 'description': 'Battery State of Charge', 'unit': '%', 'scale': 0.1, 'default': 950},
        236: {'name': 'DC_GROUND_FAULT', 'description': 'Ground Fault Resistance', 'unit': 'kΩ', 'scale': 0.1, 'default': 5000},
        
        # --- Environmental Measurements (250-269) ---
        250: {'name': 'ENV_TEMP_OUT', 'description': 'Outdoor Temperature', 'unit': '°C', 'scale': 0.1, 'default': 220},
        251: {'name': 'ENV_HUMIDITY', 'description': 'Relative Humidity', 'unit': '%', 'scale': 0.1, 'default': 550},
        252: {'name': 'ENV_WIND_SPEED', 'description': 'Wind Speed', 'unit': 'm/s', 'scale': 0.1, 'default': 35},
        253: {'name': 'ENV_WIND_DIR', 'description': 'Wind Direction', 'unit': '°', 'scale': 1, 'default': 225},
        254: {'name': 'ENV_SOLAR_RAD', 'description': 'Solar Radiation', 'unit': 'W/m²', 'scale': 1, 'default': 650},
        255: {'name': 'ENV_RAIN_RATE', 'description': 'Rain Rate', 'unit': 'mm/h', 'scale': 0.1, 'default': 0},
        
        # --- Line/Cable Measurements (270-289) ---
        270: {'name': 'LINE_LOADING', 'description': 'Line Loading Percent', 'unit': '%', 'scale': 0.1, 'default': 720},
        271: {'name': 'LINE_TEMP', 'description': 'Conductor Temperature', 'unit': '°C', 'scale': 0.1, 'default': 450},
        272: {'name': 'LINE_SAG', 'description': 'Line Sag', 'unit': 'm', 'scale': 0.01, 'default': 850},
        273: {'name': 'LINE_TENSION', 'description': 'Conductor Tension', 'unit': 'kN', 'scale': 0.1, 'default': 250},
        
        # --- Demand Measurements (290-299) ---
        290: {'name': 'DEMAND_KW_MAX', 'description': 'Maximum kW Demand', 'unit': 'kW', 'scale': 0.1, 'default': 1500},
        291: {'name': 'DEMAND_KW_AVG', 'description': 'Average kW Demand', 'unit': 'kW', 'scale': 0.1, 'default': 1100},
        292: {'name': 'DEMAND_KVA_MAX', 'description': 'Maximum kVA Demand', 'unit': 'kVA', 'scale': 0.1, 'default': 1550},
        293: {'name': 'DEMAND_I_MAX', 'description': 'Maximum Current Demand', 'unit': 'A', 'scale': 0.01, 'default': 12500},
    },
    
    # =========================================================================
    # HOLDING REGISTERS (Read/Write Analog Values) - Function Code 03/06/16
    # =========================================================================
    'holding_registers': {
        # --- Setpoints and Control Values (0-49) ---
        0: {'name': 'SP_V_TARGET', 'description': 'Voltage Setpoint', 'unit': 'V', 'scale': 0.1, 'default': 1200},
        1: {'name': 'SP_PF_TARGET', 'description': 'Power Factor Setpoint', 'unit': '', 'scale': 0.001, 'default': 950},
        2: {'name': 'SP_MW_TARGET', 'description': 'MW Setpoint', 'unit': 'MW', 'scale': 0.1, 'default': 750},
        3: {'name': 'SP_MVAR_TARGET', 'description': 'MVAR Setpoint', 'unit': 'MVAR', 'scale': 0.1, 'default': 200},
        4: {'name': 'SP_FREQ_TARGET', 'description': 'Frequency Setpoint', 'unit': 'Hz', 'scale': 0.01, 'default': 6000},
        5: {'name': 'SP_TAP_TARGET', 'description': 'Tap Position Setpoint', 'unit': '', 'scale': 1, 'default': 8},
        
        # --- Protection Settings (50-99) ---
        50: {'name': 'SET_50_PICKUP', 'description': '50 Inst OC Pickup', 'unit': 'A', 'scale': 0.01, 'default': 50000},
        51: {'name': 'SET_51_PICKUP', 'description': '51 TOC Pickup', 'unit': 'A', 'scale': 0.01, 'default': 12000},
        52: {'name': 'SET_51_TD', 'description': '51 Time Dial', 'unit': '', 'scale': 0.01, 'default': 300},
        53: {'name': 'SET_51_CURVE', 'description': '51 Curve Type', 'unit': '', 'scale': 1, 'default': 3},
        54: {'name': 'SET_50N_PICKUP', 'description': '50N Ground Inst Pickup', 'unit': 'A', 'scale': 0.01, 'default': 5000},
        55: {'name': 'SET_51N_PICKUP', 'description': '51N Ground TOC Pickup', 'unit': 'A', 'scale': 0.01, 'default': 1200},
        56: {'name': 'SET_51N_TD', 'description': '51N Time Dial', 'unit': '', 'scale': 0.01, 'default': 200},
        57: {'name': 'SET_27_PICKUP', 'description': '27 UV Pickup', 'unit': 'V', 'scale': 0.1, 'default': 900},
        58: {'name': 'SET_27_DELAY', 'description': '27 UV Delay', 'unit': 's', 'scale': 0.01, 'default': 300},
        59: {'name': 'SET_59_PICKUP', 'description': '59 OV Pickup', 'unit': 'V', 'scale': 0.1, 'default': 1320},
        60: {'name': 'SET_59_DELAY', 'description': '59 OV Delay', 'unit': 's', 'scale': 0.01, 'default': 300},
        61: {'name': 'SET_81U_PICKUP', 'description': '81U UF Pickup', 'unit': 'Hz', 'scale': 0.01, 'default': 5950},
        62: {'name': 'SET_81U_DELAY', 'description': '81U UF Delay', 'unit': 's', 'scale': 0.01, 'default': 100},
        63: {'name': 'SET_81O_PICKUP', 'description': '81O OF Pickup', 'unit': 'Hz', 'scale': 0.01, 'default': 6050},
        64: {'name': 'SET_81O_DELAY', 'description': '81O OF Delay', 'unit': 's', 'scale': 0.01, 'default': 100},
        65: {'name': 'SET_46_PICKUP', 'description': '46 Neg Seq OC Pickup', 'unit': 'A', 'scale': 0.01, 'default': 6000},
        66: {'name': 'SET_47_PICKUP', 'description': '47 Neg Seq OV Pickup', 'unit': 'V', 'scale': 0.1, 'default': 60},
        67: {'name': 'SET_49_PICKUP', 'description': '49 Thermal OL Pickup', 'unit': '%', 'scale': 0.1, 'default': 1000},
        68: {'name': 'SET_49_TC', 'description': '49 Thermal Time Const', 'unit': 'min', 'scale': 0.1, 'default': 300},
        
        # --- Transformer Control Settings (100-119) ---
        100: {'name': 'XFMR_TAP_MODE', 'description': 'Tap Changer Mode (0=Man/1=Auto)', 'unit': '', 'scale': 1, 'default': 1},
        101: {'name': 'XFMR_TAP_BW', 'description': 'Tap Control Bandwidth', 'unit': 'V', 'scale': 0.1, 'default': 24},
        102: {'name': 'XFMR_TAP_DELAY', 'description': 'Tap Change Delay', 'unit': 's', 'scale': 1, 'default': 60},
        103: {'name': 'XFMR_COOL_MODE', 'description': 'Cooling Mode', 'unit': '', 'scale': 1, 'default': 1},
        104: {'name': 'XFMR_FAN_STAGE1', 'description': 'Fan Stage 1 Temp', 'unit': '°C', 'scale': 0.1, 'default': 550},
        105: {'name': 'XFMR_FAN_STAGE2', 'description': 'Fan Stage 2 Temp', 'unit': '°C', 'scale': 0.1, 'default': 650},
        106: {'name': 'XFMR_PUMP_TEMP', 'description': 'Oil Pump Start Temp', 'unit': '°C', 'scale': 0.1, 'default': 700},
        
        # --- Capacitor Bank Control (120-139) ---
        120: {'name': 'CAP_MODE', 'description': 'Cap Bank Mode (0=Man/1=Auto)', 'unit': '', 'scale': 1, 'default': 1},
        121: {'name': 'CAP_VAR_SP', 'description': 'VAR Setpoint', 'unit': 'kVAR', 'scale': 0.1, 'default': 0},
        122: {'name': 'CAP_PF_SP', 'description': 'PF Setpoint', 'unit': '', 'scale': 0.001, 'default': 950},
        123: {'name': 'CAP_V_SP', 'description': 'Voltage Setpoint', 'unit': 'V', 'scale': 0.1, 'default': 1200},
        124: {'name': 'CAP_DELAY_ON', 'description': 'Step On Delay', 'unit': 's', 'scale': 1, 'default': 300},
        125: {'name': 'CAP_DELAY_OFF', 'description': 'Step Off Delay', 'unit': 's', 'scale': 1, 'default': 300},
        126: {'name': 'CAP_MAX_OPS_DAY', 'description': 'Max Operations/Day', 'unit': '', 'scale': 1, 'default': 6},
        
        # --- Generator Control (140-159) ---
        140: {'name': 'GEN_MODE', 'description': 'Generator Mode', 'unit': '', 'scale': 1, 'default': 1},
        141: {'name': 'GEN_MW_SP', 'description': 'MW Setpoint', 'unit': 'MW', 'scale': 0.1, 'default': 750},
        142: {'name': 'GEN_MVAR_SP', 'description': 'MVAR Setpoint', 'unit': 'MVAR', 'scale': 0.1, 'default': 200},
        143: {'name': 'GEN_V_SP', 'description': 'Voltage Setpoint', 'unit': 'V', 'scale': 0.1, 'default': 1200},
        144: {'name': 'GEN_PF_SP', 'description': 'Power Factor Setpoint', 'unit': '', 'scale': 0.001, 'default': 950},
        145: {'name': 'GEN_RAMP_RATE', 'description': 'Ramp Rate', 'unit': 'MW/min', 'scale': 0.1, 'default': 50},
        
        # --- Alarm Setpoints (160-199) ---
        160: {'name': 'ALM_V_HI', 'description': 'High Voltage Alarm', 'unit': 'V', 'scale': 0.1, 'default': 1260},
        161: {'name': 'ALM_V_LO', 'description': 'Low Voltage Alarm', 'unit': 'V', 'scale': 0.1, 'default': 1140},
        162: {'name': 'ALM_V_HI_HI', 'description': 'High-High Voltage Alarm', 'unit': 'V', 'scale': 0.1, 'default': 1320},
        163: {'name': 'ALM_V_LO_LO', 'description': 'Low-Low Voltage Alarm', 'unit': 'V', 'scale': 0.1, 'default': 1080},
        164: {'name': 'ALM_I_HI', 'description': 'High Current Alarm', 'unit': 'A', 'scale': 0.01, 'default': 11000},
        165: {'name': 'ALM_I_HI_HI', 'description': 'High-High Current Alarm', 'unit': 'A', 'scale': 0.01, 'default': 12500},
        166: {'name': 'ALM_FREQ_HI', 'description': 'High Frequency Alarm', 'unit': 'Hz', 'scale': 0.01, 'default': 6030},
        167: {'name': 'ALM_FREQ_LO', 'description': 'Low Frequency Alarm', 'unit': 'Hz', 'scale': 0.01, 'default': 5970},
        168: {'name': 'ALM_TEMP_HI', 'description': 'High Temperature Alarm', 'unit': '°C', 'scale': 0.1, 'default': 750},
        169: {'name': 'ALM_TEMP_HI_HI', 'description': 'High-High Temp Alarm', 'unit': '°C', 'scale': 0.1, 'default': 850},
        170: {'name': 'ALM_PF_LO', 'description': 'Low Power Factor Alarm', 'unit': '', 'scale': 0.001, 'default': 850},
    },
    
    # =========================================================================
    # DISCRETE INPUTS (Read-Only Digital Status) - Function Code 02
    # =========================================================================
    'discrete_inputs': {
        # --- Breaker/Switch Status (0-29) ---
        0: {'name': 'BKR_52A', 'description': 'Breaker 52A Status (Closed)', 'default': 1},
        1: {'name': 'BKR_52B', 'description': 'Breaker 52B Status (Open)', 'default': 0},
        2: {'name': 'BKR_READY', 'description': 'Breaker Ready', 'default': 1},
        3: {'name': 'BKR_SPRING_CHRG', 'description': 'Spring Charged', 'default': 1},
        4: {'name': 'BKR_LOCKOUT', 'description': 'Breaker Lockout', 'default': 0},
        5: {'name': 'BKR_LOCAL', 'description': 'Local Control Mode', 'default': 0},
        6: {'name': 'BKR_REMOTE', 'description': 'Remote Control Mode', 'default': 1},
        7: {'name': 'BKR_TRIP_COIL_MON', 'description': 'Trip Coil Monitor OK', 'default': 1},
        8: {'name': 'BKR_CLOSE_COIL_MON', 'description': 'Close Coil Monitor OK', 'default': 1},
        9: {'name': 'BKR_SF6_ALARM', 'description': 'SF6 Low Pressure Alarm', 'default': 0},
        10: {'name': 'DS_89A_CLOSED', 'description': 'Disconnect 89A Closed', 'default': 1},
        11: {'name': 'DS_89B_CLOSED', 'description': 'Disconnect 89B Closed', 'default': 0},
        12: {'name': 'GND_SW_89G', 'description': 'Ground Switch 89G Closed', 'default': 0},
        
        # --- Protection Status (30-59) ---
        30: {'name': 'PROT_ENABLED', 'description': 'Protection Enabled', 'default': 1},
        31: {'name': 'PROT_50_PICKUP', 'description': '50 Element Pickup', 'default': 0},
        32: {'name': 'PROT_51_PICKUP', 'description': '51 Element Pickup', 'default': 0},
        33: {'name': 'PROT_50N_PICKUP', 'description': '50N Element Pickup', 'default': 0},
        34: {'name': 'PROT_51N_PICKUP', 'description': '51N Element Pickup', 'default': 0},
        35: {'name': 'PROT_27_PICKUP', 'description': '27 UV Pickup', 'default': 0},
        36: {'name': 'PROT_59_PICKUP', 'description': '59 OV Pickup', 'default': 0},
        37: {'name': 'PROT_81U_PICKUP', 'description': '81U UF Pickup', 'default': 0},
        38: {'name': 'PROT_81O_PICKUP', 'description': '81O OF Pickup', 'default': 0},
        39: {'name': 'PROT_46_PICKUP', 'description': '46 Neg Seq OC Pickup', 'default': 0},
        40: {'name': 'PROT_47_PICKUP', 'description': '47 Neg Seq OV Pickup', 'default': 0},
        41: {'name': 'PROT_49_PICKUP', 'description': '49 Thermal OL Pickup', 'default': 0},
        42: {'name': 'PROT_50_TRIP', 'description': '50 Element Trip', 'default': 0},
        43: {'name': 'PROT_51_TRIP', 'description': '51 Element Trip', 'default': 0},
        44: {'name': 'PROT_50N_TRIP', 'description': '50N Element Trip', 'default': 0},
        45: {'name': 'PROT_51N_TRIP', 'description': '51N Element Trip', 'default': 0},
        46: {'name': 'PROT_27_TRIP', 'description': '27 UV Trip', 'default': 0},
        47: {'name': 'PROT_59_TRIP', 'description': '59 OV Trip', 'default': 0},
        48: {'name': 'PROT_81U_TRIP', 'description': '81U UF Trip', 'default': 0},
        49: {'name': 'PROT_81O_TRIP', 'description': '81O OF Trip', 'default': 0},
        50: {'name': 'PROT_LOCKOUT', 'description': 'Protection Lockout', 'default': 0},
        51: {'name': 'PROT_RECL_ENABLED', 'description': 'Recloser Enabled', 'default': 1},
        52: {'name': 'PROT_RECL_SHOT1', 'description': 'Recloser Shot 1', 'default': 0},
        53: {'name': 'PROT_RECL_SHOT2', 'description': 'Recloser Shot 2', 'default': 0},
        54: {'name': 'PROT_RECL_SHOT3', 'description': 'Recloser Shot 3', 'default': 0},
        55: {'name': 'PROT_RECL_LOCKOUT', 'description': 'Recloser Lockout', 'default': 0},
        
        # --- Transformer Status (60-79) ---
        60: {'name': 'XFMR_ONLINE', 'description': 'Transformer Online', 'default': 1},
        61: {'name': 'XFMR_OIL_TEMP_ALM', 'description': 'Oil Temperature Alarm', 'default': 0},
        62: {'name': 'XFMR_WNDG_TEMP_ALM', 'description': 'Winding Temperature Alarm', 'default': 0},
        63: {'name': 'XFMR_OIL_LEVEL_LO', 'description': 'Oil Level Low', 'default': 0},
        64: {'name': 'XFMR_PRESS_HI', 'description': 'Pressure High', 'default': 0},
        65: {'name': 'XFMR_PRESS_REL', 'description': 'Pressure Relief', 'default': 0},
        66: {'name': 'XFMR_BUCHHOLZ_ALM', 'description': 'Buchholz Alarm', 'default': 0},
        67: {'name': 'XFMR_BUCHHOLZ_TRIP', 'description': 'Buchholz Trip', 'default': 0},
        68: {'name': 'XFMR_FAN1_RUN', 'description': 'Cooling Fan 1 Running', 'default': 1},
        69: {'name': 'XFMR_FAN2_RUN', 'description': 'Cooling Fan 2 Running', 'default': 0},
        70: {'name': 'XFMR_PUMP1_RUN', 'description': 'Oil Pump 1 Running', 'default': 0},
        71: {'name': 'XFMR_PUMP2_RUN', 'description': 'Oil Pump 2 Running', 'default': 0},
        72: {'name': 'XFMR_TAP_LOCAL', 'description': 'Tap Changer Local Mode', 'default': 0},
        73: {'name': 'XFMR_TAP_AUTO', 'description': 'Tap Changer Auto Mode', 'default': 1},
        74: {'name': 'XFMR_TAP_FAULT', 'description': 'Tap Changer Fault', 'default': 0},
        75: {'name': 'XFMR_DGA_ALARM', 'description': 'Dissolved Gas Alarm', 'default': 0},
        
        # --- Generator Status (80-99) ---
        80: {'name': 'GEN_ONLINE', 'description': 'Generator Online', 'default': 1},
        81: {'name': 'GEN_SYNC_CHECK', 'description': 'Sync Check OK', 'default': 1},
        82: {'name': 'GEN_EXCITER_ON', 'description': 'Exciter On', 'default': 1},
        83: {'name': 'GEN_AVR_AUTO', 'description': 'AVR Auto Mode', 'default': 1},
        84: {'name': 'GEN_GOV_AUTO', 'description': 'Governor Auto Mode', 'default': 1},
        85: {'name': 'GEN_READY', 'description': 'Generator Ready', 'default': 1},
        86: {'name': 'GEN_STATOR_TEMP_ALM', 'description': 'Stator Temp Alarm', 'default': 0},
        87: {'name': 'GEN_ROTOR_TEMP_ALM', 'description': 'Rotor Temp Alarm', 'default': 0},
        88: {'name': 'GEN_BEARING_ALM', 'description': 'Bearing Alarm', 'default': 0},
        89: {'name': 'GEN_VIBRATION_ALM', 'description': 'Vibration Alarm', 'default': 0},
        90: {'name': 'GEN_REVERSE_PWR', 'description': 'Reverse Power', 'default': 0},
        91: {'name': 'GEN_LOSS_EXCIT', 'description': 'Loss of Excitation', 'default': 0},
        92: {'name': 'GEN_LOSS_FIELD', 'description': 'Loss of Field', 'default': 0},
        
        # --- Capacitor Bank Status (100-119) ---
        100: {'name': 'CAP_STEP1_ON', 'description': 'Cap Bank Step 1 On', 'default': 1},
        101: {'name': 'CAP_STEP2_ON', 'description': 'Cap Bank Step 2 On', 'default': 1},
        102: {'name': 'CAP_STEP3_ON', 'description': 'Cap Bank Step 3 On', 'default': 1},
        103: {'name': 'CAP_STEP4_ON', 'description': 'Cap Bank Step 4 On', 'default': 0},
        104: {'name': 'CAP_STEP5_ON', 'description': 'Cap Bank Step 5 On', 'default': 0},
        105: {'name': 'CAP_AUTO_MODE', 'description': 'Auto Mode Active', 'default': 1},
        106: {'name': 'CAP_UNBAL_ALM', 'description': 'Unbalance Alarm', 'default': 0},
        107: {'name': 'CAP_OV_ALM', 'description': 'Overvoltage Alarm', 'default': 0},
        108: {'name': 'CAP_FUSE_FAIL', 'description': 'Fuse Failure', 'default': 0},
        
        # --- DC System Status (120-139) ---
        120: {'name': 'DC_CHARGER_ON', 'description': 'Charger On', 'default': 1},
        121: {'name': 'DC_CHARGER_FAULT', 'description': 'Charger Fault', 'default': 0},
        122: {'name': 'DC_BATT_DISC', 'description': 'Battery Disconnected', 'default': 0},
        123: {'name': 'DC_GND_FAULT', 'description': 'Ground Fault Detected', 'default': 0},
        124: {'name': 'DC_LO_VOLT_ALM', 'description': 'Low Voltage Alarm', 'default': 0},
        125: {'name': 'DC_HI_VOLT_ALM', 'description': 'High Voltage Alarm', 'default': 0},
        126: {'name': 'DC_EQUAL_MODE', 'description': 'Equalize Mode', 'default': 0},
        127: {'name': 'DC_FLOAT_MODE', 'description': 'Float Mode', 'default': 1},
        
        # --- Communication Status (140-149) ---
        140: {'name': 'COMM_SCADA_OK', 'description': 'SCADA Comm OK', 'default': 1},
        141: {'name': 'COMM_RTU_OK', 'description': 'RTU Comm OK', 'default': 1},
        142: {'name': 'COMM_GPS_SYNC', 'description': 'GPS Time Sync OK', 'default': 1},
        143: {'name': 'COMM_IRIG_B_OK', 'description': 'IRIG-B Sync OK', 'default': 1},
        144: {'name': 'COMM_DNP3_OK', 'description': 'DNP3 Comm OK', 'default': 1},
        145: {'name': 'COMM_IEC61850_OK', 'description': 'IEC61850 GOOSE OK', 'default': 1},
        
        # --- Alarms Summary (150-169) ---
        150: {'name': 'ALM_ANY_ACTIVE', 'description': 'Any Alarm Active', 'default': 0},
        151: {'name': 'ALM_CRITICAL', 'description': 'Critical Alarm', 'default': 0},
        152: {'name': 'ALM_MAJOR', 'description': 'Major Alarm', 'default': 0},
        153: {'name': 'ALM_MINOR', 'description': 'Minor Alarm', 'default': 0},
        154: {'name': 'ALM_MAINT_REQ', 'description': 'Maintenance Required', 'default': 0},
        155: {'name': 'ALM_COMM_FAIL', 'description': 'Communication Failure', 'default': 0},
        156: {'name': 'ALM_SELF_TEST_FAIL', 'description': 'Self Test Failure', 'default': 0},
    },
    
    # =========================================================================
    # COILS (Read/Write Digital Controls) - Function Code 01/05/15
    # =========================================================================
    'coils': {
        # --- Breaker Controls (0-19) ---
        0: {'name': 'CMD_BKR_CLOSE', 'description': 'Breaker Close Command', 'default': 0},
        1: {'name': 'CMD_BKR_TRIP', 'description': 'Breaker Trip Command', 'default': 0},
        2: {'name': 'CMD_BKR_RESET', 'description': 'Breaker Reset Command', 'default': 0},
        3: {'name': 'CMD_LOCKOUT_RESET', 'description': 'Lockout Reset Command', 'default': 0},
        4: {'name': 'CMD_DS_89A_CLOSE', 'description': 'DS 89A Close Command', 'default': 0},
        5: {'name': 'CMD_DS_89A_OPEN', 'description': 'DS 89A Open Command', 'default': 0},
        6: {'name': 'CMD_DS_89B_CLOSE', 'description': 'DS 89B Close Command', 'default': 0},
        7: {'name': 'CMD_DS_89B_OPEN', 'description': 'DS 89B Open Command', 'default': 0},
        
        # --- Protection Controls (20-39) ---
        20: {'name': 'CMD_PROT_ENABLE', 'description': 'Enable Protection', 'default': 0},
        21: {'name': 'CMD_PROT_DISABLE', 'description': 'Disable Protection', 'default': 0},
        22: {'name': 'CMD_RECL_ENABLE', 'description': 'Enable Recloser', 'default': 0},
        23: {'name': 'CMD_RECL_DISABLE', 'description': 'Disable Recloser', 'default': 0},
        24: {'name': 'CMD_RECL_RESET', 'description': 'Reset Recloser', 'default': 0},
        25: {'name': 'CMD_TARGETS_RESET', 'description': 'Reset Target LEDs', 'default': 0},
        26: {'name': 'CMD_EVENT_CLEAR', 'description': 'Clear Event Log', 'default': 0},
        27: {'name': 'CMD_DEMAND_RESET', 'description': 'Reset Demand Values', 'default': 0},
        28: {'name': 'CMD_ENERGY_RESET', 'description': 'Reset Energy Counters', 'default': 0},
        
        # --- Transformer Controls (40-59) ---
        40: {'name': 'CMD_TAP_RAISE', 'description': 'Tap Changer Raise', 'default': 0},
        41: {'name': 'CMD_TAP_LOWER', 'description': 'Tap Changer Lower', 'default': 0},
        42: {'name': 'CMD_TAP_AUTO', 'description': 'Tap Changer Auto Mode', 'default': 0},
        43: {'name': 'CMD_TAP_MANUAL', 'description': 'Tap Changer Manual Mode', 'default': 0},
        44: {'name': 'CMD_FAN1_START', 'description': 'Start Fan 1', 'default': 0},
        45: {'name': 'CMD_FAN1_STOP', 'description': 'Stop Fan 1', 'default': 0},
        46: {'name': 'CMD_FAN2_START', 'description': 'Start Fan 2', 'default': 0},
        47: {'name': 'CMD_FAN2_STOP', 'description': 'Stop Fan 2', 'default': 0},
        48: {'name': 'CMD_PUMP1_START', 'description': 'Start Oil Pump 1', 'default': 0},
        49: {'name': 'CMD_PUMP1_STOP', 'description': 'Stop Oil Pump 1', 'default': 0},
        50: {'name': 'CMD_COOL_AUTO', 'description': 'Cooling Auto Mode', 'default': 0},
        51: {'name': 'CMD_COOL_MANUAL', 'description': 'Cooling Manual Mode', 'default': 0},
        
        # --- Capacitor Bank Controls (60-79) ---
        60: {'name': 'CMD_CAP_STEP1_ON', 'description': 'Step 1 On', 'default': 0},
        61: {'name': 'CMD_CAP_STEP1_OFF', 'description': 'Step 1 Off', 'default': 0},
        62: {'name': 'CMD_CAP_STEP2_ON', 'description': 'Step 2 On', 'default': 0},
        63: {'name': 'CMD_CAP_STEP2_OFF', 'description': 'Step 2 Off', 'default': 0},
        64: {'name': 'CMD_CAP_STEP3_ON', 'description': 'Step 3 On', 'default': 0},
        65: {'name': 'CMD_CAP_STEP3_OFF', 'description': 'Step 3 Off', 'default': 0},
        66: {'name': 'CMD_CAP_STEP4_ON', 'description': 'Step 4 On', 'default': 0},
        67: {'name': 'CMD_CAP_STEP4_OFF', 'description': 'Step 4 Off', 'default': 0},
        68: {'name': 'CMD_CAP_STEP5_ON', 'description': 'Step 5 On', 'default': 0},
        69: {'name': 'CMD_CAP_STEP5_OFF', 'description': 'Step 5 Off', 'default': 0},
        70: {'name': 'CMD_CAP_ALL_ON', 'description': 'All Steps On', 'default': 0},
        71: {'name': 'CMD_CAP_ALL_OFF', 'description': 'All Steps Off', 'default': 0},
        72: {'name': 'CMD_CAP_AUTO', 'description': 'Cap Auto Mode', 'default': 0},
        73: {'name': 'CMD_CAP_MANUAL', 'description': 'Cap Manual Mode', 'default': 0},
        
        # --- Generator Controls (80-99) ---
        80: {'name': 'CMD_GEN_START', 'description': 'Generator Start', 'default': 0},
        81: {'name': 'CMD_GEN_STOP', 'description': 'Generator Stop', 'default': 0},
        82: {'name': 'CMD_GEN_SYNC', 'description': 'Initiate Sync', 'default': 0},
        83: {'name': 'CMD_GEN_CLOSE', 'description': 'Close Generator Breaker', 'default': 0},
        84: {'name': 'CMD_GEN_TRIP', 'description': 'Trip Generator', 'default': 0},
        85: {'name': 'CMD_EXCITER_ON', 'description': 'Exciter On', 'default': 0},
        86: {'name': 'CMD_EXCITER_OFF', 'description': 'Exciter Off', 'default': 0},
        87: {'name': 'CMD_AVR_AUTO', 'description': 'AVR Auto Mode', 'default': 0},
        88: {'name': 'CMD_AVR_MANUAL', 'description': 'AVR Manual Mode', 'default': 0},
        89: {'name': 'CMD_GOV_AUTO', 'description': 'Governor Auto Mode', 'default': 0},
        90: {'name': 'CMD_GOV_MANUAL', 'description': 'Governor Manual Mode', 'default': 0},
        91: {'name': 'CMD_RAISE_V', 'description': 'Raise Voltage', 'default': 0},
        92: {'name': 'CMD_LOWER_V', 'description': 'Lower Voltage', 'default': 0},
        93: {'name': 'CMD_RAISE_MW', 'description': 'Raise MW', 'default': 0},
        94: {'name': 'CMD_LOWER_MW', 'description': 'Lower MW', 'default': 0},
        
        # --- System Controls (100-119) ---
        100: {'name': 'CMD_ALARM_ACK', 'description': 'Acknowledge All Alarms', 'default': 0},
        101: {'name': 'CMD_ALARM_RESET', 'description': 'Reset All Alarms', 'default': 0},
        102: {'name': 'CMD_LED_TEST', 'description': 'LED Test', 'default': 0},
        103: {'name': 'CMD_SELF_TEST', 'description': 'Initiate Self Test', 'default': 0},
        104: {'name': 'CMD_TIME_SYNC', 'description': 'Force Time Sync', 'default': 0},
        105: {'name': 'CMD_CONFIG_SAVE', 'description': 'Save Configuration', 'default': 0},
        106: {'name': 'CMD_CONFIG_RESTORE', 'description': 'Restore Default Config', 'default': 0},
        107: {'name': 'CMD_REBOOT', 'description': 'System Reboot', 'default': 0},
    }
}

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
        # Initialize data blocks with expanded size
        self.coils = ModbusSequentialDataBlock(0, [0] * REGISTER_COUNT)
        self.discrete_inputs = ModbusSequentialDataBlock(0, [0] * REGISTER_COUNT)
        self.holding_registers = ModbusSequentialDataBlock(0, [0] * REGISTER_COUNT)
        self.input_registers = ModbusSequentialDataBlock(0, [0] * REGISTER_COUNT)
        
        # Initialize with power industry default values
        self._initialize_power_defaults()
        
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
        
        # Simulation state
        self.simulation_running = False
        self.simulation_thread = None
    
    def _initialize_power_defaults(self):
        """Initialize all registers with power industry default values"""
        # Initialize input registers
        for addr, config in POWER_REGISTER_MAP['input_registers'].items():
            self.input_registers.setValues(addr, [config['default']])
        
        # Initialize holding registers
        for addr, config in POWER_REGISTER_MAP['holding_registers'].items():
            self.holding_registers.setValues(addr, [config['default']])
        
        # Initialize discrete inputs
        for addr, config in POWER_REGISTER_MAP['discrete_inputs'].items():
            self.discrete_inputs.setValues(addr, [config['default']])
        
        # Initialize coils
        for addr, config in POWER_REGISTER_MAP['coils'].items():
            self.coils.setValues(addr, [config['default']])
    
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
            # Get the variable name if it exists in the register map
            var_name = None
            if register_type in POWER_REGISTER_MAP:
                reg_map = POWER_REGISTER_MAP[register_type]
                if address in reg_map:
                    var_name = reg_map[address]['name']
            
            change = {
                'timestamp': datetime.now().isoformat(),
                'type': register_type,
                'address': address,
                'name': var_name,
                'old_value': old_value,
                'new_value': new_value
            }
            self.last_changes.append(change)
            if len(self.last_changes) > 100:
                self.last_changes.pop(0)
    
    def get_coil(self, address):
        values = self.coils.getValues(address, 1)
        return values[0]
    
    def set_coil(self, address, value):
        old_value = self.get_coil(address)
        self.coils.setValues(address, [value])
        self.track_change('coils', address, old_value, value)
    
    def get_discrete_input(self, address):
        values = self.discrete_inputs.getValues(address, 1)
        return values[0]
    
    def set_discrete_input(self, address, value):
        old_value = self.get_discrete_input(address)
        self.discrete_inputs.setValues(address, [value])
        self.track_change('discrete_inputs', address, old_value, value)
    
    def get_holding_register(self, address):
        values = self.holding_registers.getValues(address, 1)
        return values[0]
    
    def set_holding_register(self, address, value):
        old_value = self.get_holding_register(address)
        if value < 0:
            value = 0xFFFF + value + 1
        self.holding_registers.setValues(address, [value])
        self.track_change('holding_registers', address, old_value, value)
    
    def get_input_register(self, address):
        values = self.input_registers.getValues(address, 1)
        return values[0]
    
    def set_input_register(self, address, value):
        old_value = self.get_input_register(address)
        if value < 0:
            value = 0xFFFF + value + 1
        self.input_registers.setValues(address, [value])
        self.track_change('input_registers', address, old_value, value)
    
    def get_recent_changes(self):
        with self.lock:
            return self.last_changes[-50:]
    
    def get_register_map(self):
        """Return the power register map for API access"""
        return POWER_REGISTER_MAP
    
    def get_all_values_by_category(self, category):
        """Get all values for a specific category with metadata"""
        result = {}
        if category == 'input_registers':
            for addr, config in POWER_REGISTER_MAP['input_registers'].items():
                raw_value = self.get_input_register(addr)
                scaled_value = raw_value * config.get('scale', 1)
                result[config['name']] = {
                    'address': addr,
                    'raw_value': raw_value,
                    'scaled_value': scaled_value,
                    'unit': config.get('unit', ''),
                    'description': config['description']
                }
        elif category == 'holding_registers':
            for addr, config in POWER_REGISTER_MAP['holding_registers'].items():
                raw_value = self.get_holding_register(addr)
                scaled_value = raw_value * config.get('scale', 1)
                result[config['name']] = {
                    'address': addr,
                    'raw_value': raw_value,
                    'scaled_value': scaled_value,
                    'unit': config.get('unit', ''),
                    'description': config['description']
                }
        elif category == 'discrete_inputs':
            for addr, config in POWER_REGISTER_MAP['discrete_inputs'].items():
                result[config['name']] = {
                    'address': addr,
                    'value': self.get_discrete_input(addr),
                    'description': config['description']
                }
        elif category == 'coils':
            for addr, config in POWER_REGISTER_MAP['coils'].items():
                result[config['name']] = {
                    'address': addr,
                    'value': self.get_coil(addr),
                    'description': config['description']
                }
        return result

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
        'register_count': REGISTER_COUNT,
        'recent_changes': simulator.get_recent_changes()
    })

@app.route('/api/status')
def get_status():
    """Get current status of common registers"""
    state.add_connection(request.remote_addr)
    
    # Return a subset of commonly monitored values
    return jsonify({
        'voltage': {
            'V_L1_N': simulator.get_input_register(0) * 0.1,
            'V_L2_N': simulator.get_input_register(1) * 0.1,
            'V_L3_N': simulator.get_input_register(2) * 0.1,
            'V_L1_L2': simulator.get_input_register(3) * 0.1,
            'V_L2_L3': simulator.get_input_register(4) * 0.1,
            'V_L3_L1': simulator.get_input_register(5) * 0.1,
        },
        'current': {
            'I_L1': simulator.get_input_register(20) * 0.01,
            'I_L2': simulator.get_input_register(21) * 0.01,
            'I_L3': simulator.get_input_register(22) * 0.01,
            'I_N': simulator.get_input_register(23) * 0.01,
        },
        'power': {
            'P_TOTAL': simulator.get_input_register(43) * 0.1,
            'Q_TOTAL': simulator.get_input_register(47) * 0.1,
            'S_TOTAL': simulator.get_input_register(51) * 0.1,
            'PF_TOTAL': simulator.get_input_register(55) * 0.001,
        },
        'frequency': {
            'FREQ': simulator.get_input_register(70) * 0.01,
        },
        'breaker': {
            'BKR_52A': simulator.get_discrete_input(0),
            'BKR_52B': simulator.get_discrete_input(1),
            'BKR_READY': simulator.get_discrete_input(2),
        },
        'transformer': {
            'XFMR_OIL_TEMP': simulator.get_input_register(100) * 0.1,
            'XFMR_WNDG_TEMP': simulator.get_input_register(101) * 0.1,
            'XFMR_LOAD_PCT': simulator.get_input_register(103) * 0.1,
            'XFMR_TAP_POS': simulator.get_input_register(106),
        }
    })

@app.route('/api/register_map')
def get_register_map():
    """Get the complete power industry register map"""
    return jsonify(POWER_REGISTER_MAP)

@app.route('/api/category/<category>')
def get_category_values(category):
    """Get all values for a specific category"""
    if category not in ['input_registers', 'holding_registers', 'discrete_inputs', 'coils']:
        return jsonify({'error': 'Invalid category'}), 400
    
    return jsonify(simulator.get_all_values_by_category(category))

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
            'coils': {i: simulator.get_coil(i) for i in range(REGISTER_COUNT)},
            'discrete_inputs': {i: simulator.get_discrete_input(i) for i in range(REGISTER_COUNT)},
            'holding_registers': {i: simulator.get_holding_register(i) for i in range(REGISTER_COUNT)},
            'input_registers': {i: simulator.get_input_register(i) for i in range(REGISTER_COUNT)}
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

@app.route('/api/reset_defaults', methods=['POST'])
def reset_defaults():
    """Reset all registers to power industry defaults"""
    try:
        simulator._initialize_power_defaults()
        return jsonify({'success': True, 'message': 'All registers reset to defaults'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

def run_modbus_server():
    """Run Modbus TCP server"""
    logging.basicConfig()
    log = logging.getLogger()
    log.setLevel(logging.INFO)
    
    identity = ModbusDeviceIdentification()
    identity.VendorName = 'Power Industry IED Simulator'
    identity.ProductCode = 'PWR-IED-SIM'
    identity.VendorUrl = 'http://localhost:5000'
    identity.ProductName = 'Power Industry IED Simulator for SEL RTAC'
    identity.ModelName = 'Raspberry Pi Power Simulator'
    identity.MajorMinorRevision = '3.0.0'
    
    state.modbus_running = True
    print(f"[MODBUS] Starting Modbus TCP Server on {SERVER_IP}:{SERVER_PORT}")
    print(f"[MODBUS] Modbus Address: {MODBUS_ADDRESS}")
    print(f"[MODBUS] Register Count: {REGISTER_COUNT} per type")
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
    print("POWER INDUSTRY IED SIMULATOR - Professional Edition v3.0")
    print("=" * 70)
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Modbus TCP: {SERVER_IP}:{SERVER_PORT} (Unit ID: {MODBUS_ADDRESS})")
    print(f"Web Interface: http://0.0.0.0:{FLASK_PORT}")
    print(f"Register Count: {REGISTER_COUNT} per type")
    print("-" * 70)
    print("Configured Power Industry Variables:")
    print(f"  - Input Registers: {len(POWER_REGISTER_MAP['input_registers'])} variables")
    print(f"  - Holding Registers: {len(POWER_REGISTER_MAP['holding_registers'])} variables")
    print(f"  - Discrete Inputs: {len(POWER_REGISTER_MAP['discrete_inputs'])} variables")
    print(f"  - Coils: {len(POWER_REGISTER_MAP['coils'])} variables")
    total_vars = (len(POWER_REGISTER_MAP['input_registers']) + 
                  len(POWER_REGISTER_MAP['holding_registers']) +
                  len(POWER_REGISTER_MAP['discrete_inputs']) + 
                  len(POWER_REGISTER_MAP['coils']))
    print(f"  - Total: {total_vars} power industry variables")
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

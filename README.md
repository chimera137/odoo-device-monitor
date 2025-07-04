# odoo-device-monitor
Odoo Module for PLC Device Monitoring and Business Integration

## Overview
This repository contains the `odoo-device-monitor` module, a custom Odoo ERP add-on designed to provide a unified dashboard and business logic integration for PLC devices (currently Modbus and OPC UA). It enables real-time monitoring, mapping of PLC data to Odoo business fields, and seamless updates to Manufacturing and Inventory processes.

This is a Third Party Module for Odoo ERP.

## Features
- **Unified Device Dashboard**: Aggregates and displays all Modbus and OPC UA devices in a single view.
- **Business Field Mapping**: Map PLC registers/nodes to Odoo business fields (e.g., production quantity, scrap, inventory).
- **Flexible Update Conditions**: Supports always update, on value change, or on threshold for each mapping.
- **Automatic Business Updates**: Updates Manufacturing Orders, creates scrap records, and more based on live PLC data.


## System Architecture Context
The `odoo-device-monitor` module is a key part of a multi-vendor PLC integration system for Odoo ERP. It acts as the business logic layer, working in conjunction with:
- [Modbus Connector](https://github.com/chimera137/odoo-modbus-connector)
- [OPC UA Connector](https://github.com/chimera137/odoo-opcua-connector)

These connector modules handle the direct communication with PLCs and expose device data to Odoo. The Device Monitor module consumes this data, maps it to business logic, and updates Odoo's core applications.

## Getting Started

### Prerequisites
- Odoo ERP (v16.0 or higher recommended) instance.
- At least one connector module installed (Modbus or OPC UA).
- PLC devices or simulators for testing.

### Installation
1. **Clone this repository:**
   `git clone https://github.com/chimera137/odoo-device-monitor.git`

2. **Place the module:** Copy the `odoo-device-monitor` folder into your Odoo custom add-ons path (e.g., /path/to/odoo/addons/)

3. **Update and Install in Odoo:**
    - Restart your Odoo service.
    - Navigate to the Apps menu in your Odoo instance.
    - Click "Update Apps List" (if you don't see the module immediately).
    - Search for "Device Monitor" and install the module.

## Usage
Once the device_monitor module is installed in Odoo and at least one connector is running:
1. **Access Device Monitor:**
   Navigate to Manufacturing (or a custom menu if defined) -> Device Monitor.

2. **Add and Configure Business Mappings:**
   For each device, define mappings from PLC registers/nodes to Odoo business fields. Choose the update condition (always, on value change, on threshold).

3. **Real-Time Integration:**
   As PLC data is received, the device monitor will update the mapped business fields in Odoo (e.g., production orders, scrap, inventory).

### Integration with Connector Modules
This module is designed to work with:
- [Modbus Connector](https://github.com/chimera137/odoo-modbus-connector)
- [OPC UA Connector](https://github.com/chimera137/odoo-opcua-connector)

Install and configure the appropriate connector(s) to enable device data acquisition.

## Acknowledgement
This project was developed as part of an undergraduate thesis for the Department of Electrical Engineering / Teknik Elektro at Petra Christian University Surabaya, Indonesia. The insights and methodologies explored herein contribute to the academic research in the field of industrial automation (IIoT) and ERP integration.

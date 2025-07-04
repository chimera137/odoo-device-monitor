{
    'name': 'Device Monitor',
    'version': '1.0',
    'category': 'Manufacturing',
    'summary': 'Monitor PLC devices and integrate with Odoo business apps',
    'description': """
Device Monitor Module
====================
This module provides a unified interface to monitor PLC devices (Modbus and OPC UA)
and integrate their data with Odoo business applications.

Features:
---------
* Monitor Modbus and OPC UA devices
* Map PLC data to business fields
* Automatic updates to Manufacturing and Inventory
* Configurable update conditions
* Real-time monitoring dashboard
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': [
        'base',
        'mrp',
        'stock',
        'modbus_connector',
        'opcua_connector',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/device_monitor_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
} 
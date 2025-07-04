from odoo import http
from odoo.http import request
import json

class DeviceMonitorController(http.Controller):
    @http.route('/device_monitor/api/v1/devices', type='json', auth='user')
    def get_devices(self, **kwargs):
        """Get all devices with their current status and values"""
        devices = request.env['device.monitor'].search([])
        result = {
            'opcua_devices': [],
            'modbus_devices': []
        }

        for device in devices:
            device_data = {
                'id': device.id,
                'name': device.name,
                'device_type': device.device_type,
                'device_id': device.device_id,
                'status': device.status,
                'values': json.loads(device.last_values) if device.last_values else {},
                'error': device.last_error,
                'is_polling': device.is_polling,
                'alert_thresholds': json.loads(device.alert_thresholds),
                'register_aliases': json.loads(device.register_aliases)
            }

            if device.device_type == 'opcua':
                result['opcua_devices'].append(device_data)
            else:
                result['modbus_devices'].append(device_data)

        return result

    @http.route('/device_monitor/api/v1/devices/<int:device_id>', type='json', auth='user')
    def get_device(self, device_id, **kwargs):
        """Get a specific device's data"""
        device = request.env['device.monitor'].browse(device_id)
        if not device.exists():
            return {'error': 'Device not found'}

        return {
            'id': device.id,
            'name': device.name,
            'device_type': device.device_type,
            'device_id': device.device_id,
            'status': device.status,
            'values': json.loads(device.last_values) if device.last_values else {},
            'error': device.last_error,
            'is_polling': device.is_polling,
            'alert_thresholds': json.loads(device.alert_thresholds),
            'register_aliases': json.loads(device.register_aliases)
        }

    @http.route('/device_monitor/api/v1/devices/<int:device_id>/thresholds', type='json', auth='user')
    def set_thresholds(self, device_id, thresholds, **kwargs):
        """Set alert thresholds for a device"""
        device = request.env['device.monitor'].browse(device_id)
        if not device.exists():
            return {'error': 'Device not found'}

        device.alert_thresholds = json.dumps(thresholds)
        return {'success': True}

    @http.route('/device_monitor/api/v1/devices/<int:device_id>/aliases', type='json', auth='user')
    def set_aliases(self, device_id, aliases, **kwargs):
        """Set register aliases for a device"""
        device = request.env['device.monitor'].browse(device_id)
        if not device.exists():
            return {'error': 'Device not found'}

        device.register_aliases = json.dumps(aliases)
        return {'success': True}

    @http.route('/device_monitor/api/v1/devices/<int:device_id>/polling', type='json', auth='user')
    def set_polling(self, device_id, is_polling, **kwargs):
        """Enable or disable polling for a device"""
        device = request.env['device.monitor'].browse(device_id)
        if not device.exists():
            return {'error': 'Device not found'}

        device.is_polling = is_polling
        return {'success': True} 
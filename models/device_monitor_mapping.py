from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class DeviceMonitorMapping(models.Model):
    _name = 'device.monitor.mapping'
    _description = 'PLC to Business Field Mapping'
    _order = 'sequence, id'

    sequence = fields.Integer('Sequence', default=10)
    monitor_id = fields.Many2one('device.monitor', string='Device Monitor', required=True)
    
    # PLC Configuration
    plc_register = fields.Char('PLC Register/Node', required=True,
        help="For Modbus: Register address (e.g., 'Register 0')\n"
             "For OPC UA: Node ID (e.g., ns=2;s=Channel1.Device1.Tag1)")
    
    # Business Integration
    business_model = fields.Selection([
        ('mrp.production', 'Production Order'),
        ('stock.move', 'Inventory Move')
    ], string='Business Model', required=True)
    
    business_field = fields.Selection([
        ('qty_producing', 'Quantity Producing'),
        ('qty_scrap', 'Scrap Quantity'),
        ('product_qty', 'Total Quantity'),
        ('finished_lot_id', 'Lot/Serial Number'),
        ('workorder_id.duration', 'Work Duration')
    ], string='Business Field', required=True)
    
    # Update Conditions
    update_condition = fields.Selection([
        ('always', 'Always Update'),
        ('threshold', 'On Threshold'),
        ('change', 'On Value Change')
    ], string='Update Condition', default='always', required=True)
    
    threshold_value = fields.Float('Threshold Value',
        help="Value that triggers the update when using threshold condition")
    
    last_value = fields.Float('Last Value',
        help="Last value read from PLC for change detection")
    
    last_update_time = fields.Datetime('Last Update Time',
        help="Timestamp of the last successful update")
    
    active = fields.Boolean('Active', default=True)
    
    @api.onchange('business_model')
    def _onchange_business_model(self):
        """Reset business field when model changes"""
        self.business_field = False
    
    @api.onchange('update_condition')
    def _onchange_update_condition(self):
        """Reset threshold value when condition changes"""
        if self.update_condition != 'threshold':
            self.threshold_value = 0.0

    @api.constrains('business_model', 'business_field')
    def _check_field_validity(self):
        valid_combinations = {
            'mrp.production': ['qty_producing', 'qty_scrap', 'product_qty', 'finished_lot_id'],
            'stock.move': ['product_uom_qty', 'quantity_done']
        }
        for record in self:
            if record.business_model in valid_combinations:
                if record.business_field not in valid_combinations[record.business_model]:
                    raise ValidationError(
                        f"Field {record.business_field} is not valid for model {record.business_model}"
                    )
    
    def name_get(self):
        result = []
        for record in self:
            name = f"{record.monitor_id.name} - {record.plc_register} → {record.business_model}.{record.business_field}"
            result.append((record.id, name))
        return result 
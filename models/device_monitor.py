from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
from datetime import timedelta

_logger = logging.getLogger(__name__)

class DeviceMonitor(models.Model):
    _name = 'device.monitor'
    _description = 'PLC to Odoo Integration Monitor'
    _order = 'name'

    name = fields.Char('Name', required=True)
    device_id = fields.Reference([
        ('modbus.device', 'Modbus Device'),
        ('opcua.device', 'OPC UA Device')
    ], string='PLC Device', required=True, ondelete='cascade')
    
    device_type = fields.Selection([
        ('modbus', 'Modbus'),
        ('opcua', 'OPC UA')
    ], compute='_compute_device_type', store=True)
    
    active = fields.Boolean('Active', default=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('running', 'Running'),
        ('stopped', 'Stopped'),
        ('error', 'Error')
    ], default='draft', string='Status', copy=False)
    
    # Value Tracking Fields
    last_update = fields.Datetime('Last Update', readonly=True)
    register_values = fields.Json('Register Values', default={}, readonly=True)  # Stores all values
    last_value = fields.Float('Last Value', readonly=True)  # Last processed value
    error_message = fields.Text('Error Message', readonly=True)
    
    # Business Links
    product_id = fields.Many2one('product.product', 'Manufactured Product')
    workcenter_id = fields.Many2one('mrp.workcenter', 'Work Center')
    business_mapping_ids = fields.One2many(
        'device.monitor.mapping', 
        'monitor_id', 
        string='Business Field Mappings'
    )

    # Display Fields
    register_values_display = fields.Text(
        'Register Values',
        compute='_compute_register_display'
    )

    @api.depends('device_id')
    def _compute_device_type(self):
        for record in self:
            if record.device_id:
                record.device_type = record.device_id._name.split('.')[0]
            else:
                record.device_type = False

    @api.depends('register_values')
    def _compute_register_display(self):
        for record in self:
            if not record.register_values or not isinstance(record.register_values, dict):
                record.register_values_display = "No data"
            else:
                lines = []
                for reg, val in sorted(record.register_values.items()):
                    # Find matching mapping for display name
                    mapping = record.business_mapping_ids.filtered(
                        lambda m: str(m.plc_register) == str(reg)
                    )[:1]
                    reg_name = mapping.business_field if mapping else f"Register {reg}"
                    lines.append(f"{reg_name}: {val}")
                
                record.register_values_display = "\n".join(lines) or "No mapped values"

    def action_start(self):
        self.ensure_one()
        try:
            # Start polling on the device
            if self.device_type in ('modbus', 'opcua'):
                self.device_id.action_start_polling()
            self.write({'state': 'running', 'error_message': False})
        except Exception as e:
            self.state = 'error'
            self.error_message = str(e)
            raise UserError(_('Failed to start device: %s') % str(e))

    def action_stop(self):
        self.ensure_one()
        try:
            # Stop polling on the device
            if self.device_type in ('modbus', 'opcua'):
                self.device_id.action_stop_polling()
            self.write({'state': 'stopped'})
        except Exception as e:
            self.state = 'error'
            self.error_message = str(e)
            raise UserError(_('Failed to stop device: %s') % str(e))

    def _process_plc_data(self, register, value):
        self.ensure_one()
        try:
            _logger.info(f"⏩ Processing register {register} with value {value}")
            current_values = {}
            if isinstance(self.register_values, dict):
                current_values = self.register_values.copy()
            str_register = str(register)
            float_value = float(value)
            _logger.info(f"Current register state: {current_values}")
            _logger.info(f"Debug: Incoming str_register for processing: '{str_register}'")
            for m in self.business_mapping_ids.filtered(lambda x: x.active):
                plc_register_str = str(m.plc_register or '').strip()
                _logger.info(f"Debug: Active mapping plc_register: '{plc_register_str}' (Comparing against '{str_register}')")
            current_values[str_register] = float_value
            self.write({
                'register_values': current_values,
                'last_update': fields.Datetime.now(),
                'last_value': float_value,
                'error_message': False
            })
            # Robust register matching
            mappings = self.business_mapping_ids.filtered(
                lambda m: m.active and (
                    str(m.plc_register or '').strip() == str_register or
                    str(m.plc_register or '').replace('Register ', '').strip("'\"") == str_register.replace('Register ', '').strip("'\"")
                )
            )
            _logger.info(f"Found {len(mappings)} mappings for register '{register}'")
            for mapping in mappings:
                try:
                    _logger.info("Processing mapping: %s.%s" % (mapping.business_model, mapping.business_field))
                    update = False
                    if mapping.update_condition == 'always':
                        update = True
                    elif mapping.update_condition == 'threshold':
                        update = float_value >= mapping.threshold_value
                    elif mapping.update_condition == 'change':
                        update = float_value != mapping.last_value
                    if update:
                        success = self._update_business_field(
                            mapping,
                            float_value
                        )
                        _logger.info(f"Update {'succeeded' if success else 'failed'}")
                        if success:
                            mapping.write({'last_value': float_value, 'last_update_time': fields.Datetime.now()})
                            _logger.info(f"Updated mapping {mapping.id} last_value to {float_value}")
                    else:
                        _logger.info(f"Update condition not met for mapping {mapping.id}")
                except Exception as e:
                    _logger.error(f"Mapping processing failed: {str(e)}", exc_info=True)
                    continue
        except Exception as e:
            error_msg = f"PLC processing error: {str(e)}"
            _logger.error(error_msg, exc_info=True)
            self.write({
                'state': 'error',
                'error_message': error_msg
            })

    def _update_business_field(self, mapping, value):
        self.ensure_one()
        try:
            model = self.env[mapping.business_model]
            field = mapping.business_field
            _logger.info(f"Starting update for {model._description}.{field} = {value}")
            # Find the correct MO by product and workcenter
            record = None
            if mapping.business_model == 'mrp.production':
                domain = [
                    ('state', 'in', ['confirmed', 'progress']),
                    ('product_id', '=', self.product_id.id)
                ]
                if self.workcenter_id:
                    domain.append(('workorder_ids.workcenter_id', '=', self.workcenter_id.id))
                record = model.search(domain, order='date_start desc', limit=1)
                if not record:
                    _logger.warning(f"No active MO found for product '{self.product_id.display_name}' and workcenter '{self.workcenter_id.name if self.workcenter_id else 'N/A'}'")
                    return False
                if field == 'qty_producing':
                    record.write({'qty_producing': value})
                    _logger.info(f"Updated MO {record.name} qty_producing to {value}")
                    return True
                elif field == 'qty_scrap':
                    # Always create a stock.scrap record when triggered
                    scrap = self.env['stock.scrap'].create({
                        'production_id': record.id,
                        'product_id': record.product_id.id,
                        'scrap_qty': value,
                        'product_uom_id': record.product_uom_id.id,
                        'origin': record.name,
                        'workorder_id': record.workorder_ids[:1].id if record.workorder_ids else False,
                    })
                    _logger.info(f"Created scrap record {scrap.name} with {value} units for MO {record.name}")
                    return True
                else:
                    # Try to write to any other field generically
                    try:
                        record.write({field: value})
                        _logger.info(f"Updated {model._name}.{field} to {value}")
                        return True
                    except Exception as e:
                        _logger.error(f"Update failed: {str(e)}", exc_info=True)
                        return False
            else:
                # For other models, just write generically to the first found record
                record = model.search([], limit=1)
                if record:
                    try:
                        record.write({field: value})
                        _logger.info(f"Updated {model._name}.{field} to {value}")
                        return True
                    except Exception as e:
                        _logger.error(f"Update failed: {str(e)}", exc_info=True)
                        return False
                else:
                    _logger.warning(f"No record found for model {model._name}")
                    return False
        except Exception as e:
            _logger.error(f"Update failed: {str(e)}", exc_info=True)
            self.env.cr.rollback()
            return False

    def action_view_related_mos(self):
        """Return an action to view related manufacturing orders."""
        self.ensure_one()
        domain = [
            ('state', 'in', ['confirmed', 'progress']),
            ('product_id', '=', self.product_id.id)
        ]
        if self.workcenter_id:
            domain.append(('workcenter_id', '=', self.workcenter_id.id))
            
        return {
            'name': _('Active Manufacturing Orders'),
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.production',
            'view_mode': 'tree,form',
            'domain': domain,
            'context': self.env.context
        }

    #for testing
    def test_mrp_update(self):
        """Test method to verify MRP integration"""
        for monitor in self:
            _logger.info(f"Testing monitor {monitor.name}")
            
            # Verify product and workcenter
            if not monitor.product_id:
                _logger.error("No product linked!")
                continue
                
            # Find target MO
            domain = [('product_id', '=', monitor.product_id.id), ('state', 'in', ['confirmed', 'progress'])]
            if monitor.workcenter_id:
                domain.append(('workorder_ids.workcenter_id', '=', monitor.workcenter_id.id))
                
            mo = self.env['mrp.production'].search(domain, limit=1, order='date_start desc')
            _logger.info(f"Found MO: {mo.name if mo else 'None'}")
            
            # Test quantity update
            if mo:
                _logger.info("Testing qty_producing update...")
                monitor._update_production_quantity(mo, min(10, mo.product_qty))
                
                _logger.info("Testing scrap creation...")
                monitor._update_scrap_quantity(mo, 1)

    def verify_mrp_linkage(self):
        """Debug method to verify MRP connections"""
        for monitor in self:
            _logger.info(f"\n=== Verifying Monitor: {monitor.name} ===")
            
            # Check product link
            if not monitor.product_id:
                _logger.error("❌ No product linked!")
                continue
                
            _logger.info(f"✅ Product: {monitor.product_id.name}")
            
            # Check work center
            wc_info = monitor.workcenter_id.name if monitor.workcenter_id else "Not set"
            _logger.info(f"ℹ️ Work Center: {wc_info}")
            
            # Find matching MOs
            domain = [
                ('product_id', '=', monitor.product_id.id),
                ('state', 'in', ['confirmed', 'progress'])
            ]
            if monitor.workcenter_id:
                domain.append(('workorder_ids.workcenter_id', '=', monitor.workcenter_id.id))
                
            mos = self.env['mrp.production'].search(domain)
            
            if not mos:
                _logger.warning(f"⚠️ No matching MOs found!")
                _logger.info(f"Search domain used: {domain}")
            else:
                _logger.info(f"🔍 Found {len(mos)} matching MO(s):")
                for mo in mos:
                    _logger.info(f" - {mo.name}: Qty={mo.qty_producing}/{mo.product_qty}, State={mo.state}, WC={[wo.workcenter_id.name for wo in mo.workorder_ids]}")
                    
            # Check mappings
            _logger.info("\n🔗 Business Mappings:")
            for mapping in monitor.business_mapping_ids:
                last_update_str = fields.Datetime.to_string(mapping.last_update_time) if mapping.last_update_time else "Never"
                _logger.info(f" - Register '{mapping.plc_register}' → {mapping.business_model}.{mapping.business_field} | Last Value: {mapping.last_value} at {last_update_str}")
    
    # Comment out the test method to avoid confusion
    # def test_business_logic_update(self):
    #     pass
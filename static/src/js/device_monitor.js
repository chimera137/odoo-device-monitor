odoo.define('device_monitor.form', function(require) {
    "use strict";

    var FormController = require('web.FormController');
    var FormView = require('web.FormView');
    var FormRenderer = require('web.FormRenderer');
    var core = require('web.core');
    var QWeb = core.qweb;
    var ajax = require('web.ajax');

    var DeviceMonitorFormRenderer = FormRenderer.extend({
        events: _.extend({}, FormRenderer.prototype.events, {
            'click .o_device_refresh': '_onRefreshClick',
            'click .o_device_toggle_polling': '_onTogglePollingClick',
            'click .o_device_set_threshold': '_onSetThresholdClick',
            'click .o_device_set_alias': '_onSetAliasClick',
        }),

        _onRefreshClick: function(ev) {
            ev.preventDefault();
            this._refreshDevice();
        },

        _onTogglePollingClick: function(ev) {
            ev.preventDefault();
            var self = this;
            var deviceId = this.state.data.id;
            var isPolling = !this.state.data.is_polling;

            ajax.jsonRpc('/device_monitor/api/v1/devices/' + deviceId + '/polling', 'call', {
                is_polling: isPolling
            }).then(function() {
                self._refreshDevice();
            });
        },

        _onSetThresholdClick: function(ev) {
            ev.preventDefault();
            var self = this;
            var deviceId = this.state.data.id;
            var register = $(ev.currentTarget).data('register');
            var minValue = parseFloat($(ev.currentTarget).data('min'));
            var maxValue = parseFloat($(ev.currentTarget).data('max'));

            ajax.jsonRpc('/device_monitor/api/v1/devices/' + deviceId + '/thresholds', 'call', {
                thresholds: {
                    [register]: {
                        min: minValue,
                        max: maxValue
                    }
                }
            }).then(function() {
                self._refreshDevice();
            });
        },

        _onSetAliasClick: function(ev) {
            ev.preventDefault();
            var self = this;
            var deviceId = this.state.data.id;
            var register = $(ev.currentTarget).data('register');
            var alias = $(ev.currentTarget).data('alias');

            ajax.jsonRpc('/device_monitor/api/v1/devices/' + deviceId + '/aliases', 'call', {
                aliases: {
                    [register]: alias
                }
            }).then(function() {
                self._refreshDevice();
            });
        },

        _refreshDevice: function() {
            var self = this;
            var deviceId = this.state.data.id;

            ajax.jsonRpc('/device_monitor/api/v1/devices/' + deviceId, 'call', {})
                .then(function(data) {
                    self.state.data = data;
                    self._render();
                });
        },

        _render: function() {
            var self = this;
            return this._super.apply(this, arguments).then(function() {
                // Add custom rendering logic here
                self._updateStatus();
                self._updateValues();
                self._updateAlerts();
            });
        },

        _updateStatus: function() {
            var status = this.state.data.status;
            this.$('.o_device_status').removeClass('text-success text-danger text-warning')
                .addClass('text-' + (status === 'connected' ? 'success' : status === 'error' ? 'danger' : 'warning'))
                .text(status);
        },

        _updateValues: function() {
            var values = this.state.data.values || {};
            var aliases = this.state.data.register_aliases || {};
            var html = '';

            _.each(values, function(value, register) {
                var alias = aliases[register] || register;
                html += '<div class="o_device_value">';
                html += '<span class="o_device_register">' + alias + ':</span>';
                html += '<span class="o_device_value">' + value + '</span>';
                html += '</div>';
            });

            this.$('.o_device_values').html(html);
        },

        _updateAlerts: function() {
            var alerts = this.state.data.alerts || [];
            var html = '';

            _.each(alerts, function(alert) {
                html += '<div class="alert alert-warning">' + alert + '</div>';
            });

            this.$('.o_device_alerts').html(html);
        }
    });

    var DeviceMonitorFormView = FormView.extend({
        config: _.extend({}, FormView.prototype.config, {
            Renderer: DeviceMonitorFormRenderer,
        }),
    });

    core.form_registry.add('device_monitor_form', DeviceMonitorFormView);

    return DeviceMonitorFormView;
}); 
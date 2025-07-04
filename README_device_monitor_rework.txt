Device Monitor Module - Recommended Rework Plan
===============================================

Purpose:
--------
Transform the device_monitor module from a duplicate device registry into a true dashboard/monitor that aggregates and displays all devices from modbus_connector and opcua_connector.

Key Recommendations:
--------------------
1. **Do NOT duplicate device records.**
   - Remove the device.monitor model as a separate registry.
   - Instead, read directly from modbus.device and opcua.device models.

2. **Unified Dashboard View:**
   - Create a new model or use a computed model/view to aggregate all devices from both connectors.
   - Display device name, type (Modbus/OPC UA), status, last values, and alerts in a single list/kanban/dashboard view.
   - Allow filtering/grouping by device type, status, etc.

3. **Polling and Status:**
   - Show polling status and allow starting/stopping polling by calling the methods on the original modbus.device or opcua.device records.
   - Do not implement separate polling logic in device_monitor.

4. **Alerts and Thresholds:**
   - Display alert status by reading threshold/alert fields from the original device records.
   - Optionally, provide a summary of all active alerts across all devices.

5. **Actions:**
   - Provide actions (buttons) to view device details, start/stop polling, or jump to the original device record.

6. **No More Manual Device ID Input:**
   - Device Monitor should automatically list all devices from both connectors.
   - No need for the user to manually input device IDs.

7. **(Optional) API/Controller:**
   - If you want to expose a unified API, create a controller that queries both device models and returns a combined JSON response.

8. **Remove/Disable the 'Run Test' Button:**
   - Since device_monitor will not own device records, this button is no longer relevant.

Implementation Steps:
---------------------
- Remove the device.monitor model and related views.
- Create a new dashboard view (tree/list/kanban) that queries modbus.device and opcua.device.
- Add computed fields or helper methods to display unified status, values, and alerts.
- Add actions to interact with the original device records.
- Update the menu to point to the new dashboard view.

Focus on business integration first, then return to this rework when ready. 
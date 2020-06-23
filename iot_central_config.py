# user configurable values

id_scope = "<ID Scope found in IoT application - Administration -> Device connection page>"
device_id = "<Device ID can be either an application unique name or a pre-created device in IoT Central>"
group_symmetric_key = "<Shared Access Signature token found in IoT application - Administration -> Device connection page>"
device_symmetric_key = "<Device Primary Key found in the device details Connect popup window>"
model_identity = "<Model Identity found in Device templates -> Edit Identity -> Identity>"
use_websockets = True  # True to use web sockets for MQTT connection to get through firewall proxies
use_group_symmetric_key = False  # set true to use group_symmetric_key and false to use device_symmetric_key
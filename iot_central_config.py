# user configurable values

# IoT Central connection settings
id_scope = "<ID Scope found in IoT application - Administration -> Device connection page>"
device_id = "<Device ID can be either an application unique name or a pre-created device in IoT Central>"
model_identity = "<Model Identity found in Device templates -> Edit Identity -> Identity>"

# device symmetric key support - default
device_symmetric_key = "<Device Primary Key found in the device details Connect popup window>"

# group symmetric key support
use_group_symmetric_key = False  # set True to use group_symmetric_key and False to use device_symmetric_key
group_symmetric_key = "<Shared Access Signature token found in IoT application - Administration -> Device connection page>"

# X509 support
use_x509 = False  # set True to use X509 certificate authentication (use_group_symmetric_key must be set False)
x509_public_cert_file = "<location (relative to this file) of the public cert file in PEM format>"
x509_private_cert_file = "<location (relative to this file) of the private cert file in PEM format>"
x509_pass_phrase = "<pass phrase for the private cert file>"

# General config settings
use_websockets = True  # set True to use web sockets for MQTT connection to get through firewall proxies
use_cached_credentials = False  # True to use cached credentials to connect to IoT Hub

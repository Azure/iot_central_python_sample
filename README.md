# Iot_Central_Python_Sample
Interacting with Azure IoT Central using a device written in Python

uses the Azure IoT Native Python Device SDK details found here: https://github.com/Azure/azure-iot-sdk-python/tree/master/azure-iot-device

The code requires the use of Python version 3.7+ for optimal use

The code uses six library for detecting Q+[enter] key press to perform clean shutdown
 
install the libraries with: 

```
pip install azure-iot-device si
```

The capability model for IoT Central is in the file device-capability-model.json and should be loaded into the IoT Central application
Views will need to be created to see the telemetry, properties and commands

In the code add the necessary values for id_scope, device_symmetric_key or group_symmetric_key, device_id, model_identity 
and set use_websockets to true or false depending on if MQTT ports are blocked or not

Features enabled in this sample:
  * Supports DPS with cached DPS credentials (to file system) so a DPS call is not needed every connection
  * Supports symmetric key and X509 certificate DPS and hub connection
  * Supports using group symmetric key to generate a device symmetric key
  * if connection fails with cached credentials falls back to re-call DPS
  * Supports device side registration of the device in IoT Central with auto-association to a device model
  * Illustrates sending telemetry to IoT Central
  * Illustrates sending reported properties
  * Illustrates receiving desired properties and acknowledging them correctly back to IoT Central
  * Illustrates receiving direct methods and acknowledging them and returning a return value
  * Illustrates receiving Cloud to device (C2D) messages
  * Auto reconnects are handled by the Python device SDK

This sample application uses the device template model in the device-capability-model.json file.  This template should be imported into the IoT Central application, and appropriate views generated or created from the device template.

To use first open the iot_central_config.py file and enter in the necessary configuration information based on you IoT Central application

```python
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
use_cached_credentials = False # True to use cached credentials to connect to IoT Hub
```

After filling in the configuration information run the iot_central_sample.py file using:

```
python iot_central_sample.py
```

You should see similar output to the following from the application (pressing the Q key and enter will exit the application):

```
RegistrationStage(RequestAndResponseOperation): Op will transition into polling after interval 2.  Setting timer.
The complete registration result is abc123
iotc-6f3e7a04-1498-46cb-8af8-299e1cc4315c.azure-devices.net
initialAssignment
null
Press Q to quit
sending message: {"temp": 89.000000, "humidity": 32.000000}
Sending reported property: {'text': {'value': '6UiewI1SxpSzxI5lQjjqDyhUU0Ekmzrb'}}
Sending reported property: {'boolean': {'value': True}}
Sending reported property: {'number': {'value': 64}}
completed sending message
sending message: {"temp": 78.000000, "humidity": 42.000000}
completed sending message
sending message: {"temp": 70.000000, "humidity": 12.000000}
completed sending message
sending message: {"temp": 74.000000, "humidity": 42.000000}
completed sending message
Sending reported property: {'text': {'value': 'oGafYZ2c2601DRjONuD5G6y4FjCPuFGH'}}
sending message: {"temp": 94.000000, "humidity": 32.000000}
completed sending message
q
Quitting...
Disconnecting from IoT Hub
```
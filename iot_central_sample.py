
import os
import time
import asyncio
import base64
import hmac
import hashlib
import random
import json
import string
from six.moves import input


# uses the Azure IoT Device SDK for Python (Native Python libraries)
from azure.iot.device.aio import ProvisioningDeviceClient
from azure.iot.device.aio import IoTHubDeviceClient
from azure.iot.device import Message
from azure.iot.device import X509
from azure.iot.device import MethodResponse
from azure.iot.device import exceptions


# configurable values imported from iot_central_config.py module
from iot_central_config import *


# global variable declarations
provisioning_host = "global.azure-devices-provisioning.net"
device_client = None
terminate = False


# derives a symmetric device key for a device id using the group symmetric key
def derive_device_key(device_id, group_symmetric_key):
    message = device_id.encode("utf-8")
    signing_key = base64.b64decode(group_symmetric_key.encode("utf-8"))
    signed_hmac = hmac.HMAC(signing_key, message, hashlib.sha256)
    device_key_encoded = base64.b64encode(signed_hmac.digest())
    return device_key_encoded.decode("utf-8")


# cache the DPS registration values to a file - could be stored in any nonvolatile storage (file, flash, etc.)
def write_dps_cache_to_file(cache):
    with open('dpsCache.json', 'w') as f:
        json.dump(cache, f, sort_keys=True)


# reads the cached DPS registration values from a file
def read_dps_cache_from_file():
    with open('dpsCache.json', 'r') as f:
        cache = json.load(f)
    return cache


# define behavior for halting the application
def keyboard_monitor(killTasks):
    global terminate
    while not terminate:
        selection = input("Press Q to quit\n")
        if selection == "Q" or selection == "q":
            print("Quitting...")
            for task in killTasks:
                task.cancel()
            terminate = True


# coroutine that sends telemetry on a set frequency until terminated
async def send_telemetry(device_client, send_frequency):
    while not terminate:
        payload = '{"temp": %f, "humidity": %f}' % (random.randrange(60.0, 95.0), random.randrange(10.0, 100.0))
        print("sending message: %s" % (payload))
        msg = Message(payload)
        await device_client.send_message(msg)
        print("completed sending message")
        await asyncio.sleep(send_frequency)


# coroutine that sends reported properties on a set frequency until terminated
async def send_reportedProperty(device_client, key, dataType, send_frequency):
    while not terminate:
        value = None
        if dataType == "bool":
            value = random.choice([True, False])
        elif dataType == "number":
            value = random.randrange(0, 100)
        elif dataType == "string":
            value = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(32)])
        reported_payload = {key: {"value": value}}
        print("Sending reported property: {}".format(reported_payload))
        try:
            await device_client.patch_twin_reported_properties(reported_payload)
        except:
            print("error")
        await asyncio.sleep(send_frequency)


# builds the acknowledge reported property for a desired property from IoT Central
async def desired_ack(json_data, status_code, status_text):
    # respond with IoT Central confirmation
    key = list(json_data.keys())[0]
    if list(json_data.keys())[0] == "$version":
        key = list(json_data.keys())[1]

    reported_payload = {key:{"value":json_data[key]['value'],"statusCode":status_code,"status":status_text,"desiredVersion":json_data['$version']}}
    print(reported_payload)
    await device_client.patch_twin_reported_properties(reported_payload)


# coroutine that handles desired properties from IoT Central (or hub) until terminated
async def twin_patch_handler(device_client):
    while not terminate:
        patch = await device_client.receive_twin_desired_properties_patch()
        print("the data in the desired properties patch was: {}".format(patch))
        # acknowledge the desired property back to IoT Central
        await desired_ack(patch, 200, "completed")


async def direct_method_handler(device_client):
    while not terminate:
        method_request = (
            await device_client.receive_method_request()
        )  # Wait for unknown method calls
        print("executing direct method: %s(%s)" % (method_request.name, method_request.payload))

        method_response = None
        if method_request.name == "echo":
            # send response - echo back the payload
            method_response = MethodResponse.create_from_method_request(method_request, 200, method_request.payload)
        else:
            # send bad request status code
            method_response = MethodResponse.create_from_method_request(method_request, 400, "unknown command")

        await device_client.send_method_response(method_response)


async def message_listener(device_client):
    while not terminate:
        message = await device_client.receive_message()  # blocking call
        print("the data in the message received was ")
        print(message.data)
        print("custom properties are")
        print(message.custom_properties)
        print("content Type: {0}".format(message.content_type))
        print("")


# main function: looks for cached DPS information in the file dpsCache.json and uses it to do a direct connection to the IoT hub.
# if the connection fails it falls back to DPS to get new credentials and caches those.  
# Reconnects are handled by the underlying Python device SDK.
async def main():
    global device_client
    global device_symmetric_key

    random.seed()
    dps_registered = False
    connected = False
    connection_retry_count = 1
    x509 = None

    while (not connected): # and (connection_retry_count < 3):
        if use_cached_credentials and os.path.exists('dpsCache.json'):
            dps_cache = read_dps_cache_from_file()
            if dps_cache[2] == device_id:
                dps_registered = True
            else:
                os.remove('dpsCache.json')
                continue
        else:
            if use_x509:
                current_path = os.path.dirname(os.path.abspath(__file__))
                x509 = X509(
                    cert_file=os.path.join(current_path, x509_public_cert_file),
                    key_file=os.path.join(current_path, x509_private_cert_file),
                    pass_phrase=x509_pass_phrase
                )
                provisioning_device_client = ProvisioningDeviceClient.create_from_x509_certificate(
                    provisioning_host=provisioning_host,
                    registration_id=device_id,
                    id_scope=id_scope,
                    x509=x509,
                    websockets=use_websockets
                )
            else:
                if use_group_symmetric_key:
                    device_symmetric_key = derive_device_key(device_id, group_symmetric_key)

                provisioning_device_client = ProvisioningDeviceClient.create_from_symmetric_key(
                    provisioning_host=provisioning_host,
                    registration_id=device_id,
                    id_scope=id_scope,
                    symmetric_key=device_symmetric_key,
                    websockets=use_websockets
                )

            provisioning_device_client.provisioning_payload = '{"iotcModelId":"%s"}' % (model_identity)
            registration_result = None
            try:
                registration_result = await provisioning_device_client.register()
            except exceptions.CredentialError:
                print("Credential Error")
            except exceptions.ConnectionFailedError: 
                print("Connection Failed Error")
            except exceptions.ConnectionDroppedError: # error if the key is wrong
                print("Connection Dropped Error")
            except exceptions.ClientError as inst: # error if the device is blocked
                print("ClientError")
            except Exception:
                print("Unknown Exception")

            dps_cache = (device_symmetric_key, registration_result.registration_state.assigned_hub, registration_result.registration_state.device_id)
            if use_cached_credentials:
                write_dps_cache_to_file(dps_cache)

            print("The complete registration result is %s" % (registration_result.registration_state))
            if registration_result.status == "assigned":
                dps_registered = True

        if dps_registered:
            if use_x509:
                device_client = IoTHubDeviceClient.create_from_x509_certificate(
                    x509=x509,
                    hostname=registration_result.registration_state.assigned_hub,
                    device_id=registration_result.registration_state.device_id,
                )
            else:
                device_client = IoTHubDeviceClient.create_from_symmetric_key(
                    symmetric_key=dps_cache[0],
                    hostname=dps_cache[1],
                    device_id=dps_cache[2],
                    websockets=use_websockets
                )

        # connect
        try:
            await device_client.connect()
            connected = True
        except:
            print("Connection failed, retry %d of 3" % (connection_retry_count))
            if os.path.exists('dpsCache.json'):
                os.remove('dpsCache.json')
                dps_registered = False
            connection_retry_count = connection_retry_count + 1
        
    # add desired property listener
    twin_listener = asyncio.create_task(twin_patch_handler(device_client))

    # add direct method listener
    direct_method_listener = asyncio.create_task(direct_method_handler(device_client)) 

    # add C2D listener
    c2d_listener = asyncio.create_task(message_listener(device_client))

    # add tasks to send telemetry (every 5 seconds) and reported properties (every 20, 25, 30 seconds respectively)
    telemetry_loop = asyncio.create_task(send_telemetry(device_client, 5))
    reported_loop1 = asyncio.create_task(send_reportedProperty(device_client, "text", "string", 20))
    reported_loop2 = asyncio.create_task(send_reportedProperty(device_client, "boolean", "bool", 25))
    reported_loop3 = asyncio.create_task(send_reportedProperty(device_client, "number", "number", 30))
    keyboard_loop = asyncio.get_running_loop().run_in_executor(None, keyboard_monitor, [twin_listener, direct_method_listener, c2d_listener])

    #awit the tasks ending before exiting
    try:
        await asyncio.gather(twin_listener, c2d_listener, direct_method_listener, telemetry_loop, reported_loop1, reported_loop2, reported_loop3, keyboard_loop)
    except asyncio.CancelledError:
        pass # ignore the cancel actions on twin_listener and direct_method_listener

    # finally, disconnect
    print("Disconnecting from IoT Hub")
    await device_client.disconnect()


# start the main routine
if __name__ == "__main__":
    asyncio.run(main())

    # If using Python 3.6 or below, use the following code instead of asyncio.run(main()):
    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(main())
    # loop.close()
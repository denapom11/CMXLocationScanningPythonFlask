#!flask/bin/python

"""
Cisco Meraki Location Scanning Receiver

A simple example demonstrating how to interact with the CMX API.

How it works:
- Meraki access points will listen for WiFi clients that are searching for a network to join and log the events.
- The "observations" are then collected temporarily in the cloud where additional information can be added to
the event, such as GPS, X Y coordinates and additional client details.
- Meraki will first send a GET request to this CMX receiver, which expects to receieve a "validator" key that matches
the Meraki network's validator.
- Meraki will then send a JSON message to this application's POST URL (i.e. http://yourserver/ method=[POST])
- The JSON is checked to ensure it matches the expected secret, version and observation device type.
- The resulting data is sent to the "save_data(data)" function where it can be sent to a databse or other service
    - This example will simply print the CMX data to the console.

Default port: 5000

Cisco Meraki CMX Documentation
https://documentation.meraki.com/MR/Monitoring_and_Reporting/CMX_Analytics#CMX_Location_API

Written by Cory Guynn
2016

www.InternetOfLEGO.com
"""

# Libraries
from pprint import pprint
from flask import Flask
from flask import json
from flask import request
from flask import render_template
import sys, getopt
import json
import requests
import shutil

############## USER DEFINED SETTINGS ###############
# MERAKI SETTINGS
#validator = "EnterYourValidator"
#secret = "EnterYourSecret"
#version = "2.0" # This code was written to support the CMX JSON version specified
locationdata = 'Location Data Holder'
mapImage = ''
####################################################


app = Flask(__name__)


# Respond to Meraki with validator
@app.route('/', methods=['GET'])
def get_validator():
    print("validator sent to: ",request.environ['REMOTE_ADDR'])
    return validator

# Accept CMX JSON POST
@app.route('/', methods=['POST'])
def get_locationJSON():
    global locationdata

    if not request.json or not 'data' in request.json:
        return("invalid data",400)
    locationdata = request.json
    pprint(locationdata, indent=1)
    print("Received POST from ",request.environ['REMOTE_ADDR'])

    # Verify secret
    if locationdata['secret'] != secret:
        print("secret invalid:", locationdata['secret'])
        return("invalid secret",403)
    else:
        print("secret verified: ", locationdata['secret'])

    # Verify version
    if locationdata['version'] != version:
        print("invalid version")
        return("invalid version",400)
    else:
        print("version verified: ", locationdata['version'])

    # Determine device type
    if locationdata['type'] == "DevicesSeen":
        print("WiFi Devices Seen")
    elif locationdata['type'] == "BluetoothDevicesSeen":
        print("Bluetooth Devices Seen")
    else:
        print("Unknown Device 'type'")
        return("invalid device type",403)

    # Return success message
    return "Location Scanning POST Received"

@app.route('/go', methods=['GET'])
def get_go():
    global url
    global username
    global password
    global locationdata
    global mapImage

    cmxlocationapi()

    mapImage = locationdata[0]["mapInfo"]["image"]["imageName"]
    print("this is the map " + mapImage)

    endpoint = "https://" + url + "/api/config/v1/maps/imagesource/" + mapImage
    print("trying " + endpoint)

    try:
        response = requests.request("GET", endpoint, auth=(username, password), stream=True)
        print("Got Map")

        with open("static/" + mapImage, 'wb') as f:
            response.raw.decode_content = True
            shutil.copyfileobj(response.raw, f)

    except Exception as e:
        print(e)

    return render_template('index.html', mapImage = mapImage)


def cmxlocationapi():
    global url
    global username
    global password
    global locationdata

    endpoint = "https://" + url + "/api/location/v2/clients"
    print("trying " + endpoint)
    mapImage = ''

    try:
        response = requests.request("GET", endpoint, auth=(username, password))
        print("got data")
        response = response.json()
        locationdata = response
        print(locationdata)
    except Exception as e:
        print(e)


@app.route('/clients/', methods=['GET'])
def get_clients():
    global locationdata

    cmxlocationapi()
    if locationdata != 'Location Data Holder':
        return json.dumps(locationdata)
    return ''


@app.route('/clients/<clientMac>', methods=['GET'])
def get_individualclients(clientMac):
    global locationdata

    cmxlocationapi()
    for client in locationdata:
        if client["macAddress"] == clientMac:
            return json.dumps(client)

    return ''

# Launch application with supplied arguments

def main(argv):
    global username
    global password
    global url


    try:
       opts, args = getopt.getopt(argv,"hu:p:l:",["username=","password=","url="])
    except getopt.GetoptError:
       print ('locationscanningreceiver.py -u <username> -p <password> -l <url>')
       sys.exit(2)
    for opt, arg in opts:
       if opt == '-h':
           print ('locationscanningreceiver.py -u <username> -p <password> -l <url>')
           sys.exit()
       elif opt in ("-u", "--username"):
           username  = arg
       elif opt in ("-p", "--password"):
           password = arg
       elif opt in ("-l", "--url"):
           url = arg

    print ('username: '+ username)
    print ('password: '+ password)
    print ('url: '+ url)


if __name__ == '__main__':
    main(sys.argv[1:])
    app.run(port=5001,debug=False)

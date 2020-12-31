import csv, minimalmodbus, ctypes, configparser
from datetime import datetime
from time import time, sleep 
from gpiozero import MCP3008

config = configparser.ConfigParser()
config.read('config.ini')

maxRecordId = int(config['DEFAULT']['CURRENT_MAX_RECORD_ID'])

def getFieldnames(numOfTiltmeters, numOfMirals):
    fieldnames = ['Id', 'Timestamp']

    for i in range(numOfMirals):
        fieldnames.append('Miral{}-Voltage'.format(i))
        fieldnames.append('Miral{}-Linear-Position'.format(i))

    for i in range(numOfTiltmeters):
        fieldnames.append('Tiltmeter{}-X-Angle'.format(i))
        fieldnames.append('Tiltmeter{}-Y-Angle'.format(i))
        fieldnames.append('Tiltmeter{}-Temperature'.format(i))

    return fieldnames

def getTiltmeters(numOfTiltmeters):
    tiltmeters = []
    port = config['DEFAULT']['TILTMETER_PORT']

    for id in range(1, numOfTiltmeters+1):
        instrument = minimalmodbus.Instrument(port, id)
        instrument.serial.baudrate = 9600
        tiltmeters.append(instrument)

    return tiltmeters

def getMirals(numOfMirals):
    mirals = []

    for id in range(numOfMirals):
        channel = MCP3008(id)
        mirals.append(channel)

    return mirals

def readTiltmeter(instrument):
    try:
        values = instrument.read_registers(2, 4)
        angles = list(map(lambda x: hex(x)[2:], values))

        x, y = angles[0] + angles[1], angles[2] + angles[3]
        x, y = int(x, 16), int(y, 16)
        x, y = ctypes.c_int32(x).value, ctypes.c_int32(y).value
        x, y = x/10000, y/10000

        values = instrument.read_registers(6, 2)

        x_temp, y_temp = list(map(lambda x: hex(x)[2:], values))
        x_temp, y_temp = int(x_temp, 16), int(y_temp, 16)
        x_temp, y_temp = ctypes.c_int16(x_temp).value, ctypes.c_int16(y_temp).value
        x_temp, y_temp = x_temp/100, y_temp/100
    
    except:
        return None

    data = {
        'Tiltmeter-X-Angle': x,
        'Tiltmeter-Y-Angle': y,
        'Tiltmeter-Temperature': x_temp
    }

    return data

def readMiral(channel):
    miralVolt = (channel.value / 1.0) * 5.0
    miralPos = 13.16 * miralVolt + 0.4175

    data = {
        'Miral-Voltage': miralVolt,
        'Miral-Linear-Position': miralPos
    }

    return data

def readSensors(tiltmeters, mirals):
    global maxRecordId
    maxRecordId += 1

    record = {
        'Id': maxRecordId,
        'Timestamp': datetime.now()
    }        

    for idx, instrument in enumerate(tiltmeters):
        values = readTiltmeter(instrument)             
        if values:
            record['Tiltmeter{}-X-Angle'.format(idx)] = values['Tiltmeter-X-Angle']
            record['Tiltmeter{}-Y-Angle'.format(idx)] = values['Tiltmeter-Y-Angle']
            record['Tiltmeter{}-Temperature'.format(idx)] = values['Tiltmeter-Temperature']
        else:
            record['Tiltmeter{}-X-Angle'.format(idx)] = None 
            record['Tiltmeter{}-Y-Angle'.format(idx)] = None
            record['Tiltmeter{}-Temperature'.format(idx)] = None

    for idx, channel in enumerate(mirals):
        values = readMiral(channel)
        record['Miral{}-Voltage'.format(idx)] = values['Miral-Voltage']
        record['Miral{}-Linear-Position'.format(idx)] = values['Miral-Linear-Position']

    return record

def saveFile(data, filename, fieldnames):
    with open(filename, mode='w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def main():
    numOfMirals = int(config['DEFAULT']['NUMBER_OF_MIRALS'])
    numOfTiltmeters = int(config['DEFAULT']['NUMBER_OF_TILTMETERS'])

    fieldnames = getFieldnames(numOfTiltmeters, numOfMirals)

    tiltmeters = getTiltmeters(numOfTiltmeters)
    mirals = getMirals(numOfMirals) 

    data = []
    current_timestamp = datetime.now()
    filename = 'records/{}.csv'.format(current_timestamp)
    start = time()

    while True:
        if time() - start >= int(config['DEFAULT']['SAVE_INTERVAL']):
            saveFile(data, filename, fieldnames)
            data = []
            current_timestamp = datetime.now()
            filename = 'records/{}.csv'.format(current_timestamp)
            start = time()

        record = readSensors(tiltmeters, mirals)
        data.append(record)
        
        sleep(int(config['DEFAULT']['READ_INTERVAL']))


if __name__ == "__main__":
    main()
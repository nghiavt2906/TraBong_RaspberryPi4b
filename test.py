import configparser

config = configparser.ConfigParser()
config.read('config.ini')

config.set('DEFAULT', 'CURRENT_MAX_RECORD_ID', str(99999999))

with open('config.ini', 'w') as configfile:
    config.write(configfile)
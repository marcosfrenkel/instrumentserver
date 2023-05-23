"""
If any instrument in the config does not have values for SERVERFIELDS or GUIFIELD, the values inside of it are added
to the config as defaults. If you are adding any extra fields to the config make sure to add the default values on those
variables since we parse the config using those.
"""
import io
import tempfile

import ruamel.yaml
from pathlib import Path

# Centralised point of extra fields for the server with its default as value
SERVERFIELDS = {'initialize': True}

# Extra fields for the GUI.
GUIFIELD = {'type': 'instrumentserver.gui.instruments.GenericInstrument', 'kwargs': {}}

def loadConfig(configPath: str):
    """
    Loads the config for the instrumentserver. From 1 config file it splits the respective fields into 3 different
    objects: a serverConfig (the configurations for the server), a stationConfig(the qcodes station config file clean
    of any extra config fields), and a GUI config file (any config that the GUI of the server needs).

    The qcodes station only accepts the path of an actual file for its config. So after loading the YAML file,
    the added fields are removed from the loaded dictionary. After that it is converted to a byte stream and written
    into a temporary file. what is returned here is the path to that temporary file, after the station loads the
    file, it gets deleted automatically
    """
    configPath = Path(configPath)
    serverConfig = {}  # Config for the server
    guiConfig = {}  # Individual gui config of each instrument
    fullConfig = {}  # serverConfig + guiConfig + any unfilled fields. Used for creating instruments from the gui

    yaml = ruamel.yaml.YAML()
    rawConfig = yaml.load(configPath)

    # Removing any extra fields
    for instrumentName, configDict in rawConfig['instruments'].items():
        serverConfig[instrumentName] = {}
        for field, default in SERVERFIELDS.items():
            if field in configDict:
                fieldSetting = configDict.pop(field)
                if fieldSetting is None:
                    raise AttributeError(f'"{field}" field cannot be None')
                serverConfig[instrumentName][field] = fieldSetting
            else:
                serverConfig[instrumentName][field] = default

        # we don't go through the entire gui because generic is a special setting
        # and we only have 2 different options for now
        if 'gui' in configDict:
            guiDict = configDict.pop('gui')
            if guiDict is None:
                raise AttributeError(f'"gui" field cannot be None')
            if 'type' in guiDict:
                if guiDict['type'] == 'generic' or guiDict['type'] == 'Generic':
                    guiDict['type'] = GUIFIELD['type']
            # If the user does not specify a gui, the default one will be used
            else:
                guiDict['type'] = GUIFIELD['type']

            guiConfig[instrumentName] = guiDict
        else:
            guiConfig[instrumentName] = GUIFIELD

        fullConfig[instrumentName] = {'gui': guiConfig[instrumentName], **configDict, **serverConfig[instrumentName]}

    # Creating the file like object
    with io.BytesIO() as ioBytesFile:
        yaml.dump(rawConfig, ioBytesFile)
        stationConfig = ioBytesFile.getvalue()

    # Storing the file like object in a temporary file to pass to the station config
    tempFile = tempfile.NamedTemporaryFile(delete=False)
    tempFile.write(stationConfig)
    tempFile.seek(0)
    tempFilePath = tempFile.name

    # You need to return the tempFile itself so that the garbage collector doesn't touch it
    return tempFilePath, serverConfig, fullConfig, tempFile

















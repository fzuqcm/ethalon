"""
Prepare global constants.
"""
INITIAL_FREQ = 10**7
INTERVAL_CALIB = 10**5
INTERVAL_HALF = 10**4 // 1
INTERVAL_STEP = 40
POLYFIT_COEFFICIENT = 0.95
DISSIPATION_PERCENT = 0.707
CSV_SEPARATOR = ','
DATE_SEPARATOR = '_'
RAW_DATA_SEPARATOR = ';'
OUTPUT_EXT = 'output'
RAW_DATA_EXT = 'txt'


class Status:
    """
    Available statuses of the device.
    """
    READY = 1
    CALIBRATING = 2
    CALIBRATED = 3
    CALIB_ERR = 4
    MEASURING = 5


class Command:
    """
    Supported commands for the firmware.
    """
    CALIBRATE = 'c'
    MEASURE = 'm'

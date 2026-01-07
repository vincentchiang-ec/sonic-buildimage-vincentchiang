#############################################################################
# Edgecore
#
# Thermal contains an implementation of SONiC Platform Base API and
# provides the thermal device status which are available in the platform
#
#############################################################################

import os
import os.path
import glob

try:
    from sonic_platform_base.thermal_base import ThermalBase
    from .helper import APIHelper
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

NUM_PORT = 56
THERMAL_PATH = "/sys/switch/sensor/temp"
XSFP_PATH = "/sys/switch/transceiver/eth"
CPU_TEMP_PATH = "/sys/bus/platform/drivers/coretemp/coretemp.0/hwmon/hwmon*/temp"
OFFSET_OF_CPU = (4-1) # 3:lm75 1:lsw 5:cpu
OFFSET_OF_XSFP = (9-1) # 3:lm75 1:lsw 5:cpu
XSFP_HIGH_CRITICAL_THRESHOLD = 75
XSFP_HIGH_THRESHOLD = 70
XSFP_LOW_CRITICAL_THRESHOLD = 0
XSFP_LOW_THRESHOLD = 0
CPU_HIGH_THRESHOLD = 95
CPU_HIGH_CRITICAL_THRESHOLD = 110
CPU_LOW_CRITICAL_THRESHOLD = 0

class Thermal(ThermalBase):
    """Platform-specific Thermal class"""

    THERMAL_NAME_LIST = []

    def __init__(self, thermal_index=0):
        self._api_helper = APIHelper()
        self.index = thermal_index
        # Add thermal name
        self.THERMAL_NAME_LIST.append("MAC Around")    #"7-004c/hwmon/hwmon*/"
        self.THERMAL_NAME_LIST.append("COMe bottom")   #"7-004b/hwmon/hwmon*/"
        self.THERMAL_NAME_LIST.append("Air Outlet")    #"7-004a/hwmon/hwmon*/"
        self.THERMAL_NAME_LIST.append("LSW_CORE")
        self.THERMAL_NAME_LIST.append("CPU_Package")  # cat /sys/bus/platform/drivers/coretemp/coretemp.0/hwmon/hwmon*/temp1_input
        self.THERMAL_NAME_LIST.append("CPU_CORE0")    # cat /sys/bus/platform/drivers/coretemp/coretemp.0/hwmon/hwmon*/temp2_input
        self.THERMAL_NAME_LIST.append("CPU_CORE1")    # cat /sys/bus/platform/drivers/coretemp/coretemp.0/hwmon/hwmon*/temp3_input
        self.THERMAL_NAME_LIST.append("CPU_CORE2")    # cat /sys/bus/platform/drivers/coretemp/coretemp.0/hwmon/hwmon*/temp4_input
        self.THERMAL_NAME_LIST.append("CPU_CORE3")    # cat /sys/bus/platform/drivers/coretemp/coretemp.0/hwmon/hwmon*/temp5_input

    def get_temperature(self):
        """
        Retrieves current temperature reading from thermal
        Returns:
            A float number of current temperature in Celsius up to nearest thousandth
            of one degree Celsius, e.g. 30.125
        """
        if(self.index > OFFSET_OF_XSFP):
            index = self.index - OFFSET_OF_XSFP
            temp_path = "{}{}/{}".format(XSFP_PATH, index, 'temp_input')
            temp = self._api_helper.read_txt_file(temp_path)
        # elif(self.index > OFFSET_OF_CPU):
        #     index = self.index - OFFSET_OF_CPU
        #     temp_path_cmd = "cat {}{}{}".format(CPU_TEMP_PATH, index, '_input')
        #     ret, temp =  self._api_helper.run_command(temp_path_cmd)
        #     if ret == True:
        #         temp = float(temp)/1000
        #     else:
        #         temp = None
        else:
            index = self.index
            temp_path = "{}{}/{}".format(THERMAL_PATH, index, 'temp_input')
            temp = self._api_helper.read_txt_file(temp_path)

        if (temp is not None) and (temp != 'NA'):
            return float(temp)
        else:
            return 'N/A'

    def get_high_threshold(self):
        """
        Retrieves the high threshold temperature of thermal
        Returns:
            A float number, the high threshold temperature of thermal in Celsius
            up to nearest thousandth of one degree Celsius, e.g. 30.125
        """
        if(self.index > OFFSET_OF_XSFP):
            threshold = XSFP_HIGH_THRESHOLD
        # elif(self.index > OFFSET_OF_CPU):
        #     index = self.index - OFFSET_OF_CPU
        #     threshold = CPU_HIGH_THRESHOLD
            # temp_path_cmd = "cat {}{}{}".format(CPU_TEMP_PATH, index, '_max')
            # ret, threshold =  self._api_helper.run_command(temp_path_cmd)
            # if ret == True:
            #     threshold = float(threshold)/1000
            # else:
            #     threshold = None
        else:
            index = self.index
            threshold_path = "{}{}/{}".format(THERMAL_PATH, index, 'temp_max')
            threshold = self._api_helper.read_txt_file(threshold_path)

        if (threshold is not None) and (threshold != 'NA'):
            return float(threshold)
        else:
            return 'N/A'

    def get_high_critical_threshold(self):
        """
        Retrieves the high critical threshold temperature of thermal
        Returns:
            A float number, the high critical threshold temperature of thermal in Celsius
            up to nearest thousandth of one degree Celsius, e.g. 30.125
        """
        if(self.index > OFFSET_OF_XSFP):
            threshold = XSFP_HIGH_CRITICAL_THRESHOLD
        # elif(self.index > OFFSET_OF_CPU):
        #     index = self.index - OFFSET_OF_CPU
        #     threshold = CPU_HIGH_CRITICAL_THRESHOLD
            # temp_path_cmd = "cat {}{}{}".format(CPU_TEMP_PATH, index, '_crit')
            # ret, threshold =  self._api_helper.run_command(temp_path_cmd)
            # if ret == True:
            #     threshold = float(threshold)/1000
            # else:
            #     threshold = None
        else:
            index = self.index
            threshold_path = "{}{}/{}".format(THERMAL_PATH, index, 'temp_max_crit')
            threshold = self._api_helper.read_txt_file(threshold_path)
            if (threshold is not None) and (threshold != 'NA'):
                threshold = float(threshold)

        if (threshold is not None) and (threshold != 'NA'):
            return float(threshold)
        else:
            return 'N/A'


    def get_name(self):
        """
        Retrieves the name of the thermal device
            Returns:
            string: The name of the thermal device
        """
        if(self.index > OFFSET_OF_XSFP):
            name = "{}{}".format("xSFP Module ", self.index - OFFSET_OF_XSFP)
        else:
            name_path = "{}{}/{}".format(THERMAL_PATH, self.index, 'temp_alias')
            name = self._api_helper.read_txt_file(name_path)
            if name is None or name == 'NA':
                return 'N/A'
            # name = self.THERMAL_NAME_LIST[self.index]
        return name

    def get_presence(self):
        """
        Retrieves the presence of the Thermal
        Returns:
            bool: True if Thermal is present, False if not
        """
        if(self.index > OFFSET_OF_XSFP):
            index = self.index - OFFSET_OF_XSFP
            thermal_index_path = "{}{}".format(XSFP_PATH, index)
            status_path = "{}{}/{}".format(XSFP_PATH, index, 'present')
        # elif(self.index > OFFSET_OF_CPU):
        #     index = self.index - OFFSET_OF_CPU
        #     thermal_index_path = "{}{}{}".format(CPU_TEMP_PATH, index, '_input')
        #     if os.path.exists(thermal_index_path):
        #         return True
        #     else:
        #         return False
        else:
            index = self.index
            thermal_index_path = "{}{}".format(THERMAL_PATH, index)
            status_path = "{}{}/{}".format(THERMAL_PATH, index, 'status')

        if os.path.isdir(thermal_index_path):
            thermal_status = self._api_helper.read_txt_file(status_path)
            if (thermal_status is None) or (thermal_status == 'NA'):
                return False
            return True
        else:
            return False

    def get_status(self):
        """
        Retrieves the operational status of the device
        Returns:
            A boolean value, True if device is operating properly, False if not
        """
        if(self.index > OFFSET_OF_XSFP):
            return self.get_presence()
        # elif(self.index > OFFSET_OF_CPU):
        #     return self.get_presence()
        else:
            index = self.index
            status_path = "{}{}/{}".format(THERMAL_PATH, index, 'status')
            thermal_status = self._api_helper.read_txt_file(status_path)
            if thermal_status is not None and (thermal_status != 'NA'):
                if int(thermal_status, 0) == 0:
                    return True
                else:
                    return False
            else:
                return False

    def get_low_threshold(self):
        """
        Retrieves the low threshold temperature of thermal

        Returns:
            A float number, the low threshold temperature of thermal in Celsius
            up to nearest thousandth of one degree Celsius, e.g. 30.125
        """
        if(self.index > OFFSET_OF_XSFP):
            threshold = XSFP_LOW_THRESHOLD
        # elif(self.index > OFFSET_OF_CPU):
        #     threshold = CPU_LOW_CRITICAL_THRESHOLD
        else:
            index = self.index
            threshold_path = "{}{}/{}".format(THERMAL_PATH, index, 'temp_min')
            threshold = self._api_helper.read_txt_file(threshold_path)
        if threshold is None or threshold == 'NA':
            return 'N/A'
        else:
            return float(threshold)

    def get_low_critical_threshold(self):
        """
        Retrieves the low critical threshold temperature of thermal
        Returns:
            A float number, the low critical threshold temperature of thermal in Celsius
            up to nearest thousandth of one degree Celsius, e.g. 30.125
        """
        if(self.index > OFFSET_OF_XSFP):
            threshold = XSFP_LOW_CRITICAL_THRESHOLD
        # elif(self.index > OFFSET_OF_CPU):
        #     threshold = CPU_LOW_CRITICAL_THRESHOLD
        else:
            index = self.index
            threshold_path = "{}{}/{}".format(THERMAL_PATH, index, 'temp_min_crit')
            threshold = self._api_helper.read_txt_file(threshold_path)
        if threshold == 'NA':
            return 'N/A'
        else:
            return float(threshold)


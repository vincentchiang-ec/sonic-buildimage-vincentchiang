#############################################################################
# Edgecore
#
# Module contains an implementation of SONiC Platform Base API and
# provides the PSUs status which are available in the platform
#
#############################################################################

#import sonic_platform

from re import T


try:
    from sonic_platform_base.psu_base import PsuBase
    from .helper import APIHelper
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

PSU_STATUS_ABSENT = 0
PSU_STATUS_OK = 1
PSU_STATUS_NOT_OK = 2
PSU_INDEX_START = 1

S3IP_LED_DARK =         0
S3IP_LED_GREEN =        1
S3IP_LED_RED =          3
S3IP_LED_GREEN_BLINK =  5
S3IP_LED_RED_BLINK =    7

PSU_DRV_PATH ="/sys/switch/psu/psu{}/"

PSU_NAME_LIST = ["PSU-1", "PSU-2"]
PSU_NUM_FAN = [1, 1]
PSU_HWMON_I2C_MAPPING = {
    0: {
        "num": 1,
        "addr": "5a"
    },
    1: {
        "num": 2,
        "addr": "58"
    },
}

class Psu(PsuBase):
    """Platform-specific Psu class"""

    def __init__(self, psu_index=0):
        PsuBase.__init__(self)
        self.index = psu_index
        self._api_helper = APIHelper()

        self.i2c_num = PSU_HWMON_I2C_MAPPING[self.index]["num"]
        self.i2c_addr = PSU_HWMON_I2C_MAPPING[self.index]["addr"]
        # self.hwmon_path = PSU_DRV_PATH.format(self.i2c_num, self.i2c_addr)
        self.hwmon_path = PSU_DRV_PATH.format(self.index + PSU_INDEX_START)
        # self.i2c_num = PSU_CPLD_I2C_MAPPING[self.index]["num"]
        # self.i2c_addr = PSU_CPLD_I2C_MAPPING[self.index]["addr"]
        # self.cpld_path = PSU_DRV_PATH.format(self.i2c_num, self.i2c_addr)
        # self.__initialize_fan()


    def __initialize_fan(self):
        from sonic_platform.fan import Fan
        for fan_index in range(0, PSU_NUM_FAN[self.index]):
            fan = Fan(fan_index, 0, is_psu_fan=True, psu_index=self.index)
            self._fan_list.append(fan)


    def get_voltage(self):
        """
        Retrieves current PSU voltage output
        Returns:
            A float number, the output voltage in volts,
            e.g. 12.1
        """
        vout_path = "{}{}".format(self.hwmon_path, 'out_vol')
        vout_val=self._api_helper.read_txt_file(vout_path)
        if (vout_val is not None) and (vout_val != 'NA'):
            return float(vout_val)
        else:
            return 0


    def get_current(self):
        """
        Retrieves present electric current supplied by PSU
        Returns:
            A float number, the electric current in amperes, e.g 15.4
        """
        iout_path = "{}{}".format(self.hwmon_path, 'out_curr')
        iout_val=self._api_helper.read_txt_file(iout_path)
        if (iout_val is not None) and (iout_val != 'NA'):
            return float(iout_val)
        else:
            return 0


    def get_power(self):
        """
        Retrieves current energy supplied by PSU
        Returns:
            A float number, the power in watts, e.g. 302.6
        """
        pout_path = "{}{}".format(self.hwmon_path, 'out_power')
        pout_val=self._api_helper.read_txt_file(pout_path)
        if (pout_val is not None) and (pout_val != 'NA'):
            return float(pout_val)
        else:
            return 0


    def get_input_power(self):
        """
        Retrieves current energy supplied by PSU
        Returns:
            A float number, the power in watts, e.g. 302.6
        """
        pout_path = "{}{}".format(self.hwmon_path, 'in_power')
        pout_val=self._api_helper.read_txt_file(pout_path)
        if (pout_val is not None) and (pout_val != 'NA'):
            return float(pout_val)
        else:
            return 0


    def get_output_power(self):
        """
        Retrieves current energy supplied by PSU
        Returns:
            A float number, the power in watts, e.g. 302.6
        """
        pout_path = "{}{}".format(self.hwmon_path, 'out_power')
        pout_val=self._api_helper.read_txt_file(pout_path)
        if (pout_val is not None) and (pout_val != 'NA'):
            return float(pout_val)
        else:
            return 0


    def get_powergood_status(self):
        """
        Retrieves the powergood status of PSU
        Returns:
            A boolean, True if PSU has stablized its output voltages and passed all
            its internal self-tests, False if not.
        """
        return self.get_status()


    def set_status_led(self, color):
        """
        Sets the state of the PSU status LED
        Args:
            color: A string representing the color with which to set the PSU status LED
                   Note: Only support green and off
        Returns:
            bool: True if status LED state is set successfully, False if not
        """
        return False #Controlled by HW


    def get_status_led(self):
        """
        Gets the state of the PSU status LED
        Returns:
            A string, one of the predefined STATUS_LED_COLOR_* strings above
        """
        led_status_path = "{}{}".format(self.hwmon_path, 'led_status')
        led_status_val = self._api_helper.read_txt_file(led_status_path)
        if (led_status_val is None) or (led_status_val == 'NA'):
            return self.STATUS_LED_COLOR_OFF
        return {
            S3IP_LED_DARK: self.STATUS_LED_COLOR_OFF,
            S3IP_LED_GREEN: self.STATUS_LED_COLOR_GREEN,
            S3IP_LED_RED: self.STATUS_LED_COLOR_RED,
            S3IP_LED_GREEN_BLINK: "green blink",
            S3IP_LED_RED_BLINK: "red blink"
        }.get(int(led_status_val), self.STATUS_LED_COLOR_OFF)


    def get_temperature(self):
        """
        Retrieves current temperature reading from PSU
        Returns:
            A float number of current temperature in Celsius up to nearest thousandth
            of one degree Celsius, e.g. 30.125
        """
        temp0_path = "{}{}".format(self.hwmon_path, 'temp0/temp_input')
        temp0_val = self._api_helper.read_txt_file(temp0_path)
        if (temp0_val is not None) and (temp0_val != 'NA'):
            return float(temp0_val)
        else:
            return False


    def get_temperature_high_threshold(self):
        """
        Retrieves the high threshold temperature of PSU
        Returns:
            A float number, the high threshold temperature of PSU in Celsius
            up to nearest thousandth of one degree Celsius, e.g. 30.125
        """
        temp0_path = "{}{}".format(self.hwmon_path, 'temp0/temp_max')
        temp0_max = self._api_helper.read_txt_file(temp0_path)
        if (temp0_max is not None) and (temp0_max != 'NA'):
            return float(temp0_max)
        else:
            return False


    def get_voltage_high_threshold(self):
        """
        Retrieves the high threshold PSU voltage output
        Returns:
            A float number, the high threshold output voltage in volts,
            e.g. 12.1
        """
        return float(13.0)


    def get_voltage_low_threshold(self):
        """
        Retrieves the low threshold PSU voltage output
        Returns:
            A float number, the low threshold output voltage in volts,
            e.g. 12.1
        """
        return float(11.0)


    def get_name(self):
        """
        Retrieves the name of the device
            Returns:
            string: The name of the device
        """
        return PSU_NAME_LIST[self.index]


    def get_presence(self):
        """
        Retrieves the presence of the PSU
        Returns:
            bool: True if PSU is present, False if not
        """
        psu_status_path = "{}{}".format(self.hwmon_path, 'status')
        psu_status = self._api_helper.read_txt_file(psu_status_path)
        if (psu_status is not None) and (psu_status != 'NA'):
            if int(psu_status) == PSU_STATUS_ABSENT:
                return False
            else:
                return True
        else:
            return False


    def get_status(self):
        """
        Retrieves the operational status of the device
        Returns:
            A boolean value, True if device is operating properly, False if not
        """
        psu_status_path = "{}{}".format(self.hwmon_path, 'status')
        psu_status = self._api_helper.read_txt_file(psu_status_path)
        if (psu_status is not None) and (psu_status != 'NA'):
            if int(psu_status) == PSU_STATUS_OK:
                return True
            else:
                return False
        else:
            return False


    def get_model(self):
        """
        Retrieves the psu model name
        Returns:
            A string value, model name
        """
        model_name_path = "{}{}".format(self.hwmon_path, 'model_name')
        model_name = self._api_helper.read_txt_file(model_name_path)
        if (model_name is not None) and (model_name != 'NA'):
            return model_name
        else:
            return 'NA'


    def get_serial(self):
        """
        Retrieves the psu serial number
        Returns:
            A string value, serial num
        """
        serial_number_path = "{}{}".format(self.hwmon_path, 'serial_number')
        serial_number = self._api_helper.read_txt_file(serial_number_path)
        if (serial_number is not None) and (serial_number != 'NA'):
            return serial_number
        else:
            return 'NA'


    def get_hw_version(self):
        """
        Retrieves the serial number of a power supply unit (PSU) defined
                by 1-based index <idx>
        :param idx: An integer, 1-based index of the PSU of which to query serial number
        :return: String, denoting serial number of the PSU unit
        """
        hardware_version_path = "{}{}".format(self.hwmon_path, 'hardware_version')
        hardware_version = self._api_helper.read_txt_file(hardware_version_path)
        if (hardware_version is not None) and (hardware_version != 'NA'):
            return hardware_version
        else:
            return 'NA'


    def get_sw_version(self):
        """
        Retrieves the serial number of a power supply unit (PSU) defined
                by 1-based index <idx>
        :param idx: An integer, 1-based index of the PSU of which to query serial number
        :return: String, denoting serial number of the PSU unit
        """
        #not support for this psu
        return 'NA'


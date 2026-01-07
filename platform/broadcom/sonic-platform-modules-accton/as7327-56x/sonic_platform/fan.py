#############################################################################
# Edgecore
#
# Module contains an implementation of SONiC Platform Base API and
# provides the fan status which are available in the platform
#
#############################################################################


try:
    from sonic_platform_base.fan_base import FanBase
    from .helper import APIHelper
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

FAN_INDEX_START = 1
MOTOR_INDEX_START = 0
PSU_INDEX_START = 1

FAN_STATUS_ABSENT = 0
FAN_STATUS_OK = 1
FAN_STATUS_NOT_OK = 2
PSU_STATUS_ABSENT = 0
PSU_STATUS_OK = 1
PSU_STATUS_NOT_OK = 2

S3IP_LED_DARK =         0
S3IP_LED_GREEN =        1
S3IP_LED_RED =          3
S3IP_LED_GREEN_BLINK =  5
S3IP_LED_RED_BLINK =    7

FAN_DIR_F2B = 1
FAN_DIR_B2F = 0

PSU_FAN_MAX_RPM = 23000

FAN_DRV_PATH = "/sys/switch/fan/fan{}/{}"
FAN_MOTOR_DRV_PATH = "/sys/switch/fan/fan{}/motor{}/{}"

PSU_DRV_PATH = "/sys/switch/psu/psu{}/{}"

PSU_I2C_MAPPING = {
    0: {
        "num": 1,
        "addr": "5a"
    },
    1: {
        "num": 2,
        "addr": "58"
    },
}

FAN_NAME_LIST = ["FAN-1F", "FAN-1R", "FAN-2F", "FAN-2R",
                 "FAN-3F", "FAN-3R", "FAN-4F", "FAN-4R"]

FAN_MOTOR_FRONT = 0
FAN_MOTOR_REAR  = 1
LOW_SPEED_PART_NUMBER = "GFB0412EHS-DB6H"
HIGH_SPEED_PART_NUMBER = "DFPK0456B2GY0R5"
FAN_DEFAULT_TOLERANCE = 10
FAN_TYPE_SPEED_THRESHOLD = {
    HIGH_SPEED_PART_NUMBER:{ #F2B
        FAN_MOTOR_FRONT: {
            0  :0,
            30 :8910,
            40 :11880,
            50 :14850,
            60 :17820,
            70 :20790,
            80 :23760,
            90 :26730,
            100:29700
        },
        FAN_MOTOR_REAR: {
            0  :0,
            30 :7410,
            40 :9880,
            50 :12350,
            60 :14820,
            70 :17290,
            80 :19760,
            90 :22230,
            100:24700
        },
    },
    LOW_SPEED_PART_NUMBER:{ #F2B
        FAN_MOTOR_FRONT: {
            0  :0,
            30 :5100,
            40 :7500,
            50 :9420,
            60 :11430,
            70 :13350,
            80 :15300,
            90 :17100,
            100:19110
        },
        FAN_MOTOR_REAR: {
            0  :0,
            30 :4800,
            40 :6990,
            50 :8730,
            60 :10500,
            70 :12360,
            80 :14100,
            90 :15840,
            100:17790
        },
    },
}
fan_speed_threshold = FAN_TYPE_SPEED_THRESHOLD.get(HIGH_SPEED_PART_NUMBER)

class Fan(FanBase):
    """Platform-specific Fan class"""

    def __init__(self, fan_tray_index, fan_index=0, is_psu_fan=False, psu_index=0):
        self._api_helper=APIHelper()
        self.fan_motor_index = fan_index + MOTOR_INDEX_START
        self.fan_tray_index = fan_tray_index + FAN_INDEX_START

        self.is_psu_fan = is_psu_fan
        if self.is_psu_fan:
            self.psu_index = psu_index + PSU_INDEX_START
            self.psu_i2c_num = PSU_I2C_MAPPING[psu_index]['num']
            self.psu_i2c_addr = PSU_I2C_MAPPING[psu_index]['addr']
            # self.psu_hwmon_path = PSU_DRV_PATH.format(self.psu_index)
        FanBase.__init__(self)


    def get_direction(self):
        """
        Retrieves the direction of fan
        Returns:
            A string, either FAN_DIRECTION_INTAKE or FAN_DIRECTION_EXHAUST
            depending on fan direction
        """
        direction = self.FAN_DIRECTION_EXHAUST

        if not self.is_psu_fan: #For FAN
            direction_path = FAN_DRV_PATH.format(self.fan_tray_index, 'direction')
            fan_direction = self._api_helper.read_txt_file(direction_path)
            if (fan_direction is not None) and (fan_direction != 'NA'):
                if int(fan_direction) == FAN_DIR_F2B:
                    direction = self.FAN_DIRECTION_EXHAUST
                elif int(fan_direction) == FAN_DIR_B2F:
                    direction = self.FAN_DIRECTION_INTAKE
                else:
                    direction = 'NA'
        else: #For PSU
            direction = self.FAN_DIRECTION_EXHAUST

        return direction

    def _rpm_to_pwm(self, rpm):
        if not self.is_psu_fan: #For FAN
            global fan_speed_threshold
            # index = self.fan_motor_index
            motor_num = self.fan_motor_index

            fan_speed_threshold_dict = fan_speed_threshold.get(motor_num)
            if fan_speed_threshold_dict is None:
                return 0
            if rpm >= max(fan_speed_threshold_dict.values()):
                return 100

            pwm = 0
            pwm_list = fan_speed_threshold_dict.keys()
            pwm_list = sorted(pwm_list)
            for index in range(len(pwm_list) - 1):
                pwm_low = pwm_list[index]
                pwm_high = pwm_list[index + 1]

                rpm_low = fan_speed_threshold_dict.get(pwm_list[index])
                rpm_high = fan_speed_threshold_dict.get(pwm_list[index + 1])
                if rpm_low is None or rpm_high is None:
                    return 0
                if rpm == rpm_high:
                    pwm = pwm_list[index + 1]
                    break
                if rpm > rpm_low and rpm < rpm_high:
                    pwm = pwm_list[index]
                    offset = (rpm-rpm_low)*(pwm_high-pwm_low)/(rpm_high-rpm_low)
                    pwm += int(offset)
        else:#for psu
            pwm = int(100*rpm/PSU_FAN_MAX_RPM)

        if (pwm >= 100) and (pwm < 110):
            pwm = 100
        return pwm

    def get_speed(self):
        """
        Retrieves the speed of fan as a percentage of full speed
        Returns:
            An integer, the percentage of full fan speed, in the range 0 (off)
                 to 100 (full speed)
        """
        speed = 0

        if not self.is_psu_fan: #For FAN

            status = self.get_status()
            if(status == False):
                rpm_path = FAN_MOTOR_DRV_PATH.format(self.fan_tray_index, self.fan_motor_index, 'speed')
            else:
                rpm_path = FAN_MOTOR_DRV_PATH.format(self.fan_tray_index, self.fan_motor_index, 'speed_target')
            rpm_str = self._api_helper.read_txt_file(rpm_path)
            if (rpm_str is not None) and (rpm_str != 'NA'):
                speed = int(rpm_str, 10)
                speed_pwm = self._rpm_to_pwm(speed)
            else:
                return 0

        else: #For PSU
            psu_fan_path = PSU_DRV_PATH.format(self.psu_index, 'fan_speed')
            psu_fan_speed_rpm = self._api_helper.read_txt_file(psu_fan_path)
            if (psu_fan_speed_rpm is not None) and (psu_fan_speed_rpm != 'NA'):
                speed = int(float(psu_fan_speed_rpm))
                speed_pwm = self._rpm_to_pwm(speed)
            else:
                return 0

        return int(speed_pwm)


    def get_target_speed(self):
        """
        Retrieves the target (expected) speed of the fan
        Returns:
            An integer, the percentage of full fan speed, in the range 0 (off)
                 to 100 (full speed)

        Note:
            speed_pc = pwm_target/255*100

            0   : when PWM mode is use
            pwm : when pwm mode is not use
        """
        speed_target = 0

        if not self.is_psu_fan: #For FAN
            rpm_path = FAN_MOTOR_DRV_PATH.format(self.fan_tray_index, self.fan_motor_index, 'speed_target')
            rpm_str = self._api_helper.read_txt_file(rpm_path)
            if (rpm_str is not None) and (rpm_str != 'NA'):
                speed_target = int(rpm_str, 10)
                speed_target_pwm = self._rpm_to_pwm(speed_target)
            else:
                return 0

        else: #For PSU
            psu_fan_path = PSU_DRV_PATH.format(self.psu_index, 'fan_speed')
            psu_fan_speed_rpm = self._api_helper.read_txt_file(psu_fan_path)
            if (psu_fan_speed_rpm is not None) and (psu_fan_speed_rpm != 'NA'):
                speed_target = int(float(psu_fan_speed_rpm))
                speed_target_pwm = self._rpm_to_pwm(speed_target)
            else:
                return 0

        return int(speed_target_pwm)


    def get_speed_tolerance(self):
        """
        Retrieves the speed tolerance of the fan
        Returns:
            An integer, the percentage of variance from target speed which is
                 considered tolerable
        """
        speed_tolerance = FAN_DEFAULT_TOLERANCE
        """
        if not self.is_psu_fan: #For FAN
            rpm_path = FAN_MOTOR_DRV_PATH.format(self.fan_tray_index, self.fan_motor_index, 'speed_tolerance')
            rpm_str = self._api_helper.read_txt_file(rpm_path)
            if (rpm_str is not None) and (rpm_str != 'NA'):
                speed_tolerance = int(rpm_str, 10)
            else:
                return 0
        else: #For PSU
            psu_fan_path = PSU_DRV_PATH.format(self.psu_index, 'fan_speed')
            psu_fan_speed_rpm = self._api_helper.read_txt_file(psu_fan_path)
            if (psu_fan_speed_rpm is not None) and (psu_fan_speed_rpm != 'NA'):
                speed_tolerance = int(float(psu_fan_speed_rpm))/10
            else:
                return 0
        """
        return int(speed_tolerance)


    def set_speed(self, speed):
        """
        Sets the fan speed
        Args:
            speed: An integer, the percentage of full fan speed to set fan to,
                   in the range 0 (off) to 100 (full speed)
        Returns:
            A boolean, True if speed is set successfully, False if not
        """
        pwm = int(speed)
        pwm = min(pwm, 100)
        pwm = max(pwm, 30)

        if not self.is_psu_fan and self.get_presence(): #For FAN
            speed_path = FAN_MOTOR_DRV_PATH.format( self.fan_tray_index, self.fan_motor_index, 'ratio')
            return self._api_helper.write_txt_file(speed_path, pwm)

        return False


    def set_status_led(self, color):
        """
        Sets the state of the fan module status LED
        Args:
            color: A string representing the color with which to set the
                   fan module status LED
        Returns:
            bool: True if status LED state is set successfully, False if not
        """
        return False #Not supported


    def get_status_led(self):
        """
        Gets the state of the fan status LED
        Returns:
            A string, one of the predefined STATUS_LED_COLOR_* strings above
        """
        if not self.is_psu_fan: #For FAN
            led_status_path = FAN_DRV_PATH.format(self.fan_tray_index, "led_status")
            led_status_str = self._api_helper.read_txt_file(led_status_path)

            if (led_status_str is not None) and (led_status_str != 'NA'):
                led_status = int(led_status_str)
                return {
                    S3IP_LED_RED: self.STATUS_LED_COLOR_RED,
                    S3IP_LED_GREEN: self.STATUS_LED_COLOR_GREEN,
                    S3IP_LED_DARK: self.STATUS_LED_COLOR_OFF
                }.get(led_status, self.STATUS_LED_COLOR_OFF)
            else:
                return self.STATUS_LED_COLOR_OFF
        else: #For PSU Not supported
            return "NA"


    def get_name(self):
        """
        Retrieves the name of the device
            Returns:
            string: The name of the device
        """
        if not self.is_psu_fan: #For FAN
            fan_name = FAN_NAME_LIST[(self.fan_tray_index-FAN_INDEX_START)*2 + self.fan_motor_index]
        else: #For PSU
            fan_name = "PSU-{} FAN-1".format(self.psu_index)

        return fan_name


    def get_presence(self):
        """
        Retrieves the presence of the FAN
        Returns:
            bool: True if FAN is present, False if not
        """
        if not self.is_psu_fan: #For FAN
            present_path = FAN_DRV_PATH.format(self.fan_tray_index, "status")
            present_str = self._api_helper.read_txt_file(present_path)
            if (present_str is not None) and (present_str != 'NA'):
                if int(present_str) == FAN_STATUS_ABSENT:
                    return False
                else:
                    return True
            else:
                return False
        else: #For PSU
            psu_status_path = PSU_DRV_PATH.format(self.psu_index, 'status')
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
        Retrieves the operational status of FAN defined
        :return: Boolean,
            - True if FAN is operating properly: FAN is inserted and powered in the device
            - False if FAN is faulty: FAN is inserted in the device but not powered
        """
        if not self.is_psu_fan: #For FAN
            status_path = FAN_DRV_PATH.format(self.fan_tray_index, "status")
            status_str = self._api_helper.read_txt_file(status_path)
            if (status_str is not None) and (status_str != 'NA'):
                if(int(status_str) == FAN_STATUS_OK):
                    return True
                else:
                    return False
            else:
                return False
        else: #For PSU
            psu_status_path = PSU_DRV_PATH.format(self.psu_index, 'status')
            psu_status = self._api_helper.read_txt_file(psu_status_path)
            if (psu_status is not None) and (psu_status != 'NA'):
                if(int(psu_status) == FAN_STATUS_OK):
                    return True
                else:
                    return False
            else:
                return False


    def get_model(self):
        """
        Retrieves the model number/name of a fan unit defined
                by 1-based index <idx>
        :param idx: An integer, 1-based index of the fan of which to query model number
        :return: String, denoting model number/name
        """
        if not self.is_psu_fan: #For FAN
            model_path = FAN_DRV_PATH.format(self.fan_tray_index, "model_name")
            model_str = self._api_helper.read_txt_file(model_path)
            if (model_str is not None) and (model_str != 'NA'):
                return model_str
            else:
                return 'NA'
        else: #For PSU
            psu_model_path = PSU_DRV_PATH.format(self.psu_index, 'model_name')
            psu_model_str = self._api_helper.read_txt_file(psu_model_path)
            if (psu_model_str is not None) and (psu_model_str != 'NA'):
                return psu_model_str
            else:
                return 'NA'


    def get_serial(self):
        """
        Retrieves the serial number of a fan defined
                by 1-based index <idx>
        :param idx: An integer, 1-based index of the fan of which to query serial number
        :return: String, denoting serial number of the fan unit
        """
        if not self.is_psu_fan: #For FAN
            serial_path = FAN_DRV_PATH.format(self.fan_tray_index, "serial_number")
            serial_str = self._api_helper.read_txt_file(serial_path)
            if (serial_str is not None) and (serial_str != 'NA'):
                return serial_str
            else:
                return 'NA'
        else: #For PSU
            psu_serial_path = PSU_DRV_PATH.format(self.psu_index, 'serial_number')
            psu_serial_str = self._api_helper.read_txt_file(psu_serial_path)
            if (psu_serial_str is not None) and (psu_serial_str != 'NA'):
                return psu_serial_str
            else:
                return 'NA'


    def get_hw_version(self):
        """
        Retrieves the hw_version of a fan defined
                by 1-based index <idx>
        :param idx: An integer, 1-based index of the fan of which to query hw_version
        :return: String, denoting hw_version of the fan unit
        """
        if not self.is_psu_fan: #For FAN
            hw_version_path = FAN_DRV_PATH.format(self.fan_tray_index, "hardware_version")
            hw_version_str = self._api_helper.read_txt_file(hw_version_path)
            if (hw_version_str is not None) and (hw_version_str != 'NA'):
                return hw_version_str
            else:
                return 'NA'
        else: #For PSU
            psu_hw_version_path = PSU_DRV_PATH.format(self.psu_index, 'hardware_version')
            psu_hw_version_str = self._api_helper.read_txt_file(psu_hw_version_path)
            if (psu_hw_version_str is not None) and (psu_hw_version_str != 'NA'):
                return psu_hw_version_str
            else:
                return 'NA'


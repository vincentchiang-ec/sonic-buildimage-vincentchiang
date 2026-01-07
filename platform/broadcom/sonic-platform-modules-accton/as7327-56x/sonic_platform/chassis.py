#############################################################################
# Edgecore
#
# Module contains an implementation of SONiC Platform Base API and
# provides the Chassis information which are available in the platform
#
#############################################################################

import os
import sys

try:
    from sonic_platform_base.chassis_base import ChassisBase
    from .helper import APIHelper
    from .event import SfpEvent
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

NUM_FAN_TRAY = 4
NUM_FAN = 2
NUM_PSU = 2
FANS_PER_PSU = 1
NUM_THERMAL = 65 #3:lm75 1:lsw 5:cpu 56:port
NUM_PORT = 56
NUM_COMPONENT = 5
HOST_REBOOT_CAUSE_PATH = "/host/reboot-cause/"
PMON_REBOOT_CAUSE_PATH = "/usr/share/sonic/platform/api_files/reboot-cause/"
REBOOT_CAUSE_FILE = "reboot-cause.txt"
PREV_REBOOT_CAUSE_FILE = "previous-reboot-cause.txt"
HOST_CHK_CMD = "docker > /dev/null 2>&1"
PANEL_LED_PATH = "/sys/switch/sysled/{}"

S3IP_LED_DARK =         0
S3IP_LED_GREEN =        1
S3IP_LED_RED =          3
S3IP_LED_GREEN_BLINK =  5
S3IP_LED_RED_BLINK =    7

class Chassis(ChassisBase):
    """Platform-specific Chassis class"""
    STATUS_LED_COLOR_GREEN = "green"
    STATUS_LED_COLOR_RED = "red"
    STATUS_LED_COLOR_RED_BLINK = "red blink"
    STATUS_LED_COLOR_GREEN_BLINK = "green blink"
    STATUS_LED_COLOR_OFF = "off"

    def __init__(self):
        ChassisBase.__init__(self)
        self._api_helper = APIHelper()
        self._api_helper = APIHelper()
        self.is_host = self._api_helper.is_host()

        self.config_data = {}

        #for support SONiC 201911
        # self.__initialize_fan()
        #for support SONiC 202012
        self.__initialize_fan_drawers()
        self.__initialize_psu()
        self.__initialize_thermals()
        self.__initialize_components()
        self.__initialize_sfp()
        self.__initialize_eeprom()
        self.__initialize_event()

    def __initialize_event(self):
        # SFP event
        if not self.sfp_module_initialized:
            self.__initialize_sfp()
        self._event = SfpEvent(self._sfp_list)
        self.event_module_initialized = True

    def __initialize_sfp(self):
        from sonic_platform.sfp import Sfp
        for index in range(0, NUM_PORT):
            sfp = Sfp(index)
            self._sfp_list.append(sfp)
        self.sfp_module_initialized = True

    def __initialize_fan(self):
        from sonic_platform.fan import Fan
        for fant_index in range(0, NUM_FAN_TRAY + NUM_PSU):
            #FAN
            if fant_index < NUM_FAN_TRAY:
                for fan_index in range(0, NUM_FAN):
                    fan = Fan(fant_index, fan_index)
                    self._fan_list.append(fan)
            #PSU FAN
            elif fant_index >= NUM_FAN_TRAY:
                for i in range(0, FANS_PER_PSU):
                    self._fan_list.append(Fan(fant_index, i, is_psu_fan=True, psu_index=fant_index-NUM_FAN_TRAY))

    def __initialize_fan_drawers(self):
        from sonic_platform.fan_drawers import FanDrawer
        for fant_index in range(0, NUM_FAN_TRAY + NUM_PSU):
            fan_drawer = FanDrawer(fant_index)
            self._fan_drawer_list.append(fan_drawer)

    def __initialize_psu(self):
        from sonic_platform.psu import Psu
        for index in range(0, NUM_PSU):
            psu = Psu(index)
            self._psu_list.append(psu)

    def __initialize_thermals(self):
        from sonic_platform.thermal import Thermal
        for index in range(0, NUM_THERMAL):
            thermal = Thermal(index)
            self._thermal_list.append(thermal)

    def __initialize_eeprom(self):
        from sonic_platform.eeprom import Tlv
        self._eeprom = Tlv()
        self.eeprom_initialized = True

    def __initialize_components(self):
        from sonic_platform.component import Component
        for index in range(0, NUM_COMPONENT):
            component = Component(index)
            self._component_list.append(component)

    def __initialize_watchdog(self):
        from sonic_platform.watchdog import Watchdog
        self._watchdog = Watchdog()


    def __is_host(self):
        return os.system(HOST_CHK_CMD) == 0

    def __read_txt_file(self, file_path):
        try:
            with open(file_path, 'r') as fd:
                data = fd.read()
                return data.strip()
        except IOError:
            pass
        return None

    def initizalize_system_led(self):
        return True

    ##############################################
    # Component methods
    ##############################################
    def get_all_components(self):
        """
        Retrieves all components available on this chassis

        Returns:
            A list of objects derived from ComponentBase representing all components
            available on this chassis
        """
        return self._component_list

    ##############################################
    # Fan methods
    ##############################################
    def get_all_fans(self):
        """
        Retrieves all fan modules available on this chassis

        Returns:
            A list of objects derived from FanBase representing all fan
            modules available on this chassis
        """
        return self._fan_list

    def get_all_fan_drawers(self):
        """
        Retrieves all fan drawers available on this chassis

        Returns:
            A list of objects derived from FanDrawerBase representing all fan
            drawers available on this chassis
        """
        return self._fan_drawer_list

    ##############################################
    # PSU methods
    ##############################################
    def get_all_psus(self):
        """
        Retrieves all power supply units available on this chassis

        Returns:
            A list of objects derived from PsuBase representing all power
            supply units available on this chassis
        """
        return self._psu_list

    ##############################################
    # THERMAL methods
    ##############################################
    def get_all_thermals(self):
        """
        Retrieves all thermals available on this chassis

        Returns:
            A list of objects derived from ThermalBase representing all thermals
            available on this chassis
        """
        return self._thermal_list

    def get_name(self):
        """
        Retrieves the name of the device
            Returns:
            string: The name of the device
        """
        return self._api_helper.hwsku

    def get_presence(self):
        """
        Retrieves the presence of the Chassis
        Returns:
            bool: True if Chassis is present, False if not
        """
        return True

    def get_status(self):
        """
        Retrieves the operational status of the device
        Returns:
            A boolean value, True if device is operating properly, False if not
        """
        return True

    def get_base_mac(self):
        """
        Retrieves the base MAC address for the chassis
        Returns:
            A string containing the MAC address in the format
            'XX:XX:XX:XX:XX:XX'
        """
        if not self.eeprom_initialized:
            self.__initialize_eeprom()
        return self._eeprom.get_mac()

    def get_model(self):
        """
        Retrieves the model number (or part number) of the device
        Returns:
            string: Model/part number of device
        """
        if not self.eeprom_initialized:
            self.__initialize_eeprom()
        return self._eeprom.get_pn()

    def get_serial(self):
        """
        Retrieves the hardware serial number for the chassis
        Returns:
            A string containing the hardware serial number for this chassis.
        """
        if not self.eeprom_initialized:
            self.__initialize_eeprom()
        return self._eeprom.get_serial()

    def get_serial_number(self):
        """
        Retrieves the hardware serial number for the chassis
        Returns:
            A string containing the hardware serial number for this chassis.
        """
        if not self.eeprom_initialized:
            self.__initialize_eeprom()
        return self._eeprom.get_serial()

    def get_system_eeprom_info(self):
        """
        Retrieves the full content of system EEPROM information for the chassis
        Returns:
            A dictionary where keys are the type code defined in
            OCP ONIE TlvInfo EEPROM format and values are their corresponding
            values.
        """
        if not self.eeprom_initialized:
            self.__initialize_eeprom()
        return self._eeprom.get_eeprom()

    # Possible reboot causes
    REBOOT_CAUSE_POWER_LOSS = "Power Loss"
    REBOOT_CAUSE_WATCHDOG = "Watchdog"
    REBOOT_CAUSE_HARDWARE_OTHER = "Hardware - Other"
    REBOOT_CAUSE_NON_HARDWARE = "Non-Hardware"
    REBOOT_CAUSE_CPU_WARM_RESET = "CPU warm reset"
    REBOOT_CAUSE_BMC_SHUTDOWN = "BMC shutdown"
    REBOOT_CAUSE_CPU_EC_NO_HB = "BIOS EC heart beat timeout"
    REBOOT_CAUSE_CPU_CPU_ERROR = "CPU error with S3 S4 no output"

    def get_reboot_cause(self):
        """
        Retrieves the cause of the previous reboot

        Returns:
            A tuple (string, string) where the first element is a string
            containing the cause of the previous reboot. This string must be
            one of the predefined strings in this class. If the first string
            is "REBOOT_CAUSE_HARDWARE_OTHER", the second string can be used
            to pass a description of the reboot cause.
        """
        hw_reboot_cause = self._api_helper.read_txt_file("/sys/switch/cpld/reboot_cause") or "Unknown"
        prev_reboot_cause = {
            '0': (self.REBOOT_CAUSE_NON_HARDWARE, 'Unknown'),
            '1': (self.REBOOT_CAUSE_HARDWARE_OTHER, self.REBOOT_CAUSE_POWER_LOSS),
            '6': (self.REBOOT_CAUSE_HARDWARE_OTHER, self.REBOOT_CAUSE_WATCHDOG),
            '9': (self.REBOOT_CAUSE_CPU_WARM_RESET, ''),
            '12': (self.REBOOT_CAUSE_BMC_SHUTDOWN, ''),
            '15': (self.REBOOT_CAUSE_HARDWARE_OTHER, self.REBOOT_CAUSE_CPU_EC_NO_HB),
            '16': (self.REBOOT_CAUSE_HARDWARE_OTHER, self.REBOOT_CAUSE_CPU_CPU_ERROR)
        }.get(hw_reboot_cause, (self.REBOOT_CAUSE_NON_HARDWARE, 'Unknown'))

        return prev_reboot_cause

    def get_change_event(self, timeout=0):
        # SFP event
        if not self.event_module_initialized:
            self.__initialize_event()
        status, sfp_event = self._event.get_sfp_event(timeout)

        return status, sfp_event

    def get_sfp(self, index):
        """
        Retrieves sfp represented by (1-based) index <index>
        Args:
            index: An integer, the index (1-based) of the sfp to retrieve.
            The index should be the sequence of a physical port in a chassis,
            starting from 1.
            For example, 1 for Ethernet0, 2 for Ethernet4 and so on.
        Returns:
            An object dervied from SfpBase representing the specified sfp
        """
        sfp = None
        if not self.sfp_module_initialized:
            self.__initialize_sfp()

        try:
            # The index will start from 1
            sfp = self._sfp_list[index-1]
        except IndexError:
            sys.stderr.write("SFP index {} out of range (1-{})\n".format(
                             index, len(self._sfp_list)))
        return sfp

    ##############################################
    # System LED methods
    ##############################################

    def set_status_led(self, color):
        """
        Sets the state of the system LED

        Args:
            color: A string representing the color with which to set the
                   system LED

        Returns:
            bool: True if system LED state is set successfully, False if not
        """
        return False #Not supported

    def get_status_led(self):
        """
        Gets the state of the system LED

        Returns:
            A string, one of the valid LED color strings which could be vendor
            specified.
        """

        led_status_path = PANEL_LED_PATH.format("sys_led_status")
        led_status_str = self._api_helper.read_txt_file(led_status_path)

        if (led_status_str is not None) and (led_status_str.strip() != 'NA'):
            led_status = int(led_status_str)
            return {
                S3IP_LED_RED: self.STATUS_LED_COLOR_RED,
                S3IP_LED_GREEN: self.STATUS_LED_COLOR_GREEN,
                S3IP_LED_RED_BLINK: self.STATUS_LED_COLOR_RED_BLINK,
                S3IP_LED_GREEN_BLINK: self.STATUS_LED_COLOR_GREEN_BLINK,
                S3IP_LED_DARK: self.STATUS_LED_COLOR_OFF
            }.get(led_status, self.STATUS_LED_COLOR_OFF)
        return 'N/A'
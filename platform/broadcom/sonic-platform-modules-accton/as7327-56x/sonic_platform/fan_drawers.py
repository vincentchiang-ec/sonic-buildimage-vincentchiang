#!/usr/bin/env python

########################################################################
#
# Module contains an implementation of SONiC Platform Base API and
# provides the Fan-Drawers' information available in the platform.
#
########################################################################

try:
    from sonic_platform_base.fan_drawer_base import FanDrawerBase
    from sonic_platform.fan import Fan
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

NUM_FAN = 2
FANS_PER_PSU = 1
NUM_FAN_TRAY = 4

class FanDrawer(FanDrawerBase):
    """Platform-specific Fan class"""

    def __init__(self, fantray_index):

        FanDrawerBase.__init__(self)

        self.fantrayindex = fantray_index
        #FAN
        if fantray_index < NUM_FAN_TRAY:
            for i in range(0, NUM_FAN):
                self._fan_list.append(Fan(fantray_index, i))

        #2PSU each PSU has one fan
        if fantray_index >= NUM_FAN_TRAY:
            for i in range(0, FANS_PER_PSU):
                self._fan_list.append(Fan(fantray_index, i, is_psu_fan=True, psu_index=fantray_index-NUM_FAN_TRAY))

    def get_name(self):
        """
        Retrieves the fan drawer name
        Returns:
            string: The name of the device
        """
        return "FanTray {}".format(self.fantrayindex)

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

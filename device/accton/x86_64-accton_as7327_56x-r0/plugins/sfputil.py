# sfputil.py
#
# Platform-specific SFP transceiver interface for SONiC
#

try:
    import time
    import string
    import pprint
    from ctypes import create_string_buffer
    from sonic_sfp.sfputilbase import SfpUtilBase
except ImportError as e:
    raise ImportError("%s - required module not found" % str(e))

#from xcvrd
SFP_STATUS_REMOVED = '0'
SFP_STATUS_INSERTED = '1'
MIN_WAIT_TIME = 200 # 0.2 sec

class SfpUtil(SfpUtilBase):
    """Platform-specific SfpUtil class"""

    PORT_START = 1
    PORT_END = 56
    PORTS_IN_BLOCK = 56
    QSFP_DD_PORT_START = 1
    QSFP_DD_PORT_END = 56

    _port_to_is_present = {}
    _port_to_lp_mode = {}

    _port_to_eeprom_mapping = {}

    _port_to_i2c_mapping = {
        1:  101,
        2:  102,
        3:  103,
        4:  104,
        5:  105,
        6:  106,
        7:  107,
        8:  108,
        9:  109,
        10: 110,
        11: 111,
        12: 112,
        13: 113,
        14: 114,
        15: 115,
        16: 116,
        17: 117,
        18: 118,
        19: 119,
        20: 120,
        21: 121,
        22: 122,
        23: 123,
        24: 124,
        25: 125,
        26: 126,
        27: 127,
        28: 128,
        29: 129,
        30: 130,
        31: 131,
        32: 132,
        33: 133,
        34: 134,
        35: 135,
        36: 136,
        37: 137,
        38: 138,
        39: 139,
        40: 140,
        41: 141,
        42: 142,
        43: 143,
        44: 144,
        45: 145,
        46: 146,
        47: 147,
        48: 148,
        49: 149,
        50: 150,
        51: 151,
        52: 152,
        53: 153,
        54: 154,
        55: 155,
        56: 156

    }

    @property
    def port_start(self):
        return self.PORT_START

    @property
    def port_end(self):
        return self.PORT_END

    @property
    def qsfp_ports(self):
        return []

    @property
    def qsfp_dd_port_start(self):
        return self.QSFP_DD_PORT_START

    @property
    def qsfp_dd_port_end(self):
        return self.QSFP_DD_PORT_END

    @property
    def qsfp_dd_ports(self):
        return range(self.QSFP_DD_PORT_START, self.QSFP_DD_PORT_END + 1)

    @property
    def port_to_eeprom_mapping(self):
        return self._port_to_eeprom_mapping

    def __init__(self):
        eeprom_path = '/sys/bus/i2c/devices/i2c-{0}/{0}-0050/eeprom'
        for x in range(self.port_start, self.port_end+1):
            self.port_to_eeprom_mapping[x] = eeprom_path.format(self._port_to_i2c_mapping[x])

        self.get_transceiver_change_event()
        SfpUtilBase.__init__(self)

    def get_eeprom_dom_raw(self, port_num):
        if port_num in self.qsfp_ports:
            # QSFP DOM EEPROM is also at addr 0x50 and thus also stored in eeprom_ifraw
            return None
        elif port_num in self.qsfp_dd_ports:
            ifraw = self._read_eeprom_devid(port_num, self.IDENTITY_EEPROM_ADDR, 0, 128)
            identifier = int(ifraw[0], 16)
            # 1Eh QSFP+ or later with Common Management Interface Specification (CMIS)
            # 18h QSFP-DD Double Density 8X Pluggable Transceiver (INF-8628)
            if identifier == 0x1E or identifier == 0x18:
                # Page 11h (Lane Status)
                lane_status = self._read_eeprom_devid(port_num, self.IDENTITY_EEPROM_ADDR, 128 * 18, 128)
                return ifraw + lane_status
            else:
                return None
        else:
            # Read dom eeprom at addr 0x51
            return self._read_eeprom_devid(port_num, self.IDENTITY_EEPROM_ADDR, 256)

    def get_presence(self, port_num):
        # Check for invalid port_num
        if port_num < self.port_start or port_num > self.port_end:
            return False

        try:
            present_file = open("/sys/switch/transceiver/eth{0}/present".format(port_num), "r")
        except IOError as e:
            #print("Error: unable to open file: %s" % str(e))
            return False

        data = present_file.readline().rstrip()

        if data == "0":
            return False

        return True

    def get_low_power_mode(self, port_num):
        if port_num < self.port_start or port_num > self.port_end:
            return False

        try:
            lpmode_file = open("/sys/switch/transceiver/eth{0}/lpmode".format(port_num), "r")
        except IOError as e:
            #print("Error: unable to open file: %s" % str(e))
            return False

        data = lpmode_file.readline().rstrip()

        if data == "0":
            return False

        return True

    def set_low_power_mode(self, port_num, lpmode):
        if port_num < self.port_start or port_num > self.port_end:
            return False

        try:
            lpmode_file = open("/sys/switch/transceiver/eth{0}/lpmode".format(port_num), "r+")
        except IOError as e:
            #print("Error: unable to open file: %s" % str(e))
            return False

        data = "1" if lpmode is True else "0"

        lpmode_file.seek(0)
        lpmode_file.write(data)
        lpmode_file.close()

        return True

    def reset(self, port_num):
         raise NotImplementedError

    @property
    def _get_present_bitmap(self):
        ret = 0
        for port in range(self.PORT_START, self.PORT_END + 1):
            ret += (self.get_presence(port) << (port - self.PORT_START))

        return int(ret)

    data = {'valid':0, 'last':0, 'present':0}
    def _get_transceiver_change_event(self, timeout=2000):
        now = time.time()
        port_dict = {}
        port = 0

        if timeout < MIN_WAIT_TIME:
            timeout = MIN_WAIT_TIME
        timeout = (timeout) / float(1000) # Convert to secs

        if now < (self.data['last'] + timeout) and self.data['valid']:
            time.sleep(timeout)
            return True, {}

        reg_value = self._get_present_bitmap
        changed_ports = self.data['present'] ^ reg_value
        if changed_ports:
            for port in range (self.port_start, self.port_end+1):
                # Mask off the bit corresponding to our port
                mask = (1 << (port - self.port_start))
                if changed_ports & mask:
                    if (reg_value & mask) == 0:
                        port_dict[port] = SFP_STATUS_REMOVED
                    else:
                        port_dict[port] = SFP_STATUS_INSERTED

            # Update cache
            self.data['present'] = reg_value
            self.data['last'] = now
            self.data['valid'] = 1
            #pprint.pprint(port_dict)
            return True, port_dict
        else:
            self.data['last'] = now
            time.sleep(timeout)
            return True, {}
        return False, {}

    def get_transceiver_change_event(self, timeout=2000):
        status = True
        change_dict = {}
        change_dict['sfp'] = {}
        if timeout < MIN_WAIT_TIME and timeout != 0:
            timeout = MIN_WAIT_TIME
        self.data['valid'] = 0
        timeleft = timeout
        while self.data['valid'] == 0:
            status, change_dict = self._get_transceiver_change_event(MIN_WAIT_TIME)
            if(timeout == 0):
                pass
            else:
                timeleft = timeleft - MIN_WAIT_TIME
                if timeleft <= 0:
                    break
        return status, change_dict


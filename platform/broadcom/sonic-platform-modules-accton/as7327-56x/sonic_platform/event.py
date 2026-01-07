try:
    import time
    import sys
    from .helper import APIHelper
    try:
        from sonic_py_common.logger import Logger
    except:
        # print("sonic_py_common.logger" + " - required module not found" "try import sonic_daemon_base.daemon_base")
        try:
            from sonic_daemon_base.daemon_base import Logger
        except ImportError as e1:
            raise ImportError(repr(e1) + " - required module not found")
except ImportError as e:
    raise ImportError(repr(e) + " - required module not found")

SFP_TYPE = "SFP"
QSFP_TYPE = "QSFP"
QSFP_DD_TYPE = "QSFP_DD"

def getstatusoutput(cmd):
    if sys.version_info.major == 2:
        # python2
        import commands
        return commands.getstatusoutput( cmd )
    else:
        # python3
        import subprocess
        return subprocess.getstatusoutput( cmd )

MIN_WAIT_TIME = 200
EEPROM_PATH = 'cat /sys/bus/i2c/devices/{}-0050/eeprom_status '
class SfpEvent:
    ''' Listen to insert/remove sfp events '''

    def __init__(self, sfp_list):
        self._api_helper = APIHelper()
        self._sfp_list = sfp_list
        self._logger = Logger()

    sfp_change_event_data = {'valid': 0, 'last': 0, 'present': 0}
    def _get_sfp_event(self, timeout=0):
        now = time.time()
        port_dict = {}
        change_dict = {}
        change_dict['sfp'] = port_dict

        if timeout < MIN_WAIT_TIME:
            timeout = MIN_WAIT_TIME
        timeout = timeout / float(1000)  # Convert to secs

        if now < (self.sfp_change_event_data['last'] + timeout) and self.sfp_change_event_data['valid']:
            time.sleep(timeout)
            return True, change_dict

        eeprom_map = 0

        for sfp in self._sfp_list:
            if(sfp.port_num > 0):
                break
        ret, eeprom_map = sfp.get_presence_all()
        if ret == False:
            change_dict['sfp'] = {}
            return False, change_dict

        changed_ports = self.sfp_change_event_data['present'] ^ eeprom_map #bitmap
        if changed_ports:
            for sfp in self._sfp_list:
                i=sfp.port_num-1
                if (changed_ports & (1 << i)):
                    if (eeprom_map & (1 << i)) == 0:
                        port_dict[i+1] = '0'
                        sfp.viable = 0
                        sfp.eeprom_raw = []
                        print('output port'+str(sfp.port_num))
                    else:
                        print('inport port'+str(sfp.port_num))
                        port_dict[i+1] = '1'

            # Update the cache dict
            self.sfp_change_event_data['present'] = eeprom_map #bitmap
            self.sfp_change_event_data['last'] = now
            self.sfp_change_event_data['valid'] = 1
            return True, change_dict
        else:
            self.sfp_change_event_data['last'] = now
            time.sleep(timeout)
            return True, change_dict

    def get_sfp_event(self, timeout=0):
        status = True
        change_dict = {}
        change_dict['sfp'] = {}
        if timeout < MIN_WAIT_TIME and timeout != 0:
            timeout = MIN_WAIT_TIME
        self.sfp_change_event_data['valid'] = 0
        timeleft = timeout
        while self.sfp_change_event_data['valid'] == 0:
            status, change_dict = self._get_sfp_event(MIN_WAIT_TIME)
            if(timeout == 0):
                pass
            else:
                timeleft = timeleft - MIN_WAIT_TIME
                if timeleft <= 0:
                    break
        return status, change_dict

    def set_sfp_i2c_scl(self,     port, plugins):
        #print("port {} plugins {}".format(port,plugins))
        for sfp in self._sfp_list:
            if(sfp.port_num != port):
                continue

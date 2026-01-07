import os
import struct
import subprocess
import sys
from mmap import *

HOST_CHK_CMD = "docker > /dev/null 2>&1"
EMPTY_STRING = ""


class APIHelper():

    def __init__(self):
        try:
            from sonic_py_common import device_info
            (self.platform, self.hwsku) = device_info.get_platform_and_hwsku()
        except:
            # print("sonic_py_common" + " - required module not found" "try import sonic_daemon_base.daemon_base")
            try:
                from sonic_daemon_base.daemon_base import DaemonBase
                myDaemonBase = DaemonBase()
                (self.platform, self.hwsku) = myDaemonBase.get_platform_and_hwsku()
            except ImportError as e1:
                raise ImportError(repr(e1) + " - required module not found")

    def is_host(self):
        return os.system(HOST_CHK_CMD) == 0

    def pci_get_value(self, resource, offset):
        status = True
        result = ""
        try:
            fd = os.open(resource, os.O_RDWR)
            mm = mmap(fd, 0)
            mm.seek(int(offset))
            read_data_stream = mm.read(4)
            result = struct.unpack('I', read_data_stream)
        except Exception:
            status = False
        return status, result

    def getstatusoutput(self, cmd):
        if sys.version_info.major == 2:
            # python2
            import commands
            ret, output = commands.getstatusoutput(cmd)
        else:
            # python3
            import subprocess
            ret, output = subprocess.getstatusoutput(cmd)
        if ret:
            status = False
            print('Failed :'+cmd)
        else:
            status = True
        return status, output

    def run_command(self, cmd):
        status = True
        result = ""
        try:
            if sys.version_info.major == 2:
                # python2
                import commands
                _status, result = commands.getstatusoutput(cmd)
                if _status != 0:
                    status = False
            else:
                # python3
                import subprocess
                _status, result = subprocess.getstatusoutput(cmd)
                if _status != 0:
                    status = False
        except Exception:
            status = False
        return status, result

    def run_interactive_command(self, cmd):
        try:
            os.system(cmd)
        except Exception:
            return False
        return True

    def read_txt_file(self, file_path):
        try:
            with open(file_path, 'r') as fd:
                data = fd.read()
                return data.strip()
        except IOError:
            pass
        return None

    def write_txt_file(self, file_path, value):
        try:
            with open(file_path, 'w') as fd:
                fd.write(str(value))
        except IOError:
            return False
        return True

    def ipmi_raw(self, netfn, cmd):
        status = True
        result = ""
        try:
            cmd = "ipmitool raw {} {}".format(str(netfn), str(cmd))
            p = subprocess.Popen(
                cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            raw_data, err = p.communicate()
            if err == '':
                result = raw_data.strip()
            else:
                status = False
        except Exception:
            status = False
        return status, result

    def ipmi_fru_id(self, id, key=None):
        status = True
        result = ""
        try:
            cmd = "ipmitool fru print {}".format(str(
                id)) if not key else "ipmitool fru print {0} | grep '{1}' ".format(str(id), str(key))

            p = subprocess.Popen(
                cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            raw_data, err = p.communicate()
            if err == '':
                result = raw_data.strip()
            else:
                status = False
        except Exception:
            status = False
        return status, result

    def ipmi_set_ss_thres(self, id, threshold_key, value):
        status = True
        result = ""
        try:
            cmd = "ipmitool sensor thresh '{}' {} {}".format(str(id), str(threshold_key), str(value))
            p = subprocess.Popen(
                cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            raw_data, err = p.communicate()
            if err == '':
                result = raw_data.strip()
            else:
                status = False
        except Exception:
            status = False
        return status, result

#############################################################################
# Celestica
#
# Component contains an implementation of SONiC Platform Base API and
# provides the components firmware management function
#
#############################################################################

import shlex
import subprocess

try:
    import os
    import syslog
    from sonic_platform_base.component_base import ComponentBase
    from .helper import APIHelper
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

SYS_CPLD_ADDR_MAPPING = {
    "SYS_CPLD": "1"
}

PORT_CPLD_ADDR_MAPPING = {
    "PORT_CPLD": "1",
}

FAN_CPLD_ADDR_MAPPING = {
    "FAN_CPLD": "1",
}

FPGA_ADDR_MAPPING = {
    "FPGA": "1"
}
BASE_PATH = "/sys/switch/"
CPLD_PATH = "cpld/cpld"
FPGA_PATH = "fpga/fpga"
BIOS_VERSION_PATH = "/sys/class/dmi/id/bios_version"
COMPONENT_LIST= [
   ("SYS_CPLD", "Mianboard System CPLD code version"),
   ("PORT_CPLD", "PORT_CPLD code version"),
   ("FPGA", "Subcard borad FPGA code version"),
   ("BIOS", "Basic Input/Output System code version"),
   ("BMC", "Baseboard Management Controller")

]
COMPONENT_DES_LIST = ["CPLD","Basic Input/Output System"]

def _update_cpld_firmware(image_path):
    sys_cpld_flag_path = "/run/cpld1_flag"
    cmd = "{}{}{}".format("/usr/local/bin/cpldupd -u MX7327 ", image_path," -c DO_REAL_TIME_ISP 1")
    try:
        # os.system("busybox devmem 0xfc80100e 8 0xf8")
        print(cmd)
        ret = os.system(cmd)
        if(ret):
            return False
        os.mknod(sys_cpld_flag_path)
    except Exception:
        return False
    return True

def _update_port_cpld_firmware(image_path):
    port_cpld_flag_path = "/run/cpld2_flag"
    cmd = "{}{}{}".format("/usr/local/bin/cpldupd -u MX7327 ", image_path," -c DO_REAL_TIME_ISP 1")
    try:
        # os.system("busybox devmem 0xfc80100e 8 0xfa")
        print(cmd)
        ret = os.system(cmd)
        if(ret):
            return False
        os.mknod(port_cpld_flag_path)
    except Exception:
        return False
    return True

def _update_fpga_firmware(image_path):
    fpga_flag_path = "/run/fpga_flag"
    cmd = "{}{}".format("/usr/local/bin/fpga_upd_pcie -W -F ", image_path)
    try:
        # os.system("busybox devmem 0xfc801015 8 0x01")
        ret = os.system("/usr/local/bin/fpga_upd_pcie -O")
        if(ret):
            return False
        ret = os.system("/usr/local/bin/fpga_upd_pcie -R -A 0 -L 64")
        if(ret):
            return False
        ret = os.system("/usr/local/bin/fpga_upd_pcie -E")
        if(ret):
            return False
        ret = os.system(cmd)
        if(ret):
            return False
        os.mknod(fpga_flag_path)
    except Exception:
        return False
    return True

def _update_bios_firmware(image_path):
    cmd = "{}{}{}".format("/usr/local/bin/flashrom -p internal -i bios -w ", image_path, ' --ifd -N ')
    try:
        print(cmd)
        ret = os.system(cmd)
        if(ret):
            return False
    except Exception:
        return False
    return True


class Component(ComponentBase):
    """Platform-specific Component class"""

    DEVICE_TYPE = "component"

    def __init__(self, component_index=0):
        self._api_helper=APIHelper()
        ComponentBase.__init__(self)
        self.index = component_index
        self.name = self.get_name()

    def __run_command(self, command):
        # Run bash command and print output to stdout
        try:
            process = subprocess.Popen(
                shlex.split(command), stdout=subprocess.PIPE)
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
            rc = process.poll()
            if rc != 0:
                return False
        except Exception:
            return False
        return True

    def __get_bios_version(self):
        # Retrieves the BIOS firmware version
        try:
            with open(BIOS_VERSION_PATH, 'r') as fd:
                bios_version = fd.read()
                return bios_version.strip()
        except Exception as e:
            return None

    def __get_cpld_version(self):
        # Retrieves the CPLD firmware version
        try:
            cpld_path = "{}{}{}{}".format(BASE_PATH, CPLD_PATH, 1, '/hw_version')
            cpld_version_raw = self._api_helper.read_txt_file(cpld_path)
            cpld_version = "{}".format(cpld_version_raw)
        except Exception as e:
            print('Get exception when read sys cpld')
            cpld_version = 'None'

        return cpld_version

    def __get_port_cpld_version(self):
        # Retrieves the CPLD firmware version
        try:
            cpld_path = "{}{}{}{}".format(BASE_PATH, CPLD_PATH, 2, '/hw_version')
            cpld_version_raw = self._api_helper.read_txt_file(cpld_path)
            cpld_version = "{}".format(cpld_version_raw)
        except Exception as e:
            print('Get exception when read port cpld')
            cpld_version = 'None'

        return cpld_version

    def _get_fpga_version(self):
        # Retrieves the FPGA firmware version
        try:
            fpga_path = "{}{}{}{}".format(BASE_PATH, FPGA_PATH, 1, '/hw_version')
            fpga_version_raw = self._api_helper.read_txt_file(fpga_path)
            fpga_version = "{}".format(fpga_version_raw)
        except Exception as e:
            print('Get exception when read fpga')
            fpga_version = 'None'

        return fpga_version

    def _get_bmc_card_plug(self):
        try:
            bmc_status_path = "/sys/switch/bmc/status"
            bmc_status_raw = self._api_helper.read_txt_file(bmc_status_path)
            if "1" == bmc_status_raw.strip():
                return True
            else:
                return False

        except Exception as e:
            print(e)
            return False

    def _get_bmc_version(self):
        try:
            if not self._get_bmc_card_plug():
                return 'Not plug'

            #get_fpga_cpld_bmc_ver_cmd = "ipmitool mc info"
            mc_info = subprocess.check_output("ipmitool mc info", shell=True).decode('ascii').splitlines()
            bmc_mojor_version = "ERROR"
            bmc_minor_version = "ERROR"
            for line in mc_info:
                bmc_mojor_version = "1.00"
                # if "Firmware Revision" in line:
                #     bmc_mojor_version = line.split(":")[1].strip()
                if "Aux Firmware Rev Info" in line:
                    bmc_minor_version = mc_info[mc_info.index(line)+1].strip()
            bmc_version = "{}.{:02x}".format(bmc_mojor_version,int(bmc_minor_version,16))
            return bmc_version
        except Exception as e:
            print('Get exception when read BMC version.')
            return None

    def get_name(self):
        """
        Retrieves the name of the component
         Returns:
            A string containing the name of the component
        """
        return COMPONENT_LIST[self.index][0]

    def get_description(self):
        """
        Retrieves the description of the component
            Returns:
            A string containing the description of the component
        """
        return COMPONENT_LIST[self.index][1]
        #return "testhwsku"

    def get_firmware_version(self):
        """
        Retrieves the firmware version of module
        Returns:
            string: The firmware versions of the module
        """
        fw_version = None
        if self.name == "BIOS":
            fw_version = self.__get_bios_version()
        elif "SYS_CPLD" in self.name:
            fw_version = self.__get_cpld_version()
        elif "PORT_CPLD" in self.name:
            fw_version = self.__get_port_cpld_version()
        elif "FPGA" in self.name:
            fw_version = self._get_fpga_version()
        elif "BMC" in self.name:
            fw_version = self._get_bmc_version()

        return fw_version

    def install_firmware(self, image_path):
        """
        Install firmware to module
        Args:
            image_path: A string, path to firmware image
        Returns:
            A boolean, True if install successfully, False if not
        """
        ret = True
        if self.index == 0:         # SYS_CPLD
            print('Warning, Update SYS_CPLD, please wait, and reboot after done.')
            ret = _update_cpld_firmware(image_path)
        elif self.index == 1:         # PORT_CPLD
            print('Warning, Update PORT_CPLD and PORT_CPLD, please wait, and reboot after done.')
            ret = _update_port_cpld_firmware(image_path)
        elif self.index == 2:       # FPGA
            print('Warning, Update FPGA, please wait, and reboot after done.')
            ret = _update_fpga_firmware(image_path)
        elif self.index == 3:       # BIOS
            print('Warning, Update BIOS, please wait, and reboot after done.')
            ret = _update_bios_firmware(image_path)
        else:
            print('Unsupport component')
            return False
        if ret == False:
            msg = "UpgradeFirmWareFail Report:The firmware upgrade failed(Name=[{}])".format(self.name)
            syslog.syslog(syslog.LOG_ERR, msg)
        else:
            print("#############################################################")
            print("{} upgrade success, please reboot!".format(self.name))
            print("#############################################################")
        return True

    def update_firmware(self, image_path):
        """
        Install firmware to module
        Args:
            image_path: A string, path to firmware image
        Returns:
            A boolean, True if install successfully, False if not
        """
        ret = True
        if self.index == 0:         # SYS_CPLD
            print('Warning, Update SYS_CPLD, please wait, and reboot after done.')
            _update_cpld_firmware(image_path)
        elif self.index == 1:         # PORT_CPLD
            print('Warning, Update PORT_CPLD, please wait, and reboot after done.')
            _update_port_cpld_firmware(image_path)
        elif self.index == 2:       # FPGA
            print('Warning, Update FPGA, please wait, and reboot after done.')
            _update_fpga_firmware(image_path)
        elif self.index == 3:       # BIOS
            print('Warning, Update BIOS, please wait, and reboot after done.')
            _update_bios_firmware(image_path)
        else:
            print('Unsupport component')
            return False
        if ret == False:
            msg = "UpgradeFirmWareFail Report:The firmware upgrade failed(Name=[{}])".format(self.name)
            syslog.syslog(syslog.LOG_ERR, msg)
        else:
            print("#############################################################")
            print("{} upgrade success, please reboot!".format(self.name))
            print("#############################################################")
        return True


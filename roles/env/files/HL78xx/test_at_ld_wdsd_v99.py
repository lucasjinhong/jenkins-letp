"""
Description:
Local Download AT commands test cases :: WDSD
Performs local upgrade test from normal <-> .99 version (i.e. A->B->A)

    A = SOFT_INI_Soft_Version
    B = SOFT_INI_Wdsd_Version

Input Parameters:
SOFT_INI_Soft_Version (Base version)
SOFT_INI_Wdsd_Version (Target WDSD version)
AVMS_LOCAL_DELTA      (Local path of the AVMS package (.ua) from normal->.99)
AVMS_LOCAL_DELTA99    (Local path of the AVMS package (.ua) from .99->normal)
"""


import time
import os
import ast
from datetime import datetime
import serial
from xmodem import XMODEM
import pytest
import swilog
import VarGlobal
from avms_upgrade import autoflash
from autotest import (PRINT_START_FUNC, PRINT_TEST_RESULT, FOTA_Update_Duration)
from autotest import pytestmark  # noqa # pylint: disable=unused-import

timeout = 15

def xmodem_send(slink, baudrate, dwlfile, logmsg="silent", modem_mode="xmodem1k"):
    """Function to xmodem send firmware file"""
    hCom = serial.Serial(slink, baudrate, timeout=180)
    VarGlobal.myColor = VarGlobal.colorLsit[8]
    print("\n\nxmodem send - start: ", "("+logmsg+")", dwlfile)
    def getc(size, timeout=1):
        global xmodem_displaybuffer
        answer = hCom.read(size)
        # logmsg - raw
        if logmsg == "raw":
            sys.stdout.write(answer)
        # logmsg - buffer
        if logmsg == "buffer":
            xmodem_displaybuffer += answer
            if len(xmodem_displaybuffer) > 500:
                #for each_char in xmodem_displaybuffer:
                sys.stdout.write(
                    xmodem_displaybuffer.replace("\x06", "<ACK>").replace("\x15", "<NAK>"))
                xmodem_displaybuffer = ""
        return answer
    def putc(data, timeout=1):
        size = hCom.write(data)
        return size

    modem = XMODEM(getc, putc, modem_mode)
    stream = open(dwlfile, 'rb')
    start_time = datetime.now()
    status = modem.send(stream, retry=8)
    end_time = datetime.now()
    stream.close()
    # display time spent in receive
    print("\n\nxmodem send - completed")
    download_time = (end_time - start_time).seconds * 1000.0 +\
                    (end_time - start_time).microseconds / 1000.0
    print("download_time : %f second(s)\n" % (download_time/1000.0))

    return status

@pytest.fixture
def ld_wdsd_v99_setup_teardown(target_at, read_config, non_network_tests_setup_teardown):
    """Test case setup and teardown."""
    state = non_network_tests_setup_teardown
    if state == "OK":
        print("General Test Setup Success")

    print("\nA_HL_INT_LD_WDSD_0001 TC Start:\n")

    print("\n------------Test's preambule Start------------")

    phase = int(read_config.findtext("autotest/Features_PHASE"))
    if phase == 0:
        pytest.skip("Phase 0 : No AT+WDSD command")

    # Variable Init
    SOFT_INI_Soft_Version = read_config.findtext("autotest/SOFT_INI_Soft_Version")
    slink2 = read_config.findtext("module/slink2/name")
    AVMSZipPath = ast.literal_eval(read_config.findtext("autotest/AVMSZipPath"))
    AVMS_LOCAL_DELTA = read_config.findtext("autotest/AVMS_LOCAL_DELTA")
    AVMS_LOCAL_DELTA99 = read_config.findtext("autotest/AVMS_LOCAL_DELTA99")
    if not AVMS_LOCAL_DELTA or not AVMS_LOCAL_DELTA99:
        raise Exception(
            "-->Problem: Enter your AVMS_LOCAL_DELTA and AVMS_LOCAL_DELTA99 fields in autotest.xml")
    if not os.path.isfile(AVMS_LOCAL_DELTA):
        raise Exception("-->Problem: no file %s" % AVMS_LOCAL_DELTA)
    if not os.path.isfile(AVMS_LOCAL_DELTA99):
        raise Exception("-->Problem: no file %s" % AVMS_LOCAL_DELTA99)
    Autoflasher = int(read_config.findtext("autotest/Features_Autoflasher"))
    relay_port = read_config.findtext("hardware/power_supply/com/port")
    relay_num = read_config.findtext("hardware/power_supply/port_nb")

    test_nb = ""
    test_ID = "A_HL_INT_LD_WDSD_0001"
    PRINT_START_FUNC(test_nb + test_ID)

    print("\n----- Testing Start -----\n")
    yield test_ID
    print("\n----- WDSD v99 TearDown -----\n")

    # Restore module to base version if test script failed
    if Autoflasher and VarGlobal.statOfItem == "NOK":
        rsp = target_at.run_at_cmd("ATI3", timeout, ["OK"])
        version = rsp.split("\r\n")[1]

        if not version == SOFT_INI_Soft_Version:
            if AVMSZipPath == ['']:
                autoflash(SOFT_INI_Soft_Version, slink2, relay_port, relay_num)
            else:
                autoflash(SOFT_INI_Soft_Version, slink2, relay_port, relay_num, AVMSZipPath[0])


def A_HL_INT_LD_WDSD_0001(read_config, ld_wdsd_v99_setup_teardown, target_at):
    """
    Check WDSD AT Command and local upgrade from normal to/from .99 build.
    Nominal/Valid use case.
    """
    test_ID = ld_wdsd_v99_setup_teardown

    # Variable Init
    slink2 = read_config.findtext("module/slink2/name")
    BaudRate = read_config.findtext("module/slink2/speed")
    soft_version = read_config.findtext("autotest/SOFT_INI_Soft_Version")
    wdsd_version = ast.literal_eval(read_config.findtext("autotest/SOFT_INI_Wdsd_Version"))
    AVMS_LOCAL_DELTA = read_config.findtext("autotest/AVMS_LOCAL_DELTA")
    AVMS_LOCAL_DELTA99 = read_config.findtext("autotest/AVMS_LOCAL_DELTA99")

    # Start Test
    print("\n------------Test Case Start------------")

    try:
        # AT+WDSI?
        wdsi_rsp = target_at.run_at_cmd("AT+WDSI?", timeout, ["OK"])
        wdsi = wdsi_rsp.split(": ")[1].split("\r\n")[0]
        print("\nDefault wdsi is: " + wdsi)

        target_at.run_at_cmd("AT+WDSI=4479", timeout, ["OK"])

        # AT+WDSC?
        wdsc_rsp = target_at.run_at_cmd("AT+WDSC?", timeout, ["OK"])
        wdsc = wdsc_rsp.split(": ")[3].split("\r\n")[0]
        print("\nDefault User Agreements for package install: " + wdsc)

        target_at.run_at_cmd("AT+WDSC=2,1", timeout, ["OK"])

        # AT+CMEE?
        cmee_rsp = target_at.run_at_cmd("AT+CMEE?", timeout, ["OK"])
        cmee = cmee_rsp.split(": ")[1].split("\r\n")[0]
        print("\nDefault cmee is: " + cmee)

        target_at.run_at_cmd("AT+CMEE=1", timeout, ["OK"])

        # AT+WDSD?
        wdsd_rsp = target_at.run_at_cmd("AT+WDSD=?", timeout, ["OK"])
        wdsd_max = wdsd_rsp.split(": ")[1].split("-")[1].split(")")[0]
        print("Max size in bytes: " + wdsd_max)

        target_at.run_at_cmd("AT+WDSD=0", timeout, [r"\+CME\sERROR:\s3"])

        # Perform upgrade/downgrade firmware for normal/.99 builds
        for i in range(2):
            if i == 0:
                swilog.step("Local upgrade from %s to %s" % (soft_version, wdsd_version[0]))
                delta_path = AVMS_LOCAL_DELTA
                version = soft_version
                wdsd = wdsd_version[0]
            else:
                swilog.step("Local upgrade from %s to %s" % (wdsd_version[0], soft_version))
                delta_path = AVMS_LOCAL_DELTA99
                version = wdsd_version[0]
                wdsd = soft_version

            target_at.run_at_cmd("AT+CGMR", timeout, [version, "OK"])

            package_size = os.path.getsize(delta_path)
            print("package_size : %f KB\n" % (package_size/1000.0))

            target_at.run_at_cmd("AT+WDSD=" + str(package_size), timeout, ["%s" % chr(21)])

            Download_Is_Successful = xmodem_send(slink2, BaudRate, delta_path)

            if not Download_Is_Successful:
                print("-------->Problem: download fail !!!")
                VarGlobal.statOfItem = "NOK"
            else:
                target_at.expect("OK")
                target_at.expect(r"\+WDSI:\s3")
                start_time = datetime.now()
                target_at.run_at_cmd("AT+WDSR=4", 20 * timeout, ["OK", r"\+WDSI:\s14" ,r"\+WDSI:\s16"])
                end_time = datetime.now()
                time.sleep(10)
                target_at.run_at_cmd("ATE0", timeout, ["OK"])

                # Verify the firmware version after Local upgrade
                target_at.run_at_cmd("AT+CGMR", timeout, [wdsd, "OK"])

                # Unlock Module
                target_at.run_at_cmd("AT!UNLOCK=\"A710\"", timeout, ["OK|ERROR"])

                swilog.info("Local upgrade from %s to %s is successful!\n" % (version, wdsd))
                upgrade_time = (end_time - start_time).seconds * 1000.0 +\
                               (end_time - start_time).microseconds / 1000.0
                print("upgrade_time : %f second(s)\n" % (upgrade_time/1000.0))

        # Restore default values
        target_at.run_at_cmd("AT+CMEE=" + cmee, timeout, ["OK"])
        target_at.run_at_cmd("AT+WDSI=" + wdsi, timeout, ["OK"])
        target_at.run_at_cmd("AT+WDSC=" + wdsc, timeout, ["OK"])

    except Exception as err_msg:
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)

    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)

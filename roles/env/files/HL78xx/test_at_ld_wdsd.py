"""
Description:
Local Download AT commands test cases :: WDSD
Performs continuous local upgrade test from the list of version(s)
in SOFT_INI_Wdsd_Version. Script will perform continuous Local upgrade from version A->B->C->D.

    A = SOFT_INI_Soft_Version
    B to D = List in SOFT_INI_Wdsd_Version

Input Parameters:
SOFT_INI_Soft_Version (Base version)
SOFT_INI_Wdsd_Version (Target WDSD version(s))
AVMS_LOCAL_DELTAS (Location of AVMS packages)
    - provide a list of local delta packages (.ua) in local directory

WARNING:
If you want the module to end up back into original version (A),
you must define that as the last parameter in SOFT_INI_Wdsd_Version & AVMS_LOCAL_DELTAS.

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
from autotest import (PRINT_START_FUNC, PRINT_TEST_RESULT, FOTA_Update_Duration, SWI_Reset_Module)
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
def ld_wdsd_setup_teardown(
        ensure_local_package_exists, target_at,
        read_config, non_network_tests_setup_teardown):
    """Test case setup and teardown."""
    state = non_network_tests_setup_teardown
    if state == "OK":
        print("General Test Setup Success")

    print("\nA_HL_INT_LD_WDSD_0000 TC Start:\n")

    print("\n------------Test's preambule Start------------")

    phase = int(read_config.findtext("autotest/Features_PHASE"))
    if phase == 0:
        pytest.skip("Phase 0 : No AT+WDSD command")

    # Variable Init
    HARD_INI = read_config.findtext("autotest/HARD_INI")
    SOFT_INI_Soft_Version = read_config.findtext("autotest/SOFT_INI_Soft_Version")
    slink2 = read_config.findtext("module/slink2/name")
    AVMSZipPath = ast.literal_eval(read_config.findtext("autotest/AVMSZipPath"))
    AVMS_LOCAL_DELTAS = ast.literal_eval(read_config.findtext("autotest/AVMS_LOCAL_DELTAS"))
    if AVMS_LOCAL_DELTAS == ['']:
        AVMS_LOCAL_DELTAS = ensure_local_package_exists
    Autoflasher = int(read_config.findtext("autotest/Features_Autoflasher"))
    relay_port = read_config.findtext("hardware/power_supply/com/port")
    relay_num = read_config.findtext("hardware/power_supply/port_nb")

    test_nb = ""
    test_ID = "A_HL_INT_LD_WDSD_0000"
    PRINT_START_FUNC(test_nb + test_ID)

    print("\n----- Testing Start -----\n")

    yield test_ID, AVMS_LOCAL_DELTAS

    print("\n----- WDSD TearDown -----\n")

    # Restore switracemode if changed during upgrade test
    switracemode = target_at.run_at_cmd("AT+SWITRACEMODE?", timeout, ["OK"])
    if switracemode.find("RnD") == -1:
        target_at.run_at_cmd("AT+SWITRACEMODE=RnD", timeout, ["OK"])
        SWI_Reset_Module(target_at, HARD_INI)

    # Restore module to base version if test script failed
    if Autoflasher and VarGlobal.statOfItem == "NOK":
        rsp = target_at.run_at_cmd("ATI3", timeout, ["OK"])
        version = rsp.split("\r\n")[1]

        if not version == SOFT_INI_Soft_Version:
            if AVMSZipPath == ['']:
                autoflash(SOFT_INI_Soft_Version, slink2, relay_port, relay_num)
            else:
                autoflash(SOFT_INI_Soft_Version, slink2, relay_port, relay_num, AVMSZipPath[0])


def A_HL_INT_LD_WDSD_0000(read_config, ld_wdsd_setup_teardown, target_at):
    """
    Check WDSD AT Command and and perform local upgrade to/from another build.
    Nominal/Valid use case.
    """
    test_ID = ld_wdsd_setup_teardown[0]

    # Variable Init
    slink2 = read_config.findtext("module/slink2/name")
    BaudRate = read_config.findtext("module/slink2/speed")
    soft_version = read_config.findtext("autotest/SOFT_INI_Soft_Version")
    wdsd_version = ast.literal_eval(read_config.findtext("autotest/SOFT_INI_Wdsd_Version"))
    AVMS_LOCAL_DELTAS = ld_wdsd_setup_teardown[1]

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

        # Set target_version to base version
        target_version = soft_version

        # Start WDSD loop
        for version, delta_path in zip(wdsd_version, AVMS_LOCAL_DELTAS):

            # Assign base and target version
            base_version = target_version
            target_version = version
            swilog.step("Local upgrade from %s to %s" % (base_version, target_version))

            target_at.run_at_cmd("AT+CGMR", timeout, [base_version, "OK"])

            package_size = os.path.getsize(delta_path)
            print("package_size : %f KB\n" % (package_size/1000.0))

            target_at.run_at_cmd("AT+WDSD=" + str(package_size), timeout, ["%s" % chr(21)])

            Download_Is_Successful = xmodem_send(slink2, BaudRate, delta_path)

            if not Download_Is_Successful:
                print("-------->Problem: download fail !!!")
                VarGlobal.statOfItem = "NOK"
            else:
                target_at.expect("OK")
                target_at.expect(r"\+WDSI\:\s3")
                target_at.run_at_cmd("AT+WDSR=4", timeout, ["OK", r"\+WDSI:\s14"])
                start_time = datetime.now()
                target_at.expect(r"\+WDSI:\s16", FOTA_Update_Duration/1000 + 300)
                end_time = datetime.now()
                time.sleep(10)
                target_at.run_at_cmd("ATE0", timeout, ["OK"])

                # Verify the firmware version after Local upgrade
                target_at.run_at_cmd("AT+CGMR", timeout, [target_version, "OK"])

                # Unlock Module
                target_at.run_at_cmd("AT!UNLOCK=\"A710\"", timeout, ["OK|ERROR"])

                swilog.info(
                    "Local upgrade from %s to %s is successful!\n" % (base_version, target_version))
                upgrade_time = (end_time - start_time).seconds * 1000.0 +\
                               (end_time - start_time).microseconds / 1000.0
                print("upgrade_time : %f second(s)\n" % (upgrade_time/1000.0))

                print("\nPreparing for next upgrade or script cleanup...\n")
                time.sleep(2)

        # Restore default values
        target_at.run_at_cmd("AT+CMEE=" + cmee, timeout, ["OK"])
        target_at.run_at_cmd("AT+WDSI=" + wdsi, timeout, ["OK"])
        target_at.run_at_cmd("AT+WDSC=" + wdsc, timeout, ["OK"])

    except Exception as err_msg:
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)

    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)

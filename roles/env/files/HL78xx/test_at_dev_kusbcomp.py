"""
USB Composition AT Command test cases :: KUSBCOMP
"""

import subprocess
import pytest
import swilog
import VarGlobal
from autotest import *

swilog.info("\n----- Program start -----\n")

@pytest.fixture
def usb_cleanup(target_cli, target_at):
    """
    Fixture to restore USB setting for end of test and/or exception
    """
    yield

    print("\n===================================================")
    print("\nRestoring USB setting to default...")
    print("\n===================================================")
    SagSendAT(target_cli, "\r\nat AT+KUSBCOMP=0\r")
    SagWaitResp(target_cli, ["OK"], 4000)
    SagSendAT(target_cli, "reset\r")
    SagWaitResp(target_cli, ["Performing reboot..."], 4000)
    SagSleep(Booting_Duration+5000)
    # Unlock module
    SagSendAT(target_at, "AT+CMEE=0\r")
    SagWaitResp(target_at, ["OK"], 5000)
    SagSendAT(target_at, "AT!UNLOCK=\"A710\"\r")
    SagWaitResp(target_at, ["OK|ERROR"], 5000)

def checkUSBconfig(COMn_cli, config):
    """
    Function to check current USB configuration via CLI
    Return ACM, UsbCompMode and UsbEnable values
    """
    # Get CDC-ACM
    if "ACM" in config:
        SagSendAT(COMn_cli, "\r\nconfig -g manager.uartMapping." + config + "\r")
    else:
        # Get UsbCompMode Value
        if config == "UsbCompMode":
            SagSendAT(COMn_cli, "\r\nconfig -g manager.UsbCompMode.Value\r")
        # Get USB Enable Setting
        elif config == "UsbEnable":
            SagSendAT(COMn_cli, "\r\nconfig -g manager.USB.enabled\r")

    result = SagWaitResp(COMn_cli, [">*\r\n*\r\n>"], 4000)
    configuration = result.split("\r\n")[-2]
    print("\n" + config + ": %s" % configuration)

    return configuration

# -------------------------- Module Initialization ----------------------------------
def A_HL_INT_DEV_KUSBCOMP_0000(target_cli, target_at, read_config, usb_cleanup, non_network_tests_setup_teardown):
    """
    Check KUSBCOMP AT Commands. Nominal/Valid use case
    """
    print("\nA_HL_DEV_KUSBCOMP_0000 TC Start:\n")
    test_environment_ready = "Ready"
    print("\n------------Test's preambule Start------------")

    phase = int(read_config.findtext("autotest/Features_PHASE"))
    if phase < 2:
        pytest.skip("Phase < 2 : No AT+KUSBCOMPxxx commands")

    # Variable Init
    timeout = 10
    HARD_INI = read_config.findtext("autotest/HARD_INI")
    SIM_Pin1 = read_config.findtext("autotest/PIN1_CODE")
    USBEnabled = "true"
    USBDisabled = "false"
    USBCompModeEnabled = "1"
    USBCompModeDisabled = "0"
    ACMDevice = "/dev/ttyACM"
    cmdACM = "ls " + ACMDevice + "*"
    numACM = subprocess.getoutput(cmdACM)
    initACM = numACM.count(ACMDevice)
    swilog.info("Initial number of ACM devices: %s" % initACM)

    # Service on ACM ports
    ACM = ["AT_1", "AT_PPP_AUX", "NMEA", "SFP_LOGGER", "MAC_VIA_MAP"]

    # Module Init
    SagSendAT(target_at, 'AT+CMEE=1\r')
    SagWaitnMatchResp(target_at, ['\r\nOK\r\n'], 4000)

    test_nb = ""
    test_ID = "A_HL_DEV_KUSBCOMP_0000"
    PRINT_START_FUNC(test_nb + test_ID)

    print("\n------------Test's preambule End------------")

     # Start Test
    print("\n------------Test Case Start------------")

    try:
        # Verify AT+KUSBCOMP Commands
        # Check +KUSBCOMP AT Test Command
        print("\n---- AT Test Command ----")
        target_at.run_at_cmd("AT+KUSBCOMP=?", timeout,
                          [r"\+KUSBCOMP:\s\(0-1\),\(0-5\),\(0-5\),\(0-5\)", "OK"])

        # Check +KUSBCOMP AT Read Command
        print("\n---- AT Read Command ----")
        target_at.run_at_cmd("AT+KUSBCOMP?", timeout, [r"\+KUSBCOMP:\s0,0,0,0", "OK"])

        # Check +KUSBCOMP AT Write Command
        print("\n\n---- AT Write Test 1: Verify USB disabled ----")
        target_at.run_at_cmd("AT+KUSBCOMP=0", timeout, ["OK"])
        target_at.run_at_cmd("AT+KUSBCOMP?", timeout, [r"\+KUSBCOMP:\s0,0,0,0", "OK"])
        if ((checkUSBconfig(target_cli, "UsbCompMode") != USBCompModeDisabled) or
                (checkUSBconfig(target_cli, "UsbEnable") != USBDisabled)):
            raise Exception("USB configuration is not correct - USB settings should be disabled!")

        print("\n\n---- AT Write Test 2: Verify USB enabled (default) ----")
        target_at.run_at_cmd("AT+KUSBCOMP=1", timeout, ["OK"])
        target_at.run_at_cmd("AT+KUSBCOMP?", timeout, [r"\+KUSBCOMP:\s1,1,2,3", "OK"])
        if ((checkUSBconfig(target_cli, "UsbCompMode") != USBCompModeEnabled) or
                (checkUSBconfig(target_cli, "UsbEnable") != USBEnabled) or
                (checkUSBconfig(target_cli, "ACM0") != ACM[0]) or
                (checkUSBconfig(target_cli, "ACM1") != ACM[1]) or
                (checkUSBconfig(target_cli, "ACM2") != ACM[2])):
            raise Exception("USB configuration was not configured correctly")

        print("\n\n---- AT Write Test 3: Verify USB enabled (1 ACM setting) ----")
        target_at.run_at_cmd("AT+KUSBCOMP=1,1", timeout, ["OK"])
        target_at.run_at_cmd("AT+KUSBCOMP?", timeout, [r"\+KUSBCOMP:\s1,1,0,0", "OK"])
        if ((checkUSBconfig(target_cli, "UsbCompMode") != USBCompModeEnabled) or
                (checkUSBconfig(target_cli, "UsbEnable") != USBEnabled) or
                (checkUSBconfig(target_cli, "ACM0") != ACM[0]) or
                (checkUSBconfig(target_cli, "ACM1") != "N") or
                (checkUSBconfig(target_cli, "ACM2") != "N")):
            raise Exception("USB configuration was not configured correctly")

        print("\n\n---- AT Write Test 4: Verify USB enabled (2 ACM settings) ----")
        target_at.run_at_cmd("AT+KUSBCOMP=1,1,2", timeout, ["OK"])
        target_at.run_at_cmd("AT+KUSBCOMP?", timeout, [r"\+KUSBCOMP:\s1,1,2,0", "OK"])
        if ((checkUSBconfig(target_cli, "UsbCompMode") != USBCompModeEnabled) or
                (checkUSBconfig(target_cli, "UsbEnable") != USBEnabled) or
                (checkUSBconfig(target_cli, "ACM0") != ACM[0]) or
                (checkUSBconfig(target_cli, "ACM1") != ACM[1]) or
                (checkUSBconfig(target_cli, "ACM2") != "N")):
            raise Exception("USB configuration was not configured correctly")

        print("\n\n---- AT Write Test 5: Verify USB enabled (3 ACM settings) ----")
        target_at.run_at_cmd("AT+KUSBCOMP=1,1,2,3", timeout, ["OK"])
        target_at.run_at_cmd("AT+KUSBCOMP?", timeout, [r"\+KUSBCOMP:\s1,1,2,3", "OK"])
        if ((checkUSBconfig(target_cli, "UsbCompMode") != USBCompModeEnabled) or
                (checkUSBconfig(target_cli, "UsbEnable") != USBEnabled) or
                (checkUSBconfig(target_cli, "ACM0") != ACM[0]) or
                (checkUSBconfig(target_cli, "ACM1") != ACM[1]) or
                (checkUSBconfig(target_cli, "ACM2") != ACM[2])):
            raise Exception("USB configuration was not configured correctly")

        print("\n\n---- AT Write Test 6: Verify USB enabled (ACM setting blank) ----")
        target_at.run_at_cmd("AT+KUSBCOMP=1,1,,3", timeout, ["OK"])
        target_at.run_at_cmd("AT+KUSBCOMP?", timeout, [r"\+KUSBCOMP:\s1,1,0,3", "OK"])
        if ((checkUSBconfig(target_cli, "UsbCompMode") != USBCompModeEnabled) or
                (checkUSBconfig(target_cli, "UsbEnable") != USBEnabled) or
                (checkUSBconfig(target_cli, "ACM0") != ACM[0]) or
                (checkUSBconfig(target_cli, "ACM1") != "N") or
                (checkUSBconfig(target_cli, "ACM2") != ACM[2])):
            raise Exception("USB configuration was not configured correctly")

        print("\n\n---- AT Write Test 7: Verify USB enabled (ACM setting 0) ----")
        target_at.run_at_cmd("AT+KUSBCOMP=1,0,2,3", timeout, ["OK"])
        target_at.run_at_cmd("AT+KUSBCOMP?", timeout, [r"\+KUSBCOMP:\s1,0,2,3", "OK"])
        if ((checkUSBconfig(target_cli, "UsbCompMode") != USBCompModeEnabled) or
                (checkUSBconfig(target_cli, "UsbEnable") != USBEnabled) or
                (checkUSBconfig(target_cli, "ACM0") != "N") or
                (checkUSBconfig(target_cli, "ACM1") != ACM[1]) or
                (checkUSBconfig(target_cli, "ACM2") != ACM[2])):
            raise Exception("USB configuration was not configured correctly")

        print("\n\n---- AT Write Test 8: Verify Edge and Invalid Cases ----")
        target_at.run_at_cmd("AT+KUSBCOMP=", timeout, [r"\+CME ERROR:\s3"])
        target_at.run_at_cmd("AT+KUSBCOMP=0,1", timeout, [r"\+CME ERROR:\s3"])
        target_at.run_at_cmd("AT+KUSBCOMP=0,1,2", timeout, [r"\+CME ERROR:\s3"])
        target_at.run_at_cmd("AT+KUSBCOMP=0,1,2,3", timeout, [r"\+CME ERROR:\s3"])
        target_at.run_at_cmd("AT+KUSBCOMP=1,1,1", timeout, [r"\+CME ERROR:\s3"])
        target_at.run_at_cmd("AT+KUSBCOMP=1,1,1,1", timeout, [r"\+CME ERROR:\s3"])
        target_at.run_at_cmd("AT+KUSBCOMP=1,1,1,2", timeout, [r"\+CME ERROR:\s3"])
        target_at.run_at_cmd("AT+KUSBCOMP=1,1,2,1", timeout, [r"\+CME ERROR:\s3"])
        target_at.run_at_cmd("AT+KUSBCOMP=1,6", timeout, [r"\+CME ERROR:\s3"])
        target_at.run_at_cmd("AT+KUSBCOMP=2", timeout, [r"\+CME ERROR:\s3"])

        # Verify ACM Ports Are Enabled After Reboot
        print("\n\n---- Verify ACM Ports Are Enabled After Reboot ----")
        target_at.run_at_cmd("AT+KUSBCOMP=1", timeout, ["OK"])

        print("\nReboot module for +KUSBCOMP command to take effect...")
        target_at.run_at_cmd("AT+CFUN=1,1", timeout, ["OK"])
        SagSleep(Booting_Duration+5000)

        try:
            print("\nVerify AT Commands no longer work on ttyUSB...\n")
            target_at.run_at_cmd("AT", timeout, ["OK"])
            VarGlobal.statOfItem = "NOK"
            raise Exception("AT Commands should not work!!!")
        except:
            print("\n\nUSB Composition has been changed successfully!\n")

        # Verify Three ACM ports are enabled
        output = subprocess.getoutput(cmdACM)
        print("Verify Three ACM ports are enabled upon AT+KUSBCOMP=1")
        print(output)
        swilog.info("Number of ACM devices: %s" % output.count(ACMDevice))
        if output.count(ACMDevice) != (initACM + 3):
            swilog.error("Check if ACM ports are enabled!")
            VarGlobal.statOfItem = "NOK"

        # Restore USB Configuration via CLI port
        SagSendAT(target_cli, "\r\nat AT+KUSBCOMP=0\r")
        SagWaitResp(target_cli, ["OK"], 4000)
        SagSendAT(target_cli, "reset\r")
        SagWaitResp(target_cli, ["Performing reboot..."], 4000)
        SagSleep(Booting_Duration+5000)

        # Verify AT port response
        print("\nVerify AT port is enabled...\n")
        target_at.run_at_cmd("AT", timeout, [r"\D"])
        print("")

        # Verify ACM ports are disabled
        output = subprocess.getoutput(cmdACM)
        print("Verify Three ACM ports are disabled upon AT+KUSBCOMP=0")
        print(output)
        swilog.info("Number of ACM devices: %s" % output.count(ACMDevice))
        if output.count(ACMDevice) != initACM:
            swilog.error("Check if ACM ports are disabled!")
            VarGlobal.statOfItem = "NOK"

    except Exception as err_msg:
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)
    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)

swilog.info("\n----- Program End -----\n")

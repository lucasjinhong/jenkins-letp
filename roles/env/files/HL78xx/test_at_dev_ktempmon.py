import pytest
import time
import swilog
import pexpect
import VarGlobal
import ast
from autotest import *

swilog.info("\n----- Program start -----\n")

# -------------------------- Module Initialization ----------------------------------
def A_HL_INT_DEV_KTEMPMON_0000(target_at, read_config, non_network_tests_setup_teardown):
    """
    Check KTEMPMON AT Commands. Nominal/Valid use case
    """
    print("\nA_HL_INT_DEV_KTEMPMON_0000 TC Start:\n")
    test_environment_ready = "Ready"
    print("\n------------Test's preambule Start------------")

    phase = int(read_config.findtext("autotest/Features_PHASE"))
    if phase < 2:
        pytest.skip("Phase < 2 : No AT+KTEMPMONxxx commands")

    # Variable Init
    timeout = 15
    GPIO_str = read_config.findtext("autotest/Enabled_GPIO")
    SOFT_INI_Soft_Version = read_config.findtext("autotest/SOFT_INI_Soft_Version")
    Soft_Version = two_digit_fw_version(SOFT_INI_Soft_Version)
    Max_Extreme_Temp = "120"

    # Extreme temperature
    if Soft_Version <= "04.00.00.00":
        Max_Extreme_Temp = "100"

    # Action parameter
    if ("04.06.00.00" <= Soft_Version < "05.03.00.00") or (Soft_Version >= "05.03.03.00"):
        # Airplane mode supported in 4.6.0.0
        action = r"\(0\,1\,2\,4\,6\)"
    else:
        action = r"\(0\-2\)"

    # Module Init
    target_at.run_at_cmd("ATE0", timeout, ["OK"])
    target_at.run_at_cmd("AT+CMEE=1", timeout, ["OK"])
    target_at.run_at_cmd("AT+CGMR", timeout, ["OK"])

    test_nb = ""
    test_ID = "A_HL_INT_DEV_KTEMPMON_0000"
    PRINT_START_FUNC(test_nb + test_ID)

    print("\n------------Test's preambule End------------")

     # Start Test
    print("\n------------Test Case Start------------")

    try:
        # Check +KTEMPMON AT Test Command
        target_at.run_at_cmd("AT+KTEMPMON=?", timeout,
                          [r"\+KTEMPMON:\s\(0-1\),\(0-" + Max_Extreme_Temp
                           + r"\),\(0-1\)," + action + r",\(0-255\),\("
                           + GPIO_str + r",\d+\)", "OK"])
        # Check +KTEMPMON AT Read Command
        target_at.run_at_cmd("AT+KTEMPMON?", timeout, [r"\+KTEMPMON:\s0,90,0,0,30,255", "OK"])

        # Check +KTEMPMON AT Write Commands
        # Test <mod> parameter - Enable/Disable the module's internal temperature monitor
        target_at.run_at_cmd("AT+KTEMPMON=1", timeout, ["OK"])
        target_at.run_at_cmd("AT+KTEMPMON?", timeout, [r"\+KTEMPMON:\s1,90,0,0,30,255", "OK"])
        target_at.run_at_cmd("AT+KTEMPMON=0", timeout, ["OK"])
        target_at.run_at_cmd("AT+KTEMPMON?", timeout, [r"\+KTEMPMON:\s0,90,0,0,30,255", "OK"])

        # Test <temperature> parameter - Check boundary of temperature range; set an allowable value
        target_at.run_at_cmd("AT+KTEMPMON=1,121", timeout, [r"\+CME\sERROR:\s916"])
        target_at.run_at_cmd("AT+KTEMPMON=1,-1", timeout, [r"\+CME\sERROR:\s916"])
        target_at.run_at_cmd("AT+KTEMPMON=1,70", timeout, ["OK"])
        target_at.run_at_cmd("AT+KTEMPMON?", timeout, [r"\+KTEMPMON:\s1,70,0,0,30,255", "OK"])

        # Test <urcMode> parameter - Enable/Disable the presentation of the temperature monitor URC
        target_at.run_at_cmd("AT+KTEMPMON=1,70,0", timeout, ["OK"])
        target_at.run_at_cmd("AT+KTEMPMON=1,70,1", timeout, ["OK"])
        target_at.run_at_cmd("AT+KTEMPMON?", timeout, [r"\+KTEMPMON:\s1,70,1,0,30,255", "OK"])

        # Test <action> parameter - Check the available settings
        if "04.06.00.00" <= Soft_Version < "05.03.00.00":
            target_at.run_at_cmd("AT+KTEMPMON=1,70,1,6", timeout, [r"\+CME\sERROR\:\s917"]) #tied to repGPIO
            target_at.run_at_cmd("AT+KTEMPMON=1,70,1,4", timeout, ["OK"])
        target_at.run_at_cmd("AT+KTEMPMON=1,70,1,2", timeout, [r"\+CME\sERROR:\s917"]) #tied to repGPIO
        target_at.run_at_cmd("AT+KTEMPMON=1,70,1,1", timeout, ["OK"])
        target_at.run_at_cmd("AT+KTEMPMON=1,70,1,0", timeout, ["OK"])
        target_at.run_at_cmd("AT+KTEMPMON?", timeout, [r"\+KTEMPMON:\s1,70,1,0,30,255", "OK"])

        # Test <hystime> parameter - Check boundary of hysteresis time; set an allowable value
        target_at.run_at_cmd("AT+KTEMPMON=1,70,1,0,256", timeout, [r"\+CME\sERROR:\s916"])
        target_at.run_at_cmd("AT+KTEMPMON=1,70,1,0,-1", timeout, [r"\+CME\sERROR:\s916"])
        target_at.run_at_cmd("AT+KTEMPMON=1,70,1,0,20", timeout, ["OK"])
        target_at.run_at_cmd("AT+KTEMPMON?", timeout, [r"\+KTEMPMON:\s1,70,1,0,20,255", "OK"])

        # Test <repGPIO> parameter - Use first available GPIO pin, set the action parameter, and verify AT+KGPIOCFG
        target_at.run_at_cmd("AT+KTEMPMON=1,70,1,2,20," + GPIO_str[0], timeout, ["OK"])
        target_at.run_at_cmd("AT+KTEMPMON?", timeout, [r"\+KTEMPMON:\s1,70,1,2,20," + GPIO_str[0], "OK"])
        # verify KGPIOCFG pin is occupied with KTEMPMON setting
        target_at.run_at_cmd("AT+KGPIOCFG=" + GPIO_str[0] + ",1,1", timeout, [r"\+CME\sERROR:\s3"])
        time.sleep(1)

        # Release GPIO pin
        target_at.run_at_cmd("AT+KTEMPMON=0", timeout, ["OK"])
        # Verify GPIO pin is released
        target_at.run_at_cmd("AT+KGPIOCFG?", timeout, [r"\+KGPIOCFG:\s" +GPIO_str[0] + r",0,2\r\n", "OK"])
        time.sleep(1)

        # Configure settings back to default
        print("\n\nConfigure settings back to default...")
        target_at.run_at_cmd("AT+KGPIOCFG=" + GPIO_str[0] + ",1,0", timeout, ["OK"])
        target_at.run_at_cmd("AT+KTEMPMON=0,90,0,0,30,255", timeout, ["OK"])

    except Exception as err_msg:
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)
    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)

swilog.info("\n----- Program End -----\n")

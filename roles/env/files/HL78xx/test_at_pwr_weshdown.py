import pytest
import time
import swilog
import pexpect
import VarGlobal
import ast
from autotest import *
from otii_utility import *

swilog.info( "\n----- Program start -----\n")

@pytest.fixture
def weshdown_tear_down(target_at, read_config):
    yield
    timeout = 15
    GPIO_str = read_config.findtext("autotest/Enabled_GPIO")
    # Configure settings back to default
    print("Restore configuration back to default")
    target_at.run_at_cmd("AT+KTEMPMON=0", timeout, ["OK"])
    target_at.run_at_cmd("AT+WESHDOWN=0", timeout, ["OK"])
    target_at.run_at_cmd("AT+KGPIOCFG=" + GPIO_str[0] + ",1,0", timeout, ["OK"])
    target_at.run_at_cmd("AT+KGPIOCFG=" + GPIO_str[2] + ",1,0", timeout, ["OK"])
    target_at.run_at_cmd("AT+KGPIOCFG=" + GPIO_str[4] + ",1,0", timeout, ["OK"])

# -------------------------- Module Initialization ----------------------------------
def A_HL_INT_PWR_WESHDOWN_0000(target_at, read_config, otii_setup_teardown, weshdown_tear_down, non_network_tests_setup_teardown):
    """
    Check WESHDOWN AT Commands. Nominal/Valid use case
    """
    print("\nA_HL_INT_PWR_WESHDOWN_0000 TC Start:\n")
    test_environment_ready = "Ready"
    print("\n------------Test's preambule Start------------")

    phase = int(read_config.findtext("autotest/Features_PHASE"))
    if phase < 2:
        pytest.skip("Phase < 2 : No AT+WESHDOWNxxx commands")

    # Variable Init
    timeout = 15
    GPIO_str = read_config.findtext("autotest/Enabled_GPIO")
    print ("GPIO_str: ", GPIO_str)

    test_nb = ""
    test_ID = "A_HL_INT_PWR_WESHDOWN_0000"
    PRINT_START_FUNC(test_nb + test_ID)

    print("\n------------Test's preambule End------------")

    # Start Test
    print("\n------------Test Case Start------------")

    try:
        otii_object = otii_setup_teardown
        if not otii_object:
            raise Exception("OTII device not connected")
        devices = otii_object.get_devices()
        proj = otii_object.get_active_project()
        my_arc = devices[0]

        # Check +WESHDOWN AT Test Command
        # target_at.run_at_cmd("AT+WESHDOWN=?", timeout, ["\+WESHDOWN\:\s\(0\-2\)\,\(" + GPIO_str + "\)", "OK"])

        # Check +WESHDOWN AT Read Command
        target_at.run_at_cmd("AT+WESHDOWN?", timeout, [r"\+WESHDOWN:\s0", "OK"])

        # Check +WESHDOWN AT Write Commands
        # Disable emergency shutdown feature by GPIO
        target_at.run_at_cmd("AT+WESHDOWN=0", timeout, ["OK"])

        # Enable emergency shutdown feature by GPIO, using first available GPIO pin
        target_at.run_at_cmd("AT+WESHDOWN=1," + GPIO_str[0], timeout, ["OK"])
        target_at.run_at_cmd("AT+WESHDOWN?", timeout, [r"\+WESHDOWN:\s1," + GPIO_str[0], "OK"])
        # Verify GPIO pin successfully assigned to WESHDOWN
        target_at.run_at_cmd("AT+KGPIOCFG=" + GPIO_str[0] + ",1,1", timeout, ["ERROR"])

        # Verify only one GPIO at a time can be configured for emergency shutdown - use next available GPIO pin
        target_at.run_at_cmd("AT+WESHDOWN=1," + GPIO_str[2], timeout, ["OK"])
        target_at.run_at_cmd("AT+WESHDOWN?", timeout, [r"\+WESHDOWN:\s1," + GPIO_str[2], "OK"])
        target_at.run_at_cmd("AT+KGPIOCFG=" + GPIO_str[2] + ",1,1", timeout, ["ERROR"])

        # Verify only one GPIO at a time can be configured for emergency shutdown - switch to occupied pin
        target_at.run_at_cmd("AT+KTEMPMON=1,90,0,2,30," + GPIO_str[4], timeout, ["OK"])
        target_at.run_at_cmd("AT+WESHDOWN=1," + GPIO_str[4], timeout, ["ERROR"])

        # Trigger emergency shutdown and verify no AT commands can be sent
        target_at.run_at_cmd("AT+WESHDOWN=2", timeout, ["OK"])
        try:
            print("\nVerify device entered Stand-by mode...")
            time.sleep(30)
            target_at.run_at_cmd("AT", timeout, ["OK"])
            VarGlobal.statOfItem = "NOK"
            raise Exception("AT command was sent in Stand-by mode")
        except:
            print("\n\nUnable to send AT commands while in emergency shutdown")

        # set wakeup pin
        print("set up wakeup pin")
        my_arc.set_gpo(1,True)
        SagSleep(1000)
        # unset wakeup pin
        my_arc.set_gpo(1,False)
        SagSleep(12000)

        # Verify configuration is saved in non-volatile memory and is still effective after power cycle
        target_at.run_at_cmd("AT", timeout, ["ERROR|OK"])
        target_at.run_at_cmd("AT+WESHDOWN?", timeout, [r"\+WESHDOWN:\s1," + GPIO_str[2], "OK"])
        target_at.run_at_cmd("AT+KTEMPMON?", timeout, [r"\+KTEMPMON:\s1,90,0,2,30," + GPIO_str[4], "OK"])

    except Exception as err_msg :
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)
    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)

swilog.info("\n----- Program End -----\n")

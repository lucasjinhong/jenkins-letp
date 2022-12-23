"""
SIM AT commands test cases :: CLCK.

originated from A_HL_Common_NS_CLCK_0001.py.PY validation test script.
"""

import time
import pytest
import VarGlobal
from autotest import (
    PRINT_START_FUNC,
    PRINT_TEST_RESULT,
    format_at_response,
    SWI_Reset_Module,
    SWI_Check_Module,
    SWI_Check_SIM_Ready,
)
from autotest import pytestmark  # noqa # pylint: disable=unused-import

timeout = 15


def A_HL_INT_SIM_CLCK_0000(target_at, read_config, non_network_tests_setup_teardown):
    """Check CLCK AT Command. Nominal/Valid use case."""
    print("\nA_HL_INT_SIM_CLCK_0000 TC Start:\n")
    print("\n------------Test's preambule Start------------")
    state = non_network_tests_setup_teardown
    if state == "OK":
        print("General Test Setup Success")

    # Variable Init
    SIM_Pin1 = read_config.findtext("autotest/PIN1_CODE")
    HARD_INI = read_config.findtext("autotest/HARD_INI")
    if "HL78" in HARD_INI:
        CLCK_rsp = r'\("SC","PN","PU","PS"\)'
    elif "RC51" in HARD_INI:
        CLCK_rsp = r'\("AB","AC","AG","AI","AO","IR","OI","OX","SC","FD","PN","PU","PP","PC","PF"\)'

    if not SIM_Pin1:
        pytest.skip("PIN1_CODE is blank")

    test_nb = ""
    test_ID = "A_HL_INT_SIM_CLCK_0000"
    PRINT_START_FUNC(test_nb + test_ID)

    print("\n----- Testing Start -----\n")

    try:
        target_at.run_at_cmd(
            "AT+CLCK=?", timeout, [r'\+CLCK: ' + CLCK_rsp, "OK"])

        # Make sure if the SIM is locked or not
        lock_resp = format_at_response(
            target_at.run_at_cmd('AT+CLCK="SC",2', timeout, ["OK"])
        )
        lock_resp = lock_resp[0]

        if lock_resp.find("+CLCK: 1") == -1:
            # SIM is unlocked
            # Lock SIM card
            target_at.run_at_cmd('AT+CLCK="SC",1,"' + SIM_Pin1 + '"', timeout, ["OK"])

            target_at.run_at_cmd('AT+CLCK="SC",2', timeout, [r'\+CLCK: 1', "OK"])

            # Restart module
            SWI_Reset_Module(target_at, HARD_INI)
            print("Sleep for 15 seconds after rebooting...")
            time.sleep(15)

            SWI_Check_Module(target_at)

            target_at.run_at_cmd("AT+CEREG=0", timeout, ["OK"])

            print("Sleep for 10 seconds after CEREG=0...")
            time.sleep(10)

            SWI_Check_SIM_Ready(target_at, SIM_Pin1)

            target_at.run_at_cmd('AT+CLCK="SC",2', timeout, [r'\+CLCK: 0', "OK"])
        else:
            # SIM is locked
            # Unlock SIM card
            target_at.run_at_cmd('AT+CLCK="SC",0,"' + SIM_Pin1 + '"', timeout, ["OK"])

            target_at.run_at_cmd('AT+CLCK="SC",2', timeout, [r'\+CLCK: 0', "OK"])

            # Lock SIM card
            target_at.run_at_cmd('AT+CLCK="SC",1,"' + SIM_Pin1 + '"', timeout, ["OK"])

            target_at.run_at_cmd('AT+CLCK="SC",2', timeout, [r'\+CLCK: 1', "OK"])

    except Exception as err_msg:
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)

    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)

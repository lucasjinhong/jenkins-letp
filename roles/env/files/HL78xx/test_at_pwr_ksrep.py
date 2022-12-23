"""
Power AT commands test cases :: KSREP.

originated from A_HL_Common_MECS_KSREP_0001.PY validation test script.
"""

import time
import VarGlobal
from autotest import PRINT_START_FUNC, PRINT_TEST_RESULT, format_at_response, SWI_Reset_Module
from autotest import pytestmark  # noqa # pylint: disable=unused-import

timeout = 15


def A_HL_INT_PWR_KSREP_0000(target_at, read_config, non_network_tests_setup_teardown):
    """Check KSREP AT Command. Nominal/Valid use case."""
    print("\nA_HL_INT_PWR_KSREP_0000 TC Start:\n")
    print("\n------------Test's preambule Start------------")
    state = non_network_tests_setup_teardown
    if state == "OK":
        print("General Test Setup Success")

    # Variable Init
    AT_CCID = int(read_config.findtext("autotest/Features_AT_CCID"))
    AT_percent_CCID = int(read_config.findtext("autotest/Features_AT_percent_CCID"))
    HARD_INI = read_config.findtext("autotest/HARD_INI")

    if AT_CCID:
        target_at.run_at_cmd("AT+CCID", timeout, [r"\+CCID: *", "OK"])
        if "RC51" in HARD_INI:
            target_at.run_at_cmd("AT+ICCID", timeout, ["ICCID: *", "OK"])

    if AT_percent_CCID:
        target_at.run_at_cmd("AT%CCID", timeout, ["%CCID: ", "OK"])

    # save default +KSREP
    answer = format_at_response(
        target_at.run_at_cmd("AT+KSREP?", timeout, [r"\+KSREP: ", "OK"])
    )
    #ksrep = answer[0].split(",")[0]
    ksrep = answer[0].split(",")[0][8:]
    if ksrep == "0":
        target_at.run_at_cmd("AT+KSREP=1", timeout, ["OK"])

    test_nb = ""
    test_ID = "A_HL_INT_PWR_KSREP_0000"
    PRINT_START_FUNC(test_nb + test_ID)

    print("\n----- Testing Start -----\n")

    try:
        target_at.run_at_cmd("AT", timeout, ["OK"])

        # AT+CMEE?
        result = format_at_response(
            target_at.run_at_cmd("AT+CMEE?", timeout, [r"\+CMEE: ", "OK"])
        )
        result = result[0].split(",")[0][8:]
        # default cmee
        if result:
            cmee = result
            print("\nDefault cmee is: " + cmee)
        else:
            cmee = "1"

        target_at.run_at_cmd("AT+CMEE=1", timeout, ["OK"])

        target_at.run_at_cmd("AT+CREG=0", timeout, ["OK"])

        SWI_Reset_Module(target_at, HARD_INI)

        target_at.run_at_cmd("ATE0", timeout, ["OK"])

        # AT+CMEE=1
        target_at.run_at_cmd("AT+CMEE=1", timeout, ["OK"])

        # AT+KSREP=?
        target_at.run_at_cmd("AT+KSREP=?", timeout, [r"\+KSREP: \(0-1\)", "OK"])

        # AT+CPIN?
        response = format_at_response(target_at.run_at_cmd("AT+CPIN?", timeout, ["OK"]))
        result = False
        if "+CPIN: READY" in response:
            result = True
        if result:
            resp = r"\+KSREP: 1,0"
        else:
            resp = r"\+KSREP: 1,1"

        # AT+KSREP?
        target_at.run_at_cmd("AT+KSREP?", timeout, [resp, "OK"])

        # AT+KSREP=x
        for x in [0, 1]:
            target_at.run_at_cmd("AT+KSREP=" + str(x), timeout, ["OK"])

        print("")
        print("Restore setting")
        # AT+KSREP=ksrep

        target_at.run_at_cmd("AT+KSREP=" + ksrep, timeout, ["OK"])

        # Restore default cmee
        target_at.run_at_cmd("AT+CMEE=" + cmee, timeout, ["OK"])

        # Check point 1
        if VarGlobal.statOfItem != "OK":
            raise Exception("Check point failed")

    except Exception as err_msg:
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)

    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)

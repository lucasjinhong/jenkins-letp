"""
Bearer AT commands test cases :: CGACT.

originated from A_HL_Common_GPRS_CGACT_0001.PY validation test script.
"""
import time
import ast
import pytest
import VarGlobal
from autotest import (PRINT_START_FUNC, PRINT_TEST_RESULT, format_at_response, SWI_Reset_Module)
from autotest import pytestmark  # noqa # pylint: disable=unused-import
from autotest import *

timeout = 20  # noqa # pylint: disable=unused-import

@pytest.fixture()
def cgact_setup_teardown(network_tests_setup_teardown, target_at, read_config):
    """Test case setup and teardown."""
    state = network_tests_setup_teardown

    if state == "OK":
        print("Test Setup Success")

    print("\nA_HL_INT_BEARER_CGACT_0000 TC Start:\n")

    print("\n------------Test's preambule Start------------")
    # Requires Amarisoft SIM Card for the test case
    Network = read_config.findtext("autotest/Network")
    if "amarisoft" not in str.lower(Network):
        raise Exception("Problem: Amarisoft SIM and Config should be used.")

    # Variable Init
    HARD_INI = read_config.findtext("autotest/HARD_INI")


    # default KCARRIERCFG
    result = format_at_response(target_at.run_at_cmd("AT+KCARRIERCFG?", timeout))
    if result:
        kcarriercfg = result[0].split(": ")[1]

        print("\nDefault kcarriercfg is: " + kcarriercfg)

    if kcarriercfg != "1":
        # default CGDCONT
        cgdcont = []
        result = format_at_response(target_at.run_at_cmd("AT+CGDCONT?", timeout, ["OK"]))
        for line_answer in result:
            cgdcont.append(line_answer.split(": ")[1])
            print("\nDefault cgdcont is: " + line_answer)

        # AT+CFUN=0 is needed due to ALT1250-1912/DIZZY-2257 (Since RK_02.82)
        target_at.run_at_cmd("AT+CFUN=0", timeout, ["OK"])

        # KCARRIERCFG=1
        target_at.run_at_cmd("AT+KCARRIERCFG=1", timeout*10, ["OK"])

        # Restart module
        SWI_Reset_Module(target_at, HARD_INI)

    test_nb = ""
    test_ID = "A_HL_INT_BEARER_CGACT_0000"
    PRINT_START_FUNC(test_nb + test_ID)

    print("\n----- Testing Start -----\n")
    yield test_ID
    print("\n----- CGACT TearDown -----\n")

    if kcarriercfg != "1":
        # Restore default KCARRIERCFG
        # AT+CFUN=0 is needed due to ALT1250-1912/DIZZY-2257 (Since RK_02.82)
        target_at.run_at_cmd("AT+CFUN=0", timeout, ["OK"])
        time.sleep(timeout)
        target_at.run_at_cmd("AT+KCARRIERCFG=" + kcarriercfg, timeout*10, ["OK"])

        # Restart module
        SWI_Reset_Module(target_at, HARD_INI)

        # Restore default CGDCONT
        for cgdcont_elem in cgdcont:
            target_at.run_at_cmd("AT+CGDCONT=" + cgdcont_elem, timeout, ["OK"])


def A_HL_INT_BEARER_CGACT_0000(target_at, read_config, cgact_setup_teardown):
    """Check CGACT AT Command. Nominal/Valid use case."""

    # Variable Init
    PARAM_GPRS_APN = ast.literal_eval(read_config.findtext("autotest/Network_APN"))
    PARAM_GPRS_PDP = ast.literal_eval(read_config.findtext("autotest/Network_PDP_type"))
    MAX_PDP_CONTEXT = int(read_config.findtext("autotest/Network_MAX_PDP_context"))
    SOFT_INI_Soft_Version = read_config.findtext("autotest/SOFT_INI_Soft_Version")
    Soft_Version = two_digit_fw_version(SOFT_INI_Soft_Version)

    test_ID = cgact_setup_teardown

    # Start Test
    print("\n------------Test Case Start------------")

    try:
        # AT+CGACT?
        cgact = target_at.run_at_cmd("AT+CGACT?", timeout, ["\r\nOK"])

        # Modify script due to HYB-354
        if Soft_Version >= "05.04.00.00":
            target_at.run_at_cmd(
                "AT+CGACT?",
                timeout,
                [r"\+CGACT: 2,0", r"\+CGACT: 3,1", r"\+CGACT: 4,0", r"\+CGACT: 6,0", r"\+CGACT: 7,0", r"\+CGACT: 10,0", r"\+CGACT: 11,0", "OK"],
            )
        else:
            for i in range(0, MAX_PDP_CONTEXT):
                assert cgact.split("+CGACT: ")[i + 1].split(",")[0] == str(i + 1), \
                "MAX_PDP_CONTEXT doesn't match"

        # undefine PDP context
        time.sleep(timeout)
        for i in range(0, 2):
            target_at.run_at_cmd("AT+CGDCONT=%d" % (i + 3), timeout * 3, ["OK"])

        # AT+CGDCONT
        for i in range(0, 2):
            target_at.run_at_cmd(
                "AT+CGDCONT="
                + str(i + 3)
                + ',"'
                + PARAM_GPRS_PDP[i]
                + '","'
                + PARAM_GPRS_APN[i] + '"',
                timeout,
                ["OK"],
            )

        # AT+CGACT=?
        target_at.run_at_cmd("AT+CGACT=?", timeout, [r"\+CGACT: \(0-1\)", "OK"])
        # AT+CGACT?
        # Modify script due to HYB-354
        if Soft_Version >= "05.04.00.00":
            target_at.run_at_cmd(
                "AT+CGACT?",
                timeout,
                [r"\+CGACT: 2,0", r"\+CGACT: 3,1", r"\+CGACT: 4,0", r"\+CGACT: 6,0", r"\+CGACT: 7,0", r"\+CGACT: 10,0", r"\+CGACT: 11,0", "OK"],
            )
        else:
            target_at.run_at_cmd(
                "AT+CGACT?",
                timeout,
                [r"\+CGACT: 1,0", r"\+CGACT: 2,0", r"\+CGACT: 3,1", r"\+CGACT: 4,0", "OK"],
            )

        # AT+CGCONTRDP=?
        target_at.run_at_cmd("AT+CGCONTRDP=?", timeout, [r"\+CGCONTRDP: \(3\)", "OK"])

        # AT+CGACT=1,4
        target_at.run_at_cmd("AT+CGACT=1,4", timeout, ["OK"])

        # Modify script due to HYB-354
        if Soft_Version >= "05.04.00.00":
            target_at.run_at_cmd(
                "AT+CGACT?",
                timeout,
                [r"\+CGACT: 2,0", r"\+CGACT: 3,1", r"\+CGACT: 4,1", r"\+CGACT: 6,0", r"\+CGACT: 7,0", r"\+CGACT: 10,0", r"\+CGACT: 11,0", "OK"],
            )
        else:
            target_at.run_at_cmd(
                "AT+CGACT?",
                timeout,
                [r"\+CGACT: 1,0", r"\+CGACT: 2,0", r"\+CGACT: 3,1", r"\+CGACT: 4,1", "OK"],
            )

        # AT+CGCONTRDP=?
        target_at.run_at_cmd("AT+CGCONTRDP=?", timeout, [r"\+CGCONTRDP: \(3,4\)", "OK"])

        # AT+CGCONTRDP=3
        target_at.run_at_cmd("AT+CGCONTRDP=3", timeout, [r"\+CGCONTRDP: 3,?,*", "OK"])

        # AT+CGCONTRDP=4
        target_at.run_at_cmd("AT+CGCONTRDP=4", timeout, [r"\+CGCONTRDP: 4,?,*", "OK"])

        # AT+CGACT=0,4
        target_at.run_at_cmd("AT+CGACT=0,4", timeout, ["OK"])
        # Modify script due to HYB-354
        if Soft_Version >= "05.04.00.00":
            target_at.run_at_cmd(
                "AT+CGACT?",
                timeout,
                [r"\+CGACT: 2,0", r"\+CGACT: 3,1", r"\+CGACT: 4,0", r"\+CGACT: 6,0", r"\+CGACT: 7,0", r"\+CGACT: 10,0", r"\+CGACT: 11,0", "OK"],
            )
        else:
            target_at.run_at_cmd(
                "AT+CGACT?",
                timeout,
                [r"\+CGACT: 1,0", r"\+CGACT: 2,0", r"\+CGACT: 3,1", r"\+CGACT: 4,0", "OK"],
            )

        # AT+CGCONTRDP=?
        target_at.run_at_cmd("AT+CGCONTRDP=?", timeout, [r"\+CGCONTRDP: \(3\)", "OK"])

        # undefine PDP context
        target_at.run_at_cmd("AT+CGDCONT=4", timeout, ["OK"])

    except Exception as err_msg:
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)

    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)

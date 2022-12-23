"""
SIM AT commands test cases :: CCIS.

originated from A_HL_Common_MECS_CCID_0001.PY validation test script.
"""

import pytest
import time
import os
import re
import VarGlobal
from autotest import *
from autotest import PRINT_START_FUNC, PRINT_TEST_RESULT, C_TIMER_LOW
from autotest import pytestmark  # noqa # pylint: disable=unused-import

timeout = 15


def A_HL_INT_SIM_CCID_0000(target_at, read_config, non_network_tests_setup_teardown):
    """Check CCID AT Command. Nominal/Valid use case."""
    print("\nA_HL_INT_SIM_CCID_0000 TC Start:\n")
    print("\n------------Test's preambule Start------------")
    state = non_network_tests_setup_teardown
    if state == "OK":
        print("General Test Setup Success")

    # Variable Init
    SIM_Pin1 = read_config.findtext("autotest/PIN1_CODE")
    SIM_CCID = read_config.findtext("autotest/SIM_CCID")
    AT_CCID = int(read_config.findtext("autotest/Features_AT_CCID"))
    AT_percent_CCID = int(read_config.findtext("autotest/Features_AT_percent_CCID"))
    HARD_INI = read_config.findtext("autotest/HARD_INI")
    SOFT_INI_Soft_Version = read_config.findtext("autotest/SOFT_INI_Soft_Version")
    Soft_Version = two_digit_fw_version(SOFT_INI_Soft_Version)
    cmd_resp = "ERROR"

    if not SIM_Pin1:
        pytest.skip("PIN1_CODE is blank")
    if not SIM_CCID:
        pytest.skip("SIM_CCID is blank")

    if AT_CCID:
        target_at.run_at_cmd("AT+CCID", timeout, [r"\+CCID: *", "OK"])
        if "RC51" in HARD_INI:
            target_at.run_at_cmd("AT+ICCID", timeout, ["ICCID: *", "OK"])

    if AT_percent_CCID:
        target_at.run_at_cmd("AT%CCID", timeout, [r"\%CCID: *", "OK"])

    test_nb = ""
    test_ID = "A_HL_INT_SIM_CCID_0000"
    PRINT_START_FUNC(test_nb + test_ID)
    VarGlobal.statOfItem = "OK"

    print("\n------------Test's preambule End------------")

    # Start Test
    print("\n------------Test Case Start------------")

    try:
        if AT_percent_CCID:

            target_at.run_at_cmd("AT%CCID=?", C_TIMER_LOW, ["OK"])

            target_at.run_at_cmd("AT%CCID", C_TIMER_LOW, [r"\%CCID: " + SIM_CCID, "OK"])

        if AT_CCID:

            if Soft_Version >= "04.07.00.00":
                target_at.run_at_cmd("AT+CCID=?", C_TIMER_LOW, [cmd_resp])
            else:
                target_at.run_at_cmd("AT+CCID=?", C_TIMER_LOW, ["OK"])

            target_at.run_at_cmd("AT+CCID?", C_TIMER_LOW, [r"\+CCID: " + SIM_CCID, "OK"])

            target_at.run_at_cmd("AT+CCID", C_TIMER_LOW, [r"\+CCID: " + SIM_CCID, "OK"])

            if "RC51" in HARD_INI:

                target_at.run_at_cmd("AT+ICCID=?", C_TIMER_LOW, ["OK"])

                target_at.run_at_cmd("AT+ICCID", C_TIMER_LOW, ["ICCID: " + SIM_CCID, "OK"])

        if not (AT_percent_CCID or AT_CCID):
            VarGlobal.statOfItem = "NOK"

    except Exception as err_msg:
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)

    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)

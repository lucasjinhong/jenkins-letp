"""
Devices AT commands test cases :: DSR
originated from A_HL_Common_V25TER_ATandS_0001.PY validation test script
"""

import pytest
import time
import os
import VarGlobal
import re
import com
from autotest import *

def A_HL_INT_DEV_DSR_0000(target_at, read_config, network_tests_setup_teardown):
    """
    Check DSR AT Command. Nominal/Valid use case
    """
    print("\nA_HL_INT_DEV_DSR_0000 TC Start:\n")
    test_environment_ready = "Ready"

    # Variable Init
    HARD_INI = read_config.findtext("autotest/HARD_INI")
    AT_CCID = int(read_config.findtext("autotest/Features_AT_CCID"))
    AT_percent_CCID = int(read_config.findtext("autotest/Features_AT_percent_CCID"))
    phase = int(read_config.findtext("autotest/Features_PHASE"))
    if phase == 0:
        pytest.skip("Phase 0 : No DSR feature")

    if AT_CCID:
        SagSendAT(target_at, 'AT+CCID\r')
        SagWaitnMatchResp(target_at, ['\r\n+CCID: *\r\n'], 4000)
        SagWaitnMatchResp(target_at, ['OK'], 4000)
        if "RC51" in HARD_INI:
            SagSendAT(target_at, 'AT+ICCID\r')
            SagWaitnMatchResp(target_at, ['\r\nICCID: *\r\n'], 4000)
            SagWaitnMatchResp(target_at, ['OK'], 4000)

    if AT_percent_CCID:
        SagSendAT(target_at, 'AT%CCID\r')
        SagWaitnMatchResp(target_at, ['\r\n%CCID: *\r\n'], 4000)
        SagWaitnMatchResp(target_at, ['\r\nOK\r\n'], 4000)

    test_nb = ""
    test_ID = "A_HL_INT_DEV_DSR_0000"
    PRINT_START_FUNC(test_nb + test_ID)
    dsr = ""

    print("\n----- Testing Start -----\n")

    try:
        # Default DSR config
        SagSendAT(target_at, 'AT&V\r')
        answer = SagWaitResp(target_at, ["\r\n*\r\n\r\nOK\r\n"], C_TIMER_LOW)
        if "HL78" in HARD_INI:
            result = SagMatchResp(answer, ["\r\nACTIVE PROFILE:\r\n*&S*\r\n*"])
            if result:
                dsr = "&S" + answer.split("\r\n")[2].split("&S")[1].split(" ")[0]
        elif "RC51" in HARD_INI:
            result = SagMatchResp(answer, ["\r\n*&S:*\r\n"])
            if result:
                dsr = "&S" + answer.split("&S: ")[1].split(";")[0]
        print("\nDefault DSR is: " + dsr)

        # AT&S0 : DSR signal is always active
        SagSendAT(target_at, 'AT&S0\r')
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], C_TIMER_LOW)

        # Display Current Configuration
        SagSendAT(target_at, 'AT&V\r')
        if "HL78" in HARD_INI:
            SagWaitnMatchResp(target_at, ["\r\nACTIVE PROFILE:\r\n*&S0*\r\n\r\nOK\r\n"], C_TIMER_LOW)
        elif "RC51" in HARD_INI:
            SagWaitnMatchResp(target_at, ["\r\n*&S: 0;*\r\n\r\nOK\r\n"], C_TIMER_LOW)

        SagSleep(2000)
        if target_at.dsr:
            print("DSR signal is active")
        else:
            print("Problem: DSR signal is not active")
            VarGlobal.statOfItem="NOK"

        # AT&S1 : DSR signal is always inactive
        SagSendAT(target_at, 'AT&S1\r')
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], C_TIMER_LOW)

        # Display Current Configuration
        SagSendAT(target_at, 'AT&V\r')
        if "HL78" in HARD_INI:
            SagWaitnMatchResp(target_at, ["\r\nACTIVE PROFILE:\r\n*&S1*\r\n\r\nOK\r\n"], C_TIMER_LOW)
        elif "RC51" in HARD_INI:
            SagWaitnMatchResp(target_at, ["*&S: 1;*\r\n\r\nOK\r\n"], C_TIMER_LOW)

        SagSleep(2000)
        if target_at.dsr:
            print("Problem: DSR signal is active")
            VarGlobal.statOfItem="NOK"
        else:
            print("DSR signal is not active")

    except Exception as err_msg :
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)

    if dsr != "":
        # Restore default DSR
        SagSendAT(target_at, 'AT%s\r' % dsr)
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], C_TIMER_LOW)

    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)

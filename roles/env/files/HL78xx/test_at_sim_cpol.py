"""
SIM AT commands test cases :: CPOL
originated from A_HL_Common_NS_CPOL_0001.PY validation test script
"""

import pytest
import time
import os
import VarGlobal
from autotest import *

def A_HL_INT_SIM_CPOL_0000(target_at, read_config, network_tests_setup_teardown):
    """
    Check CPOL AT Command. Nominal/Valid use case
    """

    print("\nA_HL_INT_SIM_CPOL_0000 TC Start:\n")
    test_environment_ready = "Ready"

    print("\n------------Test's preambule Start------------")

    # Variable Init
    SIM_Pin1 = read_config.findtext("autotest/PIN1_CODE")
    if not SIM_Pin1:
        pytest.skip("PIN1_CODE is blank")

    test_nb = ""
    test_ID = "A_HL_INT_SIM_CPOL_0000"
    PRINT_START_FUNC(test_nb + test_ID)

    # Start Test
    print("\n------------Test Case Start------------")

    try:
        # AT+CPLS=2
        SagSendAT(target_at, "AT+CPLS=2\r")
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 4000)

        # AT+CPOL=?
        SagSendAT(target_at, "AT+CPOL=?\r")
        SagWaitnMatchResp(target_at, ["\r\n+CPOL: *\r\n\r\nOK\r\n"], 4000)

        # AT+CPOL?
        #MAI watching. Test SIM shall have EF_HPLMNwAct set and UST service set as well and expected response updated accordingly
        SagSendAT(target_at, "AT+CPOL?\r")
        #CFO: Update
        #SagWaitnMatchResp(target_at, ["\r\n+CPOL: *\r\n\r\nOK\r\n"], 10000)
        SagWaitnMatchResp(target_at, ["*\r\nOK\r\n"], 10000)

        # AT+CPLS=0
        SagSendAT(target_at, "AT+CPLS=0\r")
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 4000)

        # AT+CPOL?
        #MAI watching. Test SIM shall have EF PLMNAct and UST set as well set and expected response updated accordingly
        SagSendAT(target_at, "AT+CPOL?\r")
        #CFO: Update
        #SagWaitnMatchResp(target_at, ["\r\n+CPOL: *\r\n\r\nOK\r\n"], 10000)
        SagWaitnMatchResp(target_at, ["*\r\nOK\r\n"], 10000)

    except Exception as err_msg :
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)

    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)


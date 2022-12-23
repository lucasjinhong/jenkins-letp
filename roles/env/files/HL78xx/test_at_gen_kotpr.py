import pytest
import swilog
import pexpect
import VarGlobal
from autotest import *

swilog.info( "\n----- Program start -----\n")

# -------------------------- Module Initialization ----------------------------------
def A_HL_INT_GEN_KOTPR_0000(target_at, read_config, non_network_tests_setup_teardown):
    """
    Check KOTPR AT commands. Nominal/Valid use case
    """
    print("\nA_HL_GEN_KOTPR_0000 TC Start:\n")
    test_environment_ready = "Ready"

    test_nb = ""
    test_ID = "A_HL_GEN_KOTPR_0000"
    PRINT_START_FUNC(test_nb + test_ID)

    # Start Test
    print("\n------------Test Case Start------------")

    try:
        # Check KOTPR AT Test Command
        SagSendAT(target_at, "AT+KGSN=3\r")
        answer = SagWaitResp(target_at, ["*\r\nOK\r\n"], 2000)
        fsn = '"' + answer.split("\r\n")[1].split(" ")[1] + '"'

        SagSendAT(target_at, "AT+KOTPR=\"FSN\"\r")
        answer = SagWaitResp(target_at, ["*\r\nOK\r\n"], 2000)
        fsn_result = answer.split("\r\n")[1].split(" ")[1]

        if (fsn != fsn_result):
            VarGlobal.statOfItem = "NOK"

        SagSendAT(target_at, "AT+CGSN\r")
        answer = SagWaitResp(target_at, ["*\r\nOK\r\n"], 2000)
        imei = answer.split("\r\n")[1]

        SagSendAT(target_at, "AT+KOTPR=\"IMEI\"\r")
        answer = SagWaitResp(target_at, ["*\r\nOK\r\n"], 2000)
        imei_result = answer.split("\r\n")[1].split(" ")[1]

        if (imei != imei_result):
            VarGlobal.statOfItem = "NOK"

    except Exception as err_msg :
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)
    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)

swilog.info( "\n----- Program End -----\n")

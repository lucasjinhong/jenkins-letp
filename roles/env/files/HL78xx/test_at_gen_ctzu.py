import pytest
import swilog
import pexpect
import VarGlobal
from autotest import *

swilog.info( "\n----- Program start -----\n")

# -------------------------- Module Initialization ----------------------------------
def A_HL_INT_GEN_CTZU_0000(target_at, read_config, non_network_tests_setup_teardown):
    """
    Check CTZU AT commands. Nominal/Valid use case
    """
    print("\nA_HL_GEN_CTZU_0000 TC Start:\n")
    test_environment_ready = "Ready"

    test_nb = ""
    test_ID = "A_HL_GEN_CTZU_0000"
    PRINT_START_FUNC(test_nb + test_ID)

    # Start Test
    print("\n------------Test Case Start------------")

    try:
        # Check CTZU AT Test Command
        SagSendAT(target_at, "AT+CTZU?\r")
        answer = SagWaitResp(target_at, ["*\r\nOK\r\n"], 2000)
        result = answer.split("\r\n")[1].split( )[1]
        print(("\nDefault CTZU status is: "+result))

        if (result == "0"):
           ctzu_value = "1"
        elif (result == "1"):
           ctzu_value = "0"
        else:
           VarGlobal.statOfItem = "NOK"

        # Set CTZU new value
        SagSendAT(target_at, "AT+CTZU=%s\r"%ctzu_value)
        answer = SagWaitResp(target_at, ["*\r\nOK\r\n"], 2000)

        # Check that the new value has been correctly set
        SagSendAT(target_at, "AT+CTZU?\r")
        answer = SagWaitResp(target_at, ["*\r\nOK\r\n"], 2000)
        set_result = answer.split("\r\n")[1].split( )[1]
        if (set_result != ctzu_value):
           VarGlobal.statOfItem = "NOK"
           raise Exception("Set CTZU parameter failed")

        # Set CTZU back to default value
        SagSendAT(target_at,"AT+CTZU=%s\r"% result)
        answer = SagWaitResp(target_at, ["*\r\nOK\r\n"], 2000)

    except Exception as err_msg :
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)
    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)

swilog.info( "\n----- Program End -----\n")

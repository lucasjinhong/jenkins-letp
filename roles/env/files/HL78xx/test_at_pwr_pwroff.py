"""
Power AT commands test cases :: CPOF/CPWROFF
originated from A_HL_Common_MECS_CPWROFF_0001.PY validation test script
"""

import pytest
import pexpect
import time
import os
import VarGlobal
import re
from autotest import *
from otii_utility import *

def A_HL_INT_PWR_PWROFF_0000(target_at, read_config, otii_setup_teardown, non_network_tests_setup_teardown):
    """
    Check CPOF/CPWROFF AT Command. Nominal/Valid use case
    """
    print("\nA_HL_INT_PWR_PWROFF_0000 TC Start:\n")
    test_environment_ready = "Ready"

    print("\n------------Test's preambule Start------------")

    test_nb = ""
    test_ID = "A_HL_INT_PWR_PWROFF_0000"
    PRINT_START_FUNC(test_nb + test_ID)

    print("\n----- Testing Start -----\n")

    try:
        print("---------- TEST CASE CPOFF ----------")

        otii_object = otii_setup_teardown
        if not otii_object:
            raise Exception("OTII device not connected")
        devices = otii_object.get_devices()
        proj = otii_object.get_active_project()
        my_arc = devices[0]

        SagSleep(1000)

        # AT+CPOF
        SagSendAT(target_at, "AT+CPOF\r")
        SagWaitnMatchResp(target_at, ['\r\nOK\r\n'], 4000)

        SagSleep(1000)

        # Check no answer for AT cmd
        target_at.send('AT')
        idx = target_at.expect(['\r\nOK\r\n', pexpect.TIMEOUT], 4)

        if idx != 1:
            print("Failed!!! Timeout expected. No answer is supposed to be returned")
            VarGlobal.statOfItem = "NOK"

        # set wakeup pin
        my_arc.set_gpo(1,True)
        my_arc.set_gpo(1,False)
        # For HL78xx.5.4.8.0 version, modify the script to wait 60 seconds after the device is powered on
        #SagSleep(HibernateBooting_Duration)
        SagSleep(100000)

        # AT
        SagSendAT(target_at, "AT\r")
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n", "\r\nERROR\r\n"], 4000)

        print("---------- TEST CASE CPWROFF ----------")

        SagSleep(1000)

        #Test Command
        SagSendAT(target_at, 'AT+CPWROFF=?\r')
        SagWaitnMatchResp(target_at, ['\r\nOK\r\n'], 4000)

        # AT+CPWROFF
        SagSendAT(target_at, "AT+CPWROFF\r")
        SagWaitnMatchResp(target_at, ['\r\nOK\r\n'], 4000)

        SagSleep(1000)

        # Check no answer for AT cmd
        target_at.send('AT')
        idx = target_at.expect(['\r\nOK\r\n', pexpect.TIMEOUT], 4)

        if idx != 1:
            print("Failed!!! Timeout expected. No answer is supposed to be returned")
            VarGlobal.statOfItem = "NOK"

        # set wakeup pin
        my_arc.set_gpo(1,True)
        my_arc.set_gpo(1,False)

        # For HL78xx.5.4.8.0 version, modify the script to wait 60 seconds after the device is powered on
        #SagSleep(HibernateBooting_Duration)
        SagSleep(100000)

        # AT
        SagSendAT(target_at, "AT\r")
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n", "\r\nERROR\r\n"], 4000)

    except Exception as err_msg :
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)

    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)


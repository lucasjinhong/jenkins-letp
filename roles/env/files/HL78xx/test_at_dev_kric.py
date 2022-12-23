"""
Devices AT commands test cases :: KRIC
originated from A_HL_Common_MECS_KRIC_0005.PY validation test script
"""

import pytest
import time
import os
import VarGlobal
import re
from datetime import datetime
from autotest import *

def A_HL_INT_DEV_KRIC_0000(target_at, read_config, network_tests_setup_teardown):
    """
    Check KRIC AT Command. Nominal/Valid use case
    """

    print("\nA_HL_INT_DEV_KRIC_0000 TC Start:\n")
    test_environment_ready = "Ready"

    print("\n------------Test's preambule Start------------")

    # Variable Init
    SIM_Pin1 = read_config.findtext("autotest/PIN1_CODE")
    AT_CCID = read_config.findtext("autotest/Features_AT_CCID")
    AT_percent_CCID = read_config.findtext("autotest/Features_AT_percent_CCID")
    phase = int(read_config.findtext("autotest/Features_PHASE"))
    Config_Name = read_config.findtext("autotest/Network_Config/Config_Name")
    SOFT_INI_Soft_Version = read_config.findtext("autotest/SOFT_INI_Soft_Version")
    Soft_Version = two_digit_fw_version(SOFT_INI_Soft_Version)
    HARD_INI = read_config.findtext("autotest/HARD_INI")

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
        SagWaitnMatchResp(target_at, ['\r\n%CCID: *\r\n'], 2000)
        SagWaitnMatchResp(target_at, ['\r\nOK\r\n'], 2000)

    test_nb = ""
    test_ID = "A_HL_INT_DEV_KRIC_0000"
    PRINT_START_FUNC(test_nb + test_ID)

    print("\n----- Testing Start -----\n")

    try:
        # check if SIM is locked
        lockedSIM = 0
        SagSendAT(target_at, 'AT+CLCK="SC",2\r')
        lock_resp = SagWaitResp(target_at,["\r\n+CLCK: ?\r\n\r\nOK\r\n"], 4000)
        if lock_resp.find('+CLCK: 0')==-1:
            # SIM locked => unlock SIM
            lockedSIM = 1
            SagSendAT(target_at, 'AT+CLCK="SC",0,"' + SIM_Pin1 + '"\r')
            SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 4000)

        # AT+KRIC=?
        SagSendAT(target_at, "AT+KRIC=?\r")
        if (phase > 0):
            if Soft_Version <= "04.00.00.00":
                SagWaitnMatchResp(target_at, ["\r\n+KRIC: (0-242),(0),(1-5),(0,2)\r\n"], 3000)
            # Add for HL78 v5.4.4.1
            elif Soft_Version >= "05.04.04.01":
                SagWaitnMatchResp(target_at, ["\r\n+KRIC: (0-498),(0),(1-5),(0,2),(0-1)\r\n"], 3000)
            else:
                SagWaitnMatchResp(target_at, ["\r\n+KRIC: (0-242),(0),(1-5),(0,2),(0-1)\r\n"], 3000)
        else:
            SagWaitnMatchResp(target_at, ["\r\n+KRIC: (0-240),(0),(1-5),(0,2)\r\n"], 3000)
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 3000)

        # AT+KRIC?
        SagSendAT(target_at, "AT+KRIC?\r")
        answer = SagWaitResp(target_at, ["*\r\nOK\r\n"], 3000)
        if Soft_Version <= "04.00.00.00":
            result = SagMatchResp(answer, ["\r\n+KRIC: *,0,1,0\r\n"])
        else:
            result = SagMatchResp(answer, ["\r\n+KRIC: *,0,1,0,0\r\n"])
        # default KRIC
        if result:
            kric = answer.split("\r\n")[1].split(": ")[1]
            print("\nDefault kric is: "+kric)
        else:
            kric = "0,0,1,0,0"

        for k in [16, 32, 64, 128]:
            # AT+KRIC=k,0,1,0
            if Soft_Version <= "04.00.00.00":
                SagSendAT(target_at, 'AT+KRIC=%d,0,1,0\r'%k)
            else:
                SagSendAT(target_at, 'AT+KRIC=%d,0,1,0,0\r'%k)
            SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], C_TIMER_LOW)

            # AT+KRIC?
            SagSendAT(target_at, "AT+KRIC?\r")
            if Soft_Version <= "04.00.00.00":
                SagWaitnMatchResp(target_at, ["\r\n+KRIC: %d,0,1,0\r\n"%k], 3000)
            else:
                SagWaitnMatchResp(target_at, ["\r\n+KRIC: %d,0,1,0,0\r\n"%k], 3000)
            SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 3000)

            # Check KRIC value is saved in non-volatile memory after reset.
            SWI_Reset_Module(target_at, HARD_INI)

            # AT+KRIC?
            SagSendAT(target_at, "AT+KRIC?\r")
            if Soft_Version <= "04.00.00.00":
                SagWaitnMatchResp(target_at, ["\r\n+KRIC: %d,0,1,0\r\n"%k], 3000)
            else:
                SagWaitnMatchResp(target_at, ["\r\n+KRIC: %d,0,1,0,0\r\n"%k], 3000)
            SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 3000)

        # RI activated on network state change for 1 second
        if Soft_Version <= "04.00.00.00":
            SagSendAT(target_at, 'AT+KRIC=16,0,1,0\r')
        else:
            SagSendAT(target_at, 'AT+KRIC=16,0,1,0,0\r')
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], C_TIMER_LOW)

        # Deactivate network
        if Config_Name == "2G":
            SagSendAT(target_at, 'AT+CGACT=0\r')
            SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], C_TIMER_LOW)
        else:
            SagSendAT(target_at, 'AT+CFUN=0\r')
            SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], C_TIMER_LOW)

        start_time = datetime.now()
        diff_time = 0
        first_time = 0
        last_time = 0
        while diff_time <= 2000:
            ri = target_at.ri
            end_time = datetime.now()
            diff_time = (end_time - start_time).seconds * 1000.0 + (end_time - start_time).microseconds / 1000.0
            if ri:
                if first_time == 0:
                    first_time = diff_time
                last_time = diff_time

        if target_at.ri:
            VarGlobal.statOfItem = "NOK"
            print("Problem!! RI still pulsed, pls check")

        duration = (last_time - first_time) / 1000.0
        if duration == 0.0:
            VarGlobal.statOfItem = "NOK"
            print("Problem!! RI fail, pls check")
        else:
            print("pulse duration : %f second(s)"%duration)

        # RI activated on network state change for 5 seconds
        if Soft_Version <= "04.00.00.00":
            SagSendAT(target_at, 'AT+KRIC=16,0,5,0\r')
        else:
            SagSendAT(target_at, 'AT+KRIC=16,0,5,0,0\r')
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], C_TIMER_LOW)

        # Reactivate network
        if Config_Name == "2G":
            SagSendAT(target_at, 'AT+CGATT=1\r')
            SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], C_TIMER_LOW)
        else:
            SagSendAT(target_at, 'AT+CFUN=1\r')
            SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], C_TIMER_LOW)

        start_time = datetime.now()
        diff_time = 0
        first_time = 0
        last_time = 0
        while diff_time <= 7000:
            ri = target_at.ri
            end_time = datetime.now()
            diff_time = (end_time - start_time).seconds * 1000.0 + (end_time - start_time).microseconds / 1000.0
            if ri:
                if first_time == 0:
                    first_time = diff_time
                last_time = diff_time

        if target_at.ri:
            VarGlobal.statOfItem = "NOK"
            print("Problem!! RI still pulsed, pls check")

        duration = (last_time - first_time) / 1000.0
        if duration == 0.0:
            VarGlobal.statOfItem = "NOK"
            print("Problem!! RI fail, pls check")
        else:
            print("pulse duration : %f second(s)"%duration)

        # Restore default values
        SagSendAT(target_at, "AT+KRIC=" + kric + "\r")
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], C_TIMER_LOW)

        if (lockedSIM == 1):
            SagSendAT(target_at, 'AT+CLCK="SC",1,"' + SIM_Pin1 + '"\r')
            SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 4000)

    except Exception as err_msg :
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)

    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)

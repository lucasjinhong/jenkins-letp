"""
SIM AT commands test cases :: CPIN
originated from A_HL_Common_MECS_CPIN_0001.PY validation test script
"""

import pytest
import time
import os
from random import choice
from autotest import *

def A_HL_INT_SIM_CPIN_0000(target_at, read_config, non_network_tests_setup_teardown):
    """
    Check CPIN AT Command. Nominal/Valid use case
    """

    print("\nA_HL_INT_SIM_CPIN_0000 TC Start:\n")
    test_environment_ready = "Ready"

    print("\n------------Test's preambule Start------------")

    # Variable Init
    SIM_CCID = read_config.findtext("autotest/SIM_CCID")
    SIM_Pin1 = read_config.findtext("autotest/PIN1_CODE")
    SIM_Puk1 = read_config.findtext("autotest/PUK1_CODE")
    AT_CCID = int(read_config.findtext("autotest/Features_AT_CCID"))
    AT_percent_CCID = int(read_config.findtext("autotest/Features_AT_percent_CCID"))
    HARD_INI = read_config.findtext("autotest/HARD_INI")
    if "HL78" in HARD_INI:
        CGMI = "Sierra Wireless"
    elif "RC51" in HARD_INI:
        CGMI = "Sierra Wireless, Incorporated"

    if not SIM_Pin1:
        pytest.skip("PIN1_CODE is blank")
    if not SIM_Puk1:
        pytest.skip("PUK1_CODE is blank")
    if not SIM_CCID:
        pytest.skip("SIM_CCID is blank")

    SIM_Pin1_incorrect = '%04d' % choice([i for i in range(10000) if i != int(SIM_Pin1)])

    SagSendAT(target_at, 'AT+CGMI\r')
    SagWaitnMatchResp(target_at, ["\r\n" + CGMI + "\r\n\r\nOK\r\n"], 2000)

    if AT_CCID:
        SagSendAT(target_at, "AT+CCID\r")
        answer = SagWaitResp(target_at, ["*\r\nOK\r\n"], 2000)
        ccid = answer.split(": ")[1].split("\r\n")[0]
        print("\nccid is: "+ccid)

    if AT_percent_CCID:
        SagSendAT(target_at, 'AT%CCID\r')
        answer = SagWaitResp(target_at, ["*\r\nOK\r\n"], 2000)
        ccid = answer.split(": ")[1].split("\r\n")[0]
        print("\nccid is: "+ccid)

    test_nb = ""
    test_ID = "A_HL_INT_SIM_CPIN_0000"
    PRINT_START_FUNC(test_nb + test_ID)
    VarGlobal.statOfItem = "OK"

    print("\n------------Test's preambule End------------")

    # Start Test
    print("\n------------Test Case Start------------")

    try:
        # Validation test updated to avoid to list SIM TEST CCIDs
        if ccid != SIM_CCID:
            raise Exception("This script need TEST SIM")

        #AT+CMEE?
        SagSendAT(target_at, "AT+CMEE?\r")
        answer = SagWaitResp(target_at, ["*\r\nOK\r\n"], C_TIMER_LOW)
        result = SagMatchResp(answer, ["\r\n+CMEE: ?\r\n"])
        # default cmee
        if result:
            cmee = answer.split("\r\n")[1].split(": ")[1]
            print("\nDefault cmee is: "+cmee)
        else:
            cmee = "1"

        # force CMEE = 1 for test
        SagSendAT(target_at, 'AT+CMEE=1\r')
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 2000)

        # AT+CPIN=?
        SagSendAT(target_at, "AT+CPIN=?\r")
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 2000)

        # SagSleep(8000)

        # AT+CPIN?
        #MAI watching. Seems that the initial condition is not under control !!! to be fixed.
        SagSendAT(target_at, "AT+CPIN?\r")
        answer = SagWaitResp(target_at, ["\r\n+CPIN: *\r\n\r\nOK\r\n"], 2000)

        print("--------------------------------")
        print(answer)
        print("--------------------------------")
        answer_part = answer.split("\r\n")
        answer_part1_code = answer_part[1].split(": ")[1]
        print(answer_part1_code)
        respcode = ["READY","SIM PIN","SIM PUK","SIM PIN2","SIM PUK2","PH-NET PIN","PH-NET PUK","PH-NETSUB PIN","PH-NETSUB PUK","PH-SP PIN","PH-SP PUK","PH-CORP PIN","PH-CORP PUK"]
        if answer_part1_code in respcode:
            print("Response is one of these: READY,SIM PIN,SIM PUK,SIM PIN2,SIM PUK2,PH-NET PIN,PH-NET PUK,PH-NETSUB PIN,PH-NETSUB PUK,PH-SP PIN,PH-SP PUK,PH-CORP PIN,PH-CORP PUK")
        elif answer_part1_code.isdigit():
            print("Error code returned, please check the module and the SIM card.")
        else:
            print("Wrong response.")
            VarGlobal.statOfItem = "NOK"

        unlockSIM = 0
        if answer_part1_code == "READY" :

            print(" ")
            print("--------------------------force SIM PIN----------------------------")
            print(" ")
            # check if SIM is locked

            SagSendAT(target_at, 'AT+CLCK="SC",2\r')
            lock_resp = SagWaitResp(target_at,["\r\n+CLCK: ?\r\n\r\nOK\r\n"], 4000)
            if lock_resp.find('+CLCK: 1')==-1:
                # SIM unlocked => lock SIM
                unlockSIM = 1
                SagSendAT(target_at, 'AT+CLCK="SC",1,"' + SIM_Pin1 + '"\r')
                SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 4000)

            # Restart Module
            SagSleep(5000)
            SWI_Reset_Module(target_at, HARD_INI)

            # Reinit CMEE for RC51xx
            if "RC51" in HARD_INI:
                SagSendAT(target_at, 'AT+CMEE=1\r')
                SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 2000)

            SagSendAT(target_at, "AT+CPIN?\r")
            answer = SagWaitResp(target_at, ["\r\n+CPIN: *\r\n\r\nOK\r\n"], 2000)
            answer_part1_code = answer.split("CPIN: ")[1].split("\r\n")[0]

        if answer_part1_code == "SIM PIN" :

            print(" ")
            print("--------------------------TEST PIN1----------------------------")
            print(" ")
            # test pin1

            SagSendAT(target_at, 'AT+CPIN="' + SIM_Pin1_incorrect + '"\r')
            SagWaitnMatchResp(target_at, ["\r\n+CME ERROR: 16\r\n"], 2000)
            SagSendAT(target_at, 'AT+CPIN="' + SIM_Pin1 + '"\r')
            SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 40000)
            SagSendAT(target_at, "AT\r")
            SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 2000)

            SagSleep(5000)

            print(" ")
            print("--------------------------TEST PUK1----------------------------")
            print(" ")
            # cfun for puk1
            SagSleep(5000)
            SWI_Reset_Module(target_at, HARD_INI)

            # Reinit CMEE for RC51xx
            if "RC51" in HARD_INI:
                SagSendAT(target_at, 'AT+CMEE=1\r')
                SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 2000)

            SagSendAT(target_at, 'AT+CGMI\r')
            SagWaitnMatchResp(target_at, ["\r\n" + CGMI + "\r\n\r\nOK\r\n"], 2000)
            SagSendAT(target_at, 'AT\r')
            SagWaitnMatchResp(target_at, ["*OK\r\n"], 2000)
            SagSendAT(target_at, 'ATE0\r')
            SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 5000)

            # test puk1

            SagSendAT(target_at, "AT+CPIN?\r")
            SagWaitnMatchResp(target_at, ["\r\n+CPIN: SIM PIN\r\n\r\nOK\r\n"], 2000)

            # input wrong pin twice
            for x in range(0, 2):
                print("Test on time %d" % (x))
                SagSendAT(target_at, 'AT+CPIN="' + SIM_Pin1_incorrect + '"\r')
                SagWaitnMatchResp(target_at, ["\r\n+CME ERROR: 16\r\n"], 2000)

            # input wrong pin the 3rd time
            print("Test on time 3, should ask for PUK1.")
            SagSendAT(target_at, 'AT+CPIN="' + SIM_Pin1_incorrect + '"\r')
            if "HL78" in HARD_INI:
                SagWaitnMatchResp(target_at, ["\r\n+CME ERROR: 16\r\n"], 2000)
            elif "RC51" in HARD_INI:
                SagWaitnMatchResp(target_at, ["\r\n+CME ERROR: 12\r\n"], 2000)

            SagSendAT(target_at, "AT+CPIN?\r")
            SagWaitnMatchResp(target_at, ["\r\n+CPIN: SIM PUK\r\n\r\nOK\r\n"], 2000)

            # input puk1
            SagSendAT(target_at, 'AT+CPIN="' + SIM_Puk1 + '","' + SIM_Pin1 + '"\r')
            SagSleep(1500)
            SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 2000)
            SagSendAT(target_at, "ATE0\r")
            SagWaitnMatchResp(target_at, ["*OK\r\n"], 5000)
            SagSendAT(target_at, 'AT+CGMI\r')
            SagWaitnMatchResp(target_at, ["\r\n" + CGMI + "\r\n\r\nOK\r\n"], 2000)
            SagSendAT(target_at, "AT+CPIN?\r")
            SagWaitnMatchResp(target_at, ["*+CPIN: READY\r\n\r\nOK\r\n"], 2000)

        else:
            VarGlobal.statOfItem = "NOK"

        # unlock SIM
        if (unlockSIM == 1):
            SagSendAT(target_at, 'AT+CLCK="SC",0,"' + SIM_Pin1 + '"\r')
            SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 4000)

        # Restore default cmee
        SagSleep(5000)
        SagSendAT(target_at, "AT+CMEE=" + cmee + "\r")
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 2000)

    except Exception as err_msg :
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)

    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)

    # ERROR REF
    # 0     Phone failure
    # 1     No connection to phone
    # 2     Phone-adapter link reserved
    # 3     Operation not allowed
    # 4     Operation not supported
    # 5     PH-SIM PIN required
    # 6     PH-FSIM PIN required
    # 7     PH-FSIM PUK required
    # 10     SIM not inserted
    # 11     SIM PIN required
    # 12     SIM PUK required
    # 13     SIM failure
    # 14     SIM busy
    # 15     SIM wrong
    # 16     Incorrect password
    # 17     SIM PIN2 required
    # 18     SIM PUK2 required

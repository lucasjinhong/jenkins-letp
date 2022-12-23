"""
Dial/call service AT commands test cases
originated from A_HL_Common_CC_ATD_0039.PY validation test script
"""

import pytest
import time
import os
import VarGlobal
from autotest import *

def A_HL_INT_DIAL_0000(target_at, read_config, network_tests_setup_teardown):
    """
    Check dial-up call can be started (ATD*99***1) and terminated using +++, no ppp link establishment. Nominal/Valid use case.
    """

    print("\nA_HL_INT_ATD_0000 TC Start:\n")
    test_environment_ready = "Ready"

    print("\n------------Test's preambule Start------------")

    # Variable Init
    AT_CCID = int(read_config.findtext("autotest/Features_AT_CCID"))
    AT_percent_CCID = int(read_config.findtext("autotest/Features_AT_percent_CCID"))
    phase = int(read_config.findtext("autotest/Features_PHASE"))
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
        SagWaitnMatchResp(target_at, ['\r\n%CCID: *\r\n'], 4000)
        SagWaitnMatchResp(target_at, ['\r\nOK\r\n'], 4000)

    test_nb = ""
    test_ID = "A_HL_INT_DIAL_0000"
    PRINT_START_FUNC(test_nb + test_ID)
    dcd = ""

    print("\n------------Test Case Start------------")

    try:
        if phase > 0:
            # Default DCD config
            SagSendAT(target_at, 'AT&V\r')
            answer = SagWaitResp(target_at, ["\r\n*\r\n\r\nOK\r\n"], C_TIMER_LOW)
            result = SagMatchResp(answer, ["\r\nACTIVE PROFILE:\r\n*&C*\r\n"])
            if result:
                dcd = "&C" + answer.split("\r\n")[2].split("&C")[1].split(" ")[0]
                print("\nDefault DCD is: "+dcd)

            #AT&C0 : DCD line is always active
            SagSendAT(target_at, "AT&C0\r")
            SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], C_TIMER_LOW)
            SagSleep(2000)
            if target_at.cd:
                print("DCD line is active")
            else:
                print("Problem: DCD line is not active")
                VarGlobal.statOfItem="NOK"

            #AT&C1 : DCD line is active in the presence of data carrier only
            SagSendAT(target_at, "AT&C1\r")
            SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], C_TIMER_LOW)
            SagSleep(2000)
            if target_at.cd:
                print("Problem: DCD line is active")
                VarGlobal.statOfItem="NOK"
            else:
                print("DCD line is not active")

        print("***************************************************************************************************************")
        print("%s: Check ATD response with PDP context 1 in LTE Mode" % test_ID)
        print("***************************************************************************************************************")

        #1. Set module to LTE mode
        #SagSendAT(target_at, 'AT+KSRAT=5\r')
        #SagWaitnMatchResp(target_at, ['\r\nOK\r\n'], 4000)
        # 2018-01-10, tqdo, Update +KSRAT setting for HL78xx
        #if RAT_Param=="RAT_2G":
        #    SagSendAT(target_at, RAT_2G_CMD  + '\r')
        #    SagWaitnMatchResp(target_at, ['\r\nOK\r\n'], 4000)
        #elif RAT_Param=="RAT_3G":
        #    SagSendAT(target_at, RAT_3G_CMD  + '\r')
        #    SagWaitnMatchResp(target_at, ['\r\nOK\r\n'], 4000)
        #elif RAT_Param=="RAT_4G":
        #    SagSendAT(target_at, RAT_4G_CMD  + '\r')
        #    SagWaitnMatchResp(target_at, ['\r\nOK\r\n'], 4000)
        #SagSleep(10000)

        #2. Setting baud rate
        SagSendAT(target_at, 'AT+IPR=115200\r')
        SagWaitnMatchResp(target_at, ['\r\nOK\r\n'], 4000)


        #3. Check PS Attach
        SagSendAT(target_at, 'AT+CGATT?\r')
        SagWaitnMatchResp(target_at, ["\r\n+CGATT: 1\r\n"], 2000)
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 2000)

        for x in range(2):
            #4. Make call from module
            SagSendAT(target_at, 'ATD*99***1#\r')
            SagWaitnMatchResp(target_at, ['\r\nCONNECT\r\n'], 4000)

            #DATA Mode
            SagSleep(3000)
            target_at.expect(".+", 5)

            if phase > 0:
                if target_at.cd:
                    print("DCD line is active")
                else:
                    print("Problem: DCD line is not active")
                    VarGlobal.statOfItem="NOK"

            #5 +++ TO SWITCH TO COMMAND MODE
            SagSendAT(target_at, "+++")
            SagWaitnMatchResp(target_at, ['*\r\nOK\r\n'], 10000)

            SagSleep(3000)
            #Command to flush remaining DATA if any (Timeout is ignored)
            #target_at.expect([".+",pexpect.TIMEOUT], 5)
            #print "\n+++ has been treated "

            SagSendAT(target_at, 'AT\r')
            SagWaitnMatchResp(target_at, ['*\r\nOK\r\n'], 10000)

            #6. Switch to data mode
            SagSendAT(target_at, 'ATO\r')
            SagWaitnMatchResp(target_at, ['\r\nCONNECT\r\n'], 4000)
            #SagWaitnMatchResp(target_at, ['\r\nOK\r\n'], 4000)

            #DATA Mode
            SagSleep(3000)
            target_at.expect(".+", 5)

            #7. Switch to command mode
            SagSendAT(target_at, '+++')
            SagWaitnMatchResp(target_at, ['*\r\nOK\r\n'], 4000)

            SagSleep(3000)
            #Command to flush remaining DATA if any (Timeout is ignored)
            #target_at.expect([".+",pexpect.TIMEOUT], 5)
            #print "\n+++ has been treated "

            SagSendAT(target_at, 'AT\r')
            SagWaitnMatchResp(target_at, ['*\r\nOK\r\n'], 10000)

            #8. Terminate call
            SagSendAT(target_at, 'ATH\r')
            SagWaitnMatchResp(target_at, ['\r\nOK\r\n'], 4000)

            #Wait a little before doing the loop again
            SagSleep(5000)

    except Exception as err_msg :
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)

    if (phase > 0) and (dcd != ""):
        # Restore default DCD
        SagSendAT(target_at, 'AT%s\r' % dcd)
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], C_TIMER_LOW)

    # Restart the device
    SWI_Reset_Module(target_at, HARD_INI)

    PRINT_TEST_RESULT( test_ID , VarGlobal.statOfItem)

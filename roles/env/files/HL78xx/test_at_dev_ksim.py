"""
Devices AT commands test cases :: KSIMDET/KSIMSET
"""

import pytest
import time
import os
import VarGlobal
from autotest import *

def A_HL_INT_DEV_KSIM_0000(target_at, read_config):
    """
    Check KSIMDET AT Command. Nominal/Valid use case
    """

    print("\nA_HL_INT_DEV_KSIM_0000 TC Start:\n")
    test_environment_ready = "Ready"

    print("\n------------Test's preambule Start------------")

    try:
        # Variable Init
        HARD_INI = read_config.findtext("autotest/HARD_INI")
        SIM_Pin1 = read_config.findtext("autotest/PIN1_CODE")
        phase = int(read_config.findtext("autotest/Features_PHASE"))
        GPIO_str = read_config.findtext("autotest/Enabled_GPIO")
        if phase < 2:
            pytest.skip("No AT+KSIMDET/AT+KSIMSEL commands")

        # Check Module state / Restart if required
        SWI_Check_Module(target_at, AT_CMD_List_Check_Module, AT_Resp_List_Check_Module, AT_Timeout_List_Check_Module, AT_Restart_CMD, AT_Restart_Resp, Booting_Duration)

        SWI_Check_SIM_Ready(target_at, SIM_Pin1, SIM_Check_CMD, SIM_Check_RESP, SIM_SET_PIN_CMD, AT_SET_SIM_RESP, UNSOLICITED_Notif, SIM_TimeOut)

        if not VarGlobal.Init_Status in ["AT_OK", "SIM_Ready"]:
            test_environment_ready = "Not_Ready"

    except Exception as e:
        print("***** Test environment check fails !!!*****")
        print(type(e))
        print(e)
        test_environment_ready = "Not_Ready"

    print("\n----- Testing Start -----\n")

    test_nb=""
    test_ID = "A_HL_INT_DEV_KSIM_0000"
    PRINT_START_FUNC(test_nb + test_ID)

    VarGlobal.statOfItem = "OK"
    ksimdet = ""
    ksimsel = ""

    try:
        if test_environment_ready == "Not_Ready":
            VarGlobal.statOfItem="NOK"
            raise Exception("---->Problem: Test Environment Is Not Ready !!!")

        # AT+KSIMDET=?
        SagSendAT(target_at, "AT+KSIMDET=?\r")
        SagWaitnMatchResp(target_at, ["\r\n+KSIMDET: (0-1)\r\n\r\nOK\r\n"], 4000)

        # AT+KSIMSEL=?
        SagSendAT(target_at, "AT+KSIMSEL=?\r")
        SagWaitnMatchResp(target_at, ["\r\n+KSIMSEL: (0,4,9,20)\r\n\r\nOK\r\n"], 4000)

        # default KSIMDET
        # if KSIMDET is set to 1 : GPIO3 is used for SIM detection
        SagSendAT(target_at, "AT+KSIMDET?\r")
        answer = SagWaitResp(target_at, ["\r\n*\r\nOK\r\n"], 4000)
        result = SagMatchResp(answer,["*\r\n+KSIMDET: ?\r\n*"])
        if result:
            ksimdet = answer.split("\r\n")[1].split(": ")[1]
            print("\nDefault ksimdet is: "+ksimdet)

        # default KSIMSEL
        SagSendAT(target_at, "AT+KSIMSEL?\r")
        answer = SagWaitResp(target_at, ["\r\n*\r\nOK\r\n"], 4000)
        result = SagMatchResp(answer,["*\r\n+KSIMSEL: *,,*\r\n*"])
        if result:
            ksimsel = answer.split("\r\n")[1].split(": ")[1].split(",")[0]
            print("\nDefault ksimsel is: "+ksimsel)

        # default WESHDOWN
        # if WESHDOWN is set to 1 : GPIO4 is used
        SagSendAT(target_at, "AT+WESHDOWN?\r")
        answer = SagWaitResp(target_at, ["\r\n*\r\nOK\r\n"], 3000)
        result = SagMatchResp(answer,["*\r\n+WESHDOWN: *\r\n*"])
        if result:
            weshdown = answer.split("\r\n")[1].split(": ")[1]
            print("\nDefault weshdown is: "+weshdown)
        else:
            weshdown = "0"

        ### Check list of supported GPIO : KSIMDET=0 ###
        if ksimdet == "1":
            SagSendAT(target_at, "AT+KSIMDET=0\r")
            SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 3000)
            # Restart module
            SWI_Reset_Module(target_at, HARD_INI)

        GPIO_list = list(map(lambda a: int(a), GPIO_str.split(",")))
        if 3 not in GPIO_list:
            GPIO_list.insert(2,3)
        GPIO_str = str(GPIO_list).replace(" ","").replace("[","").replace("]","")

        # AT+KGPIOCFG=?
        SagSendAT(target_at, "AT+KGPIOCFG=?\r")
        SagWaitnMatchResp(target_at, ["\r\n+KGPIOCFG: (%s),(0-1),(0-2)\r\n" % GPIO_str], 3000)
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 3000)

        ### Check no +SIM notification ###
        msg = input("\nExtract SIM card and hit enter to continue\n")
        idx = target_at.expect(['\r\n+SIM: 0\r\n', pexpect.TIMEOUT], 10)
        if idx != 1:
            print("Failed!!! No +SIM notification is supposed to be returned")
            VarGlobal.statOfItem = "NOK"

        msg = input("\nInsert SIM card and hit enter to continue\n")
        idx = target_at.expect(['\r\n+SIM: 1\r\n', pexpect.TIMEOUT], 10)
        if idx != 1:
            print("Failed!!! No +SIM notification is supposed to be returned")
            VarGlobal.statOfItem = "NOK"

        # Check list of supported GPIO : KSIMDET=1
        SagSendAT(target_at, "AT+KSIMDET=1\r")
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 3000)
        # Restart module
        SWI_Reset_Module(target_at, HARD_INI)

        ### define GPIO list : no GPIO3 ###
        GPIO_list = [1,2]
        if weshdown[0] == "0":
            GPIO_list.extend([4])
        GPIO_list.extend([5,6,7,8,10,11,14,15])

        GPIO_str = str(GPIO_list).replace(" ","").replace("[","").replace("]","")

        # AT+KGPIOCFG=?
        SagSendAT(target_at, "AT+KGPIOCFG=?\r")
        SagWaitnMatchResp(target_at, ["\r\n+KGPIOCFG: (%s),(0-1),(0-2)\r\n" % GPIO_str], 3000)
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 3000)

        ### Check +SIM notification ###
        msg = input("\nExtract SIM card and hit enter to continue\n")
        SagWaitnMatchResp(target_at, ["\r\n+SIM: 0\r\n"], 10000)

        msg = input("\nInsert SIM card and hit enter to continue\n")
        SagWaitnMatchResp(target_at, ["\r\n+SIM: 1\r\n"], 10000)

        ### Check values are saved in non-volatile memory ###
        for ksd, kss in zip([0,1], [0,20]):
            # AT+KSIMDET=k
            SagSendAT(target_at, "AT+KSIMDET=%d\r" % ksd)
            SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 4000)

            # AT+KSIMDET?
            SagSendAT(target_at, "AT+KSIMDET?\r")
            SagWaitnMatchResp(target_at, ["\r\n+KSIMDET: %d\r\n\r\nOK\r\n" % ksd], 4000)

            # AT+KSIMSEL=k
            SagSendAT(target_at, "AT+KSIMSEL=%d\r" % kss)
            SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 4000)

            # AT+KSIMSEL?
            SagSendAT(target_at, "AT+KSIMSEL?\r")
            SagWaitnMatchResp(target_at, ["\r\n+KSIMSEL: %d,,1\r\n\r\nOK\r\n" % kss], 4000)

            # Restart module
            SWI_Reset_Module(target_at, HARD_INI)

            # AT+KSIMDET?
            SagSendAT(target_at, "AT+KSIMDET?\r")
            SagWaitnMatchResp(target_at, ["\r\n+KSIMDET: %d\r\n\r\nOK\r\n" % ksd], 4000)

            # AT+KSIMSEL?
            SagSendAT(target_at, "AT+KSIMSEL?\r")
            SagWaitnMatchResp(target_at, ["\r\n+KSIMSEL: %d,,1\r\n\r\nOK\r\n" % kss], 4000)

    except Exception as err_msg :
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)

    if ksimdet != "":
        # Restore default ksimdet
        SagSendAT(target_at, "AT+KSIMDET=" + ksimdet + "\r")
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 4000)

    if ksimsel != "":
        # Restore default ksimsel
        SagSendAT(target_at, "AT+KSIMSEL=" + ksimsel + "\r")
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 4000)

    # Restart module
    SWI_Reset_Module(target_at, HARD_INI)

    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)

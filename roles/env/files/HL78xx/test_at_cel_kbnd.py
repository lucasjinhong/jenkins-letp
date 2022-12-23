"""
Cellular AT commands test cases :: KBND
originated from A_HL_Common_MECS_KBND_0001.PY validation test script
"""

import pytest
import time
import os
import VarGlobal
import re
import ast
from autotest import *

def A_HL_INT_CEL_KBND_0000(target_at, read_config, network_tests_setup_teardown):
    """
    Check KBND AT Command. Nominal/Valid use case
    """

    print("\nA_HL_INT_CEL_KBND_0000 TC Start:\n")
    test_environment_ready = "Ready"

    print("\n------------Test's preambule Start------------")

    # Variable Init
    HARD_INI = read_config.findtext("autotest/HARD_INI")
    SOFT_INI_Soft_Version = read_config.findtext("autotest/SOFT_INI_Soft_Version")
    Soft_Version = two_digit_fw_version(SOFT_INI_Soft_Version)
    Config_Name = read_config.findtext("autotest/Network_Config/Config_Name")
    KSRAT = read_config.findtext("autotest/Network_Config/Ksrat")
    BAND = read_config.findtext("autotest/Network_Config/Band")
    ModuleBandsLTE = ast.literal_eval(read_config.findtext("autotest/Bands/Band_LTE"))
    bandToKBNDLTE = ast.literal_eval(read_config.findtext("autotest/Bands/KBND_Dictionary"))

    if not "HL78" in HARD_INI:
        pytest.skip("KBND/KBNDCFG only supported on HL78 modules")

    # Assume basic support for at least one LTE band
    if len(ModuleBandsLTE) < 1 or len(bandToKBNDLTE) < 1:
        VarGlobal.statOfItem="NOK"
        raise Exception("---->Problem: Invalid LTE_Band input from INI file !!!")

    # Requires Amarisoft SIM Card for the test case
    Network = read_config.findtext("autotest/Network")
    if "amarisoft" not in str.lower(Network):
        raise Exception("Problem: Amarisoft SIM and Config should be used.")

    SagSendAT(target_at, 'AT+KSREP=0\r')
    SagWaitnMatchResp(target_at, ['\r\nOK\r\n'], C_TIMER_LOW)

    test_nb = ""
    test_ID = "A_HL_INT_CEL_KBND_0000"
    PRINT_START_FUNC(test_nb + test_ID)

    print("\n----- Testing Start -----\n")

    try:
        kbndList = []

        if bandToKBNDLTE != 0:
            kbndList.extend(x.lstrip('0') for x in list(bandToKBNDLTE.values()))

        SagSendAT(target_at, "AT+KBND?\r")
        answer = SagWaitResp(target_at, ["\r\n+KBND: %s,000?????????????????\r\n" % KSRAT], C_TIMER_LOW)
        result = SagMatchResp(answer,["\r\n+KBND: %s,000?????????????????\r\n" % KSRAT])
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], C_TIMER_LOW)
        if result:
            bnd = answer.split("\r\n")[1].split(" ")[1].split(",")[1]
            if bnd.lstrip('0') not in kbndList:
                raise Exception("---->Problem: <band> out of range !!!")
                VarGlobal.statOfItem = "NOK"

        # AT+KBNDCFG=?
        SagSendAT(target_at, "AT+KBNDCFG=?\r")
        SagWaitnMatchResp(target_at, ["+KBNDCFG: 0,000?????????????????\r\n+KBNDCFG: 1,*\r\n+KBNDCFG: 2,*\r\n\r\nOK\r\n"], C_TIMER_LOW)

        # AT+KBNDCFG?
        SagSendAT(target_at, "AT+KBNDCFG?\r")
        answer = SagWaitResp(target_at, ["*\r\nOK\r\n"], C_TIMER_LOW)
        result = SagMatchResp(answer, ["\r\n+KBNDCFG: 0,*\r\n+KBNDCFG: 1,*\r\n+KBNDCFG: 2,*\r\n"])
        M1_Band = answer.split("\r\n")[1].split(": ")[1].split(",")[1]
        NB1_Band = answer.split("\r\n")[2].split(": ")[1].split(",")[1]
        # default KBNDCFG
        if result:
            if Config_Name == "M1":
                kbndcfg = answer.split("\r\n")[1].split(": ")[1]
            elif Config_Name == "NB1":
                kbndcfg = answer.split("\r\n")[2].split(": ")[1]
            else:
                kbndcfg = answer.split("\r\n")[3].split(": ")[1]
            print("\nDefault kbndcfg is: "+kbndcfg)
        else:
            kbndcfg = ""

        currentBandlist = BAND.split(',')
        band = bandToKBNDLTE.get(int(currentBandlist[0])).lstrip('0')

        # AT+KBNDCFG=KSRAT,band
        SagSendAT(target_at, "AT+KBNDCFG=%s,%s\r" % (KSRAT, band))
        SagWaitnMatchResp(target_at, ["+KBNDCFG: %s,%s\r\n\r\nOK\r\n" % (KSRAT, band)], 60000)

        SWI_Reset_Module(target_at, HARD_INI)

        # AT+KBNDCFG?
        SagSendAT(target_at, "AT+KBNDCFG?\r")
        answer = str(band).zfill(20)
        if (Soft_Version >= "04.06.00.00" and Soft_Version < "05.00.00.00") or (Soft_Version >= "05.03.03.00"):
            if Config_Name == "M1":
                SagWaitnMatchResp(target_at, ["+KBNDCFG: 0," + answer + "\r\n+KBNDCFG: 1," + NB1_Band + "\r\n+KBNDCFG: 2,0\r\n\r\nOK\r\n"], C_TIMER_LOW)
            elif Config_Name == "NB1":
                SagWaitnMatchResp(target_at, ["+KBNDCFG: 0," + M1_Band + "\r\n+KBNDCFG: 1," + answer + "\r\n+KBNDCFG: 2,0\r\n\r\nOK\r\n"], C_TIMER_LOW)
            else:
                SagWaitnMatchResp(target_at, ["+KBNDCFG: 0," + M1_Band + "\r\n+KBNDCFG: 1," + NB1_Band + "\r\n+KBNDCFG: 2," + answer + "\r\n\r\nOK\r\n"], C_TIMER_LOW)
        else:
            if Config_Name == "M1":
                SagWaitnMatchResp(target_at, ["+KBNDCFG: 0," + answer + "\r\n+KBNDCFG: 1,0\r\n+KBNDCFG: 2,0\r\n\r\nOK\r\n"], C_TIMER_LOW)
            elif Config_Name == "NB1":
                SagWaitnMatchResp(target_at, ["+KBNDCFG: 0,0\r\n+KBNDCFG: 1," + answer + "\r\n+KBNDCFG: 2,0\r\n\r\nOK\r\n"], C_TIMER_LOW)
            else:
                SagWaitnMatchResp(target_at, ["+KBNDCFG: 0,0\r\n+KBNDCFG: 1,0\r\n+KBNDCFG: 2," + answer + "\r\n\r\nOK\r\n"], C_TIMER_LOW)

        # Restore default KBNDCFG
        if kbndcfg != "":
            SagSendAT(target_at, "AT+KBNDCFG=" + kbndcfg + "\r")
            SagWaitnMatchResp(target_at, ["+KBNDCFG: " + kbndcfg + "\r\n\r\nOK\r\n"], 60000)

    except Exception as err_msg:
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)

    # Restart module
    SWI_Reset_Module(target_at, HARD_INI)

    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)


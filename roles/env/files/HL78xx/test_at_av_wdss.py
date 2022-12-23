"""
AV AT commands test cases :: WDSx
originated from A_HL_Common_AVMS_WDSS_0005.PY validation test script
"""

import pytest
import time
import os
import VarGlobal
import re
import requests
import json
import ast
from autotest import pytestmark
from autotest import PRINT_START_FUNC, PRINT_TEST_RESULT
from autotest import (
    SagSendAT, SagWaitnMatchResp, SagWaitResp,
    SagSleep, SagMatchResp)
from autotest import (
    SWI_Reset_Module, SWI_Check_Module, SWI_Check_Network_Config,
    SWI_Check_SIM_Ready, SWI_Check_Network_Coverage)
from autotest import (
    is_valid_fw, ensure_network_connection)
from autotest import (
    AT_CMD_List_Check_Module, AT_Resp_List_Check_Module,
    AT_Timeout_List_Check_Module,
    AT_Restart_CMD, AT_Restart_Resp,
    SIM_Check_CMD, SIM_Check_RESP,
    SIM_SET_PIN_CMD, AT_SET_SIM_RESP,
    UNSOLICITED_Notif,
    AT_CMD_List_Net_Registration, AT_RESP_List_Net_Registration)
from autotest import (
    Booting_Duration, SIM_TimeOut, FOTA_Update_Duration)
from avms_upgrade import (
    av_session_config, av_upgrade_session,
    restore_backup, download_firmware, autoflash)
import swilog
from otii_utility import *

@pytest.fixture
def setup_wdss(target_at):
    SagSendAT(target_at, 'AT+WDSS=1,0\r')
    SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 3000)
    SagSendAT(target_at, 'AT+WDSS=2,1\r')
    SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 3000)


def A_HL_INT_AV_WDSS_0000(
    target_cli, target_at,
    avms_client,
    otii_setup_teardown,
    avms_user_agree_on, setup_wdss,
    read_config):
    """
    Check WDSx AT Command. Nominal/Valid use case
    """

    print("\nA_HL_INT_AV_WDSS_0000 TC Start:\n")
    test_environment_ready = "Ready"

    print("\n------------Test's preambule Start------------")

    # Variable Init
    SIM_Pin1 = read_config.findtext("autotest/PIN1_CODE")
    PARAM_GPRS_APN = ast.literal_eval(read_config.findtext("autotest/Network_APN"))
    PARAM_GPRS_PDP = ast.literal_eval(
        read_config.findtext("autotest/Network_PDP_type"))
    SOFT_INI_Soft_Version = read_config.findtext("autotest/SOFT_INI_Soft_Version")
    SOFT_INI_Fota_Version = ast.literal_eval(read_config.findtext("autotest/SOFT_INI_Fota_Version"))
    client_id = read_config.findtext("autotest/client_id")
    client_secret = read_config.findtext("autotest/client_secret")
    company = read_config.findtext("autotest/company")
    user = read_config.findtext("autotest/user")
    password = read_config.findtext("autotest/password")
    uid = read_config.findtext("autotest/uid")
    if not uid:
        raise Exception("---->Problem: Enter your device uid in 'uid' field in autotest.xml")

    Config_Name = read_config.findtext("autotest/Network_Config/Config_Name")
    HARD_INI = read_config.findtext("autotest/HARD_INI")
    KSRAT = read_config.findtext("autotest/Network_Config/Ksrat")
    BAND = read_config.findtext("autotest/Network_Config/Band")
    Max_Try_Net_Registration = int(
        read_config.findtext("autotest/Network_Config/Max_Try_Net_Registration"))
    AT_KSRAT = int(read_config.findtext("autotest/Features_AT_KSRAT"))
    if not KSRAT or not BAND or not Max_Try_Net_Registration:
        raise Exception(("---->Problem: Enter your network configs "
            "'KSRAT' 'BAND' and 'Max_Try_Net_Registration'"))

    phase = int(read_config.findtext("autotest/Features_PHASE"))

    timeout = 15
    relay_port = read_config.findtext("hardware/power_supply/com/port")
    relay_num = read_config.findtext("hardware/power_supply/port_nb")

    try:
        # Check Module state / Restart if required
        SWI_Check_Module(
            target_at,
            AT_CMD_List_Check_Module, AT_Resp_List_Check_Module,
            AT_Timeout_List_Check_Module,
            AT_Restart_CMD, AT_Restart_Resp,
            Booting_Duration)

        # Network Initialization
        SWI_Check_Network_Config(
            target_at,
            KSRAT, BAND,
            AT_Restart_CMD, AT_Restart_Resp,
            Booting_Duration, AT_KSRAT)

        # Check SIM state
        SWI_Check_SIM_Ready(
            target_at,
            SIM_Pin1,
            SIM_Check_CMD, SIM_Check_RESP,
            SIM_SET_PIN_CMD, AT_SET_SIM_RESP,
            UNSOLICITED_Notif,
            SIM_TimeOut)

        # Check Cell Network state
        SWI_Check_Network_Coverage(
            target_at, HARD_INI, KSRAT,
            AT_CMD_List_Net_Registration, AT_RESP_List_Net_Registration,
            Max_Try_Net_Registration)

        if not VarGlobal.Init_Status in ["Network_Registration_Ready"]:
            test_environment_ready = "Not_Ready"

        # Check Soft release
        SagSendAT(target_at, "AT+CGMR\r")
        if not SagWaitnMatchResp(
                target_at, ["\r\n"+SOFT_INI_Soft_Version+"\r\n\r\nOK\r\n"], 2000):
            test_environment_ready = "Not_Ready"

    except Exception as e:
        print("***** Test environment check fails !!!*****")
        print(type(e))
        print(e)
        test_environment_ready = "Not_Ready"

    print("\n----- Testing Start -----\n")

    test_nb=""
    test_ID = "A_HL_INT_AV_WDSS_0000"
    PRINT_START_FUNC(test_nb + test_ID)

    otii_object = otii_setup_teardown

    VarGlobal.statOfItem = "OK"
    try:
        if test_environment_ready == "Not_Ready":
            VarGlobal.statOfItem="NOK"
            raise Exception("---->Problem: Test Environment Is Not Ready !!!")

        print("\n----- NETWORK CONFIGURATION :: %s -----\n" % Config_Name)

        # check if SIM is locked
        sim_locked = 0
        SagSendAT(target_at, 'AT+CLCK="SC",2\r')
        lock_resp = SagWaitResp(target_at,["\r\n+CLCK: ?\r\n\r\nOK\r\n"], 4000)
        if lock_resp.find('+CLCK: 0')==-1:
            # SIM locked => unlock SIM
            sim_locked = 1
            SagSendAT(target_at, 'AT+CLCK="SC",0,"' + SIM_Pin1 + '"\r')
            SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 4000)

        # Check if CREG <> 0
        creg_enabled = 0
        SagSendAT(target_at, "AT+CREG?\r")
        creg_resp = SagWaitResp(target_at,["\r\n+CREG: ?,?\r\n\r\nOK\r\n"], 4000)
        if creg_resp.find('+CREG: 0')==-1:
            # CREG enabled => disable CREG
            creg_enabled = 1
            creg = creg_resp.split("\r\n")[1].split(": ")[1].split(",")[0]
            print("\nDefault creg is: "+creg)
            SagSendAT(target_at, 'AT+CREG=0\r')
            SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 4000)

        # AT+WDSC=?
        SagSendAT(target_at, 'AT+WDSC=?\r')
        SagWaitnMatchResp(target_at, ['\r\n+WDSC: (0-2,5,6),(0-1)\r\n'], 3000)
        SagWaitnMatchResp(target_at, ['+WDSC: 3,(0-525600)\r\n'], 3000)
        SagWaitnMatchResp(
            target_at,
            [('+WDSC: 4,'
              '(0-20160),(1-20160),(1-20160),(1-20160),'
              '(1-20160),(1-20160),(1-20160),(1-20160)\r\n')], 3000)
        SagWaitnMatchResp(target_at, ['\r\nOK\r\n'], 3000)

        # AT+WDSC?
        SagSendAT(target_at, 'AT+WDSC?\r')
        # Ensure that module requires agreement before AVMS connection
        SagWaitnMatchResp(target_at, ['\r\n+WDSC: 0,1\r\n'], 3000)
        SagWaitnMatchResp(target_at, ['+WDSC: 1,0\r\n'], 3000)
        SagWaitnMatchResp(target_at, ['+WDSC: 2,0\r\n'], 3000)
        SagWaitnMatchResp(target_at, ['+WDSC: 3,0\r\n'], 3000)
        SagWaitnMatchResp(target_at, ['+WDSC: 4,*\r\n'], 3000)
        SagWaitnMatchResp(target_at, ['+WDSC: 5,0\r\n'], 3000)
        SagWaitnMatchResp(target_at, ['+WDSC: 6,0\r\n'], 3000)
        SagWaitnMatchResp(target_at, ['\r\nOK\r\n'], 3000)

        # AT+WDSR?
        SagSendAT(target_at, 'AT+WDSR=?\r')
        SagWaitnMatchResp(target_at, ['\r\n+WDSR: (0-9),(0-1440)\r\n'], 3000)
        SagWaitnMatchResp(target_at, ['\r\nOK\r\n'], 3000)

        # AT+WDSI=?
        SagSendAT(target_at, 'AT+WDSI=?\r')
        SagWaitnMatchResp(
            target_at, ['\r\n+WDSI: (0-127,256-383,4096-4223,4352-4479)\r\n'], 3000)
        SagWaitnMatchResp(target_at, ['\r\nOK\r\n'], 3000)

        # AT+WDSI?
        SagSendAT(target_at, 'AT+WDSI?\r')
        answer = SagWaitResp(target_at, ["*\r\nOK\r\n"], 3000)
        result = SagMatchResp(answer, ["\r\n+WDSI: *\r\n"])
        # default WDSI
        if result:
            wdsi = answer.split(": ")[1].split("\r\n")[0]
            print("\nDefault wdsi is: "+wdsi)
        else:
            wdsi = "0"

        # AT+WDSS=?
        SagSendAT(target_at, 'AT+WDSS=?\r')
        SagWaitnMatchResp(target_at, ['\r\n+WDSS: 1,(0-1)'], 3000)
        if phase > 0:
            SagWaitnMatchResp(target_at, ["\r\n+WDSS: 2,(1-2)\r\n\r\nOK\r\n"], 3000)
        else:
            SagWaitnMatchResp(target_at, ["\r\n+WDSS: 2,(1-1)\r\n\r\nOK\r\n"], 3000)

        # AT+WDSS?
        SagSendAT(target_at, 'AT+WDSS?\r')
        SagWaitnMatchResp(target_at, ['\r\n+WDSS: 1,0'], 3000)
        SagWaitnMatchResp(target_at, ['\r\n+WDSS: 2,1\r\n\r\nOK\r\n'], 3000)

        # AT+WDSI=4479
        SagSendAT(target_at, 'AT+WDSI=4479\r')
        SagWaitnMatchResp(target_at, ['\r\nOK\r\n'], 3000)

        # Set target_version to base version
        target_version = SOFT_INI_Soft_Version

       # Log FOTA path
        swilog.info("-----------------------------------------")
        swilog.info("Test FOTA path:")
        swilog.info("From: " + SOFT_INI_Soft_Version)
        for fota_version in SOFT_INI_Fota_Version:
            swilog.info("To: " + fota_version)
        swilog.info("-----------------------------------------\n")

        # Start AVMS Loop
        for fota_version in SOFT_INI_Fota_Version:

            # Assign base and target version
            base_version = target_version
            target_version = fota_version
            swilog.step("Test upgrade from %s to %s" % (base_version, target_version))

            # Check registration status
            target_at.run_at_cmd("AT+COPS?", timeout, ["OK"])

            print("\n----- av_session_ctrl -----\n")
            av_session_config(target_at, avms_client, target_version, HARD_INI)

            if '.99' in fota_version:
                # Test delaying the connection only on first try
                av_upgrade_session(target_at, avms_client, otii_object, base_version, target_version, relay_port, relay_num, user_agreement=True, delay=True)
                SagSendAT(target_at, 'AT+WDSS=1,0\r')
                SagWaitnMatchResp(target_at, ['\r\n+WDSI: 8'], 3000)
            else:
                av_upgrade_session(target_at, avms_client, otii_object, base_version, target_version, relay_port, relay_num, user_agreement=True)

            SagSleep(1000)
            # AT+CGMR
            SagSendAT(target_at, "AT+CGMR\r")
            SagWaitnMatchResp(target_at, ["\r\n"+target_version+"\r\n\r\nOK\r\n"], 2000)

            print("\nPreparing for next FOTA test (script cleanup)\n")
            time.sleep(2)

        # Restore default values
        SagSendAT(target_at, 'AT+WDSI=' + wdsi + '\r')
        SagWaitnMatchResp(target_at, ['\r\nOK\r\n'], 3000)

        if (sim_locked == 1):
            SagSendAT(target_at, 'AT+CLCK="SC",1,"' + SIM_Pin1 + '"\r')
            SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 4000)

        if (creg_enabled == 1):
            SagSendAT(target_at, "AT+CREG=" + creg + "\r")
            SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 4000)

    except Exception as err_msg :
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)

    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)


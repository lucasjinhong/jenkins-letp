"""
IP connectivity AT commands test cases :: KTCPSTART
originated from A_INTEL_LTE_PROTOCOM_KTCPSTART_0007.PY validation test script
"""

import pytest
import time
import os
import VarGlobal
import ast
from autotest import *
import threading
import socket_server
import time
from datetime import timedelta
from datetime import datetime

def Setup_Module_kCnxCfg(target_at, GPRS_Cfg):
    global MAX_CNX_CNT
    print("target_at: +KCNXCFG Connection Configuration...")

    for n in range(VarGlobal.iCnxStart, VarGlobal.iCnxStart + VarGlobal.iCnxTotal):
        SagSendAT(target_at, 'AT+KCNXCFG=%d,"GPRS","%s","%s","%s"\r' % (n, GPRS_Cfg[0], GPRS_Cfg[1], GPRS_Cfg[2]))
        if SagWaitnMatchResp(target_at, ["*\r\nOK\r\n"], 3000) != True:
            print("\nPROBLEM: +KCNXCFG command %d response is incorrect.\n" % n)

def Setup_Module_kCgdcont(target_at, GPRS_Cfg):
    print("target_at: +CGDCONT Connection Configuration...")

    global MAX_CNX_CNT
    SagSendAT(target_at, 'AT+CGATT?\r')
    SagWaitnMatchResp(target_at, ["*\r\nOK\r\n"], 5000)

    SagSleep(1000)
    SagSendAT(target_at, 'AT+CGATT=0\r')
    SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 10000, update_result="not_critical")

    SagSleep(1000)
    SagSendAT(target_at, 'AT+CGATT?\r')
    SagWaitnMatchResp(target_at, ["*\r\nOK\r\n"], 5000)

    SagSendAT(target_at, 'AT+CGDCONT?\r')
    SagWaitnMatchResp(target_at, ["*\r\nOK\r\n"], 5000)
    for n in range(VarGlobal.iCnxStart, VarGlobal.iCnxStart + VarGlobal.iCnxTotal):
        SagSendAT(target_at, 'AT+CGDCONT=%d,"%s","%s"\r' % (n, GPRS_Cfg[3], GPRS_Cfg[0]))
        if SagWaitnMatchResp(target_at, ["*\r\nOK\r\n"], 10000) != True:
            print("\nPROBLEM: +CGDCONT command %d response is incorrect.\n" % n)
    SagSendAT(target_at, 'AT+CGDCONT?\r')
    SagWaitnMatchResp(target_at, ["*\r\nOK\r\n"], 5000)

    #Added as +KCNXCFG does not attach automatically - Issue?
    SagSleep(5000)
    SagSendAT(target_at, 'AT+CGATT=1\r')
    SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 10000)

def A_HL_INT_IP_KTCPSTART_0000(target_at, read_config, network_tests_setup_teardown):
    """
    Check KUDPxxx AT Command. Nominal/Valid use case
    """

    print("\nA_HL_INT_IP_KTCPSTART_0000 TC Start:\n")
    test_environment_ready = "Ready"

    print("\n------------Test's preambule Start------------")

    # Variable Init
    HARD_INI = read_config.findtext("autotest/HARD_INI")
    SIM_GPRS_APN = ast.literal_eval(read_config.findtext("autotest/Network_APN"))[0]
    SIM_GPRS_LOGIN = ast.literal_eval(read_config.findtext("autotest/Network_APN_login"))[0]
    SIM_GPRS_PASSWORD = ast.literal_eval(read_config.findtext("autotest/Network_APN_password"))[0]
    PARAM_GPRS_PDP = ast.literal_eval(read_config.findtext("autotest/Network_PDP_type"))[0]
    Network = read_config.findtext("autotest/Network")
    #Modify for TPE
    if "amarisoft" in str.lower(Network):
        PARAM_HL_ECHO_SERVER_IP = read_config.findtext("autotest/IntegrationVMServer")
        PARAM_HL_TCP_ECHO_PORT = read_config.findtext("host/socket_server/tcp_1/port")
    else:
        PARAM_HL_ECHO_SERVER_IP = read_config.findtext("autotest/legato_flake_server")
        PARAM_HL_TCP_ECHO_PORT = read_config.findtext("autotest/flake_echo_port")

    if not PARAM_HL_ECHO_SERVER_IP:
        VarGlobal.statOfItem = "NOK"
        raise Exception("---->Problem: Enter your IP Address (ip_address or legato_flake_server) in autotest.xml (ifconfig information)")
    print("PARAM_HL_ECHO_SERVER_IP")
    print(PARAM_HL_ECHO_SERVER_IP)

    GPRS_Cfg = (SIM_GPRS_APN, SIM_GPRS_LOGIN, SIM_GPRS_PASSWORD, PARAM_GPRS_PDP)
    VarGlobal.iCnxStart = 1
    VarGlobal.iCnxTotal = 1
    END_CODE = "--EOF--Pattern--"
    DATA_EXCHANGED = "This is a simple TCP Protocol test"
    nData = len(DATA_EXCHANGED)
    phase = int(read_config.findtext("autotest/Features_PHASE"))

    # Check Module state / Restart if required
    SWI_Reset_Module(target_at, HARD_INI)

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

    SagSendAT(target_at, 'AT+CMEE=1\r')
    SagWaitnMatchResp(target_at, ['*\r\nOK\r\n'], 4000)

    test_nb = ""
    test_ID = "A_HL_INT_IP_KTCPSTART_0000"
    PRINT_START_FUNC(test_nb + test_ID)

    print("\n----- Testing Start -----\n")

    try:
        # default CGDCONT
        cgdcont = []
        SagSendAT(target_at, "AT+CGDCONT?\r")
        answer = SagWaitResp(target_at, ["\r\n*\r\n\r\nOK\r\n"], 5000)
        for line_answer in answer.split("\r\n"):
            result = SagMatchResp(line_answer, ["+CGDCONT: *"])
            if result:
                cgdcont.append(line_answer.split(": ")[1])
                print("\nDefault cgdcont is: "+cgdcont[-1])

        # Default K config
        SagSendAT(target_at, 'AT&V\r')
        answer = SagWaitResp(target_at, ["\r\n*\r\n\r\nOK\r\n"], C_TIMER_LOW)
        result = SagMatchResp(answer, ["\r\nACTIVE PROFILE:\r\n*\r\n*"])
        if result:
            k = answer.split("\r\n")[2].split(" ")[9]
            print("\nDefault K is: "+k)
        else:
            k = "&K3"

        # Enable bi-directional hardware flow control
        SagSendAT(target_at, "AT&K3\r")
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 3000)

        cnx_cnf = VarGlobal.iCnxStart

        # GPRS Connection Configuration.
        Setup_Module_kCgdcont(target_at, GPRS_Cfg)
        Setup_Module_kCnxCfg(target_at, GPRS_Cfg)

        # Connection Timer Configuration.
        SagSendAT(target_at, 'AT+KCNXTIMER=' + str(cnx_cnf) + ',30,2,60,30\r')
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 3000)

        # TCP Connection Configuration
        target_at.run_at_cmd('AT+KTCPCFG=' + str(cnx_cnf) + ',0,\"' + PARAM_HL_ECHO_SERVER_IP + '\",' + PARAM_HL_TCP_ECHO_PORT, 15, [r"\+KTCPCFG:\s\d", "OK"])
        rsp = target_at.run_at_cmd("AT+KTCPCFG?", 15, ["OK"])

        if "+KTCPCFG: " in rsp:
            session_id = rsp.split("+KTCPCFG: ")[-1].split(",")[0]
            SagSendAT(target_at, 'AT+KTCPCFG?\r')
            SagWaitnMatchResp(target_at, ["\r\n+KTCPCFG: " + session_id + ',0,' + str(cnx_cnf) + ',0,,"' + PARAM_HL_ECHO_SERVER_IP + '",' + PARAM_HL_TCP_ECHO_PORT + ',*,0,0,0\r\n'], 3000)
            SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 3000)

            # Start TCP Connection
            SagSendAT(target_at, 'AT+KTCPSTART=' + session_id + '\r')

            if SagWaitnMatchResp(target_at, ["*\r\nCONNECT\r\n"], 12000):
                start = datetime.now()
                SagSendAT(target_at, DATA_EXCHANGED)
                SagSendAT(target_at, END_CODE)
                if not SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 3000):
                    VarGlobal.statOfItem = "NOK"
                    print("Failed!!! End code could not end the data sending.")

                else:
                    # Check receive data over same TCPSocket
                    SagWaitnMatchResp(target_at, ["*\r\n+KTCP_DATA: " + session_id + ","+ str(nData) + "\r\n"], 3000)
                    SagSendAT(target_at, "AT+KTCPRCV="+ session_id +","+ str(nData) + "\r")
                    if SagWaitnMatchResp(target_at, ["*\r\nCONNECT\r\n"], 12000):
                        SagWaitnMatchResp(target_at, [END_CODE], 5000)
                        if not SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 5000):
                            VarGlobal.statOfItem = "NOK"
                            print("Failed!!! still in data mode.")

            # Close created session
            SagSendAT(target_at, 'AT+KTCPCLOSE=' + session_id + ',1\r')
            SagWaitnMatchResp(target_at, ["*\r\nOK\r\n"], 3000)
            if phase < 3:
                #Idle time down counting started for disconnection
                SagWaitnMatchResp(target_at, ["*\r\n+KCNX_IND: " + session_id+ ",5,30\r\n"], 40000)
                #Disconnected due to network
                if (phase > 0):
                    SagWaitnMatchResp(target_at, ["*\r\n+KCNX_IND: " + session_id+ ",3\r\n"], 40000)
                else:
                    SagWaitnMatchResp(target_at, ["*\r\n+KCNX_IND: " + session_id+ ",0,0\r\n"], 40000)

            # Delete created session
            SagSendAT(target_at, 'AT+KTCPDEL=' + session_id + '\r')
            SagWaitnMatchResp(target_at, ["*\r\nOK\r\n"], 3000)

        else:
            VarGlobal.statOfItem = "NOK"
            swilog.error("Unable to configure TCP connection!")

        # Restore default cmee
        SagSendAT(target_at, "AT+CMEE=" + cmee + "\r")
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 2000)

        # Restore default CGDCONT
        for cgdcont_elem in cgdcont:
            SagSendAT(target_at, "AT+CGDCONT=" + cgdcont_elem + "\r")
            SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 10000)

        # Restore default K
        SagSendAT(target_at, 'AT%s\r' % k)
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], C_TIMER_LOW)

    except Exception as e:
        print(e)
        VarGlobal.statOfItem = "NOK"

    # Restore Module
    SWI_Reset_Module(target_at, HARD_INI)

    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)

"""
IP connectivity AT commands test cases :: KUDPxxx
originated from A_HL_Common_PROTOCOM_KUDPSND_0001.PY validation test script
"""

import pytest
import time
import os
from datetime import datetime
import VarGlobal
import ast
from autotest import *
import socket_server

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
    SagSleep(10000)
    SagSendAT(target_at, 'AT+CGATT=1\r')
    SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 10000)

def A_HL_INT_IP_KUDP_0000(target_at, read_config, network_tests_setup_teardown, udp_server):
    """
    Check KUDPxxx AT Command. Nominal/Valid use case
    """

    print("\nA_HL_INT_IP_KUDP_0000 TC Start:\n")
    test_environment_ready = "Ready"

    print("\n------------Test's preambule Start------------")

    # Variable Init
    HARD_INI = read_config.findtext("autotest/HARD_INI")
    SIM_GPRS_APN = ast.literal_eval(read_config.findtext("autotest/Network_APN"))[0]
    SIM_GPRS_LOGIN = ast.literal_eval(read_config.findtext("autotest/Network_APN_login"))[0]
    SIM_GPRS_PASSWORD = ast.literal_eval(read_config.findtext("autotest/Network_APN_password"))[0]
    PARAM_GPRS_PDP = ast.literal_eval(read_config.findtext("autotest/Network_PDP_type"))[0]
    Network = read_config.findtext("autotest/Network")
    if "amarisoft" in str.lower(Network):
        PARAM_HL_ECHO_SERVER_IP = read_config.findtext("host/ip_address")
        PARAM_HL_UDP_ECHO_PORT = read_config.findtext("host/socket_server/udp_1/port")
    else:
        PARAM_HL_ECHO_SERVER_IP = read_config.findtext("autotest/legato_flake_server")
        PARAM_HL_UDP_ECHO_PORT = read_config.findtext("autotest/flake_echo_port")

    if not PARAM_HL_ECHO_SERVER_IP:
        VarGlobal.statOfItem = "NOK"
        raise Exception("---->Problem: Enter your IP Address (ip_address or legato_flake_server) in autotest.xml (ifconfig information)")
    print("PARAM_HL_ECHO_SERVER_IP")
    print(PARAM_HL_ECHO_SERVER_IP)

    GPRS_Cfg = (SIM_GPRS_APN, SIM_GPRS_LOGIN, SIM_GPRS_PASSWORD, PARAM_GPRS_PDP)
    VarGlobal.iCnxStart = 1
    VarGlobal.iCnxTotal = 1
    END_CODE = "--EOF--Pattern--"
    DATA_EXCHANGED = "This is a simple UDP Protocol test"
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
    test_ID = "A_HL_INT_IP_KUDP_0000"
    PRINT_START_FUNC(test_nb + test_ID)

    # Start Test
    print("\n------------Test Case Start------------")

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

        # Parameter EOF Pattern
        SagSendAT(target_at, 'AT+KPATTERN="--EOF--Pattern--"\r')
        if SagWaitnMatchResp(target_at, ["*\r\nOK\r\n"], 3000) != True:
            print("\nPROBLEM: +KPATTERN command response is incorrect.\n")

        # Enable bi-directional hardware flow control
        SagSendAT(target_at, "AT&K3\r")
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 3000)

        # Connection Timer Configuration.
        SagSendAT(target_at, 'AT+KCNXTIMER=1' + ',30,2,60,30\r')
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 3000)

        # Check Current End code.
        SagSendAT(target_at, 'AT+KPATTERN?\r')
        answer = SagWaitResp(target_at, ["\r\n+KPATTERN: *\r\n"], 3000)
        result_END_PATTERN = SagMatchResp(answer, ["\r\n+KPATTERN: *\r\n"])
        SagWaitnMatchResp(target_at, ["*OK\r\n"], 3000)

        if result_END_PATTERN:
            END_PATTERN = answer.split("\r\n")[1].split(" ")[1].split('"')[1]

        SagSleep(5000)

        Setup_Module_kCgdcont(target_at, GPRS_Cfg)
        Setup_Module_kCnxCfg(target_at, GPRS_Cfg)

        # Test Command
        SagSendAT(target_at, 'AT+KUDPSND=?\r')
        if (phase > 0):
          SagWaitnMatchResp(target_at, ["\r\n+KUDPSND: (1-6),<remote-name/ip>,(1-65535),(1-4294967295)\r\n\r\nOK\r\n"], 3000)
        else:
          SagWaitnMatchResp(target_at, ["\r\n+KUDPSND: (1-10),<remote-name/ip>,(1-65535),(1-*)\r\n\r\nOK\r\n"], 3000)

        SagSendAT(target_at, 'AT+KUDPRCV=?\r')
        SagWaitnMatchResp(target_at, ["\r\n+KUDPRCV: (1-*),(1-*)\r\n\r\nOK\r\n"], 3000)

        # Sending data (Client Mode) - data will not be received by the URC
        sTargetCnxToTest = str(VarGlobal.iCnxStart)
        sSessionId = str(1)
        SagSendAT(target_at, 'AT+KUDPCFG=' + sTargetCnxToTest + ',0,1234\r')
        result_session = SagWaitnMatchResp(target_at, ["\r\n+KUDPCFG: " + sSessionId + "\r\n"], 3000)
        SagWaitnMatchResp(target_at, ["*OK\r\n"], 3000)
        SagWaitnMatchResp(target_at, ["*\r\n+KUDP_IND: " + sSessionId + ",1\r\n"], 60000)

        # Check IP address
        SagSendAT(target_at, 'AT+KCGPADDR=' + sSessionId + '\r')
        SagWaitnMatchResp(target_at, ["\r\n+KCGPADDR: " + sSessionId + ',"*.*.*.*"\r\n'], 3000)
        SagWaitnMatchResp(target_at, ["*OK\r\n"], 3000)

        # Send DATA_EXCHANGED data
        SagSendAT(target_at, "AT+KUDPSND=" + sSessionId + ",\"" + PARAM_HL_ECHO_SERVER_IP + "\"," + PARAM_HL_UDP_ECHO_PORT + "," + str(nData) +"\r")
        if SagWaitnMatchResp(target_at, ["*\r\nCONNECT\r\n"], 3000):
            start = datetime.now()
            SagSendAT(target_at, DATA_EXCHANGED)
            SagSendAT(target_at, END_CODE)
            if not SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 3000):
                VarGlobal.statOfItem = "NOK"
                print("Failed!!! End code could not end the data sending.")

            else:
                # Check receive data over same UDP Socket
                SagWaitnMatchResp(target_at, ["*\r\n+KUDP_DATA: " + sSessionId + ","+ str(nData) + "\r\n"], 3000)
                SagSendAT(target_at, "AT+KUDPRCV="+ sSessionId +","+ str(nData) + "\r")
                if SagWaitnMatchResp(target_at, ["*\r\nCONNECT\r\n"], 3000):
                    SagWaitnMatchResp(target_at, [END_CODE], 5000)
                    if not SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 5000):
                        VarGlobal.statOfItem = "NOK"
                        print("Failed!!! still in data mode.")
                    # +KUDP_RCV is not received
                    #else:
                    # JIRA issue : HLLEAPP-210
                    #    SagWaitnMatchResp(target_at, ["*\r\n+KUDP_RCV: *\r\n"], 3000)

        # Added: Close properly session if it has been opened
        if result_session:
            # Socket Close
            SagSendAT(target_at, 'AT+KUDPCLOSE=' + sSessionId + ',1\r')
            SagWaitnMatchResp(target_at, ["*\r\nOK\r\n"], 5000)

            if phase < 3:
                #No direct connexion closed indication
                #SagWaitnMatchResp(target_at, ["*\r\n+KCNX_IND: " + session_id+ ",3\r\n"], 40000)

                #Idle time down counting started for disconnection
                SagWaitnMatchResp(target_at, ["*\r\n+KCNX_IND: " + sSessionId+ ",5,30\r\n"], 40000)
                #Disconnected due to network
                if (phase > 0):
                    SagWaitnMatchResp(target_at, ["*\r\n+KCNX_IND: " + sSessionId+ ",3\r\n"], 40000)
                else:
                    SagWaitnMatchResp(target_at, ["*\r\n+KCNX_IND: " + sSessionId+ ",0,0\r\n"], 40000)

            # Socket Delete
            SagSendAT(target_at, 'AT+KUDPDEL=' + sSessionId + '\r')
            SagWaitnMatchResp(target_at, ["*\r\nOK\r\n"], 3000)

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

    except Exception as err_msg:
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)

    # Restore Module
    SWI_Reset_Module(target_at, HARD_INI)

    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)

"""
IP connectivity AT commands test cases :: KTCPxxx
originated from A_HL_Common_PROTOCOM_KTCPSND_0001.PY validation test script
"""

import pytest
import time
import os
import VarGlobal
import ast
from autotest import *
import threading
import socket_server
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

    SagSleep(15000)
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
    SagSleep(20000)
    SagSendAT(target_at, 'AT+CGATT=1\r')
    SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 10000)

def Setup_Module_kurccfg(target_at, read_config, phase):

    # Variable Init
    SOFT_INI_Soft_Version = read_config.findtext("autotest/SOFT_INI_Soft_Version")
    Soft_Version = two_digit_fw_version(SOFT_INI_Soft_Version)

    print("target_at: +KURCCFG Connection Configuration...")

    # AT+KURCCFG=?
    SagSendAT(target_at, 'AT+KURCCFG=?\r')
    if (phase > 0):
        #For HL7800 and HL781x:
        if Soft_Version < "05.00.00.00":
            SagWaitnMatchResp(target_at, ["\r\n+KURCCFG: (\"TCPC\",\"TCPS\",\"UDPC\",\"UDPS\",\"HTTP\",\"HTTPS\",\"FTP\",\"TCP\",\"UDP\"),(0-1),(0-1)\r\n\r\nOK\r\n"], 3000)
        else:
            SagWaitnMatchResp(target_at, ["\r\n+KURCCFG: (\"TCPC\",\"TCPS\",\"UDPC\",\"UDPS\",\"HTTP\",\"HTTPS\",\"FTP\",\"MQTT\",\"TCP\",\"UDP\"),(0-1),(0-1)\r\n\r\nOK\r\n"], 3000)
    else:
        SagWaitnMatchResp(target_at, ["\r\n+KURCCFG: (\"TCPC\",\"TCPS\",\"UDPC\",\"UDPS\",\"TCP\",\"UDP\"),(0-1),(0-1)\r\n\r\nOK\r\n"], 3000)

    # AT+KURCCFG?
    SagSendAT(target_at, 'AT+KURCCFG?\r')
    SagWaitnMatchResp(target_at, ["\r\n"], 3000)
    SagWaitnMatchResp(target_at, ["+KURCCFG: \"TCPC\",1,1\r\n"], 3000)
    SagWaitnMatchResp(target_at, ["+KURCCFG: \"TCPS\",1,1\r\n"], 3000)
    SagWaitnMatchResp(target_at, ["+KURCCFG: \"UDPC\",1,1\r\n"], 3000)
    SagWaitnMatchResp(target_at, ["+KURCCFG: \"UDPS\",1,1\r\n"], 3000)
    if (phase > 0):
        SagWaitnMatchResp(target_at, ["+KURCCFG: \"HTTP\",1,1\r\n"], 3000)
        SagWaitnMatchResp(target_at, ["+KURCCFG: \"HTTPS\",1,1\r\n"], 3000)
    SagWaitnMatchResp(target_at, ["*\r\nOK\r\n"], 3000)

    # Write AT+KURCCFG
    SagSendAT(target_at, 'AT+KURCCFG=\"TCPC\",1,0\r')
    SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 3000)
    SagSendAT(target_at, 'AT+KURCCFG=\"TCPS\",0,1\r')
    SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 3000)
    SagSendAT(target_at, 'AT+KURCCFG=\"UDP\",0,0\r')
    SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 3000)
    if (phase > 0):
        SagSendAT(target_at, 'AT+KURCCFG=\"HTTP\",0,1\r')
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 3000)
        SagSendAT(target_at, 'AT+KURCCFG=\"HTTPS\",1,0\r')
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 3000)

    # Read AT+KURCCFG
    SagSendAT(target_at, 'AT+KURCCFG?\r')
    SagWaitnMatchResp(target_at, ["\r\n"], 3000)
    SagWaitnMatchResp(target_at, ["+KURCCFG: \"TCPC\",1,0\r\n"], 3000)
    SagWaitnMatchResp(target_at, ["+KURCCFG: \"TCPS\",0,1\r\n"], 3000)
    SagWaitnMatchResp(target_at, ["+KURCCFG: \"UDPC\",0,0\r\n"], 3000)
    SagWaitnMatchResp(target_at, ["+KURCCFG: \"UDPS\",0,0\r\n"], 3000)
    if (phase > 0):
        SagWaitnMatchResp(target_at, ["+KURCCFG: \"HTTP\",0,1\r\n"], 3000)
        SagWaitnMatchResp(target_at, ["+KURCCFG: \"HTTPS\",1,0\r\n"], 3000)
    SagWaitnMatchResp(target_at, ["*\r\nOK\r\n"], 3000)

    # Restore default values
    SagSendAT(target_at, 'AT+KURCCFG=\"TCP\",1,1\r')
    SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 3000)
    SagSendAT(target_at, 'AT+KURCCFG=\"UDP\",1,1\r')
    SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 3000)
    if (phase > 0):
        SagSendAT(target_at, 'AT+KURCCFG=\"HTTP\",1,1\r')
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 3000)
        SagSendAT(target_at, 'AT+KURCCFG=\"HTTPS\",1,1\r')
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 3000)

def Setup_Module_kipopt(target_at, phase):

    print("target_at: +KIPOPT Connection Configuration...")

    # AT+KIPOPT=?
    SagSendAT(target_at, 'AT+KIPOPT=?\r')
    SagWaitnMatchResp(target_at, ['+KIPOPT: 0,<UDP>,(1-100),(8-1472),(8-1452)\r\n'], 3000)
    SagWaitnMatchResp(target_at, ['+KIPOPT: 0,<TCP-based>,(0-100),(0,8-1460),(0,8-1440)\r\n'], 3000)
    SagWaitnMatchResp(target_at, ['+KIPOPT: 3,(0-1),(0-1)\r\n'], 3000)
    SagWaitnMatchResp(target_at, ['\r\n'], 3000)
    SagWaitnMatchResp(target_at, ['OK\r\n'], 3000)

    # AT+KIPOPT?
    SagSendAT(target_at, 'AT+KIPOPT?\r')
    SagWaitnMatchResp(target_at, ['+KIPOPT: 0,"TCPC",1,0,0\r\n'], 3000)
    SagWaitnMatchResp(target_at, ['+KIPOPT: 0,"TCPS",1,0,0\r\n'], 3000)
    SagWaitnMatchResp(target_at, ['+KIPOPT: 0,"UDPC",2,1020,1020\r\n'], 3000)
    SagWaitnMatchResp(target_at, ['+KIPOPT: 0,"UDPS",2,1020,1020\r\n'], 3000)
    if (phase > 0):
        SagWaitnMatchResp(target_at, ['+KIPOPT: 0,"HTTP",1,0,0\r\n'], 3000)
        SagWaitnMatchResp(target_at, ['+KIPOPT: 0,"HTTPS",1,0,0\r\n'], 3000)
    SagWaitnMatchResp(target_at, ['+KIPOPT: 3,0,0\r\n'], 3000)
    SagWaitnMatchResp(target_at, ['\r\n'], 3000)
    SagWaitnMatchResp(target_at, ['OK\r\n'], 3000)

    # Write AT+KIPOPT
    SagSendAT(target_at, 'AT+KIPOPT=0,\"TCPC\",20,100\r')
    SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 3000)
    SagSendAT(target_at, 'AT+KIPOPT=0,\"TCPS\",20,200\r')
    SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 3000)
    SagSendAT(target_at, 'AT+KIPOPT=0,\"UDP\",20,300\r')
    SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 3000)
    if (phase > 0):
        SagSendAT(target_at, 'AT+KIPOPT=0,\"HTTP\",20,100\r')
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 3000)
        SagSendAT(target_at, 'AT+KIPOPT=0,\"HTTPS\",20,100\r')
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 3000)

    # Read AT+KIPOPT
    SagSendAT(target_at, 'AT+KIPOPT?\r')
    SagWaitnMatchResp(target_at, ['\r\n'], 3000)
    SagWaitnMatchResp(target_at, ['*+KIPOPT: 0,"TCPC",20,100,0\r\n'], 3000)
    SagWaitnMatchResp(target_at, ['+KIPOPT: 0,"TCPS",20,200,0\r\n'], 3000)
    SagWaitnMatchResp(target_at, ['+KIPOPT: 0,"UDPC",20,300,1020\r\n'], 3000)
    SagWaitnMatchResp(target_at, ['+KIPOPT: 0,"UDPS",20,300,1020\r\n'], 3000)
    if (phase > 0):
        SagWaitnMatchResp(target_at, ['+KIPOPT: 0,"HTTP",20,100,0\r\n'], 3000)
        SagWaitnMatchResp(target_at, ['+KIPOPT: 0,"HTTPS",20,100,0\r\n'], 3000)
    SagWaitnMatchResp(target_at, ['+KIPOPT: 3,0,0\r\n'], 3000)
    SagWaitnMatchResp(target_at, ['\r\n'], 3000)
    SagWaitnMatchResp(target_at, ['OK\r\n'], 3000)

    # Restore default values
    SagSendAT(target_at, 'AT+KIPOPT=0,\"TCP\",1,0\r')
    SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 3000)
    SagSendAT(target_at, 'AT+KIPOPT=0,\"UDP\",2,1020\r')
    SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 3000)
    if (phase > 0):
        SagSendAT(target_at, 'AT+KIPOPT=0,\"HTTP\",1,0\r')
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 3000)
        SagSendAT(target_at, 'AT+KIPOPT=0,\"HTTPS\",1,0\r')
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 3000)

def A_HL_INT_IP_KTCP_0000(target_at, read_config, network_tests_setup_teardown, tcp_server):
    """
    Check KTCPxxx AT Command. Nominal/Valid use case
    """

    print("\nA_HL_INT_IP_KTCP_0000 TC Start:\n")
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
    test_ID = "A_HL_INT_IP_KTCP_0000"
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

        # General options configuration
        Setup_Module_kipopt(target_at, phase)

        # Enable/disable URC
        Setup_Module_kurccfg(target_at, read_config, phase)

        # Connection Timer Configuration.
        SagSendAT(target_at, 'AT+KCNXTIMER=1' + ',30,2,60,30\r')
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 3000)

        SagSleep(5000)

        Setup_Module_kCgdcont(target_at, GPRS_Cfg)
        Setup_Module_kCnxCfg(target_at, GPRS_Cfg)

        # Test Command
        SagSendAT(target_at, 'AT+KTCPSND=?\r')
        SagWaitnMatchResp(target_at, ["\r\n+KTCPSND: (1-*),(1-*)\r\n\r\nOK\r\n"], 3000)

        SagSendAT(target_at, 'AT+KTCPRCV=?\r')
        SagWaitnMatchResp(target_at, ["\r\n+KTCPRCV: (1-*),(1-*)\r\n\r\nOK\r\n"], 3000)

        if (phase > 0):
            # TCP state
            print()
            print("Check TCP State...")
            SagSendAT(target_at, 'AT+KTCPSTAT=1\r')
            # issue reported in JIRA : HLLEAPP-59
            SagWaitnMatchResp(target_at, ["\r\n+CME ERROR: 910\r\n"], 3000)

        # TCP Configuration in client mode
        print("TCP Connection Configuration 1...")
        sTargetCnxToTest = str(VarGlobal.iCnxStart)

        # TCP Connection Configuration
        target_at.run_at_cmd('AT+KTCPCFG=' + sTargetCnxToTest + ',0,\"' + PARAM_HL_ECHO_SERVER_IP + '\",' + PARAM_HL_TCP_ECHO_PORT, 15, [r"\+KTCPCFG:\s\d", "OK"])
        rsp = target_at.run_at_cmd("AT+KTCPCFG?", 15, ["OK"])

        if "+KTCPCFG: " in rsp:
            session_id = rsp.split("+KTCPCFG: ")[-1].split(",")[0]

            if (phase > 0):
                print()
                print("Check TCP State after definition...")
                SagSendAT(target_at, 'AT+KTCPSTAT=' + session_id + '\r')
                SagWaitnMatchResp(target_at, ["\r\n+KTCPSTAT: 1,-1,0,0\r\n"], 3000)
                SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 3000)

            # issue reported in JIRA : HLLEAPP-59
            #print
            #print "Poll ACK Status before starting the TCP connection..."
            #SagSendAT(target_at, 'AT+KTCPACKINFO=' + session_id + '\r')
            #SagWaitnMatchResp(target_at, ["\r\n+KTCPACKINFO: " + session_id + ",2\r\n"], 3000)
            #SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 3000)

            print()
            print("Start TCP connection....")
            SagSendAT(target_at, 'AT+KTCPCNX=' + session_id + '\r')
            SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 30000)
            #SagWaitnMatchResp(target_at, ["\r\n+KCNX_IND: 1,4,1\r\n"], 60000)

            if (phase > 0):
                print()
                print("Check TCP State When connecting...")
                SagSendAT(target_at, 'AT+KTCPSTAT=' + session_id + '\r')
                SagWaitnMatchResp(target_at, ["\r\n+KTCPSTAT: 2,-1,0,0\r\n"], 3000)
                SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 3000)

            #SagWaitnMatchResp(target_at, ["\r\n+KCNX_IND: 1,1,0\r\n"], 60000)
            #SagWaitnMatchResp(target_at, ["\r\n+KTCP_IND: " + session_id + ",1\r\n"], 60000)
            SagWaitnMatchResp(target_at, ["*\r\n+KTCP_IND: " + session_id + ",1\r\n"], 60000)

            if (phase > 0):
                print()
                print("Check TCP State When connected...")
                SagSendAT(target_at, 'AT+KTCPSTAT=' + session_id + '\r')
                SagWaitnMatchResp(target_at, ["\r\n+KTCPSTAT: 3,-1,0,0\r\n"], 3000)
                SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 3000)

            print("Check current IP address...")
            SagSendAT(target_at, 'AT+KCGPADDR\r')
            answer = SagWaitResp(target_at, ["\r\n+KCGPADDR: *.*.*.*\r\n"], 3000)
            result = SagMatchResp(answer, ["\r\n+KCGPADDR: *.*.*.*\r\n"])
            SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 3000)
            if result:
                IP = answer.split('"')[1]
                print("IP=", IP)
                if IP is "0.0.0.0":
                    VarGlobal.statOfItem = "NOK"
                    print("!!!Failed, Did not get the IP address")
                #else:
                    #print
                    #print "Poll ACK Status after TCP conncection start..."
                    #SagSendAT(target_at, 'AT+KTCPACKINFO=' + session_id + '\r')
                    #SagWaitnMatchResp(target_at, ["\r\n+KTCPACKINFO: " + session_id + ",1\r\n"], 3000)
                    #SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 3000)

            SagSendAT(target_at, "AT+KTCPSND=" + session_id + "," + str(nData) +"\r")
            if SagWaitnMatchResp(target_at, ["*\r\nCONNECT\r\n"], 3000):
                start = datetime.now()
                SagSendAT(target_at, DATA_EXCHANGED)
                SagSendAT(target_at, END_CODE)
                if not SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 3000):
                    VarGlobal.statOfItem = "NOK"
                    print("Failed!!! End code could not end the data sending.")

                else:

                    # issue reported in JIRA : HLLEAPP-61 and HLLEAPP-177
                    #SagWaitnMatchResp(target_at, ["\r\n+KTCP_ACK: " + session_id + ",1\r\n"], 30000)

                    #Check receive data over same TCPSocket
                    SagWaitnMatchResp(target_at, ["*\r\n+KTCP_DATA: " + session_id + "," + str(nData) + "\r\n"], 3000)

                    if (phase > 0):
                        print()
                        print("Check TCP State when data sending is finished...")
                        SagSendAT(target_at, 'AT+KTCPSTAT=' + session_id + '\r')
                        SagWaitnMatchResp(target_at, ["\r\n+KTCPSTAT: 3,-1,0," + str(nData) + "\r\n"], 3000)
                        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 3000)

                    SagSendAT(target_at, "AT+KTCPRCV="+ session_id +","+ str(nData) + "\r")
                    if SagWaitnMatchResp(target_at, ["*\r\nCONNECT\r\n"], 3000):
                        SagWaitnMatchResp(target_at, [END_CODE], 5000)
                        if not SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 5000):
                            VarGlobal.statOfItem = "NOK"
                            print("Failed!!! still in data mode.")
        else:
            VarGlobal.statOfItem = "NOK"
            swilog.error("Unable to configure TCP connection!")

        # Close properly session if it has been opened
        if "+KTCPCFG: " in rsp:
            if (phase > 0):
                print()
                print("Check TCP State when data receiving is finished...")
                SagSendAT(target_at, 'AT+KTCPSTAT=' + session_id + '\r')
                SagWaitnMatchResp(target_at, ["\r\n+KTCPSTAT: 3,-1,0,0\r\n"], 3000)
                SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 3000)

            print()
            print("Close created session...")
            SagSendAT(target_at, 'AT+KTCPCLOSE=' + session_id + ',1\r')
            SagWaitnMatchResp(target_at, ["*\r\nOK\r\n"], 5000)

            if phase < 3:
                #No direct connexion closed indication
                #SagWaitnMatchResp(target_at, ["*\r\n+KCNX_IND: " + session_id+ ",3\r\n"], 40000)

                #Idle time down counting started for disconnection
                SagWaitnMatchResp(target_at, ["*\r\n+KCNX_IND: " + session_id+ ",5,30\r\n"], 40000)
                #Disconnected due to network
                if (phase > 0):
                    SagWaitnMatchResp(target_at, ["*\r\n+KCNX_IND: " + session_id+ ",3\r\n"], 40000)
                else:
                    SagWaitnMatchResp(target_at, ["*\r\n+KCNX_IND: " + session_id+ ",0,0\r\n"], 40000)

            if (phase > 0):
                print()
                print("Check TCP State when TCP is closed...")
                SagSendAT(target_at, 'AT+KTCPSTAT=' + session_id + '\r')
                SagWaitnMatchResp(target_at, ["\r\n+KTCPSTAT: 5,-1,0,0\r\n"], 3000)
                SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 3000)

            #SagWaitnMatchResp(target_at, ["\r\n+KCNX_IND: 1,3\r\n"], 35000)

            print()
            print("Delete created session...")
            SagSendAT(target_at, 'AT+KTCPDEL=' + session_id + '\r')
            SagWaitnMatchResp(target_at, ["*\r\nOK\r\n"], 3000)

            if (phase > 0):
                print()
                print("Check TCP State TCP connection is deleted ...")
                SagSendAT(target_at, 'AT+KTCPSTAT=' + session_id + '\r')
                SagWaitnMatchResp(target_at, ["\r\n+CME ERROR: 910\r\n"], 3000)

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

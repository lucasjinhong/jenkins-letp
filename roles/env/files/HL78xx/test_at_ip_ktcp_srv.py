"""
IP connectivity AT commands test cases :: KTCP_SRVREQ
originated from A_HL_Common_PROTOCOM_KTCP_SRVREQ_0002.PY validation test script
"""

import pytest
import time
import os
import VarGlobal
from autotest import *
import socket
import ast


def Setup_Module_kCnxTimer(target_at, lcnx_cnf):
    print("target_at: +KCNXTIMER Connection Configuration...")
    SagSendAT(target_at, 'AT+KCNXTIMER?\r')
    SagWaitnMatchResp(target_at, ["*\r\nOK\r\n"], 3000)

    for cnx_cnf in lcnx_cnf:
        SagSendAT(target_at, 'AT+KCNXTIMER=' + str(cnx_cnf) + ',30,2,60,30\r')
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 3000)

    SagSendAT(target_at, 'AT+KCNXTIMER?\r')
    SagWaitnMatchResp(target_at, ["*+KCNXTIMER: " + str(cnx_cnf) + ",30,2,60,30*\r\nOK\r\n"], 3000)

def Setup_Module_kCnxCfg(target_at, GPRS_Cfg):
    print("target_at: +KCNXCFG Connection Configuration...")

    # SagSendAT(target_at, 'AT+KCNXCFG=1,"GPRS","%s","%s","%s"\r' % (GPRS_Cfg[0], GPRS_Cfg[1], GPRS_Cfg[2]))
    # if SagWaitnMatchResp(target_at, ["*\r\nOK\r\n"], 3000) != True:
    #     print "\nPROBLEM: +KCNXCFG command %d response is incorrect.\n" % n

    for n in range(VarGlobal.iCnxStart, VarGlobal.iCnxStart + VarGlobal.iCnxTotal):
        SagSendAT(target_at, 'AT+KCNXCFG=%d,"GPRS","%s","%s","%s"\r' % (n, GPRS_Cfg[0], GPRS_Cfg[1], GPRS_Cfg[2]))
        if SagWaitnMatchResp(target_at, ["*\r\nOK\r\n"], 3000) != True:
            print("\nPROBLEM: +KCNXCFG command %d response is incorrect.\n" % n)

def A_HL_INT_IP_KTCP_SRV_0000(target_at, read_config, network_tests_setup_teardown):
    """
    Check KTCP_SRVREQ AT Command. Nominal/Valid use case
    """
    # Number of host clients
    CONNECTION_NB = 2
    socket_list = []

    print("\nA_HL_INT_IP_KTCP_SRV_0000 TC Start:\n")
    test_environment_ready = "Ready"

    print("\n------------Test's preambule Start------------")

    # Variable Init
    HARD_INI = read_config.findtext("autotest/HARD_INI")
    SIM_GPRS_APN = ast.literal_eval(read_config.findtext("autotest/Network_APN"))[0]
    SIM_GPRS_LOGIN = ast.literal_eval(read_config.findtext("autotest/Network_APN_login"))[0]
    SIM_GPRS_PASSWORD = ast.literal_eval(read_config.findtext("autotest/Network_APN_password"))[0]
    PARAM_GPRS_PDP = ast.literal_eval(read_config.findtext("autotest/Network_PDP_type"))[0]
    AMARISOFT_IP = read_config.findtext("autotest/AmarisoftIPAddress")
    AMARISOFT_IPTABLES_BASE = int(read_config.findtext("autotest/AmarisoftIptablesBase"))
    SIM_GPRS_Cfg = (SIM_GPRS_APN, SIM_GPRS_LOGIN, SIM_GPRS_PASSWORD, PARAM_GPRS_PDP)
    VarGlobal.iCnxStart = 1
    VarGlobal.iCnxTotal = 1
    VarGlobal.lCnxToTest = [1, 2, 3, 4, 5]
    VarGlobal.CNX_TEST = VarGlobal.lCnxToTest[0]

    # Requires Amarisoft SIM Card for the test case
    Network = read_config.findtext("autotest/Network")
    if "amarisoft" not in str.lower(Network):
        raise Exception("Problem: Amarisoft SIM and Config should be used.")

    # default CGDCONT
    cgdcont = []
    SagSendAT(target_at, "AT+CGDCONT?\r")
    answer = SagWaitResp(target_at, ["\r\n*\r\n\r\nOK\r\n"], 5000)
    for line_answer in answer.split("\r\n"):
        result = SagMatchResp(line_answer, ["+CGDCONT: *"])
        if result:
            cgdcont.append(line_answer.split(": ")[1])
            print("\nDefault cgdcont is: "+cgdcont[-1])

    # detach from network
    SagSendAT(target_at, "AT+CFUN=0\r")
    SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 2000)

    #AT+CGDCONT=
    SagSendAT(target_at, 'AT+CGDCONT=1,"'+PARAM_GPRS_PDP+'","'+SIM_GPRS_APN+'"\r')
    SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 10000)

    # Restart module
    SWI_Reset_Module(target_at, HARD_INI)

    test_nb = ""
    test_ID = "A_HL_INT_IP_KTCP_SRV_0000"
    PRINT_START_FUNC(test_nb + test_ID)

    print("\n----- Testing Start -----\n")

    try:
        # Default K config
        SagSendAT(target_at, 'AT&V\r')
        answer = SagWaitResp(target_at, ["\r\n*\r\n\r\nOK\r\n"], C_TIMER_LOW)
        result = SagMatchResp(answer, ["\r\nACTIVE PROFILE:\r\n*\r\n*"])
        if result:
            k = answer.split("\r\n")[2].split(" ")[9]
            print("\nDefault K is: "+k)
        else:
            k = "&K3"

        cnx_cnf = VarGlobal.CNX_TEST

        print()
        print("target_at: Enable bi-directional hardware flow control...")
        SagSendAT(target_at, "AT&K3\r")
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 3000)

        print()
        print("target_at: GPRS Connection Configuration...")
        Setup_Module_kCnxCfg(target_at, SIM_GPRS_Cfg)

        print()
        print("target_at: Connection Timer Configuration...")
        Setup_Module_kCnxTimer(target_at, [cnx_cnf])

        print()
        END_PATTERN = '--EOF--Pattern--'
        print()

        print()
        print("target_at: Check Current End code..")
        SagSendAT(target_at, 'AT+KPATTERN="' + END_PATTERN + '"\r')
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 3000)

        print("target_at: Display PDP Address...")
        # GOLF-168
        if "HL78" in HARD_INI:
            CGPADDR = "\r\n+CGPADDR: " + str(cnx_cnf) + ",\"*\"\r\n"
        elif "RC51" in HARD_INI:
            CGPADDR = "\r\n+CGPADDR: " + str(cnx_cnf) + ",*\r\n"

        SagSendAT(target_at, 'AT+CGPADDR\r')
        answer = SagWaitResp(target_at, [CGPADDR], 3000)
        result_target_at_IP = SagMatchResp(answer, ["*" + CGPADDR + "*"])
        SagWaitnMatchResp(target_at, ["*OK\r\n"], 3000)
        if result_target_at_IP:
            if "HL78" in HARD_INI:
                target_at_IP = answer.split('"')[1]
            elif "RC51" in HARD_INI:
                target_at_IP = answer.split(',')[1]
            print("TCP Server IP =", target_at_IP)
        else:
            raise Exception("---->Problem: No IP address !!!")

        TCP_LISTEN_PORT = AMARISOFT_IPTABLES_BASE + int(target_at_IP.split(".")[3])

        i = 0
        print()
        print("target_at: TCP server Configuration ", i)
        SagSendAT(target_at, 'AT+KTCPCFG=' + str(cnx_cnf) + ',1,,' + str(TCP_LISTEN_PORT + i) + '\r')
        SagWaitnMatchResp(target_at, ["\r\n+KTCPCFG: " + str(i + 1) + "\r\n"], 3000)
        SagWaitnMatchResp(target_at, ["*OK\r\n"], 3000)

        print("target_at: Start TCP Connection ", i)
        SagSendAT(target_at, 'AT+KTCPCNX=' + str(i + 1) + '\r')
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 3000)

        SagSleep(30000)
        SagWaitnMatchResp(target_at, ["*\r\n+KTCP_IND: " + str(i + 1) + ",1\r\n"], 40000)

        for i in range(0, CONNECTION_NB):
            # Create a TCP socket
            tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            socket_list.append(tcp_socket)
            # Data should be sent to the amarisoft address at port 5000 + end address of the target
            # The iptables rules will forward to the target
            # i.e, to connect to the module @192.168.2.14, use the port 5014.
            #      to connect to the module @192.168.2.9, use the port 5009.
            print("Try to connect to the server %s port %s" % (AMARISOFT_IP, TCP_LISTEN_PORT))
            tcp_socket.connect((AMARISOFT_IP, TCP_LISTEN_PORT))
            print("connected")

        SagSleep(3000)

        for i in range(0, CONNECTION_NB):
            # Get the host TCP ip and port. It will be used by the server  to send data to client.
            tcp_client_ip, tcp_client_port = socket_list[i].getsockname()
            swilog.info("Get tcp client  %s port %d" % (tcp_client_ip, tcp_client_port))
            SagWaitnMatchResp(target_at, ["\r\n+KTCP_SRVREQ: " + str(1) + "," + str(i + 2) + ",\"" + tcp_client_ip + "\"," + str(tcp_client_port) + "\r\n"], 30000)

        data = 50*"a"
        # Send data from first client (subsession 2)
        swilog.step("send data from first client")
        socket_list[0].send(data.encode())

        # Notification on target
        SagWaitnMatchResp(target_at, ["\r\n+KTCP_DATA: %d,%d\r\n" % (2, len(data))], 3000)
        # Receive data
        SagSendAT(target_at, 'AT+KTCPRCV=2,%d\r' % len(data))
        SagWaitnMatchResp(target_at, ["\r\nCONNECT\r\n"], 3000)
        # Check that all is received
        SagWaitnMatchResp(target_at, ["%s%s\r\n" % (data, END_PATTERN)], 3000)
        SagWaitnMatchResp(target_at, ["OK\r\n"], 3000)

        swilog.step("send data back to client")
        SagSendAT(target_at, 'AT+KTCPSND=2,%d\r' % len(data))
        SagWaitnMatchResp(target_at, ["\r\nCONNECT\r\n"], 3000)
        SagSendAT(target_at, "%s%s\r" % (data, END_PATTERN))
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 3000)

        rsp = socket_list[0].recv(len(data)).decode()
        # Check that all is received
        assert rsp == data, "The received data are not correct"
        swilog.info("Received data are correct")

        for i in range(0, CONNECTION_NB):
            socket_list[i].close()
            SagWaitnMatchResp(target_at, ["\r\n+KTCP_NOTIF: " + str(i + 2) + ",4\r\n"], 3000)

        print()
        print("target_at: Close server session...")
        SagSendAT(target_at, 'AT+KTCPCLOSE=1,1\r')
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 3000)

        print()
        print("target_at: Close server session...")
        SagSendAT(target_at, 'AT+KTCPDEL=1\r')
        SagWaitnMatchResp(target_at, ["*\r\nOK\r\n"], 3000)

        # Restore default K
        SagSendAT(target_at, 'AT%s\r' % k)
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], C_TIMER_LOW)

    except Exception as e:
        print(e)
        VarGlobal.statOfItem = "NOK"

    # detach from network
    SagSendAT(target_at, "AT+CFUN=0\r")
    SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 2000)

    # Restore default CGDCONT
    for cgdcont_elem in cgdcont:
        SagSendAT(target_at, "AT+CGDCONT=" + cgdcont_elem + "\r")
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 10000)

    # Restart module
    SWI_Reset_Module(target_at, HARD_INI)

    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)

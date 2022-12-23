"""
PPP generic test case
Use Create_DialUpNoComp.sh and Start_Stop_Dialup.sh
"""
import os
import pytest
import pexpect
import swilog
import time
import ast
import VarGlobal
import com
from autotest import *

@pytest.fixture
def initdevice_clean(target_at, read_config, network_tests_setup_teardown):

    print("\nA_HL_INT_PPP_0001 TC Start:\n")
    test_environment_ready = "Ready"

    try:
        print("\n------------Test's device preambule Start-----------")
        SIM_Pin1 = read_config.findtext("autotest/PIN1_CODE")
        rootpassword = read_config.findtext("autotest/Sudo")
        if not rootpassword:
            raise Exception("---->Problem: Enter your rootpassword in 'Sudo' field in autotest.xml for ppp management")
        phase = int(read_config.findtext("autotest/Features_PHASE"))
        HARD_INI = read_config.findtext("autotest/HARD_INI")
        KSRAT = read_config.findtext("autotest/Network_Config/Ksrat")
        Network_APN = ast.literal_eval(read_config.findtext("autotest/Network_APN"))[3]
        PDPtype = ast.literal_eval(read_config.findtext("autotest/Network_PDP_type"))[3]
        Login = ast.literal_eval(read_config.findtext("autotest/Network_APN_login"))[3]
        Password = ast.literal_eval(read_config.findtext("autotest/Network_APN_password"))[3]

        # Requires Amarisoft SIM Card for the test case
        Network = read_config.findtext("autotest/Network")
        if "amarisoft" not in str.lower(Network):
            raise Exception("Problem: Amarisoft SIM and Config should be used.")

        # Restart the device
        SWI_Reset_Module(target_at, HARD_INI)

        SagSendAT(target_at, "AT&K3\r")
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 5000)

        # check if SIM is locked
        lockSIM = 0
        SagSendAT(target_at, 'AT+CLCK="SC",2\r')
        lock_resp = SagWaitResp(target_at, ["\r\n+CLCK: ?\r\n\r\nOK\r\n"], 4000)
        if lock_resp.find('+CLCK: 0') == -1:
            # SIM locked => unlock SIM
            lockSIM = 1
            SagSendAT(target_at, 'AT+CLCK="SC",0,"' + SIM_Pin1 + '"\r')
            SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 4000)

        # AT+WPPP=?
        SagSendAT(target_at, "AT+WPPP=?\r")
        if (phase > 0):
            SagWaitnMatchResp(target_at, ["\r\n+WPPP: (0-2),(1-2)\r\n"], 2000)
        else:
            # only one PDP context is present
            SagWaitnMatchResp(target_at, ["\r\n+WPPP: (0-2),(1)\r\n"], 2000)
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 2000)

        # AT+WPPP?
        SagSendAT(target_at, "AT+WPPP?\r")
        answer = SagWaitResp(target_at, ["*\r\nOK\r\n"], 2000)
        result = SagMatchResp(answer, ["\r\n+WPPP: ?,?,\"*\",\"*\"\r\n\r\n"])
        # default wppp
        if result:
            wppp = answer.split("\r\n")[1].split(": ")[1]
            print("\nDefault wppp is: " + wppp)
        else:
            wppp = "0,1,\"\",\"\""

        # default CGDCONT
        cgdcont = []
        SagSendAT(target_at, "AT+CGDCONT?\r")
        answer = SagWaitResp(target_at, ["\r\n*\r\n\r\nOK\r\n"], 5000)
        for line_answer in answer.split("\r\n"):
            result = SagMatchResp(line_answer, ["+CGDCONT: *"])
            if result:
                cgdcont.append(line_answer.split(": ")[1])
                print("\nDefault cgdcont is: " + cgdcont[-1])

        # detach from network
        SagSendAT(target_at, "AT+CFUN=0\r")
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 2000)

        # AT+CGDCONT=
        SagSendAT(target_at, 'AT+CGDCONT=1,"' + PDPtype + '","' + Network_APN + '"\r')
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 10000)

        # AT+WPPP=1
        SagSendAT(target_at, "AT+WPPP=1,1,\"%s\",\"%s\"\r" % (Login, Password))
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 10000)

        # attach to network
        #SagSendAT(target_at, "AT+CFUN=1\r")
        #SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 2000)

        # Restart the device
        SWI_Reset_Module(target_at, HARD_INI)

        SagSendAT(target_at, "AT&K3\r")
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 5000)

        # ticket : DIZZY-2275
        # AT+WPPP?
        SagSendAT(target_at, "AT+WPPP?\r")
        SagWaitnMatchResp(target_at, ["\r\n+WPPP: 1,1,\"%s\",\"%s\"\r\n" % (Login, Password)], 2000)
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 2000)

        # Check Cell Network state
        SWI_Check_Network_Coverage(target_at, HARD_INI, KSRAT, AT_CMD_List_Net_Registration, AT_RESP_List_Net_Registration, Max_Try_Net_Registration)

    except Exception as e:
        print("***** Test's device preambule Fails !!!*****")
        print(type(e))
        print(e)
        test_environment_ready = "Not_Ready"

    # If test_environment is not ready, we stop the test
    assert test_environment_ready == "Ready"

    test_nb = ""
    test_ID = "A_HL_INT_PPP_0001"
    PRINT_START_FUNC(test_nb + test_ID)

    # close UART
    target_at.close()

    yield

    # reinit UART
    target_at.reinit()

    # AT
    SagSendAT(target_at, 'AT\r')
    SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 2000)

    # detach from network
    SagSendAT(target_at, "AT+CFUN=0\r")
    SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 2000)

    # Restore default CGDCONT
    for cgdcont_elem in cgdcont:
        SagSendAT(target_at, "AT+CGDCONT=" + cgdcont_elem + "\r")
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 10000)

    # Restore default wppp
    SagSendAT(target_at, "AT+WPPP=" + wppp + "\r")
    SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 10000)

    SagSleep(5000)
    # Restart the device
    SWI_Reset_Module(target_at, HARD_INI)

    SagSendAT(target_at, "AT&K3\r")
    SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 5000)

    # lock SIM
    if (lockSIM == 1):
        SagSendAT(target_at, 'AT+CLCK="SC",1,"' + SIM_Pin1 + '"\r')
        SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 4000)

    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)


@pytest.fixture
def initppp_clean(initdevice_clean, read_config):

    slink = read_config.findtext("module/slink2/name")
    Serial_BaudRate = read_config.findtext("module/slink2/speed")

    rootpassword = read_config.findtext("autotest/Sudo")
    # Network interface (ie Ethernet Link) is settled in config/host.xml. It can be given by "ifconfig"
    hostnetworkif = read_config.findtext("host/network_if")

    # PPP Init part - initdevice_clean (before yield) should have been called (SIM,network check)

    # Cut host network interface before PPP establishment for enabling PPP routing without setting
    Command = 'sudo -S ifconfig %s down' % hostnetworkif
    swilog.info(Command)
    exit = os.system('echo "%s" | ' % rootpassword + Command)
    assert exit == 0, 'sudo ifconfig enp0s3 down issue'

    time.sleep(1)

    # PPP establishment
    Command = 'sudo -S $LETP_TESTS/tools/Create_DialUpNoComp.sh hl78xx %s 1 %s' % (slink, Serial_BaudRate)
    swilog.info(Command)
    exit = os.system('echo "%s" | ' % rootpassword + Command)
    assert exit == 0, 'sudo Create_DialUpNoComp.sh issue'

    time.sleep(2)

    Command = 'sudo -S $LETP_TESTS/tools/Start_Stop_Dialup.sh 1 hl78xx'
    swilog.info(Command)
    exit = os.system('echo "%s" | ' % rootpassword + Command)
    assert exit == 0, 'sudo Start_Stop_Dialup.sh 1 issue'

    time.sleep(5)

    yield

    # Cleaning part - initdevice_clean (after yield) should be called after to clean - No assert in this part of code

    # Stop ppp0 link
    Command = 'sudo -S $LETP_TESTS/tools/Start_Stop_Dialup.sh 0 hl78xx'
    swilog.info(Command)
    exit = os.system('echo "%s" | ' % rootpassword + Command)
    #assert exit==0, 'sudo Start_Stop_Dialup.sh 0 issue'
    time.sleep(5)

    # Set back host network interface
    Command = 'sudo -S ifconfig %s up' % hostnetworkif
    swilog.info(Command)
    exit = os.system('echo "%s" | ' % rootpassword + Command)
    #assert exit==0, 'sudo ifconfig enp0s3 up issue'
    time.sleep(2)

def A_HL_INT_PPP_0001(initppp_clean, read_config):

    # All ppp initialisation and cleaning code are done in initppp_clean and initdevice_clean
    AmarisoftIPAddress = read_config.findtext("autotest/AmarisoftIPAddress")
    DeviceLocalIPAddress = read_config.findtext("autotest/DeviceLocalIPAddress")

    # Check pp0 link creation
    Command = 'ifconfig ppp0'
    swilog.info(Command)
    (rsp, exit) = pexpect.run(Command, withexitstatus=1)
    swilog.info(rsp)
    assert exit == 0, 'ifconfig ppp0 issue'

    time.sleep(5)

    # Send ping with ppp0 to device
    Command = 'ping -c 4 -i 1 "%s"' % DeviceLocalIPAddress
    swilog.info(Command)
    (rsp, exit) = pexpect.run(Command, withexitstatus=1)
    swilog.info(rsp)
    assert exit == 0, "ping to device can't be sent"

    time.sleep(1)

    # Connect to device with FTP
    Command = 'ftp -n "%s"' % DeviceLocalIPAddress
    swilog.info(Command)
    child = pexpect.spawn(Command)
    id = child.expect([pexpect.TIMEOUT, 'unreachable', 'ftp> '])
    assert id == 2, "ftp can't be called"

    swilog.info(child.before + child.after)
    time.sleep(5)
    child.sendline('disconnect')
    swilog.info('disconnect')
    child.sendline('exit')
    swilog.info('exit')

    time.sleep(1)

    # Send ping with ppp0 to Amarisoft "192.168.2.1" to check we can still do commands
    Command = 'ping -c 4 -i 1 "%s"' % AmarisoftIPAddress
    swilog.info(Command)
    (rsp, exit) = pexpect.run(Command, withexitstatus=1)
    swilog.info(rsp)
    assert exit == 0, "ping to Amarisoft can't be sent"

    time.sleep(1)

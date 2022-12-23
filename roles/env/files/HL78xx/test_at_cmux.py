"""
CMUX connectivity AT commands test cases :: CMUX
originated from A_INTEL_LTE3G_GEN_CMUX_0173.PY validation test script
"""

import pytest
import time
import os
import VarGlobal
import re
import com
import subprocess
from autotest import *

def A_HL_INT_CMUX_0000(target_at, read_config, non_network_tests_setup_teardown):
    """
    Check CMUX AT Command. Nominal/Valid use case
    """

    print("\nA_HL_INT_CMUX_0000 TC Start:\n")
    test_environment_ready = "Ready"

    print("\n------------Test's preambule Start------------")

    # Variable Init
    HARD_INI = read_config.findtext("autotest/HARD_INI")
    slink = read_config.findtext("module/slink2/name")
    Serial_BaudRate = read_config.findtext("module/slink2/speed")
    rootpassword = read_config.findtext("autotest/Sudo")
    gsmMuxd = os.path.expandvars("$LETP_TESTS/tools/gsmMuxd")
    if not rootpassword:
      raise Exception("---->Problem: Enter your rootpassword in 'Sudo' field in autotest.xml for cmux management")

    test_nb = ""
    test_ID = "A_HL_INT_CMUX_0000"
    PRINT_START_FUNC(test_nb + test_ID)

    print("\n----- Testing Start -----\n")

    if "HL78" in HARD_INI:
        # Command to create 4 virtual ports
        Command = '%s -p %s -b %s /dev/ptmx /dev/ptmx /dev/ptmx /dev/ptmx' % (gsmMuxd, slink, Serial_BaudRate)
    elif "RC51" in HARD_INI:
        # Command to create 3 virtual ports
        Command = '%s -p %s -b %s /dev/ptmx /dev/ptmx /dev/ptmx' % (gsmMuxd, slink, Serial_BaudRate)

    killCmd = 0

    try:

        if "HL78" in HARD_INI:
            #AT+CMUX=?
            SagSendAT(target_at, "AT+CMUX=?\r")
            SagWaitnMatchResp(target_at, ["\r\n+CMUX: (0),(0),(1-8),(1-1509),(1-255),(0-100),(2-255),(1-255)\r\n"], 2000)
            SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 2000)

            #AT+CMUX?
            SagSendAT(target_at, "AT+CMUX?\r")
            SagWaitnMatchResp(target_at, ["\r\n+CMUX: 0,0,5,31,10,3,30,10,0\r\n"], 2000)
            SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 2000)

        elif "RC51" in HARD_INI:
            #AT+CMUX=?
            SagSendAT(target_at, "AT+CMUX=?\r")
            SagWaitnMatchResp(target_at, ["\r\n+CMUX:(0),(0-2),(1-6),(1-32768),(1-255),(0-100),(2-255),(1-255),(1-7)\r\r\n"], 2000)
            SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 2000)

            #AT+CMUX?
            SagSendAT(target_at, "AT+CMUX?\r")
            SagWaitnMatchResp(target_at, ["\r\n+CMUX: 0,0,1,31,10,3,30,10,2\r\r\n"], 2000)
            SagWaitnMatchResp(target_at, ["\r\nOK\r\n"], 2000)

        # ls /dev/pts
        output0 = subprocess.check_output("ls /dev/pts", shell=True).decode()
        print("output:", output0.replace("\n", " "))

        # Create 4 virtual ports
        cmd = 'sudo -S ' + Command
        swilog.info(cmd)
        exit = os.system('echo "%s" | ' % rootpassword + cmd)
        assert exit==0, 'sudo gsmMuxd issue'

        time.sleep(1)

        killCmd = 1

        # ls /dev/pts
        output1 = subprocess.check_output("ls /dev/pts", shell=True).decode()
        print("output:", output1.replace("\n", " "))

        # find virtual ports numbers
        tab0 = output0.split("\n")
        tab1 = output1.split("\n")
        tabdiff = []

        idx = 0
        for t in tab1:
            if (t != tab0[idx]):
                tabdiff.append(t)
            else:
                idx = idx + 1

        for port in tabdiff:
            # add permissions
            cmd = 'sudo -S chmod 666 /dev/pts/' + port
            swilog.info(cmd)
            exit = os.system('echo "%s" | ' % rootpassword + cmd)
            assert exit==0, 'sudo chmod issue'

            time.sleep(1)
            # mounte virtual port
            print("Monte TTY virtual port")
            tty = "/dev/pts/" + port
            # close UART
            target_at.close()
            # open virtual UART
            slink = target_at.open(tty)
            time.sleep(15)

            # send AT cmd
            print("Send AT commands through TTY virtual port")
            if "HL78" in HARD_INI:
                slink.run_at_cmd("AT%VER", 10)
                slink.run_at_cmd("AT%PDNSET?", 10)
            slink.run_at_cmd("ATI9", 10)
            slink.run_at_cmd("AT+COPS?", 10)


    except Exception as err_msg :
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)

    time.sleep(1)

    if killCmd:
        # Kill virtual ports
        cmd = 'sudo -S pkill -f \'' + Command + '\''
        swilog.info(cmd)

        exit = os.system('echo "%s" | %s' % (rootpassword, cmd))
        #ERROR CASE
        #assert exit==0, 'sudo kill issue'

        time.sleep(1)

    # reinit UART
    target_at.close()
    target_at.reinit()

    # Restore Module
    SWI_Reset_Module(target_at, HARD_INI)

    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)


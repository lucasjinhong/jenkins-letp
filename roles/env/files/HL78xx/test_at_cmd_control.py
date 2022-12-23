"""
Test :: FWINT-319/EURY-1975/ALT1250-3700: AT Command Access Level
Test :: FWINT-517/EURY-3865/3991: Add in all L3 Altair AT Commands
Check default Access Control password "A710" can control AT commands with diff level
"""

import pytest
import time
import swilog
import pexpect
import VarGlobal
from autotest import *

swilog.info( "\n----- Program start -----\n")

# -------------------------- Module Initialization ----------------------------------
def A_HL_INT_ATCMD_CONTROL_0000(target_cli, target_at, read_config, non_network_tests_setup_teardown):
    print("\nA_HL_INT_ATCMD_CONTROL_0000 TC Start:\n")
    test_environment_ready = "Ready"
    print("\n------------Test's preambule Start------------")

    # Firmware version check
    SOFT_INI_Soft_Version = read_config.findtext("autotest/SOFT_INI_Soft_Version")
    Firmware_Ver = two_digit_fw_version(SOFT_INI_Soft_Version)
    if Firmware_Ver < "04.06.00.00" or "05.03.00.00" < Firmware_Ver < "05.03.03.00":
        pytest.skip("FW<4.6 or <5.3.0.0<FW<5.3.3.0: AT Command Access Control Not Supported")

    # Variable Init
    timeout = 15
    model = read_config.findtext("autotest/HARD_INI")
    cmd_resp = "ERROR"

    # Run L1 command "AT%GETPROP" to dump svn value to test L3 ALtair "AT%SETPROP" command
    rsp = target_at.run_at_cmd("AT%GETPROP=\"SVN\"", timeout, ["OK"])
    svn = rsp.split(":")[1].split("\r\n")[0][1:-1]

    # Get IMEI to configure DTLS ID
    rsp = target_at.run_at_cmd("AT+WIMEI?", timeout, ["OK"])
    imei = rsp.split(":")[1].split("\r\n")[0].replace(" ","")

    test_nb = ""
    test_ID = "A_HL_INT_ATCMD_CONTROL_0000"
    PRINT_START_FUNC(test_nb + test_ID)

    print("\n------------Test's preambule End------------")

    # Start Test
    print("\n------------Test Case Start------------")

    try:
        # Initialize the module status
        print ("Initialize the module status")
        SagSendAT(target_cli, "\r\nsd d\r\n")
        SagSendAT(target_cli, "\r\ncd static-config\r\n")
        SagSendAT(target_cli, "\r\nrm cs6ynTzTJh\r\n")
        SagSendAT(target_cli, "\r\nrm 8Kb71jJeOf\r\n")
        SagSleep (2000)
        target_at.run_at_cmd("AT+CFUN=1,1", timeout, ["OK"])
        SagSleep (25000)

        for scenario in range(1,7):

            if scenario == 1:
                print ("------------------------------------------------------------------------------")
                print ("Test 1: Without unlock level 2~3 commands: level 3 commands get ERROR response")
                print ("------------------------------------------------------------------------------")

            elif scenario == 2:
                print ("----------------------------------------------------------------------------")
                print ("Test 2: Unlock level 2 with default pwd: level 3 commands get ERROR response")
                print ("----------------------------------------------------------------------------")
                print ("----->Unlock level 2 with wrong password: A71")
                target_at.run_at_cmd ("AT!ENTERCND=\"A71\"", timeout, ["ERROR"])
                SagSleep (5000)
                print ("----->Unlock Level 2 AT Commands with default password: A710")
                target_at.run_at_cmd ("AT!ENTERCND=\"A710\"", timeout, ["OK"])
                SagSleep (3000)

            elif scenario == 3:
                print ("---------------------------------------------------------------------------")
                print ("Test 3: Unlock level 3 with default pwd: level 1~3 commands get OK response")
                print ("---------------------------------------------------------------------------")
                print ("----->Unlock level 3 with wrong password: A7100")
                target_at.run_at_cmd ("AT!UNLOCK=\"A7100\"", timeout, ["ERROR"])
                SagSleep (5000)
                print ("----->Unlock Level 3 AT Commands with default password: A710")
                target_at.run_at_cmd ("AT!UNLOCK=\"A710\"", timeout, ["OK"])
                cmd_resp = "OK"
                SagSleep (3000)

            elif scenario == 4:
                print ("----------------------------------------------------------------------------")
                print ("Test 4: Set level 2 with customized pwd: level 3 commands get ERROR response")
                print ("----------------------------------------------------------------------------")
                target_at.run_at_cmd ("AT!ENTERCND=\"A710\"", timeout, ["OK"])
                SagSleep (3000)
                target_at.run_at_cmd ("AT!SETCND=\"password2\"", timeout, ["OK"])
                print ("")
                print ("----->Unlock level 2 with wrong password: password")
                target_at.run_at_cmd ("AT!ENTERCND=\"password\"", timeout, ["ERROR"])
                SagSleep (5000)
                print ("----->Unlock level 2 with default password: A710")
                target_at.run_at_cmd ("AT!ENTERCND=\"A710\"", timeout, ["ERROR"])
                SagSleep (10000)
                print ("----->Unlock Level 2 AT Commands with customized password: password2")
                target_at.run_at_cmd ("AT!ENTERCND=\"password2\"", timeout, ["OK"])
                cmd_resp = "ERROR"
                SagSleep (3000)

            elif scenario == 5:
                print ("---------------------------------------------------------------------------")
                print ("Test 5: Set level 3 with customized pwd: level 1~3 commands get OK response")
                print ("---------------------------------------------------------------------------")
                target_at.run_at_cmd("AT!OPENLOCK?", timeout, ["OK"])
                SagSleep (5000)
                print ("----->AT!SETLOCK is a level 3 command")
                target_at.run_at_cmd ("AT!SETLOCK=\"password3\"", timeout, ["ERROR"])
                SagSleep (5000)
                target_at.run_at_cmd ("AT!UNLOCK=\"A710\"", timeout, ["OK"])
                target_at.run_at_cmd ("AT!SETLOCK=\"password3\"", timeout, ["OK"])
                print("")
                print ("----->Unlock level 3 with wrong password: password123")
                target_at.run_at_cmd ("AT!UNLOCK=\"password123\"", timeout, ["ERROR"])
                SagSleep (10000)
                print ("----->Unlock level 3 with default password: A710")
                target_at.run_at_cmd ("AT!UNLOCK=\"A710\"", timeout, ["ERROR"])
                SagSleep (10000)
                print ("----->Unlock Level 3 AT Commands with customized password: password3")
                target_at.run_at_cmd ("AT!UNLOCK=\"password3\"", timeout, ["OK"])
                cmd_resp = "OK"
                SagSleep (3000)

            elif scenario == 6:
                print ("-----------------------------------------------------------------------")
                print ("Test 6: Set level 3 with empty pwd: level 3 commands get ERROR response")
                print ("-----------------------------------------------------------------------")
                target_at.run_at_cmd ("AT!UNLOCK=\"password3\"", timeout, ["OK"])
                target_at.run_at_cmd ("AT!SETLOCK=\"\"", timeout, ["OK"])
                print("")
                print ("----->Unlock level 3 with empty password")
                target_at.run_at_cmd ("AT!UNLOCK=\"\"", timeout, ["ERROR"])
                SagSleep (10000)
                cmd_resp = "ERROR"
                SagSleep (3000)

            # Level 1 AT Commands: select some 2 level 1 commands to check OK response
            print ("--- Run any Level 1 AT Commands: always OK response---")
            target_at.run_at_cmd("AT+GMM", timeout, ["OK"])
            target_at.run_at_cmd("AT+GMR", timeout, ["OK"])

            # Level 3 Non-Altair AT Commands
            print ("--- Run Level 3 AT Commands ---")
            target_at.run_at_cmd("AT!SECBOOTCFG?", timeout, [cmd_resp])

            # Level 3 ALTAIR Commands
            # SET/GET CFG/ACFG commands used in PRI template
            target_at.run_at_cmd("AT%SETCFG=\"SC_STATE\",\"1\"", timeout, [cmd_resp])
            target_at.run_at_cmd("AT%GETCFG=\"SC_STATE\"", timeout, [cmd_resp])
            target_at.run_at_cmd("AT%%SETACFG=\"Identification.Model.ModelNumber,%s\"" %model, timeout, [cmd_resp])

            # SETBDELAY command, test get and set commands
            if scenario ==1 or scenario == 2 or scenario == 4 or scenario == 6:
                target_at.run_at_cmd("AT%SETBDELAY?", timeout, [cmd_resp])
            else:
                bdelay = target_at.run_at_cmd("AT%SETBDELAY?", timeout, [cmd_resp])
                bdelay = bdelay.split(":")[1].split("\r\n")[0]

                # Remove spaces after equal sign for JIRA ticket ALT1250-4831
                bdelay = bdelay.lstrip()

                target_at.run_at_cmd("AT%%SETBDELAY=%s" %bdelay, timeout, [cmd_resp])

            # FILECMD and FILEDATA commands, must run together
            # Modify and update the file path for the RK3 version
            if Firmware_Ver < "05.00.00.00":
                target_at.run_at_cmd("AT%FILECMD=\"GET\",\"d:/config/swiserver\",1 ", timeout, [cmd_resp])
                target_at.run_at_cmd("AT%FILEDATA=\"READ\",1000", timeout, [cmd_resp])
            else:
                target_at.run_at_cmd("AT%FILECMD=\"GET\",\"d:/userd/generic/swiserver\",1 ", timeout, [cmd_resp])
                target_at.run_at_cmd("AT%FILEDATA=\"READ\",1000", timeout, [cmd_resp])

            # SETPROP command, requires to dump the value then set to the dumped value, FW 5.x and 4.x have different settings
            target_at.run_at_cmd("AT%%SETPROP=\"SVN\",\"%s\"" %svn, timeout, [cmd_resp])

            # Other ALT1250 AT Commands
            target_at.run_at_cmd("AT%DEVCFG=\"RD\"", timeout, [cmd_resp])
            target_at.run_at_cmd("AT%EXE=time", timeout, [cmd_resp])

            # Due to JIRA ticket ALT1250-4665, SSI did not support "overheat" command anymore.
            if Firmware_Ver >= "04.07.00.00" or Firmware_Ver >= "05.04.10.00":
                target_at.run_at_cmd("AT%OTPCMD=\"RD\",\"OVERHEAT\"", timeout, ["ERROR"])
            else:
                target_at.run_at_cmd("AT%OTPCMD=\"RD\",\"OVERHEAT\"", timeout, [cmd_resp])

            target_at.run_at_cmd("AT%TESTCFG?", timeout, [cmd_resp])
            SagSleep (3000)

            # TSTRF Command, requires to set radio off to run the command, then restore the radio after TSTRF command
            target_at.run_at_cmd("AT+CFUN=0", timeout, ["OK"])
            SagSleep (5000)
            target_at.run_at_cmd("AT%TESTCFG?", timeout, [cmd_resp])
            SagSleep (5000)
            target_at.run_at_cmd("AT+CFUN=1", timeout, ["OK"])

            # Sierrawireless NVSEED Set command
            if Firmware_Ver >= "04.06.02.00":
                if scenario ==1 or scenario == 2 or scenario == 4 or scenario == 6:
                    target_at.run_at_cmd("AT+NVSEED=128", timeout, [cmd_resp])
                else:
                    target_at.run_at_cmd("AT+NVSEED=128", timeout, [">"])
                    SagSendAT(target_cli, "\r\nreset\r\n")
                    SagSleep (25000)

            SagSleep (30000)

            # Sierrawireless AT+DWRITE and AT!DMCREDWRITE commands implemented in 4.6.3
            if Firmware_Ver >= "04.06.03.00":
                # Add waiting time
                target_at.run_at_cmd("AT+KCARRIERCFG=5", 60, ["OK"])
                SagSleep (15000)
                target_at.run_at_cmd("AT+CFUN=1,1", timeout, ["OK"])
                SagSleep (25000)

                # Due to JIRA ticket ALT1250-4847 & ALT1250-4846 , Enable LwM2M support.
                target_at.run_at_cmd("AT+dmsupport=1", timeout, ["OK"])
                target_at.run_at_cmd("AT+CFUN=1,1", timeout, ["OK"])
                SagSleep(25000)

                if scenario == 3:
                    target_at.run_at_cmd ("AT!UNLOCK=\"A710\"", timeout, ["OK"])
                elif scenario == 5:
                    target_at.run_at_cmd ("AT!UNLOCK=\"password3\"", timeout, ["OK"])
                target_at.run_at_cmd("AT+DMWRITE=\"0/0/0\",\"coaps://InteropBootstrap.dm.iot.att.com:5694\"", timeout, [cmd_resp])
                target_at.run_at_cmd("AT!DMCREDWRITE=2,%s,101" %imei, timeout, [cmd_resp])
                # restore module after test
                target_at.run_at_cmd("at%lwm2mcmd=\"EXEC_RESOURCE\",3,0,5", timeout, ["OK"])
                # Add deley time
                SagSleep (40000)
                # Add waiting time
                target_at.run_at_cmd("AT+KCARRIERCFG=0", 60, ["OK"])
                SagSleep (15000)
                target_at.run_at_cmd("AT+CFUN=1,1", timeout, ["OK"])
                SagSleep (25000)

            print("")

    except Exception as err_msg :
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)
    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)

    print ("Restore the module to original status")
    SagSendAT(target_cli, "\r\nsd d\r\n")
    SagSendAT(target_cli, "\r\ncd static-config\r\n")
    SagSendAT(target_cli, "\r\nrm cs6ynTzTJh\r\n")
    SagSendAT(target_cli, "\r\nrm 8Kb71jJeOf\r\n")
    SagSendAT(target_cli, "\r\nreset\r\n")

swilog.info("\n----- Program End -----\n")

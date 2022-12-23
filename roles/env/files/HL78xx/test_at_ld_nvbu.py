"""
Local Download AT commands test cases :: NVBU
originated from A_INTEL_LTE_NVR_NVBU_0002.PY validation test script
"""

import pytest
import time
import os
import VarGlobal
import re
import serial
from autotest import *

timeout = 15

@pytest.fixture()
def nvbu_setup_teardown(target_at, read_config, non_network_tests_setup_teardown):
    """Test case setup and teardown."""
    state = non_network_tests_setup_teardown
    if state == "OK":
        print("General Test Setup Success")

    print("\nA_HL_INT_LD_NVBU_0000 TC Start:\n")

    print("\n------------Test's preambule Start------------")

    phase = int(read_config.findtext("autotest/Features_PHASE"))
    if phase == 0:
        pytest.skip("Phase 0 : No AT+NVBU command")

    # Variable Init
    HARD_INI = read_config.findtext("autotest/HARD_INI")

    test_nb = ""
    test_ID = "A_HL_INT_LD_NVBU_0000"
    PRINT_START_FUNC(test_nb + test_ID)

    print("\n----- Testing Start -----\n")
    yield test_ID
    print("\n----- NVBU TearDown -----\n")

    # Erase old backup log
    target_at.run_at_cmd("AT+NVBU=2,1", timeout, ["OK"])

    # Restore switracemode if changed during nvbu test
    switracemode = target_at.run_at_cmd("AT+SWITRACEMODE?", timeout, ["OK"])
    if switracemode.find("RnD") == -1:
        target_at.run_at_cmd("AT+SWITRACEMODE=RnD", timeout, ["OK"])
        SWI_Reset_Module(target_at, HARD_INI)


def A_HL_INT_LD_NVBU_0000(target_at, read_config, nvbu_setup_teardown):
    """
    Check NVBU AT Command. Nominal/Valid use case
    """

    test_ID = nvbu_setup_teardown

    # Variable Init
    HARD_INI = read_config.findtext("autotest/HARD_INI")
    SOFT_INI_Soft_Version = read_config.findtext("autotest/SOFT_INI_Soft_Version")
    Soft_Version = two_digit_fw_version(SOFT_INI_Soft_Version)

    # Start Test
    print("\n------------Test Case Start------------")

    try:
        #AT+CMEE?
        rsp = target_at.run_at_cmd("AT+CMEE?", timeout, ["OK"])
        cmee = rsp.split(": ")[1].split("\r\n")[0]
        print("\nDefault cmee is: " + cmee)
        if cmee != "1":
            target_at.run_at_cmd("AT+CMEE=1", timeout, ["OK"])

        # get date
        rsp = target_at.run_at_cmd("AT+CCLK?", timeout, ["OK"])
        cclk = rsp.split(": ")[1].split("\r\n")[0]
        print("\nDefault cclk is: " + cclk)
        strDay = cclk.split("\"")[1]

        strTime = '00:00:'
        strDayNVBU = strDay[:8] + ',' + strTime
        strDayCCLK = strDayNVBU + "01+00"

        target_at.run_at_cmd("AT+CCLK=\"%s\"" % strDayCCLK, timeout, ["OK"])

        rsp = target_at.run_at_cmd("ATI9", timeout, ["OK"])
        if rsp.split("\r\n")[2]:
            strATI9 = rsp.split("\r\n")[2]
        else:
            raise Exception("---->Problem: No soft version in ATI9 !!!")

        # Expected backup log responses
        create_log = r"\S+%s\S+ Creating backup" % (strDayNVBU)
        generate_log = r"NVB generation success - backup id: 0 - date: %s\S+ - version: %s" % (strDayNVBU, strATI9)
        # Until EURY-2632 resolved (missing timestamp in 'Restoring backup id 0') remove timestamp from restore_log parameter
        # restore_log = r"\S+%s\S+ Restoring backup id 0" % (strDayNVBU)
        restore_log = r"\S+\S+ Restoring backup id 0"
        entry_log = r"Backup entry found. Date: %s\S+ - version: %s" % (strDayNVBU, strATI9)
        restore_log_1 = r"Restore part 1/2 success - backup id: 0 - date: %s\S+ - ver: %s" % (strDayNVBU, strATI9)
        restore_log_2 = "restore process part 2/2 detected - Updating dynamic configuration files"
        restore_log_3 = "dynamic files restore complete"
        success_log = "NVBACKUP restore success"
        success_log_1 = "restore part 2/2 complete"


        if Soft_Version >= "04.00.00.00":
            # AT+NVBU=?
            target_at.run_at_cmd("AT+NVBU=?", timeout, [r"\+NVBU:\s\(0-4\)", "OK"])

            print("\n---------- Verify Manual & Automatic Mode ----------\n")
            # Verify default mode is "manual"
            target_at.run_at_cmd("AT+NVBU?", timeout, ["manual", "OK"])

            # Verify "automatic" mode
            target_at.run_at_cmd("AT+NVBU=3,1", timeout, ["OK"])
            target_at.run_at_cmd("AT+NVBU?", timeout, ["automatic", "OK"])

            # Configure back to default
            target_at.run_at_cmd("AT+NVBU=3,0", timeout, ["OK"])
            target_at.run_at_cmd("AT+NVBU?", timeout, ["manual", "OK"])
        else:
            # AT+NVBU=?
            target_at.run_at_cmd("AT+NVBU=?", timeout, [r"\+NVBU:\s\(0-2\)", "OK"])

        print("\n---------- Perform Erase backup log ----------\n")
        target_at.run_at_cmd("AT+NVBU=2,1", timeout, ["OK"])
        target_at.run_at_cmd("AT+NVBU=2,0", timeout, ["OK"])

        print("\n---------- Perform +NVBU backup ----------\n")
        # manual generation of backup files from existing NV partitions
        for part_id in range (4):
            target_at.run_at_cmd(
                "AT+NVBU=0,%s" % part_id, timeout * 2,
                ["OK",r"\+NVBU_IND:\s0,0,0,\"%s\S+\",\"%s\"" % (strDayNVBU, strATI9)])

        print("\n---------- Perform +NVBU restore ----------\n")
        # manual generation of backup files from existing NV partitions
        for part_id in range (4):
            target_at.run_at_cmd("AT+NVBU=1,%s" % part_id, timeout, ["OK"])
            time.sleep(60)

            target_at.expect(r"\+NVBU_IND: 1,0,0,0,\"%s\S+\",\"%s\"" % (strDayNVBU, strATI9), 30)

            target_at.run_at_cmd("AT", timeout, ["OK"])
            target_at.run_at_cmd("ATE0", timeout, ["OK"])
            # Unlock module
            target_at.run_at_cmd("AT!UNLOCK=\"A710\"", timeout, ["OK|ERROR"])

        print("\n---------- Perform Erase Backup ----------\n")
        if Soft_Version >= "04.00.00.00":
            target_at.run_at_cmd("AT+NVBU=4", timeout, ["OK"])
        else:
            target_at.run_at_cmd("AT+NVBU=erasebackup", timeout, ["OK"])

        print("\n---------- Perform Read backup log ----------\n")
        if Soft_Version >= "05.00.00.00":
            target_at.run_at_cmd("AT+NVBU=2,0", timeout,
                [create_log, generate_log,
                create_log, generate_log,
                create_log, generate_log,
                create_log, generate_log,
                restore_log, entry_log, restore_log_1, restore_log_2, restore_log_3, success_log_1,
                restore_log, entry_log, restore_log_1, restore_log_2, restore_log_3, success_log_1,
                restore_log, entry_log, restore_log_1, restore_log_2, restore_log_3, success_log_1,
                restore_log, entry_log, restore_log_1, restore_log_2, restore_log_3, success_log_1,
                "backup storage erased", "OK"])
        if Soft_Version >= "04.00.00.00" and Soft_Version < "05.00.00.00":
            target_at.run_at_cmd("AT+NVBU=2,0", timeout,
                [create_log, generate_log,
                create_log, generate_log,
                create_log, generate_log,
                create_log, generate_log,
                restore_log, entry_log, success_log,
                restore_log, entry_log, success_log,
                restore_log, entry_log, success_log,
                restore_log, entry_log, success_log,
                "backup storage erased", "OK"])
        else:
            target_at.run_at_cmd("AT+NVBU=2,0", timeout,
                [create_log, generate_log,
                create_log, generate_log,
                create_log, generate_log,
                create_log, generate_log,
                restore_log, entry_log,
                restore_log, entry_log,
                restore_log, entry_log,
                restore_log, entry_log, "OK"])


        # Test Legacy NVBU commands to check for regression
        print("\n---------- Check Legacy NVBU commands for regression ----------\n")

        # Set clock back to match expected response
        target_at.run_at_cmd("AT+CCLK=\"%s\"" % strDayCCLK, timeout, ["OK"])

        print("\n---------- Verify Manual & Automatic Mode ----------\n")
        # Verify default mode is "manual"
        target_at.run_at_cmd("AT+NVBU=NVfeatureMode,status", timeout, ["manual", "OK"])

        # Verify "automatic" mode
        target_at.run_at_cmd("AT+NVBU=NVfeatureMode,automatic", timeout, ["OK"])
        target_at.run_at_cmd("AT+NVBU=NVfeatureMode,status", timeout, ["automatic", "OK"])

        # Configure back to default
        target_at.run_at_cmd("AT+NVBU=NVfeatureMode,manual", timeout, ["OK"])
        target_at.run_at_cmd("AT+NVBU=NVfeatureMode,status", timeout, ["manual", "OK"])

        print("\n---------- Perform Erase backup log ----------\n")
        target_at.run_at_cmd("AT+NVBU=2,1", timeout, ["OK"])
        target_at.run_at_cmd("AT+NVBU=2,0", timeout, ["OK"])

        print("\n---------- Perform +NVBU backup ----------\n")
        # manual generation of backup files from existing NV partitions
        target_at.run_at_cmd("AT+NVBU=0", timeout * 2,
                ["OK",r"\+NVBU_IND:\s0,0,0,\"%s\S+\",\"%s\"" % (strDayNVBU, strATI9)])

        print("\n---------- Perform +NVBU restore ----------\n")
        # manual generation of backup files from existing NV partitions
        target_at.run_at_cmd("AT+NVBU=1", timeout, ["OK"])
        time.sleep(60)
        target_at.expect(r"\+NVBU_IND: 1,0,0,0,\"%s\S+\",\"%s\"" % (strDayNVBU, strATI9), 30)

        target_at.run_at_cmd("AT", timeout, ["OK"])
        target_at.run_at_cmd("ATE0", timeout, ["OK"])
        # Unlock module
        target_at.run_at_cmd("AT!UNLOCK=\"A710\"", timeout, ["OK|ERROR"])

        print("\n---------- Perform Erase Backup ----------\n")
        target_at.run_at_cmd("AT+NVBU=erasebackup", timeout, ["OK"])

        print("\n---------- Perform Read backup log ----------\n")
        if Soft_Version >= "05.00.00.00":
            target_at.run_at_cmd("AT+NVBU=2,0", timeout,
                [create_log, generate_log,
                restore_log, entry_log, restore_log_1, restore_log_2, restore_log_3, success_log_1,
                "backup storage erased", "OK"])
        elif Soft_Version >= "04.00.00.00" and Soft_Version < "05.00.00.00":
            target_at.run_at_cmd("AT+NVBU=2,0", timeout,
                [create_log, generate_log,
                restore_log, entry_log, success_log,
                "backup storage erased", "OK"])
        else:
            target_at.run_at_cmd("AT+NVBU=2,0", timeout,
                [create_log, generate_log,
                restore_log, entry_log,
                "backup storage erased", "OK"])

    except Exception as err_msg:
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)

    # Restore Module
    target_at.run_at_cmd("AT+CMEE=" + cmee, timeout, ["OK"])
    target_at.run_at_cmd("AT+CCLK=" + cclk, timeout, ["OK"])
    SWI_Reset_Module(target_at, HARD_INI)

    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)

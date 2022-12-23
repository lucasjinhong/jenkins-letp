"""
Description:
Perform continuous FOTA test on AVMS server from the list of version(s) in
SOFT_INI_FOTA_Version. Script will perform continuous FOTA from version A->B->C->D.

    A = SOFT_INI_Soft_Version
    B to D = List in SOFT_INI_Fota_Version

Input Parameters:
SOFT_INI_Soft_Version (Base version)
SOFT_INI_Fota_Version (Target FOTA version(s))
AVMSZipPath (Location of AVMS packages - provide a list of either local directory(s)
                                         or server link(s))

WARNING:
If you want the module to end up back into original version (A),
you must define that as the last parameter in SOFT_INI_FOTA_VERSION.

Power Consumption:
Requires to connect OTII device to capture power comsumption data.

"""


import time
import os
import ast
from datetime import datetime
import pytest
import VarGlobal
from autotest import (
    is_valid_fw, ensure_network_connection, SWI_Reset_Module)
from avms_upgrade import (
    av_session_config, av_upgrade_session, av_upgrade_result, autoflash, open_txt_header)
from autotest import PRINT_START_FUNC, PRINT_TEST_RESULT
from autotest import pytestmark  # noqa # pylint: disable=unused-import
import swilog
from otii_utility import *

timeout = 15
timestamp = datetime.now().strftime("%y%m%d_%H%M%S")

log_dir = os.path.join(
    "./log",
    timestamp + "_" + os.path.basename(__file__))
os.makedirs(log_dir, exist_ok=True)

log_file = os.path.join(log_dir, "ensure_network_config.txt")
with open(log_file, 'w') as output:
    output.write("")

proc_file = os.path.join(log_dir, "processing_time.txt")
pwr_file = os.path.join(log_dir, "power_consumption.txt")

open_txt_header(proc_file, pwr_file)

@pytest.fixture()
def avms_package_setup_teardown(
        ensure_package_exists, target_at,
        read_config, network_tests_setup_teardown):

    print("\nA_HL_INT_AVMS_0000 TC Start:\n")
    print("\n------------Test's preambule Start------------")
    """Test case setup and teardown."""
    state = network_tests_setup_teardown
    if state == "OK":
        print("General Test Setup Success")

    # Variable Init
    SOFT_INI_Soft_Version = read_config.findtext("autotest/SOFT_INI_Soft_Version")
    slink2 = read_config.findtext("module/slink2/name")
    AVMSZipPath = ast.literal_eval(read_config.findtext("autotest/AVMSZipPath"))
    Autoflasher = int(read_config.findtext("autotest/Features_Autoflasher"))
    relay_port = read_config.findtext("hardware/power_supply/com/port")
    relay_num = read_config.findtext("hardware/power_supply/port_nb")

    test_nb = ""
    test_ID = "A_HL_INT_AVMS_0000"
    PRINT_START_FUNC(test_nb + test_ID)

    print("\n----- Testing Start -----\n")
    yield test_ID
    print("\n----- AVMS TearDown -----\n")

    # Restore module to base version if test script failed
    if Autoflasher and VarGlobal.statOfItem == "NOK":
        rsp = target_at.run_at_cmd("ATI3", timeout, ["OK"])
        version = rsp.split("\r\n")[1]

        if not version == SOFT_INI_Soft_Version:
            if AVMSZipPath == ['']:
                autoflash(SOFT_INI_Soft_Version, slink2, relay_port, relay_num)
            else:
                autoflash(SOFT_INI_Soft_Version, slink2, relay_port, relay_num, AVMSZipPath[0])


def A_HL_INT_AVMS_0000(read_config, avms_client, otii_setup_teardown, avms_package_setup_teardown, target_at):
    """
    Check AVMS AT Command. Nominal/Valid use case
    """
    test_ID = avms_package_setup_teardown

    otii_object = otii_setup_teardown

    # Variable Init
    HARD_INI = read_config.findtext("autotest/HARD_INI")
    SIM_Pin1 = read_config.findtext("autotest/PIN1_CODE")
    SOFT_INI_Soft_Version = read_config.findtext("autotest/SOFT_INI_Soft_Version")
    SOFT_INI_Fota_Version = ast.literal_eval(read_config.findtext("autotest/SOFT_INI_Fota_Version"))
    Config_Name = read_config.findtext("autotest/Network_Config/Config_Name")
    PDP = ast.literal_eval(read_config.findtext("autotest/Network_PDP_type"))[0]
    APN = ast.literal_eval(read_config.findtext("autotest/Network_APN"))[0]
    KSRAT = read_config.findtext("autotest/Network_Config/Ksrat")
    band = read_config.findtext("autotest/Network_Config/Band")
    bandToKBNDLTE = ast.literal_eval(read_config.findtext("autotest/Bands/KBND_Dictionary"))
    kbndList = []
    if bandToKBNDLTE != 0:
        kbndList.extend(x.lstrip('0') for x in list(bandToKBNDLTE.values()))
    currentBandlist = band.split(',')
    BND = bandToKBNDLTE.get(int(currentBandlist[0])).lstrip('0')

    slink2 = read_config.findtext("module/slink2/name")
    relay_port = read_config.findtext("hardware/power_supply/com/port")
    relay_num = read_config.findtext("hardware/power_supply/port_nb")
    resultList = []

    relay_port = read_config.findtext("hardware/power_supply/com/port")
    relay_num = read_config.findtext("hardware/power_supply/port_nb")
    # No reset during firmware download
    action = 0

    # Start Test
    print("\n------------Test Case Start------------")

    try:
        # Log FOTA path
        swilog.info("-----------------------------------------")
        swilog.info("Test FOTA path:")
        swilog.info("From: " + SOFT_INI_Soft_Version)
        for fota_version in SOFT_INI_Fota_Version:
            swilog.info("To: " + fota_version)
        swilog.info("-----------------------------------------\n")

        # check if SIM is locked
        sim_locked = 0
        clck_rsp = target_at.run_at_cmd("AT+CLCK=\"SC\",2", timeout, ["OK"])
        if clck_rsp.find("+CLCK: 0") == -1:
            # SIM locked => unlock SIM
            sim_locked = 1
            target_at.run_at_cmd("AT+CLCK=\"SC\",0," + SIM_Pin1, timeout, ["OK"])

        # Check if CREG != 0
        creg_enabled = 0
        creg_status = target_at.run_at_cmd("AT+CREG?", timeout, ["OK"])
        if creg_status.find("+CREG: 0") == -1:
            # CREG enabled => disable CREG
            creg_enabled = 1
            target_at.run_at_cmd("AT+CREG=0", timeout, ["OK"])

        # initialization
        target_at.run_at_cmd("AT+WDSC=0,0", timeout, ["OK"])
        target_at.run_at_cmd("AT+WDSC=2,0", timeout, ["OK"])
        target_at.run_at_cmd("AT+WDSS=1,0", timeout, ["OK"])
        target_at.run_at_cmd("AT+CEREG=2", timeout, ["OK"])
        switracemode = target_at.run_at_cmd("AT+SWITRACEMODE?", timeout, ["\r\nOK"])
        if switracemode.find("RnD") == -1:
            target_at.run_at_cmd("AT+SWITRACEMODE=RnD", timeout, ["OK"])
            SWI_Reset_Module(target_at, HARD_INI)

        # Set target_version to base version
        target_version = SOFT_INI_Soft_Version

        # Start AVMS Loop
        for fota_version in SOFT_INI_Fota_Version:

            # Assign base and target version
            base_version = target_version
            target_version = fota_version
            swilog.step("Test upgrade from %s to %s" % (base_version, target_version))

            # Check registration status
            target_at.run_at_cmd("AT+COPS?", timeout, ["OK"])

            try:
                ensure_network_connection(target_at, Config_Name, None, log_file)
                start_time = av_session_config(target_at, avms_client, target_version, HARD_INI)
                success, server_state = av_upgrade_session(target_at, avms_client, otii_object, base_version, target_version, relay_port,
                                                                                         relay_num, action, start_time, proc_file, pwr_file)
                failureReason = None
                time.sleep(10)
            except Exception as err_msg:
                VarGlobal.statOfItem = "NOK"
                print(Exception, err_msg)
                failureReason = str(err_msg)

            resultList = av_upgrade_result(target_at, slink2, relay_port, relay_num, HARD_INI, BND, APN, KSRAT, PDP, success,
                                                                server_state, base_version, target_version, failureReason, resultList, False)

            print("\nPreparing for next FOTA test (script cleanup)\n")
            time.sleep(2)

        # Restore default values
        if sim_locked == 1:
            target_at.run_at_cmd("AT+CLCK=\"SC\",1," + SIM_Pin1, timeout, ["OK"])

        if creg_enabled == 1:
            target_at.run_at_cmd("AT+CREG=" + creg_status, detimeout, ["OK"])

    except Exception as err_msg:
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)

    swilog.info("Summary of each FOTA upgrade path result")
    for result in resultList:
        swilog.info(result)

    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)

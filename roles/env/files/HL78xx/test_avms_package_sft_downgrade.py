"""
Description:
Perform FOTA from the list of version(s) in SOFT_INI_Fota_Sft_Down_Version.
Script will perform continuous FOTA from A->B, A->C, A->D

    A = SOFT_INI_Soft_Version
    B to D = List in SOFT_INI_Fota_Sft_Down_Version

Input Parameters:
SOFT_INI_Soft_Version - Base version
SOFT_INI_Fota_Sft_Down_Version - Target version(s)
AVMSZipPath - Location of AVMS package
    - provide a list, local directory or server link to the AVMS package(s)
SFT_Down_Path - Location of SFT package
    - provide a list, local directory or server link to the SFT package

Power Consumption:
Requires to connect OTII device to capture power comsumption data.
"""


import time
import os
import ast
from datetime import datetime
import pytest
import VarGlobal
from autotest import pytestmark  # noqa # pylint: disable=unused-import
from autotest import PRINT_START_FUNC, PRINT_TEST_RESULT
from autotest import (
    is_valid_fw, ensure_network_connection, SWI_Reset_Module)
from avms_upgrade import (
    av_link_app, autoflash,
    av_session_config, av_upgrade_session, av_upgrade_result, open_txt_header)
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
def avms_sft_downgrade_setup_teardown(
        ensure_package_exists_sft_down, target_at,
        read_config, network_tests_setup_teardown):
    """Test case setup and teardown."""
    state = network_tests_setup_teardown
    if state == "OK":
        print("General Test Setup Success")

    print("\nA_HL_INT_AVMS_SFT_DOWNGRADE_0000 TC Start:\n")

    print("\n------------Test's preambule Start------------")

    # Variable Init
    HARD_INI = read_config.findtext("autotest/HARD_INI")
    SOFT_INI_Soft_Version = read_config.findtext("autotest/SOFT_INI_Soft_Version")
    slink2 = read_config.findtext("module/slink2/name")
    AVMSZipPath = ast.literal_eval(read_config.findtext("autotest/AVMSZipPath"))
    Autoflasher = int(read_config.findtext("autotest/Features_Autoflasher"))
    relay_port = read_config.findtext("hardware/power_supply/com/port")
    relay_num = read_config.findtext("hardware/power_supply/port_nb")

    test_nb = ""
    test_ID = "A_HL_INT_AVMS_SFT_DOWNGRADE_0000"
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


def A_HL_INT_AVMS_SFT_DOWNGRADE_0000(
        avms_sft_downgrade_setup_teardown,
        avms_client, read_config, otii_setup_teardown, target_at):
    """
    Check AVMS AT Command. Nominal/Valid use case
    """
    test_ID = avms_sft_downgrade_setup_teardown

    otii_object = otii_setup_teardown

    # Variable Init
    HARD_INI = read_config.findtext("autotest/HARD_INI")
    SIM_Pin1 = read_config.findtext("autotest/PIN1_CODE")
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
    resultList = []

    SOFT_INI_Soft_Version = read_config.findtext("autotest/SOFT_INI_Soft_Version")
    SOFT_INI_Fota_Sft_Down_Version = ast.literal_eval(read_config.findtext("autotest/SOFT_INI_Fota_Sft_Down_Version"))
    SFTPath = ast.literal_eval(read_config.findtext("autotest/SFT_Down_Path"))
    Config_Name = read_config.findtext("autotest/Network_Config/Config_Name")
    slink2 = read_config.findtext("module/slink2/name")
    relay_port = read_config.findtext("hardware/power_supply/com/port")
    relay_num = read_config.findtext("hardware/power_supply/port_nb")

    # No reset during firmware download
    action = 0

    if SFTPath == ['']:
        SFTPath = [None]

    # Start Test
    print("\n------------Test Case Start------------")

    try:
        # Log FOTA path
        swilog.info("-----------------------------------------\n")
        swilog.info("Test FOTA path:")
        for fota_version in SOFT_INI_Fota_Sft_Down_Version:
            swilog.info("From " + SOFT_INI_Soft_Version + " to " + fota_version)
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

        # Start AVMS Loop
        for fota_version in SOFT_INI_Fota_Sft_Down_Version:

            swilog.step("Test upgrade from %s to %s" % (SOFT_INI_Soft_Version, fota_version))

            # Ensure module has base version loaded
            swilog.step("Performing autoflash upgrade to %s" % SOFT_INI_Soft_Version)
            autoflash(SOFT_INI_Soft_Version, slink2, relay_port, relay_num, SFTPath[0])

            # Verify module version after SFT (autoflash) upgrade
            if is_valid_fw(target_at, SOFT_INI_Soft_Version):
                swilog.step(
                    "Test upgrade from %s to %s" % (SOFT_INI_Soft_Version, fota_version))
            else:
                raise Exception("---->Problem: Soft Version")

            with open(log_file, 'a') as output:
                output.write(
                    "##### Test upgrade from %s to %s #####\n"
                    % (SOFT_INI_Soft_Version, fota_version))

            try:
                # Start AVMS FOTA upgrade
                ensure_network_connection(target_at, Config_Name, None, log_file)

                # Link module to base version
                uid = avms_client.get_application_uid(SOFT_INI_Soft_Version)
                av_link_app(avms_client, uid)

                start_time = av_session_config(target_at, avms_client, fota_version, HARD_INI)
                success, server_state = av_upgrade_session(target_at, avms_client, otii_object, SOFT_INI_Soft_Version, fota_version, relay_port, relay_num, action, start_time, proc_file, pwr_file)
                failureReason = None
                time.sleep(10)
            except Exception as err_msg:
                VarGlobal.statOfItem = "NOK"
                print(Exception, err_msg)
                failureReason = str(err_msg)

            resultList = av_upgrade_result(target_at, slink2, relay_port, relay_num, HARD_INI, BND, APN, KSRAT, PDP, success,
                                                                server_state, SOFT_INI_Soft_Version, fota_version, failureReason, resultList, True)

            print("\nPreparing for next FOTA test (script cleanup)\n")
            time.sleep(2)

        # Restore default values
        if sim_locked == 1:
            target_at.run_at_cmd("AT+CLCK=\"SC\",1," + SIM_Pin1, timeout, ["OK"])

        if creg_enabled == 1:
            target_at.run_at_cmd("AT+CREG=" + creg_status, timeout, ["OK"])

    except Exception as err_msg:
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)

    swilog.info("Summary of each FOTA upgrade path result")
    for result in resultList:
        swilog.info(result)

    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)

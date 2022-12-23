import pytest
import time
import swilog
import VarGlobal
from autotest import *
import logging

log = logging.getLogger("test_at_mft_pri.py")
log.setLevel(logging.INFO)
c_handler = logging.StreamHandler()
c_handler.setFormatter(
logging.Formatter("[%(name)s][%(levelname)s]: %(message)s"))
log.addHandler(c_handler)
logging.addLevelName(logging.WARNING, "\033[1;33m%s\033[1;0m" % logging.getLevelName(logging.WARNING))
logging.addLevelName(logging.ERROR, "\033[1;31m%s\033[1;0m" % logging.getLevelName(logging.ERROR))

swilog.info("\n----- Program start -----\n")

# -------------------------- Module Initialization ----------------------------------
def A_HL_INT_MFT_PRI_0000(target_at, read_config):
    """
    Check  BFT/RFT, PRI, and some other AT Commands.
    """
    print("\A_HL_INT_MFT_PRI_0000 TC Start:\n")
    test_environment_ready = "Ready"
    print("\n------------Test's preambule Start------------")
    try:
        # Variable Init
        timeout = 15

        # Firmware version
        SOFT_INI_Soft_Version = read_config.findtext("autotest/SOFT_INI_Soft_Version")
        Firmware_Ver = two_digit_fw_version(SOFT_INI_Soft_Version)

        # only execute for PPF build: PHL or 4.6.3.0
        resp = target_at.run_at_cmd("ATI3\r\n", timeout, ["OK"])
        if ("PHL" or "4.6.3.0") not in resp:
            log.warning("Please make sure it is a PPF build")
            pytest.skip("The test case is only for PPF builds.")

        # check whether it is a HL7800 or HL7802 or HL7810 or HL7812 or HL7845
        module = ""
        resp = target_at.run_at_cmd("AT+CGMM\r\n", timeout, ["OK"])
        resp = resp.split("\r\n")
        for line in resp:
            if line.find("HL7800") != -1 or line.find("HL7802") != -1 or line.find("HL7810") != -1 or line.find("HL7812") != -1 or line.find("HL7845") != -1:
                module = line
        if module == "":
            log.warning("Please make sure it is a HL7800 or HL7802 or HL7810 or HL7812 or HL7845 module")
            pytest.skip("The test case exits because it is not a HL7800 or HL7802 or HL7810 or HL7812 or HL7845 module!")

        # check whether FSN and IMEI are set correctly for new module
        resp = target_at.run_at_cmd("AT+KOTPR=\"FSN\"", timeout, ["OK"])
        resp = resp.split("\r\n")
        FSN = ""
        for line in resp:
            if line.find("+KOTPR: ") != -1:
                FSN = line.split("\"")[-2].strip()

        resp = target_at.run_at_cmd("AT+KOTPR=\"IMEI\"", timeout, ["OK"])
        resp = resp.split("\r\n")
        IMEI = ""
        for line in resp:
            if line.find("+KOTPR: ") != -1:
                IMEI = line.split(" ")[-1].strip()

        if FSN in ["", "00000000000000"] or IMEI in ["", "000000000000000"]:
            log.warning("Please check FSN and IMEI, and make sure they are set correctly!")
            pytest.skip("Test case exits because FSN or IMEI do not set correctly!")

        PN = "9000000"

        # Module Init
        target_at.run_at_cmd("ate0", timeout, ["OK"])
        target_at.run_at_cmd("AT+CMEE=1", timeout, ["OK"])

        if not VarGlobal.Init_Status in ["AT_OK"]:
            test_environment_ready = "Not_Ready"

    except Exception as e:
        print("***** Test environment check fails !!!*****")
        print(type(e))
        print(e)
        test_environment_ready = "Not_Ready"

    print("\n------------Test's preambule End------------")

    # Start Test
    print("\n------------Test Case Start------------")

    test_nb = ""
    test_ID = "A_HL_INT_MFT_PRI_0000"
    PRINT_START_FUNC(test_nb + test_ID)
    VarGlobal.statOfItem = "OK"

    try:
        if test_environment_ready == "Not_Ready":
            VarGlobal.statOfItem = "NOK"
            raise Exception("---->Problem: Test Environment Is Not Ready !!!")

        swilog.info("\n----- Testing Start -----\n")

        print("\n----- Sanity check  -----\n")

        target_at.run_at_cmd("AT+SWITRACEMODE=FACT", timeout * 2, ["OK"])
        time.sleep(15)

        print("\n----- writing values to the module  -----\n")
        if "04.06.00.00" <= Firmware_Ver < "05.00.00.00" or Firmware_Ver >= "05.03.03.00":
            target_at.run_at_cmd("AT!UNLOCK=\"A710\"", timeout, ["OK"])

        target_at.run_at_cmd("AT%SETACFG=Manufacturing.ProdTraceability.TestControl,1", timeout, ["OK"])
        target_at.run_at_cmd("AT%SETACFG=Manufacturing.ProdTraceability.BftBench,1", timeout, ["OK"])
        target_at.run_at_cmd("AT" + "%" + "SETACFG=Identification.Device.DeviceSerialNumber,\"%s\"" % (FSN), \
                          timeout, ["OK"])
        target_at.run_at_cmd("AT+KOTPW=\"FSN\",\"%s\"" % (FSN), timeout, ["OK"])
        target_at.run_at_cmd("AT+WIMEI=%s" % (IMEI), timeout, ["OK"])

        target_at.run_at_cmd("AT%OTPCMD=\"EN\"", timeout, ["OK"])
        target_at.run_at_cmd("AT+KOTPW=\"LOCK_SWI1\"", timeout, ["OK"])
        target_at.run_at_cmd("AT+KOTPW=\"LOCK_IMEI\"", timeout, ["OK"])
        target_at.run_at_cmd("AT%SETCFG=\"mac_log_sev\",\"255\"", timeout, ["OK"])
        target_at.run_at_cmd("AT%SETCFG=\"PHY_LOG_DISABLE\",\"1\"", timeout, ["OK"])
        target_at.run_at_cmd("AT%SETACFG=Manufacturing.ProdTraceability.RftBench,1", timeout, ["OK"])
        if module == "HL7802":
            print("It is a HL7802, set PRODUCTID=2.")
            target_at.run_at_cmd("AT+KOTPW=\"PRODUCTID\",2", timeout, ["OK"])
        elif module == "HL7800":
            print("It is a HL7800, set PRODUCTID=0.")
            target_at.run_at_cmd("AT+KOTPW=\"PRODUCTID\",0", timeout, ["OK"])
        # Will be implemented once HL7810/12/45 PRODUCTIDs are defined
        elif module == "HL7810" or module == "HL7812" or module == "HL7845":
            print("This is a new E0SB module, set PRODUCTID will be impleneted once PRODUCTID is defined for HL7810, HL7812 and HL7845.")
        else:
            raise Exception("Fail to match the right module, expected HL7800, HL7800-M or HL7802")

        # the following 3 commands are for PHL78xx.1.1.0.x(HL7800) or PHL78xx.2.1.0.x(HL7802) and above
        # and these commands were not supported in lower than 1.1.0.x build
        target_at.run_at_cmd("AT" + "%" + "SETACFG=Manufacturing.PRI.Part_Number,%s" % (PN), timeout, ["OK"])
        target_at.run_at_cmd("AT%SETACFG=Manufacturing.PRI.Revision,001.00X", timeout, ["OK"])
        target_at.run_at_cmd("AT%SETACFG=Manufacturing.PRI.Carrier,GENERIC", timeout, ["OK"])

        # the following 2 commands are for PHL78xx.2.1.x and above
        target_at.run_at_cmd("AT%SETACFG=manager.uartA.flowcontrol,\"1\"", timeout, ["OK"])
        target_at.run_at_cmd("AT" + "%" + "SETACFG=manager.uartA.baudrate,\"115200\"", timeout, ["OK"])

        target_at.run_at_cmd("AT+CFUN=4", timeout, ["OK"])
        target_at.run_at_cmd("AT%SIMCMD=\"SWITCH\",1", timeout, ["OK"])

        target_at.run_at_cmd("AT+CFUN=1,1\r\n", timeout * 2, ["OK"])
        time.sleep(15)

        print("\n-----  Sanity check if the commands work correctly  -----\n")
        target_at.run_at_cmd("AT\r\n", timeout, ["OK"])
        target_at.run_at_cmd("ATI3\r\n", timeout, ["OK"])
        target_at.run_at_cmd("AT+CGMM\r\n", timeout, ["OK"])
        target_at.run_at_cmd("AT+CGSN\r\n", timeout, ["OK"])

        print("\n----- SANITY CHECK for the previous writing values in PHL build  -----\n")
        if "04.06.00.00" <= Firmware_Ver < "05.00.00.00" or Firmware_Ver >= "05.03.03.00":
            target_at.run_at_cmd("AT!UNLOCK=\"A710\"", timeout, ["OK"])

        target_at.run_at_cmd("AT%GETACFG=Manufacturing.ProdTraceability.TestControl", timeout, ["1\r\nOK"])
        target_at.run_at_cmd("AT%GETACFG=Manufacturing.ProdTraceability.BftBench", timeout, ["1\r\nOK"])
        target_at.run_at_cmd("AT%GETACFG=Identification.Device.DeviceSerialNumber", timeout, [FSN + "\r\n" + "OK"])
        target_at.run_at_cmd("AT+KOTPR=\"FSN\"", timeout, ["\"" + FSN + "\"" + "\r\n\r\n" + "OK"])
        target_at.run_at_cmd("AT+WIMEI?", timeout, [IMEI + "\r\n\r\n" + "OK"])
        target_at.run_at_cmd("AT+KOTPR=\"LOCK_SWI1\"", timeout, ["1\r\n\r\nOK"])
        target_at.run_at_cmd("AT+KOTPR=\"LOCK_IMEI\"", timeout, ["1\r\n\r\nOK"])
        target_at.run_at_cmd("AT%GETCFG=\"mac_log_sev\"", timeout, ["255\r\n\r\nOK"])
        target_at.run_at_cmd("AT%GETCFG=\"PHY_LOG_DISABLE\"", timeout, ["1\r\n\r\nOK"])
        target_at.run_at_cmd("AT%GETACFG=Manufacturing.ProdTraceability.RftBench", timeout, ["1\r\nOK"])
        target_at.run_at_cmd("AT%GETACFG=Manufacturing.PRI.Part_Number", timeout, [PN + "\r\n" + "OK"])
        target_at.run_at_cmd("AT%GETACFG=Manufacturing.PRI.Revision", timeout, ["001.00X\r\nOK"])
        target_at.run_at_cmd("AT%GETACFG=Manufacturing.PRI.Carrier", timeout, ["GENERIC\r\nOK"])
        target_at.run_at_cmd("AT+SWITRACEMODE?", timeout, ["FACT\r\n\r\nOK"])
        if module == "HL7802":
            target_at.run_at_cmd("AT+KOTPR=\"PRODUCTID\"", timeout, ["2\r\n\r\nOK"])
        elif module == "HL7800":
            target_at.run_at_cmd("AT+KOTPR=\"PRODUCTID\"", timeout, ["0\r\n\r\nOK"])

    except Exception as err_msg:
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)
    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)

swilog.info("\n----- Program End -----\n")

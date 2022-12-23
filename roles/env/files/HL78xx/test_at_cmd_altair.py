import pytest
import swilog
import pexpect
import VarGlobal
import collections
from autotest import *

swilog.info( "\n----- Program start -----\n")

def get_current_band(answer):
    answer = answer.split("\r\n")
    band = ""
    for ans in answer:
        if "Bands:" in ans:
            band = ans.split(" ")[-1]
    return band

# -------------------------- Module Initialization ----------------------------------
def A_HL_INT_CMD_ALTAIR_0000(target_at, read_config, non_network_tests_setup_teardown):
    """
    Check ALTAIR AT commands in use during modules manufacturing, customization stage (PRI)
    """
    print("\nA_HL_CMD_ALTAIR_0000 TC Start:\n")
    test_environment_ready = "Ready"
    print("\n------------Test's preambule Start------------")

    phase = int(read_config.findtext("autotest/Features_PHASE"))
    if phase < 2:
        pytest.skip("Phase < 2 : secbootcfg is not supported")

    # Variable Init
    HARD_INI = read_config.findtext("autotest/HARD_INI")

    test_nb = ""
    test_ID = "A_HL_CMD_ALTAIR_0000"
    PRINT_START_FUNC(test_nb + test_ID)

    print("\n------------Test's preambule End------------")

    # Start Test
    print("\n------------Test Case Start------------")

    try:
        # Retrieve serial number from AT command AT+KGSN=3
        SagSendAT(target_at, "AT+KGSN=3\r")
        answer = SagWaitResp(target_at, ["*\r\nOK\r\n"], 2000)
        def_fsn = answer.split("\r\n")[1].split(" ")[1]

        # For FSN : change the last digit of FSN got from AT command AT+KGSN=3
        # if it is "F" it will be set to "0"
        # else it will be incremented by 1
        last_car_fsn = def_fsn[len(def_fsn)-1]
        if (last_car_fsn != 'F'):
            last_car_fsn_hex = str(hex(int(last_car_fsn, 16) +1))
            last_car_fsn =  last_car_fsn_hex[len(last_car_fsn_hex)-1].upper()
        else:
            last_car_fsn = "0"
        fsn = def_fsn[:-1] + last_car_fsn

        collection_key = {
             'Identification.Model.ModelNumber': "HL7800-T",
             'Manufacturing.ProdTraceability.RftBench': '1',
             'Manufacturing.ProdTraceability.CustoBench': '1',
             'Identification.Device.DeviceSerialNumber': fsn,
             'APNTable.Class1.Enabled':'true'
        }

        for param_key,param_value in list(collection_key.items()):

            # Check GETACFG AT Test Command : get initial value
            SagSendAT(target_at, "AT%"+"GETACFG=\"%s\"\r"% param_key)
            answer = SagWaitResp(target_at, ["*\r\nOK\r\n"], 2000)
            param_result = answer.split("\r\n")[1]

            # Check SETACFG AT Test Command : set new value
            SagSendAT(target_at, "AT%SETACFG="+param_key+','+param_value+"\r")
            answer = SagWaitResp(target_at, ["\r\nOK\r\n"], 2000)

            # Check GETACFG AT Test Command : get and check the value
            SagSendAT(target_at, "AT%"+"GETACFG=\"%s\"\r"%param_key)
            answer = SagWaitResp(target_at, ["*\r\nOK\r\n"], 2000)

            # Modify for V05.00.00.00, exclude the last blank of the string
            #if (answer.split("\r\n")[1] != param_value):
            if (answer.split("\r\n")[1].split(" ")[0] != param_value):
                VarGlobal.statOfItem = "NOK"

            # Check SETACFG AT Test Command : set back the initial value
            SagSendAT(target_at, "AT%SETACFG="+param_key+','+param_result+"\r")
            answer = SagWaitResp(target_at, ["\r\nOK\r\n"], 2000)

            # Check GETACFG AT Test Command : get and check the value
            SagSendAT(target_at, "AT%"+"GETACFG=\"%s\"\r"%param_key)
            answer = SagWaitResp(target_at, ["*\r\nOK\r\n"], 2000)

            if (answer.split("\r\n")[1] != param_result):
                VarGlobal.statOfItem = "NOK"

        # Check GETCFG AT Test Command : get initial value
        SagSendAT(target_at, "AT%GETCFG=\"BAND\"\r")
        answer = SagWaitResp(target_at, ["*\r\nOK\r\n"], 2000)
        band = answer.split("\r\n")[1].split(" ")[2]

        # Check SETCFG AT Test Command : set new value
        SagSendAT(target_at, "AT%SETCFG=\"BAND\",\"28\"\r")
        SagWaitResp(target_at, ["\r\nOK\r\n"], 2000)

        print("\nReboot module for AT%SETCFG=\"BAND\",\"28\",band command to take effect...")
        SWI_Reset_Module(target_at, HARD_INI)

        # Check GETCFG AT Test Command : get and check the value
        SagSendAT(target_at, "AT%GETCFG=\"BAND\"\r")
        answer = SagWaitResp(target_at, ["*\r\nOK\r\n"], 2000)
        cur_band = get_current_band(answer)
        if cur_band != "28":
            VarGlobal.statOfItem = "NOK"
        print(VarGlobal.statOfItem)

        # Check SETCFG AT Test Command : set back the initial value
        SagSendAT(target_at, "AT%SETCFG="+'\"BAND\",\"'+band+"\"\r")
        SagWaitResp(target_at, ["\r\nOK\r\n"], 2000)

        print("\nReboot module for AT%SETCFG=\"BAND\",band command to take effect...")
        SWI_Reset_Module(target_at, HARD_INI)

        # Check GETCFG AT Test Command : get and check the value
        SagSendAT(target_at, "AT%GETCFG=\"BAND\"\r")
        answer = SagWaitResp(target_at, ["*\r\nOK\r\n"], 2000)
        cur_band = get_current_band(answer)
        if cur_band != band:
            VarGlobal.statOfItem = "NOK"

        # Check SECBOOTCFG AT Test Command
        SagSendAT(target_at, "AT!SECBOOTCFG?\r")
        answer = SagWaitResp(target_at, ["*\r\nOK\r\n"], 2000)
        secBootMode = answer.split("\r\n")[1].split(" ")[1].split(",")[1]
        print("secBootMode = %s"%secBootMode)
        if (secBootMode == "0"):
            print("Secure boot mode disabled")
        elif (secBootMode == "1"):
            print("Secure boot mode enabled")
        else:
            VarGlobal.statOfItem = "NOK"
        print(VarGlobal.statOfItem)

    except Exception as err_msg :
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)
    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)

swilog.info( "\n----- Program End -----\n")

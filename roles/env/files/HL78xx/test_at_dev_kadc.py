import time
import pytest
import swilog
import VarGlobal
from autotest import *

timeout = 15

swilog.info("\n----- Program start -----\n")

# -------------------------- Module Initialization ----------------------------------
def A_HL_INT_DEV_KADC_0000(target_at, read_config, non_network_tests_setup_teardown):
    """
    Check KADC AT Commands. Nominal/Valid use case
    """
    print("\nA_HL_INT_DEV_KADC_0000 TC Start:\n")
    test_environment_ready = "Ready"
    print("\n------------Test's preambule Start------------")

    # Variable Init
    HARD_INI = read_config.findtext("autotest/HARD_INI")
    SOFT_INI_Soft_Version = read_config.findtext("autotest/SOFT_INI_Soft_Version")
    Soft_Version = two_digit_fw_version(SOFT_INI_Soft_Version)
    phase = int(read_config.findtext("autotest/Features_PHASE"))
    if phase < 2:
        pytest.skip("Phase < 2 : No AT+KADCxxx commands")

    # Module Init
    target_at.run_at_cmd("ATE0", timeout, ["OK"])
    target_at.run_at_cmd("AT+CMEE=1", timeout, ["OK"])
    target_at.run_at_cmd("AT+CGMR", timeout, ["OK"])

    test_nb = ""
    test_ID = "A_HL_INT_DEV_KADC_0000"
    PRINT_START_FUNC(test_nb + test_ID)

    print("\n------------Test's preambule End------------")

     # Start Test
    print("\n------------Test Case Start------------")

    try:
        # Check HL78xx +KADC AT Commands
        if "HL78" in HARD_INI:

            # Check +KADC AT Test Command
            if (Soft_Version >= "04.05.03.00" and Soft_Version < "05.00.00.00") or (Soft_Version >= "05.03.03.00"):
                target_at.run_at_cmd("AT+KADC=?", timeout, [r"\+KADC:\s\(0,2,4,7\),\(3\)", "OK"])
            else:
                target_at.run_at_cmd("AT+KADC=?", timeout, [r"\+KADC:\s\(2,4,7\),\(3\)", "OK"])

            # Test <Meas id> for ID = 0 - VBATT (VBATT voltage value in μV)
            if (Soft_Version >= "04.05.03.00" and Soft_Version < "05.00.00.00") or (Soft_Version >= "05.03.03.00"):
                target_at.run_at_cmd("AT+KADC=0", timeout, [r"\+KADC:\s\d+,\d+", "OK"])

            # Test <Meas id> for ID = 2 - THERM (internal CTN)
            result = target_at.run_at_cmd("AT+KADC=2,3", timeout, [r"\+KADC:\s,2,3,\d+", "OK"])
            temp = int(result.split("OK")[0].split(",")[3])
            print("\nInternal CTN Temperature (degrees): %i C\n" % temp)
            if temp not in range(10, 40): #Verify temp is around 25 degrees
                VarGlobal.statOfItem = "NOK"
                print("Please check internal CTN temperature!!\n\n")

            # Verify Measurement ID 4 - ADC0
            result = target_at.run_at_cmd("AT+KADC=4,3", timeout, [r"\+KADC:\s\d+,4,3", "OK"])
            ADC0 = int(result.split(": ")[1].split(",")[0])
            print("\nInput ADC0 Voltage (microvolts): %i uV\n" % ADC0)
            if ADC0 not in range(0, 1800000): #Verify AC0 is in range between 0 and 1.8V
                VarGlobal.statOfItem = "NOK"
                print("Please check input ADC0 (not in range [0; 1.8] V!!\n\n")

            # Verify Measurement ID 7 - ADC1
            result = target_at.run_at_cmd("AT+KADC=7,3", timeout, [r"\+KADC:\s\d+,7,3", "OK"])
            ADC1 = int(result.split(": ")[1].split(",")[0])
            print("\nInput ADC1 Voltage (microvolts): %i uV\n" % ADC1)
            if ADC1 not in range(0, 1800000): #Verify AC1 is in range between 0 and 1.8V
                VarGlobal.statOfItem = "NOK"
                print("Please check input ADC1 (not in range [0; 1.8] V!!\n\n")

            # Verify invalid parameters for <Meas id> and <Meas time> - test range of inputs [(0,1),10]
            if (Soft_Version >= "04.05.03.00" and Soft_Version < "05.00.00.00") or (Soft_Version >= "05.03.03.00"):
                invalidStartRange = 1
            else:
                invalidStartRange = 0
            print("\n\nVerify invalid parameters for <Meas id> - verify range of inputs [" + str(invalidStartRange) + ",10] &")
            print("Verify invalid parameters for <Meas time> - verify range of inputs [0,10]:\n")
            for Meas_id in range(invalidStartRange, 11):
                for Meas_time in range(0, 11):
                    if not ((Meas_id == 2 or Meas_id == 4 or Meas_id == 7) and Meas_time == 3):
                        target_at.run_at_cmd("AT+KADC="+str(Meas_id)+","+str(Meas_time), timeout, [r"\+CME\sERROR:\s916"])
                        time.sleep(0.1)

        # Check RC51xx +KADC AT Commands
        elif "RC51" in HARD_INI:

            #Check +KADC AT Test Command
            target_at.run_at_cmd("AT+KADC=?", timeout, [r"\+KADC:\s\(0-1\)", "OK"])

            # Check +KADC AT Read Commands
            target_at.run_at_cmd("AT+KADC?", timeout, ["ERROR"])

            # Read ADC0 (Meas ID 4) and ADC1 (Meas ID 7) and verify value is within range
            for ADC in range(2):
                result = target_at.run_at_cmd("AT+KADC?" + str(ADC), timeout, [r"\+KADC:\s\d+\suV,\s" + str(ADC), "OK"])
                voltage = int(result.split(" ")[2])

                if voltage not in range(0, 1800000):
                    VarGlobal.statOfItem = "NOK"
                    print("Please check input ADC (not in range [0; 1.8] V!!\n\n")

    except Exception as err_msg:
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)
    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)

swilog.info("\n----- Program End -----\n")

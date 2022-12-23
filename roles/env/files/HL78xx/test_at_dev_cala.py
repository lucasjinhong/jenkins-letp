import time
from datetime import datetime, timedelta
import pytest
import swilog
import VarGlobal
from autotest import *

swilog.info("\n----- Program start -----\n")

# -------------------------- Module Initialization ----------------------------------
def A_HL_INT_DEV_CALA_0000(target_at, read_config, non_network_tests_setup_teardown):
    """
    Check CALA AT Commands. Nominal/Valid use case
    """
    print("\nA_HL_INT_DEV_CALA_0000 TC Start:\n")
    test_environment_ready = "Ready"
    print("\n------------Test's preambule Start------------")

    phase = int(read_config.findtext("autotest/Features_PHASE"))
    if phase < 3:
        pytest.skip("Phase < 3 : No AT+CALAxxx commands")

    # Variable Init
    timeout = 15
    standby = 60

    # Module Init
    target_at.run_at_cmd("AT+CMEE=1", timeout, ["OK"])

    test_nb = ""
    test_ID = "A_HL_INT_DEV_CALA_0000"
    PRINT_START_FUNC(test_nb + test_ID)

    print("\n------------Test's preambule End------------")

     # Start Test
    print("\n------------Test Case Start------------")

    try:
        # Check CALA AT Test Command
        target_at.run_at_cmd("AT+CALA=?", timeout, [r"\+CALA:\s\(\"yy\/mm\/dd,hh:mm:ss\"\),\(1\)", "OK"])

        # Check CALA AT Read Command
        target_at.run_at_cmd("AT+CALA?", timeout, ["OK"])

        # Check CALA AT Write Command
        # Device clock must be set prior to CALA command
        now = datetime.now()
        target_at.run_at_cmd(now.strftime('AT+CCLK="%y/%m/%d,%X+00"'), timeout, ["OK"])
        # Set the alarm one minute from the current date and time
        now = datetime.now() + timedelta(minutes=1)
        target_at.run_at_cmd(now.strftime('AT+CALA="%y/%m/%d,%X"'), timeout, ["OK"])
        # Verify the device enters standby mode - unable to send AT commands
        try:
            print("\nVerify device entered Stand-by mode...")
            target_at.run_at_cmd("AT", timeout, ["OK"])
            # Fail the test if "OK" is received
            assert False
        except AssertionError:
            print("\n\nUnable to send AT commands while in Stand-by mode, waiting for device to wake up from 1 minute alarm timer...")
            # One minute stand-by mode
            time.sleep(standby)

            #Verify the device has waken up properly
            try:
                print("\nVerify device has waken up properly...")
                target_at.run_at_cmd("AT+CALA=?", timeout, [r"\+CALA:\s\(\"yy\/mm\/dd,hh:mm:ss\"\),\(1\)", "OK"])
            except:
                print("\nFailed!! The device did not wake up properly")
                input("\n\n\nTEST IS HALTED: SET WAKEUP PIN and hit enter to continue\n\n\n")
                SagSleep(HibernateBooting_Duration)
                assert False

        # Verify device wakes up and boots up normally
        target_at.run_at_cmd("AT+CALA=?", timeout, [r"\+CALA:\s\(\"yy\/mm\/dd,hh:mm:ss\"\),\(1\)", "OK"])

        # Verify alarm time limit
        print("\n\nVerify alarm time limit: over limit (36h24m00s)")
        now = datetime.now() + timedelta(minutes=2185)
        target_at.run_at_cmd(now.strftime('AT+CALA="%y/%m/%d,%X"'), timeout, [r"\+CME\sERROR:\s3"])

        print("\n\nVerify alarm time limit: under limit (36h23m59s)")
        now = datetime.now()
        target_at.run_at_cmd(now.strftime('AT+CCLK="%y/%m/%d,%X+00"'), timeout, ["OK"])
        now = datetime.now() + timedelta(minutes=2183) + timedelta(seconds=59)
        target_at.run_at_cmd(now.strftime('AT+CALA="%y/%m/%d,%X"'), timeout, ["OK"])
        #Wake up device to continue the test
        input("\n\n\nTEST IS HALTED: SET WAKEUP PIN and hit enter to continue the test\n\n\n")
        time.sleep(standby)

        # Verify alarm time cannot be set to the past
        now = datetime.now()
        target_at.run_at_cmd(now.strftime('AT+CCLK="%y/%m/%d,%X+00"'), timeout, ["OK"])
        print("\n\nVerify alarm cannot be set to the past (previous year):")
        now = datetime.now() - timedelta(days=365)
        target_at.run_at_cmd(now.strftime('AT+CALA="%y/%m/%d,%X"'), timeout, [r"\+CME\sERROR:\s3"])

        print("\n\nVerify alarm cannot be set to the past (previous month):")
        now = datetime.now() - timedelta(days=31)
        target_at.run_at_cmd(now.strftime('AT+CALA="%y/%m/%d,%X"'), timeout, [r"\+CME\sERROR:\s3"])

        print("\n\nVerify alarm cannot be set to the past (previous day):")
        now = datetime.now() - timedelta(days=1)
        target_at.run_at_cmd(now.strftime('AT+CALA="%y/%m/%d,%X"'), timeout, [r"\+CME\sERROR:\s3"])

        print("\n\nVerify alarm cannot be set to the past (previous hour):")
        now = datetime.now() - timedelta(minutes=60)
        target_at.run_at_cmd(now.strftime('AT+CALA="%y/%m/%d,%X"'), timeout, [r"\+CME\sERROR:\s3"])

        print("\n\nVerify alarm cannot be set to the past (previous minute):")
        now = datetime.now() - timedelta(minutes=1)
        target_at.run_at_cmd(now.strftime('AT+CALA="%y/%m/%d,%X"'), timeout, [r"\+CME\sERROR:\s3"])

        print("\n\nVerify alarm cannot be set to the past (previous second):")
        now = datetime.now() - timedelta(seconds=1)
        target_at.run_at_cmd(now.strftime('AT+CALA="%y/%m/%d,%X"'), timeout, [r"\+CME\sERROR:\s3"])

        # Verify alarm time cannot be set too far into the future
        print("\n\nVerify alarm cannot be set too far into the future (next year):")
        now = datetime.now() + timedelta(days=365)
        target_at.run_at_cmd(now.strftime('AT+CALA="%y/%m/%d,%X"'), timeout, [r"\+CME\sERROR:\s3"])

        # Verify alarm can only be set with the index <n>=1
        print("\n\nVerify alarm can only be set with the first index:")
        now = datetime.now()
        target_at.run_at_cmd(now.strftime('AT+CCLK="%y/%m/%d,%X+00"'), timeout, ["OK"])
        now = datetime.now() + timedelta(seconds=30)
        target_at.run_at_cmd(now.strftime('AT+CALA="%y/%m/%d,%X",1'), timeout, ["OK"])
        time.sleep(standby)

        print("\n\nVerify alarm cannot be set with another index:")
        now = datetime.now()
        target_at.run_at_cmd(now.strftime('AT+CCLK="%y/%m/%d,%X+00"'), timeout, ["OK"])
        now = datetime.now() + timedelta(seconds=30)
        target_at.run_at_cmd(now.strftime('AT+CALA="%y/%m/%d,%X",2'), timeout, [r"\+CME\sERROR:\s3"])
        swilog.info("\n----- Testing End -----\n")

    except Exception as err_msg:
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)
    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)

swilog.info("\n----- Program End -----\n")

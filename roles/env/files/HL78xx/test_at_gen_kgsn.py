"""
General AT commands test cases :: KGSN.

originated from A_HL_Common_GEN_KGSN_0001.PY validation test script.
"""

import re
import VarGlobal
from autotest import PRINT_START_FUNC, PRINT_TEST_RESULT, format_at_response
from autotest import pytestmark  # noqa # pylint: disable=unused-import

timeout = 15


def check_kgsn_1(target_at):
    """Check AT+KGSN=1 result."""
    response = format_at_response(
        target_at.run_at_cmd("AT+KGSN=1", timeout, [r"\+KGSN: *", "OK"])
    )[0]
    print("IMEISV = ", response)
    response = response.replace("+KGSN: ", "");
    if not re.match("^[0-9]+$", response):
        # 20150308 : PGA : changed error printing for manually set test results
        # this way, this error will be picked up by one click automatic logs compare
        print("\nNo Match : check failed")
        print("Expected: the <IMEISV> is all digits")
        print("Received: the <IMEISV> is NOT all digits")
        VarGlobal.statOfItem = "NOK"
    if len(response) != 16:
        # 20150308 : PGA : changed error printing for manually set test results
        # this way, this error will be picked up by one click automatic logs compare
        print("\nNo Match : check failed")
        print("Expected: the length of <IMEISV> is 16")
        print("Received: the length of <IMEISV> is NOT 16")
        VarGlobal.statOfItem = "NOK"

    response = response[14:15]
    if response == "99":
        # 20150308 : PGA : changed error printing for manually set test results
        # this way, this error will be picked up by one click automatic logs compare
        print("\nNo Match : check failed")
        print("Expected: <SV> in the range (0-98)")
        print("Received: <SV> NOT in the range (0-98)")
        VarGlobal.statOfItem = "NOK"


def check_kgsn_2(target_at):
    """Check AT+KGSN=2 result."""
    response = format_at_response(target_at.run_at_cmd("AT+KGSN=2", timeout, ["OK"]))[0]
    print(response)
    response = response[7:]
    print("IMEISV_STR = ", response)
    response = response.replace("+KGSN: ", "");
    if len(response) == 22:
        IMEI_14 = response[0:13]
        HYPHEN = response[14]
        IMEI_check_digit = response[15]
        SPACE = response[16]
        SV_FLAG = response[17:20]
        SV = response[20:22]
        if not re.match("^[0-9]+$", IMEI_14):
            # 20150308 : PGA : changed error printing for manually set test results
            # this error will be picked up by one click automatic logs compare
            print("\nNo Match : check failed")
            print("Expected: the 1st 14 chars of <IMEISV_STR> is all digits")
            print("Received: the 1st 14 chars of <IMEISV_STR> is NOT all digits")
            VarGlobal.statOfItem = "NOK"
        if HYPHEN != "-":
            # 20150308 : PGA : changed error printing for manually set test results
            # this error will be picked up by one click automatic logs compare
            print("\nNo Match : check failed")
            print("Expected: the 15th char of <IMEISV_STR> is hyphen")
            print("Received: the 15th char of <IMEISV_STR> is NOT hyphen")
            VarGlobal.statOfItem = "NOK"
        if not re.match("^[0-9]+$", IMEI_check_digit):
            # 20150308 : PGA : changed error printing for manually set test results
            # this error will be picked up by one click automatic logs compare
            print("\nNo Match : check failed")
            print("Expected: the 16th chars of <IMEISV_STR> is all digits")
            print("Received: the 16th chars of <IMEISV_STR> is NOT all digits")
            VarGlobal.statOfItem = "NOK"
        if SPACE != " ":
            # 20150308 : PGA : changed error printing for manually set test results
            # this error will be picked up by one click automatic logs compare
            print("\nNo Match : check failed")
            print("Expected: the 15th char of <IMEISV_STR> is space")
            print("Received: the 15th char of <IMEISV_STR> is NOT space")
            VarGlobal.statOfItem = "NOK"
        if SV_FLAG != "SV:":
            # 20150308 : PGA : changed error printing for manually set test results
            # this error will be picked up by one click automatic logs compare
            print("\nNo Match : check failed")
            print("Expected: the 16th-18th chars of <IMEISV_STR> is SV:")
            print("Received: the 16th-18th chars of <IMEISV_STR> is NOT SV:")
            VarGlobal.statOfItem = "NOK"
        if SV == "99":
            # 20150308 : PGA : changed error printing for manually set test results
            # this error will be picked up by one click automatic logs compare
            print("\nNo Match : check failed")
            print("Expected: The last 2 chars of <IMEISV_STR> SV in (0-98)")
            print("Received: The last 2 chars of <IMEISV_STR> SV NOT in (0-98)")
            VarGlobal.statOfItem = "NOK"
    else:
        # 20150308 : PGA : changed error printing for manually set test results
        # this way, this error will be picked up by one click automatic logs compare
        print("\nNo Match : check failed")
        print("Expected: the length of <IMEISV_STR> is 22")
        print("Received: the length of <IMEISV_STR> is NOT 22")
        VarGlobal.statOfItem = "NOK"


def A_HL_INT_GEN_KGSN_0000(target_at, non_network_tests_setup_teardown):
    """Check KGSN AT Command. Nominal/Valid use case."""
    print("\nA_HL_INT_GEN_KGSN_0000 TC Start:\n")
    print("\n------------Test's preambule Start------------")
    state = non_network_tests_setup_teardown
    if state == "OK":
        print("General Test Setup Success")

    test_nb = ""
    test_ID = "A_HL_INT_GEN_KGSN_0000"
    PRINT_START_FUNC(test_nb + test_ID)

    print("\n------------Test's preambule End------------")

    # Start Test
    print("\n------------Test Case Start------------")

    try:
        target_at.run_at_cmd("AT+KGSN=?", timeout, [r"\+KGSN: \(0-4\)", "OK"])

        # Read IMEI
        response = format_at_response(target_at.run_at_cmd("AT+KGSN=0", \
                                                        timeout, [r"\+KGSN: *", "OK"]))[0]

        print("IMEI = ", response)
        response = response.replace("+KGSN: ", "");
        if not re.match("^[0-9]+$", response):
            # 20150308 : PGA : changed error printing for manually set test results
            # this way, this error will be picked up by one click automatic logs compare
            print("\nNo Match : check failed")
            print("Expected: the <IMEI> is all digits")
            print("Received: the <IMEI> is NOT all digits")
            VarGlobal.statOfItem = "NOK"
        if len(response) != 15:
            # 20150308 : PGA : changed error printing for manually set test results
            # this way, this error will be picked up by one click automatic logs compare
            print("\nNo Match : check failed")
            print("Expected: the length of <IMEI> is 15")
            print("Received: the length of <IMEI> is NOT 15")
            VarGlobal.statOfItem = "NOK"

        # Read IMEISV
        check_kgsn_1(target_at)

        # Read IMEISV-STR
        check_kgsn_2(target_at)

        # Read FSN
        response = format_at_response(
            target_at.run_at_cmd("AT+KGSN=3", timeout, [r"\+KGSN: *", "OK"])
        )[0]
        print("FSN = ", response)
        response = response.replace("+KGSN: ", "");
        if len(response) != 14:
            # 20150308 : PGA : changed error printing for manually set test results
            # this way, this error will be picked up by one click automatic logs compare
            print("\nNo Match : check failed")
            print("Expected Response: the length of <FSN> is 14")
            print("Received Response: the length of <FSN> is NOT 14")
            VarGlobal.statOfItem = "NOK"

        # Read Customer Serial Number
        response = format_at_response(
            target_at.run_at_cmd("AT+KGSN=4", timeout, [r"\+KGSN: *", "OK"])
        )[0]
        print("Customer Serial Number = ", response)

    except Exception as err_msg:
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)

    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)

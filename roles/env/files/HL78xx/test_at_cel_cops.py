"""
A_HL_INT_CEL_COPS_0000 test case.

COPS originated from A_HL_Common_NS_COPS_0001.PY validation test script.
"""
import pytest
import VarGlobal
from autotest import PRINT_START_FUNC, PRINT_TEST_RESULT, format_at_response
from autotest import pytestmark  # noqa # pylint: disable=unused-import

timeout = 15


@pytest.fixture()
def cops_setup_teardown(network_tests_setup_teardown, target_at):
    """Test case setup and teardown."""
    state = network_tests_setup_teardown
    if state == "OK":
        print("General Test Setup Success")

    print("\nA_HL_INT_CEL_COPS_0000 TC Start:\n")

    print("\n------------Test's preambule Start------------")

    # AT+CMEE?
    rsp = target_at.run_at_cmd("AT+CMEE?", timeout, ["OK"])
    cmee = rsp.split("+CMEE: ")[1].split("\r\n")[0]
    print("\nDefault cmee is: " + cmee)

    test_nb = ""
    test_ID = "A_HL_INT_CEL_COPS_0000"
    PRINT_START_FUNC(test_nb + test_ID)

    print("\n----- Testing Start -----\n")

    yield test_ID

    print("\n----- COPS TearDown -----\n")

    # Restore default cmee
    target_at.run_at_cmd("AT+CMEE=" + cmee, timeout, ["OK"])


def A_HL_INT_CEL_COPS_0000(target_at, read_config, cops_setup_teardown):
    """Check COPS AT Command Nominal/Valid use case."""
    test_ID = cops_setup_teardown

    # Variable Init
    PLMN_LONG_NAME = read_config.findtext("autotest/Network_Long_Name")
    HARD_INI = read_config.findtext("autotest/HARD_INI")

    print("\n----- Testing Start -----\n")

    try:

        # ATE0+CMEE=1
        target_at.run_at_cmd("ATE0", timeout, ["OK"])
        target_at.run_at_cmd("AT+CMEE=1", timeout, ["OK"])

        target_at.run_at_cmd("AT+COPS=0,0", timeout * 5, ["OK"])

        target_at.run_at_cmd(
            "AT+COPS?", timeout * 2, [r'\+COPS: 0,0,"' + PLMN_LONG_NAME + '",?', "OK"]
        )

        # AT+COPS=
        if "HL78" in HARD_INI:
            target_at.run_at_cmd("AT+COPS=", timeout, ["OK"])

        # AT+COPS=?
        target_at.run_at_cmd("AT+COPS=?", timeout * 10, [r"\+COPS:*", "OK"])

    except Exception as err_msg:  # pylint: disable=broad-except
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)

    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)

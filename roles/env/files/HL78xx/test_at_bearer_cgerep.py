"""
Bearer AT commands test cases :: CGEREP.

Originated from A_HL_Common_GPRS_CGEREP_0001.PY validation test script.
"""
import pytest
import VarGlobal
from autotest import PRINT_START_FUNC, PRINT_TEST_RESULT, format_at_response
from autotest import pytestmark  # noqa # pylint: disable=unused-import

timeout = 15


@pytest.fixture()
def cgerep_setup_teardown(network_tests_setup_teardown, target_at):
    """Test case setup and teardown."""
    state = network_tests_setup_teardown
    if state == "OK":
        print("General Test Setup Success")

    print("\nA_HL_INT_BEARER_CGEREP_0000 TC Start:\n")

    print("\n------------Test's preambule Start------------")

    # CMD : AT+CGEREP=?
    target_at.run_at_cmd("AT+CGEREP=?", timeout, [r"\+CGEREP: \(0-2\),\(0-1\)", "OK"])

    # default CGEREP
    rsp = target_at.run_at_cmd("AT+CGEREP?", timeout, ["\r\nOK"])
    cgerep = rsp.split("+CGEREP: ")[1].split(",")[0]
    print("\nDefault cgerep is: " + cgerep)

    test_nb = ""
    test_ID = "A_HL_INT_BEARER_CGEREP_0000"
    PRINT_START_FUNC(test_nb + test_ID)

    print("\n----- Testing Start -----\n")

    yield test_ID

    print("\n----- CGEREP TearDown -----\n")

    target_at.run_at_cmd("AT+CGEREP=" + cgerep, timeout, ["OK"])


def A_HL_INT_BEARER_CGEREP_0000(target_at, cgerep_setup_teardown):
    """Check CGEREP AT Command. Nominal/Valid use case."""
    test_ID = cgerep_setup_teardown
    try:

        # AT+CGEREP=2
        target_at.run_at_cmd("AT+CGEREP=2", timeout, ["OK"])

        # AT+CGEREP=0
        target_at.run_at_cmd("AT+CGEREP=0", timeout, ["OK"])

        # AT+CGEREP=1
        target_at.run_at_cmd("AT+CGEREP=1", timeout, ["OK"])

    except Exception as err_msg:
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)

    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)

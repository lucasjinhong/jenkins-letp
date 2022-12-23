"""
Cellular AT commands test cases :: CREG.

originated from A_HL_Common_NS_CREG_0001.PY validation test script
"""
import pytest
import VarGlobal
from autotest import PRINT_START_FUNC, PRINT_TEST_RESULT, SagSleep
from autotest import pytestmark  # noqa # pylint: disable=unused-import

timeout = 25


@pytest.fixture()
def creg_setup_teardown(network_tests_setup_teardown):
    """Test case setup and teardown."""
    state = network_tests_setup_teardown
    if state == "OK":
        print("General Test Setup Success")

    print("\nA_HL_INT_CEL_CREG_0000 TC Start:\n")

    print("\n------------Test's preambule Start------------")

    test_nb = ""
    test_ID = "A_HL_INT_CEL_CREG_0000"
    PRINT_START_FUNC(test_nb + test_ID)

    print("\n----- Testing Start -----\n")
    yield test_ID


def A_HL_INT_CEL_CREG_0000(target_at, read_config, creg_setup_teardown):
    """Check CREG AT Command. Nominal/Valid use case."""
    test_ID = creg_setup_teardown

    # Variable Init
    HARD_INI = read_config.findtext("autotest/HARD_INI")

    try:
        # AT+CREG=?
        target_at.run_at_cmd("AT+CREG=?", timeout, [r"\+CREG: \(0-3\)", "OK"])

        # AT+CREG?
        target_at.run_at_cmd("AT+CREG?", timeout, ["OK"])

        # AT+CREG=
        if "HL78" in HARD_INI:
            target_at.run_at_cmd("AT+CREG=", timeout, ["OK"])

        for PARAM_CREG in [1, 2, 3, 0]:
            target_at.run_at_cmd("AT+CREG=" + str(PARAM_CREG), timeout, ["OK"])

            if PARAM_CREG in [2, 3]:
                target_at.run_at_cmd(
                    "AT+CREG?",
                    timeout,
                    [r"\+CREG: " + str(PARAM_CREG) + ",[15],*,*,?", "OK"],
                )
            else:
                target_at.run_at_cmd(
                    "AT+CREG?", timeout, [r"\+CREG: " + str(PARAM_CREG) + ",[15]", "OK"]
                )

            if PARAM_CREG != 0:

                target_at.run_at_cmd("AT+CFUN=0", timeout, ["OK", r"\+CREG: *"])
                SagSleep(15000)

                # AT+CFUN=1
                target_at.run_at_cmd("AT+CFUN=1", timeout, ["OK", r"\+CREG: *"])
                SagSleep(15000)

    except Exception as err_msg:  # pylint: disable=broad-except
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)

    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)

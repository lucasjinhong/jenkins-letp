"""
Bearer AT commands test cases :: KCNXxxx.

Originated from A_HL_Common_PROTOCOM_KCNXPROFILE_0001.PY validation test script.
"""
import ast
import pytest
import VarGlobal
from autotest import PRINT_START_FUNC, PRINT_TEST_RESULT, format_at_response
from autotest import pytestmark  # noqa # pylint: disable=unused-import

timeout = 15


@pytest.fixture()
def kcnx_setup_teardown(network_tests_setup_teardown, read_config, target_at):
    """Test case setup and teardown."""
    state = network_tests_setup_teardown
    if state == "OK":
        print("General Test Setup Success")

    print("\nA_HL_INT_BEARER_KCNX_0000 TC Start:\n")

    print("\n------------Test's preambule Start------------")

    AT_CCID = int(read_config.findtext("autotest/Features_AT_CCID"))
    AT_percent_CCID = int(read_config.findtext("autotest/Features_AT_percent_CCID"))
    HARD_INI = read_config.findtext("autotest/HARD_INI")

    if AT_CCID:
        target_at.run_at_cmd("AT+CCID", timeout, [r"\+CCID: *", "OK"])
        if "RC51" in HARD_INI:
            target_at.run_at_cmd("AT+ICCID", timeout, ["ICCID: *", "OK"])

    if AT_percent_CCID:
        target_at.run_at_cmd("AT%CCID", timeout, [r"\%CCID: *", "OK"])

    # Default K config
    result = format_at_response(target_at.run_at_cmd("AT&V", timeout, ["OK"]))
    if result:
        k = result[1].split(" ")[9]
        print("\nDefault K is: " + k)
    else:
        k = "&K3"

    print("target_at: Enable bi-directional hardware flow control...")
    target_at.run_at_cmd("AT&K3", timeout, ["OK"])

    test_nb = ""
    test_ID = "A_HL_INT_BEARER_KCNX_0000"
    PRINT_START_FUNC(test_nb + test_ID)

    print("\n----- Testing Start -----\n")
    yield test_ID
    print("\n----- KCNX TearDown -----\n")

    # Restore default K
    target_at.run_at_cmd("AT" + k, timeout, ["OK"])


def A_HL_INT_BEARER_KCNX_0000(target_at, read_config, kcnx_setup_teardown):
    """Check KCNXxxx AT Command. Nominal/Valid use case."""
    test_ID = kcnx_setup_teardown
    # Variable Init
    SIM_GPRS_APN = ast.literal_eval(read_config.findtext("autotest/Network_APN"))[0]
    SIM_GPRS_LOGIN = ast.literal_eval(
        read_config.findtext("autotest/Network_APN_login")
    )[0]
    SIM_GPRS_PASSWORD = ast.literal_eval(
        read_config.findtext("autotest/Network_APN_password")
    )[0]
    phase = int(read_config.findtext("autotest/Features_PHASE"))

    print("\n----- Testing Start -----\n")

    try:

        # AT+KCNXUP=?
        result = format_at_response(target_at.run_at_cmd("AT+KCNXUP=?", timeout, ["OK"]))
        answer = result[0].split(" ")[1]
        assert answer in ("(1-2)", "(1)")

        result = format_at_response(target_at.run_at_cmd("AT+KCNXDOWN=?", timeout, ["OK"]))
        answer = result[0].split(" ")[1]
        assert answer in ("(1-2),(0-1)", "(1),(0,1)")

        print("Checking Test Command ...")
        result = format_at_response(
            target_at.run_at_cmd("AT+KCNXPROFILE=?", timeout, ["OK"])
        )
        answer = result[0].split(" ")[1]
        assert answer in ("(1-2)", "(1)")

        print("Checking Read Command...")
        target_at.run_at_cmd("AT+KCNXPROFILE?", timeout, [r"\+KCNXPROFILE: 1", "OK"])

        print("Checking Set Command...")
        target_at.run_at_cmd("AT+KCNXPROFILE=1", timeout, ["OK"])

        print("Checking GPRS CONFIG with a dynamic IP address...")
        target_at.run_at_cmd(
            'AT+KCNXCFG=1,"GPRS","'
            + SIM_GPRS_APN
            + '","'
            + SIM_GPRS_LOGIN
            + '","'
            + SIM_GPRS_PASSWORD
            + '""',
            timeout,
            ["OK"],
        )

        print("Set profile...")
        target_at.run_at_cmd("AT+KCNXPROFILE=1", timeout, ["OK"])

        print("Checking current profile configuration...")
        target_at.run_at_cmd("AT+KCNXPROFILE?", timeout, [r"\+KCNXPROFILE: 1", "OK"])

        print("Checking GPRS CONFIG with a static IP address...")
        # Static IP not supported
        target_at.run_at_cmd(
            'AT+KCNXCFG=2,"GPRS","'
            + SIM_GPRS_APN
            + '","'
            + SIM_GPRS_LOGIN
            + '","'
            + SIM_GPRS_PASSWORD
            + '","'
            + '"192.168.10.100"',
            timeout,
            ["ERROR"],
        )

        if phase > 0:
            print()
            print("Set profile...")
            target_at.run_at_cmd("AT+KCNXPROFILE=2", timeout, ["OK"])

            print()
            print("Checking current configuration...")
            target_at.run_at_cmd("AT+KCNXPROFILE?", timeout, [r"\+KCNXPROFILE: 2", "OK"])
            # Restore profile
            target_at.run_at_cmd("AT+KCNXPROFILE=1", timeout, ["OK"])

    except Exception as err_msg:
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)

    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)

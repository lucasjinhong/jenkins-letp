"""
Cellular AT commands test cases :: CSQ.

originated from A_HL_Common_MECS_CSQ_0001.PY validation test script
"""
import pytest
import VarGlobal
from autotest import PRINT_START_FUNC, PRINT_TEST_RESULT, format_at_response
from autotest import pytestmark  # noqa # pylint: disable=unused-import

timeout = 15


@pytest.fixture()
def csq_setup_teardown(network_tests_setup_teardown, read_config, target_at):
    """Test case setup and teardown."""
    state = network_tests_setup_teardown
    if state == "OK":
        print("General Test Setup Success")

    print("\nA_HL_INT_CEL_CSQ_0000 TC Start:\n")

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

    test_nb = ""
    test_ID = "A_HL_INT_CEL_CSQ_0000"
    PRINT_START_FUNC(test_nb + test_ID)

    print("\n----- Testing Start -----\n")
    yield test_ID
    print("\n----- CSQ TearDown -----\n")


def A_HL_INT_CEL_CSQ_0000(target_at, read_config, csq_setup_teardown):
    """Check CSQ AT Command. Nominal/Valid use case."""
    test_ID = csq_setup_teardown

    try:
        # AT+CSQ=?
        target_at.run_at_cmd(
            "AT+CSQ=?", timeout, [r"\+CSQ: \(0-31,99\),\(0-7,99\)", "OK"]
        )

        # AT+CEREG?
        target_at.run_at_cmd("AT+CEREG?", timeout, [r"\+CEREG: 0,?", "OK"])

        # AT+CSQ
        answer = format_at_response(target_at.run_at_cmd("AT+CSQ", timeout, ["OK"]))
        if answer:

            # if len(resultat) == 5:
            CSQ_NOTIF = answer[0].split(": ")[0]
            CSQ_VALUE = answer[0].split(": ")[1]
            CSQ_VALUE = CSQ_VALUE.replace("\r\n", "")
            CSQ_VALUE = CSQ_VALUE.split(",")

            print("\nCSQ value =" + CSQ_VALUE[0])
            print("\nBER value =" + CSQ_VALUE[1])

            if (
                (int(CSQ_VALUE[0]) >= 0 and int(CSQ_VALUE[0]) <= 31)
                or int(CSQ_VALUE[0]) == 99
            ) and CSQ_NOTIF == "+CSQ":
                result = 0
            else:
                result = 1
                print("\nCSQ value is out of range")

            if (int(CSQ_VALUE[1]) >= 0 and int(CSQ_VALUE[1]) <= 7) or int(
                CSQ_VALUE[1]
            ) == 99:
                result = 0
            else:
                result = 1
                print("\nBER value is out of range")
        else:
            result = 1

        if result != 0:
            VarGlobal.statOfItem = "NOK"
            VarGlobal.process_stat = "NOK"
            VarGlobal.numOfFailedResponse += 1.0
            print("!!! expected response was not received")
        else:
            VarGlobal.numOfSuccessfulResponse += 1.0
            print("--> Success <OK>")

        # Check point 2
        if VarGlobal.statOfItem != "OK":
            raise Exception("Check point failed")

    except Exception as err_msg:
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)

    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)

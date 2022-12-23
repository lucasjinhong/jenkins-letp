"""Bearer AT commands test cases :: KSRAT."""

import time
import pytest
import VarGlobal
from autotest import (
    PRINT_START_FUNC,
    PRINT_TEST_RESULT,
    SagSleep,
    Booting_Duration,
    format_at_response,
    two_digit_fw_version,
)
from autotest import pytestmark  # noqa # pylint: disable=unused-import

timeout = 15


@pytest.fixture()
def ksrat_setup_teardown(network_tests_setup_teardown, target_at, read_config):
    """Test case setup and teardown."""
    state = network_tests_setup_teardown
    if state == "OK":
        print("Test Setup Success")

    print("\nA_HL_INT_BEARER_KSRAT_0000 TC Start:\n")

    print("\n------------Test's preambule Start------------")

    # Check if it is M module
    model = format_at_response(target_at.run_at_cmd("ATI", timeout, ["OK"]))
    if model[0] == "HL7800-M":
        pytest.skip("M model does not support switching KSRAT")

    # save default +KSREP
    result = format_at_response(target_at.run_at_cmd("AT+KSREP?", timeout, ["OK"]))
    ksrep = result[0].split(" ")[1].split(",")[0]
    if ksrep == "0":
        target_at.run_at_cmd("AT+KSREP=1", timeout, ["OK"])
        time.sleep(timeout)
    KSRAT = read_config.findtext("autotest/Network_Config/Ksrat")

    test_nb = ""
    test_ID = "A_HL_INT_BEARER_KSRAT_0000"
    PRINT_START_FUNC(test_nb + test_ID)

    print("\n------------Test Case Start------------")
    yield test_ID
    print("\n------------Test Case Teardown------------")
    # Restore default KSREP
    target_at.run_at_cmd("AT+KSREP=" + ksrep, timeout, ["OK"])
    time.sleep(timeout)

    # Set default KSRAT
    target_at.run_at_cmd("AT+KSRAT=" + KSRAT, timeout, ["OK"])

    # Auto reset after +KSRAT
    time.sleep(timeout * 2)

    # AT+KSRAT?
    target_at.run_at_cmd("AT+KSRAT?", timeout, [r"\+KSRAT: " + KSRAT, "OK"])


def A_HL_INT_BEARER_KSRAT_0000(target_at, read_config, ksrat_setup_teardown):
    """Check KSRAT AT Command. Nominal/Valid use case."""
    test_ID = ksrat_setup_teardown

    # Variable Init
    phase = int(read_config.findtext("autotest/Features_PHASE"))
    AT_KSRAT = int(read_config.findtext("autotest/Features_AT_KSRAT"))
    SOFT_INI_Soft_Version = read_config.findtext("autotest/SOFT_INI_Soft_Version")
    HARD_INI = read_config.findtext("autotest/HARD_INI")
    Soft_Version = two_digit_fw_version(SOFT_INI_Soft_Version)

    if AT_KSRAT == 0:
        pytest.skip("No AT+KSRAT command")

    try:

        # AT+KSRAT=?
        result = format_at_response(target_at.run_at_cmd("AT+KSRAT=?", timeout, ["OK"]))
        answer = result[0].split(" ")[1]
        # +KSRAT=2 allowed on HL7800 FW < 4.6.3.0 and 5.3.0 <= FW < 5.3.3 even though cannot attach to GSM
        if (HARD_INI == "HL7800" or HARD_INI == "HL7810" or HARD_INI == "HL7845") and ("04.06.03.00" <= Soft_Version < "05.03.00.00" or  Soft_Version >= "05.03.03.00"):
            assert answer in ("(0-1),(0-1)")
        else:
            # phase > 2 is (0-2)
            assert answer in ("(0-2),(0-1)")

        # AT+KSRAT?
        result = format_at_response(target_at.run_at_cmd("AT+KSRAT?", timeout, ["OK"]))
        def_ksrat = result[0].split(" ")[1]

        if def_ksrat:
            print("\nDefault KSRAT is: " + def_ksrat)
        else:
            def_ksrat = "0"
        # Test different scenarios
        if (phase > 2 and HARD_INI == "HL7802") or HARD_INI == "HL7812":
             ksrat_tab = ["0", "1", "2"]
        else:
            ksrat_tab = ["0", "1"]

        for k in ksrat_tab:
            if k == def_ksrat:
                continue
            # AT+KSRAT=k
            target_at.run_at_cmd("AT+KSRAT=" + k, timeout, ["OK"])

            # Auto reset after +KSRAT
            time.sleep(timeout * 3)

            # AT+KSRAT?
            target_at.run_at_cmd("AT+KSRAT?", timeout * 2, [r"\+KSRAT: " + k, "OK"])

    except Exception as err_msg:
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)

    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)

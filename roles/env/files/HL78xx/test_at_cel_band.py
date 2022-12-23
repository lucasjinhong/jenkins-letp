"""
Cellular AT commands test cases :: AT!BAND.
originated from A_INT_CEL_KBND_0000 integration test script.

Script for Qualcomm modules.
"""

import time
import pytest
import VarGlobal
from autotest import (PRINT_START_FUNC, PRINT_TEST_RESULT)
from autotest import pytestmark  # noqa # pylint: disable=unused-import

timeout = 15  # noqa # pylint: disable=unused-import

@pytest.fixture()
def band_setup_teardown(network_tests_setup_teardown, read_config):

    """Test case setup and teardown."""
    state = network_tests_setup_teardown

    if state == "OK":
        print("Test Setup Success")

    print("\nA_RC_INT_CEL_BAND_0000 TC Start:\n")

    print("\n------------Test's preambule Start------------")

    # Variable Init
    HARD_INI = read_config.findtext("autotest/HARD_INI")

    if not "RC51" in HARD_INI:
        pytest.skip("AT!BAND only supported on Qualcomm modules")

    test_nb = ""
    test_ID = "A_RC_INT_CEL_BAND_0000"
    PRINT_START_FUNC(test_nb + test_ID)

    print("\n----- Testing Start -----\n")

    yield test_ID

    print("\n----- BAND TearDown -----\n")


def A_RC_INT_CEL_BAND_0000(target_at, read_config, band_setup_teardown):
    """Check BAND AT Command. Nominal/Valid use case."""

    # Variable Init
    band_index = read_config.findtext("autotest/Network_Config/Band")
    band_list = ["0", "3", "4", "5", "6", "7", "9"]

    test_ID = band_setup_teardown

    # Start Test
    print("\n------------Test Case Start------------")

    try:
        # Check BAND AT Test Command
        target_at.run_at_cmd("AT!BAND=?", timeout,
                                   ["Index, Name",
                                    "00, All bands",
                                    "03, Europe 2G",
                                    "04, North America 2G",
                                    "05, GSM ALL",
                                    "06, Europe",
                                    "07, North America",
                                    "09, LTE ALL",
                                    "%s, *" % band_index, "OK"])

        # Check BAND AT Read Command
        target_at.run_at_cmd("AT!BAND?", timeout, ["Index, Name", band_index, "OK"])

        # Check BAND AT Write Command
        for band in band_list:
            target_at.run_at_cmd("AT!BAND=" + band, timeout, ["OK"])
            time.sleep(timeout)
            target_at.run_at_cmd("AT!BAND?", timeout, ["Index, Name", "0" + band + "*", "OK"])

        # Restore band to default
        target_at.run_at_cmd("AT!BAND=" + band_index, timeout, ["OK"])

    except Exception as err_msg:
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)

    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)

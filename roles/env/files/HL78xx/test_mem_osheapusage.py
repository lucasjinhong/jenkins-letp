"""
RC51xx sanity test script to run AT!OSHEAPUSAGE command and generate JSON file from the data.

"""
from os import path
import re
import json
import time
import pytest
import requests
import swilog
import VarGlobal
from autotest import (SagSendAT, SagWaitResp)
from autotest import (PRINT_START_FUNC, PRINT_TEST_RESULT, two_digit_fw_version)
from autotest import pytestmark  # noqa # pylint: disable=unused-import

# Elasticsearch/Kibana parameters
elasticsearch_url = "http://elasticsearch.farm.legato"
apss_index = "rc51-apss"
modem_index = "rc51-mpss"

def osheapusage_parser(resp, heap):
    """
    Function to parse OSHEAPUSAGE data

    Params:
        resp - AT response of AT!OSHEAPUSAGE
        heap - data for a specific section of heap

    Return:
        Integer values of heap data for specified section
    """

    heap = heap.split("_")[0].upper()
    data = resp.split(heap + " heap:")[1].split("\r\n\r\n")[0]

    total = int(re.findall(r'\d+', data.split("\r\n")[1])[0])
    free = int(re.findall(r'\d+', data.split("\r\n")[1])[1])
    used = int(re.findall(r'\d+', data.split("\r\n")[1])[2])
    wasted = int(re.findall(r'\d+', data.split("\r\n")[2])[0])
    header = int(re.findall(r'\d+', data.split("\r\n")[2])[1])
    blocks_count = int(re.findall(r'\d+', data.split("\r\n")[3])[0])
    blocks_used = int(re.findall(r'\d+', data.split("\r\n")[3])[1])
    largest_free = int(re.findall(r'\d+', data.split("\r\n")[3])[2])
    max_used = int(re.findall(r'\d+', data.split("\r\n")[4])[0])
    max_request = int(re.findall(r'\d+', data.split("\r\n")[4])[1])

    return (total, free, used,
            wasted, header,
            blocks_count, blocks_used, largest_free,
            max_used, max_request)


def format_json(heap_name, heap_data, tag, index):
    """
    Function to generate json file from heap data

    Params:
        heap_name - String input of heap name
        heap_data - Key values for json file
        tag - String input for Firmware version
        index - String input for index name

    Return:
        String output of generated JSON file
    """

    proc = {heap_name:{"total": heap_data[0], \
                 "free": heap_data[1], \
                 "used": heap_data[2], \
                 "wasted": heap_data[3], \
                 "header": heap_data[4], \
                 "blocks_count": heap_data[5], \
                 "blocks_used": heap_data[6], \
                 "blocks_largest_free": heap_data[7], \
                 "logical_max_used": heap_data[8], \
                 "logical_max_request": heap_data[9]}, \
                 "tag": tag}

    return json.dumps(proc, indent=4, separators=(',', ': '))


def upload_json(url, data):
    """
    Function to import JSON data to Kibana

    Params:
        url - URL of elasticsearch
        data - JSON data

    Return:
        Upload success/fail with status code
    """

    rsp = requests.post(url, json=data)
    if rsp.status_code == 200 or rsp.status_code == 201:
        swilog.info("JSON file upload successful!\n")
    else:
        swilog.error("ADD/UPDATE fails, status code = %s" % rsp.status_code)
        VarGlobal.statOfItem = "NOK"


@pytest.fixture()
def mem_osheapusage_setup_teardown(non_network_tests_setup_teardown, read_config):
    """Test case setup and teardown."""

    global HARD_INI, Soft_Version, reportDir, tag

    # Variable Init
    reportDir = path.expandvars('$LETP_WRAPPER_ATTACHMENTS')
    SOFT_INI_Soft_Version = read_config.findtext("autotest/SOFT_INI_Soft_Version")
    Soft_Version = two_digit_fw_version(SOFT_INI_Soft_Version)
    tag = SOFT_INI_Soft_Version.split(" ")[0]
    HARD_INI = read_config.findtext("autotest/HARD_INI")
    if not "RC51" in HARD_INI:
        pytest.skip("This test case is only valid for RC51xx")
    if Soft_Version < "00.07.00.00":
        pytest.skip("AT command not supported until version SWI9X05R_00.07.00.00")

    # Setup non-network settings
    state = non_network_tests_setup_teardown
    if state == "OK":
        print("General Test Setup Success")

    print("\nA_RC_MEM_OSHEAPUSAGE_0000 TC Start:\n")

    test_nb = ""
    test_ID = "A_RC_MEM_OSHEAPUSAGE_0000"
    PRINT_START_FUNC(test_nb + test_ID)

    print("\n------------Testing Start------------")

    yield test_ID

    print("\n----- Mem OSHEAPUSAGE TearDown -----\n")


def A_RC_MEM_OSHEAPUSAGE_0000(mem_osheapusage_setup_teardown, target_at):
    """
    Generate JSON file with RC51 heap data
    """
    test_ID = mem_osheapusage_setup_teardown

    # Variable Init
    heapList = ["apss_heap", "swi_heap", "amss_heap", "modem_heap"]
    jsonDir = []

    try:

        # Unlock AT command
        SagSendAT(target_at, "AT!UNLOCK=\"A710\"\r")
        SagWaitResp(target_at, ["\r\nOK\r\n"], 10000)

        SagSendAT(target_at, "AT!OSHEAPUSAGE?\r")
        result = SagWaitResp(target_at, ["*\r\nOK\r\n"], 10000)

        print("\n------ Generate Heap JSON files ------\n")

        for heap in heapList:

            # Parse OSHEAPUSAGE
            data = osheapusage_parser(result, heap)

            # Assign the index based on heap area
            if "apss_heap" in heap:
                index = apss_index
            else:
                index = modem_index

            # Generate JSON file
            heapJson = format_json(heap, data, tag, index)
            jsonPath = path.join(reportDir, tag + '_' + heap + '.json')
            jsonDir.append(jsonPath)
            with open(path.join(jsonPath), 'w') as file:
                file.write(heapJson)

            print("JSON file generated for: %s" % heap)
            print(heapJson)
            print("")

        print("\n------ Import JSON files to Kibana ------\n")

        for js in jsonDir:

            # Decode JSON data
            with open(js, "r") as read_file:
                data = json.load(read_file)

            # Assign the URL based on index
            if "apss_heap" in js:
                index = apss_index
            else:
                index = modem_index
            url = elasticsearch_url + "/%s/_doc" % index

            # Import data to Kibana
            print("Importing heap data to Kibana...")
            print("URL: %s" % url)
            print("Data:\n%s" % data)
            upload_json(url, data)
            print("")
            time.sleep(2)

    except Exception as err_msg:  # pylint: disable=broad-except
        VarGlobal.statOfItem = "NOK"
        print(Exception, err_msg)

    PRINT_TEST_RESULT(test_ID, VarGlobal.statOfItem)

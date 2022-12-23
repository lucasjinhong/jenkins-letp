#!/usr/bin/env python3
import os
import subprocess
import argparse
import yaml
import logging
import json
from time import sleep
from letp_wrapper_db import (get_module_id, get_firmware_id)
from letp_wrapper_xml import (LeTPTargetXML, LeTPAutotestXML,
                              LeTPReleaseXML, LeTPHostXML, LeTPNetworkXML,
                              LeTPRelayXML, LeTPSimDBXML, LeTPpppXML)
from integration_libs.hl78_uart import (find_at, find_cli, get_uart, get_ati9,
                                        strip_at_response, get_at_return_value,
                                        cme_error_get_info, cms_error_get_info,
                                        set_at_unlock)
from integration_libs.hl78_power_control import (relay_powercycle, otii_powercycle,
                                                 create_otii)
from integration_libs.hl78_fw import HL78Firmware as Firmware
from integration_libs.hl78_fw import HL78Module as Module
from integration_libs.hl78_fw import HL78FWRelease as Release
from integration_libs.hl78_fw import HL78Package as HL78Package
from integration_libs.hl78_fw import HL78FWSigned as HL78FWSigned
from integration_libs.avms_client import AVMSClient
from letp_wrapper_host import (get_ip_info, get_wwan_iface)
from letp_dirs import (LETP_CLAC_H_PATH, LETP_CLAC_TXT_PATH,
                       LETP_CLAC_H_LEGACY_PATH, LETP_CONFIG_PATH,
                       LOCAL_DELTA_DIR, BACKUP_DIR, DOWNLOAD_DIR,
                       AVMS_PACKAGE_DIR, LETP_TESTS,
                       LETP_WRAPPER_ROOT, LEGATO_QA_CONFIGURED, LEGATO_QA_CONFIG_PATH)
from serial import SerialException
from sim import iccid_to_siminfo, LTEBand
import re
import requests
from requests.exceptions import ConnectionError, MissingSchema, InvalidSchema
from tempfile import TemporaryDirectory, NamedTemporaryFile
from libarchive.public import file_pour
import shutil
import zipfile

# Modify for HL78xx.5.4.3.x.RK_03_02_00_00_13732_001.20211025
# firmware_regex = re.compile('(.*?)HL78..\.(\d*\.\d*\..*\.\d*)\.\S*')
firmware_regex = re.compile('(.*?)HL78..\.(\d*\.\d*\..*\.[0-9a-zA-Z]*)\.\S*')
firmware_module_list = ['HL7800', 'HL7802', 'HL7800-M', 'HL7810', 'HL7812', 'HL7845', 'RC5102', 'EM9190', 'HL7810:E0', 'HL7812:E0']
target_module_list = ['hl78xx', 'rc51xx', 'em91xx']

none_testsim_ccid_to_voice = {
    "89302720399911474046" : "16398389827",
    "89302720399911474095" : "16398385600",
    "89302720395910584058" : "12498335556"
}

log = logging.getLogger("autoconfigure")
log.setLevel(logging.INFO)
c_handler = logging.StreamHandler()
c_handler.setFormatter(
    logging.Formatter("[%(name)s][%(levelname)s]: %(message)s"))
log.addHandler(c_handler)
logging.addLevelName(logging.WARNING, "\033[1;33m%s\033[1;0m" % logging.getLevelName(logging.WARNING))
logging.addLevelName(logging.ERROR, "\033[1;31m%s\033[1;0m" % logging.getLevelName(logging.ERROR))

warning_list = []
AT_UnlockWarningOn = False

def set_sim_dns(overrides):
    autotest = LeTPAutotestXML()

    def sset(dns):
        log.info("Setting Device DNS IP Address to %s" % dns)
        autotest.set_device_dns_ip_address(dns)
        autotest.write()

    o_device_ip = overrides['autotest']['device_ip']

    if o_device_ip:
        log.info("device_ip found from config file, skipping detection")
        sset(o_device_ip)
        return

    log.info("Checking Device DNS IP from %s using `AT+CGCONTRDP`" % autotest.file_path)

    response = sendATCMD("AT+CGCONTRDP")
    if 'OK' in response[1]:
        log.warning("Not connected to network?")
    else:
        # AT Command Guide v9.3 <IP DNS_prim_addr> as index 5
        device_ip = get_at_return_value(response[1]).split(",")[5]
        log.debug("Valid response received")
        sset(device_ip)
        return device_ip

    log.warning("############################################")
    log.warning("WARNING")
    log.warning("YOU HAVE NOT SET SIM DNS address, some PPP test case may fail")
    warning_list.append("device ip is not set, ppp test case may fail")
    log.warning("")
    log.warning("############################################")

def set_ip_info(overrides):
    autotest = LeTPAutotestXML()
    host = LeTPHostXML()

    def sset(ip, iface):
        log.info("Setting host ip to %s in %s" % (ip, host.file_path))
        host.set_ip_address(ip)
        log.info("Setting host iface to %s in %s" % (iface, host.file_path))
        host.set_network_if(iface)
        host.write()

    o_ip = overrides['host']['ip_address']
    o_iface = overrides['host']['network_if']

    if o_ip and o_iface:
        log.info("local IP and iface found from config file, skipping autodetection")
        sset(o_ip, o_iface)
        return

    ip, iface = get_ip_info()
    o_ip = ip if not o_ip else o_ip
    o_iface = iface if not o_iface else o_iface

    sset(o_ip, o_iface)
    return ip, iface


def set_uart_at(overrides):
    target = LeTPTargetXML()

    def sset(ua):
        log.info("Setting AT port to %s in %s" % (ua, target.file_path))
        target.set_at(ua)
        if LEGATO_QA_CONFIGURED:
            target.set_enable_at()
        target.write()

    o_uart_at = overrides['target']['uart_at']

    if o_uart_at:
        log.info("AT UART port found from config file, skipping port detection")
        sset(o_uart_at)
        return
    else:
        try:
            port = find_at()
            if not port:
                raise SerialException("Couldn't find HL78xx device")
            uart_at = port["uart_at"]
            sset(uart_at)
            return
        except:
            log.error("AT port is not avail or opened by other terminal.")
            exit(0)


def set_uart_cli(overrides):
    target = LeTPTargetXML()
    autotest = LeTPAutotestXML()
    module_name = autotest.get_hard_ini()

    def sset(uc):
        log.info("Setting CLI port to %s in %s" % (uc, target.file_path))
        target.set_cli(uc)
        target.set_enable_cli()
        target.write()

    o_uart_cli = overrides['target']['uart_cli']

    if "RC51" in module_name:
        log.info("RC51 only supports AT port, enable UART1 and disable CLI")

        # Set up UART1
        response = sendATCMD("AT!MAPUART?")
        if '!MAPUART: 1' in response:
            log.info("Module already configured for UART1")
        else:
            log.info("Converting USB to UART1...")
            sendATCMD("AT!MAPUART=1,1")
            sendATCMD("AT!NVBACKUP=4")
            sendATCMD("AT!RESET")
            sleep(10)

            # Find updated AT port
            at_port = find_at()["uart_at"]
            sset(at_port, None)

        # Disable CLI port
        target.set_enable_cli("0")
        target.write()
        return

    if "EM91" in module_name:
        log.info("EM91 only supports AT port, disable CLI")
        # Disable CLI port
        target.set_enable_cli("0")
        target.write()
        return

    if o_uart_cli:
        log.info("CLI UART port found from config file, skipping port detection")
        sset(o_uart_cli)
        return
    else:
        try:
            uart_cli = target.get_cli() if not o_uart_cli else o_uart_cli
            port = find_cli(uart_cli=uart_cli)
            if not port:
                raise SerialException("Couldn't find HL78xx device")
            uart_cli = port["uart_cli"]
            sset(uart_cli)
            return
        except:
            log.error("CLI port is not avail or opened by other terminal.")
            exit(0)


def restore_default_settings(overrides):
    target = LeTPTargetXML()
    sendATCMD("AT+RESTOREDEFAULTS=0")
    log.info("Restore everything to defaults...")
    sleep(30)


def get_soft_version(overrides):
    target = LeTPTargetXML()
    autotest = LeTPAutotestXML()

    def sset(sv):
        log.info("Setting SOFT_INI_Soft_Version to %s" % sv)
        autotest.set_soft_version(sv)
        autotest.write()

    o_soft_version = overrides['autotest']['soft_version']

    if o_soft_version:
        log.info("soft_version found from config file, skipping detection")
        sset(o_soft_version)
        return

    log.info("Checking SOFT_INI_Soft_Version from %s using `AT+CGMR`" % autotest.file_path)
    response = sendATCMD("at+CGMR")
    if 'OK' in response:
        soft_version = response[1]
        log.debug("Valid response received")
        sset(soft_version)
        return soft_version

    raise ValueError("Invalid response received from module: %s" % cme_error_get_info(response))


def set_wdsd_version(overrides):
    target = LeTPTargetXML()
    autotest = LeTPAutotestXML()
    soft_version = autotest.get_soft_version()
    module_name = autotest.get_hard_ini()

    def sset(sv):
        log.info("Setting SOFT_INI_Wdsd_Version to %s" % sv)
        autotest.set_wdsd_version(sv)
        autotest.write()

    o_wdsd_version = overrides['autotest']['wdsd_version']
    if "EM91" in module_name:
        log.info("EM91 not support setting wdsd_version yet")
        return

    if o_wdsd_version:
        log.info("wdsd_version found from config file, skipping detection")
        wdsd_version = str(o_wdsd_version.split(','))
        sset(wdsd_version)
        return

    log.info("Checking SOFT_INI_Soft_Version: %s" % soft_version)
    main_build_version = soft_version.split(".")[1]
    if main_build_version == '3':
        split_soft_version = soft_version.split(".")
        split_soft_version[0] = split_soft_version[0].replace('B','T')
        wdsd_version = str([".".join(split_soft_version[:5]) + ".99." + split_soft_version[5]])
    else:
        wdsd_version = str([soft_version + ".99"])
    sset(wdsd_version)
    return wdsd_version


def get_hard_ini(overrides):
    target = LeTPTargetXML()
    autotest = LeTPAutotestXML()

    def sset(hi):
        log.info("Setting HARD_INI to %s" % hi)
        autotest.set_hard_ini(hi)
        autotest.write()

        if "HL78" in hi:
            target.set_name(target_module_list[0])
        elif "RC51" in hi:
            target.set_name(target_module_list[1])
        elif "EM91" in hi:
            target.set_name(target_module_list[2])
        target.write()
        log.info("Setting module/name to %s.xml" % target.get_name())

    o_hard_ini = overrides['autotest']['hard_ini']

    if o_hard_ini:
        log.info("hard_ini found from config file, skipping detection")
        sset(o_hard_ini)
        return

    log.info("Checking HARD_INI from %s using `AT+CGMM`" % autotest.file_path)
    response = sendATCMD("AT+CGMM")

    if 'OK' in response and response[1] in firmware_module_list:
        hard_ini = response[1]
        log.debug("Valid response received")
        sset(hard_ini)
        return hard_ini

    raise ValueError("Invalid response received from module: %s" % cme_error_get_info(response))


def get_imsi(overrides):
    target = LeTPTargetXML()
    autotest = LeTPAutotestXML()

    def sset(imsi):
        log.info("Setting SIM_IMSI to %s" % imsi)
        autotest.set_sim_imsi(imsi)
        autotest.write()

    o_sim_imsi = overrides['autotest']['sim_imsi']

    if o_sim_imsi:
        log.info("sim_imsi found from config file, skipping detection")
        sset(o_sim_imsi)
        return

    log.info("Checking SIM_IMSI from %s using `AT+CIMI`" % autotest.file_path)
    response = sendATCMD("AT+CIMI")
    if 'OK' in response:
        sim_imsi = response[1]
        log.debug("Valid response received")
        sset(sim_imsi)
        return sim_imsi
    else:
        log.warning((
            "Invalid response received from module "
            "(SIM not detected?)"))
        try:
            log.warning("CME ERROR: %s" % cme_error_get_info(response))
        except TypeError:
            pass
        sset("")
        return


def get_ccid(overrides):
    target = LeTPTargetXML()
    autotest = LeTPAutotestXML()
    module_name = autotest.get_hard_ini()

    def sset(ccid):
        log.info("Setting SIM_CCID to %s" % ccid)
        autotest.set_sim_ccid(ccid)
        autotest.write()

    o_sim_ccid = overrides['autotest']['sim_ccid']

    if o_sim_ccid:
        log.info("sim_ccid found from config file, skipping detection")
        sset(o_sim_ccid)
        return

    log.info("Checking SIM_CCID from %s using `AT+CCID/AT+ICCID`" % autotest.file_path)

    if "RC51" in module_name or "EM91" in module_name:
        response = sendATCMD("AT+ICCID")
    else:
        response = sendATCMD("AT+CCID")
    if 'OK' in response:
        sim_ccid = get_at_return_value(response[1])
        log.debug("Valid response received")
        sset(sim_ccid)
        return sim_ccid
    else:
        log.warning((
            "Invalid response received from module "
            "(SIM not detected?)"))
        try:
            log.warning("CME ERROR: %s" % cme_error_get_info(response))
        except TypeError:
            pass
        sset("")
        return


def set_voice_number(overrides):
    autotest = LeTPAutotestXML()

    sim_imsi = autotest.get_sim_imsi()
    iccid = autotest.get_sim_ccid()
    sim_info = iccid_to_siminfo(iccid)

    if sim_info.issuer == "amarisoft":
        if sim_imsi:
            log.info("Found sim_imsi, auto set voice number")
            voice_number = sim_imsi[-3:]
            log.info("Setting Voice_Number to %s" % voice_number)
            autotest.set_sim_voice_number(voice_number)
            autotest.write()
            return
    else:
        voice_number = none_testsim_ccid_to_voice.get(iccid)
        if voice_number:
            log.info("Setting Voice_Number to %s" % voice_number)
            autotest.set_sim_voice_number(voice_number)
            autotest.write()
            return

    sim_voice_number = overrides['autotest']['sim_voice_number']
    if sim_voice_number:
        log.info("Found voice_number in config file")
        log.info("Setting Voice_Number to %s" % voice_number)
        autotest.set_sim_voice_number(sim_voice_number)
        autotest.write()
        return

    log.warning("############################################")
    log.warning("WARNING")
    log.warning("sim_imsi not set, unable to set voice number, please enter manually")
    warning_list.append("sim_imsi not set, unable to set voice number")
    log.warning("")
    log.warning("############################################")
    return

def set_service_center_num(overrides):
    autotest = LeTPAutotestXML()

    iccid = autotest.get_sim_ccid()
    sim_info = iccid_to_siminfo(iccid)

    response = sendATCMD("AT+CSCA?")

    n = response[1].split('+CSCA: ')[1].split(',')[0]

    res = re.sub(r'[^\s\w]','',n)

    autotest.set_sim_service_center_number_tx(res)
    autotest.write()

    return

def set_default_kcarriercfg():
    autotest = LeTPAutotestXML()

    module_name = autotest.get_hard_ini()

    if "HL78" in module_name:
        response = sendATCMD("AT+KCARRIERCFG?")
        if "+KCARRIERCFG: 0" not in response:
            log.info("Set back to default KCARRIERCFG")
            response = sendATCMD("AT+KCARRIERCFG=0")
            if 'OK' in response:
                log.info("Valid response received")
            else:
                raise ValueError("Invalid response received from module: %s" % response)
    elif "RC51" in module_name:
        log.warning("AT+KCARRIERCFG not available for RC51xx module, not setting operator")
        return
    elif "EM91" in module_name:
        log.warning("AT+KCARRIERCFG not available for EM91xx module, not setting operator")
        return


def set_band_info(overrides):
    autotest = LeTPAutotestXML()
    network = LeTPNetworkXML()
    target = LeTPTargetXML()

    phase = autotest.get_phase()

    def sset(m1, nb1, ws46):
        log.info("Setting M1 bands to %s" % m1)
        network.set_m1_bands(m1)
        log.info("Setting NB1 bands to %s" % nb1)
        network.set_nb1_bands(nb1)
        log.info("Setting WS46 to %s" % ws46)
        network.set_ws46(ws46)
        network.write()

    m1_bands = overrides['network']['m1_bands']
    nb1_bands = overrides['network']['nb1_bands']

    module_name = autotest.get_hard_ini()
    iccid = autotest.get_sim_ccid()
    sim_info = iccid_to_siminfo(iccid)
    if not sim_info:
        log.warning("Unknown SIM type, not setting bands")
        warning_list.append("Unknown SIM type, not setting bands")
        return

    response = sendATCMD("AT+KSRAT?")

    if "RC51" in module_name or "EM91" in module_name:
        ksrat = 0
        log.warning("AT+KSRAT not available for RC51xx and EM91xx module")
    elif 'OK' in response:
        ksrat = int(get_at_return_value(response[1]))
        log.info("Valid response received, current RAT is %s" % ksrat)
    elif phase == 0:
        ksrat = 0
        log.info("Phase 0: AT+KSRAT not available, using RAT 0")
    else:
        raise ValueError("Invalid response received from module: %s" % response)

    log.info("Detected SIM type %s" % sim_info.issuer)

    if not m1_bands or sim_info.issuer != "amarisoft":
        m1_bands = sim_info.m1_bands.bands
    if not nb1_bands or sim_info.issuer != "amarisoft":
        nb1_bands = sim_info.nb1_bands.bands

    # Assign default index for QC module bands
    m1_index = "0A"
    nb1_index = "0B"

    response = sendATCMD("AT+WS46?")

    if "HL78" in module_name:
        ws46_response = response[1].split(': ')[1]
        sset(m1_bands, nb1_bands,ws46_response)
    elif "RC51" in module_name:
        sset([m1_index], [nb1_index],response[1])
    elif "EM91" in module_name:
        sset(["00"],["00"],response[1])
    bitmapm1 = LTEBand(m1_bands).to_bitmap()
    bitmapnb1 = LTEBand(nb1_bands).to_bitmap()

    # Set M1 band
    if "HL78" in module_name:
        if ksrat != 0:
            ksrat = 0
            cmd = "AT+KSRAT=%s" % ksrat
            log.info("Setting KSRAT to 0")
            response = sendATCMD(cmd)
            if 'OK' in response:
                log.info("Valid response received")
            else:
                raise ValueError("Invalid response received from module: %s" % response)
            sleep(10)

        cmd = "AT+KBNDCFG=%s,%s" % (ksrat, bitmapm1)

    elif "RC51" in module_name:

        log.info("Unlock module to customize specific LTE band")
        uart_at = get_uart(target.get_at())
        response = set_at_unlock(uart_at)
        uart_at.close()
        if "OK" in response:
            log.info("Setup index %s with band %s" % (m1_index, bitmapm1))
            response = sendATCMD("AT!BAND=%s,\"LTE B%s\",0,%s,0" % (m1_index, m1_bands[0], bitmapm1))
            if 'OK' in response:
                log.info("Successfully registered band index %s" % m1_index)

        cmd = "AT!BAND=%s" % m1_index
    elif "EM91" in module_name:

        cmd = "AT!BAND=00"

    log.info("Setup band for M1")
    log.info("Setting bands for RAT %s with %s" % (ksrat, cmd))
    response = sendATCMD(cmd)
    if 'OK' in response:
        log.info("Valid response received")
        #TODO: Update when RAT switching is supported on RC51xx
        if "RC51" in module_name:
            log.info("AT+KSRAT not available for RC51xx module, not setting RAT")
            return
        elif "EM91" in module_name:
            log.info("Setting default RAT to AT!SELRAT=00")
            response = sendATCMD("AT!SELRAT=00")
            if 'OK' in response:
                log.info("Valid response received")
            else:
                raise ValueError("Invalid response received from module: %s" % response)
            return
    else:
        raise ValueError("Invalid response received from module: %s" % response)

    # Set NB1 band
    module_name = autotest.get_hard_ini()
    if module_name != "HL7800-M" and (sim_info.issuer == "amarisoft" or sim_info.issuer == "ChungHwa"):
        ksrat = 1
        cmd = "AT+KSRAT=%s" % ksrat
        log.info("Setting KSRAT to 1")
        response = sendATCMD(cmd)
        if 'OK' in response:
            log.info("Valid response received")
        else:
            raise ValueError("Invalid response received from module: %s" % response)
        sleep(10)
        log.info("Setup band for NB1")
        cmd = "AT+KBNDCFG=%s,%s" % (ksrat,bitmapnb1)
        log.info("Setting bands for RAT 1 with %s" % cmd)
        response = sendATCMD(cmd)
        if 'OK' in response:
            log.info("Valid response received")
        else:
            raise ValueError("Invalid response received from module: %s" % response)

        # Set back to M1 band as default
        ksrat = 0
        cmd = "AT+KSRAT=%s" % ksrat
        log.info("Setting KSRAT to 0")
        response = sendATCMD(cmd)
        if 'OK' in response:
            log.info("Valid response received")
        else:
            raise ValueError("Invalid response received from module: %s" % response)
        sleep(10)
    else:
        log.warning("NB1 band is not setup")
        warning_list.append("NB1 band is not setup")

    cmd = "AT+CFUN=1,1"
    response = sendATCMD(cmd)
    if 'OK' in response:
        log.info("Valid response received")
    else:
        raise ValueError("Invalid response received from module: %s" % response)
    sleep(10)


def set_switracemode(overrides):
    target = LeTPTargetXML()
    autotest = LeTPAutotestXML()
    module_name = autotest.get_hard_ini()

    if "RC51" in module_name or "EM91" in module_name:
        log.warning("AT+SWITRACEMODE command not supported, not setting switracemode")
        return

    cmd = "AT+SWITRACEMODE=RnD"
    log.info("Changing SWITRACEMODE to RnD, running %s" % cmd)
    sendATCMD(cmd)
    sleep(10)
    cmd = "AT+CFUN=1,1"
    sendATCMD(cmd)
    sleep(30)
    return


def set_unlock_sim(overrides):
    target = LeTPTargetXML()
    autotest = LeTPAutotestXML()
    module_name = autotest.get_hard_ini()

    sim_pin = overrides["autotest"]["pin1_code"]
    sim_puk = overrides["autotest"]["puk1_code"]

    if not sim_pin:
        log.info("PIN not provided, using SIM default PIN")
        sim_pin = autotest.get_pin1()
    if not sim_puk:
        log.info("PUK not provided, using SIM default PUK")
        sim_puk = autotest.get_puk1()

    query = "AT+CPIN?"

    for i in range(2):
        log.info("Querying SIM status using %s" % query)
        response = sendATCMD(query)

        if "OK" in response:
            log.info("Valid response recieved: %s" % response[1])
            status = get_at_return_value(response[1])

            if status == "READY":
                log.info("SIM is already unlocked")
                return
            elif status == "SIM PIN":
                if "EM" in module_name:
                    cmd = 'AT+CPIN="%s"' % sim_pin
                    log.info("Unlocking SIM using pin %s" % cmd)
                    response = sendATCMD(cmd)
                else:
                    cmd = 'AT+CLCK="SC",0,"%s"' % sim_pin
                    log.info("Unlocking SIM using pin %s" % cmd)
                    response = sendATCMD(cmd)

                if 'OK' in response:
                    log.debug("Valid response received")
                    return
                else:
                    raise ValueError("Invalid response received from module: %s" % cme_error_get_info(response))
            elif status == "SIM PUK":
                cmd = 'AT+CPIN="%s","%s"' % (sim_puk, sim_pin)
                log.info("Unlocking SIM using puk & pin %s" % cmd)
                response = sendATCMD(cmd)

                if 'OK' in response:
                    log.debug("Valid response received")
                    return
                else:
                    raise ValueError("Invalid response received from module: %s" % cme_error_get_info(response))
            else:
                log.error("SIM is not unlocked or asking for pin, please manually troubleshoot")
                warning_list.append("SIM is not unlocked or asking for pin")
                return
        elif "ERROR" in response:
            if i == 1:
                break
            log.info("SIM query response returns ERROR, rebooting module and retry...")
            sendATCMD("AT+CFUN=1,1")
            sleep(30)
        else:
            raise ValueError("Invalid response received from module: %s" % cme_error_get_info(response))
    log.error("SIM query failed")
    warning_list.append("SIM query response gets ERROR, check SIM card")


def set_apn_info(overrides):
    autotest = LeTPAutotestXML()
    target = LeTPTargetXML()

    iccid = autotest.get_sim_ccid()
    sim_info = iccid_to_siminfo(iccid)
    network_long_name = overrides['autotest']['long_network_name']

    def sset(sim_info):

        log.info("Setting network name to %s" % sim_info.issuer)
        autotest.set_network_name(sim_info.issuer)

        apnlist = overrides['autotest']['network_apn']
        apnlogin = overrides['autotest']['network_apn_login']
        apnpass = overrides['autotest']['network_apn_passwd']
        pdplist = overrides['autotest']['network_pdp_type']

        if not apnlist or sim_info.issuer != "amarisoft":
            apnlist = []
            for apn in sim_info.apns:
                apnlist.append(apn.apn)
        if not pdplist or sim_info.issuer != "amarisoft":
            pdplist = []
            for apn in sim_info.apns:
                pdplist.append(apn.pdp_type)

        # Modify user_name/password of pap/chap for Taipei amarisoft

        #if not apnlogin and sim_info.issuer == "amarisoft":
        #    apnlogin = "['','','','papusername','chapusername']"
        #else:
        #    apnlogin = "['']"

        #if not apnpass and sim_info.issuer == "amarisoft":
        #    apnpass = "['','','','pappwd','chappwd']"
        #else:
        #    apnpass = "['']"

        if not apnlogin and sim_info.issuer == "amarisoft":
            apnlogin = "['','','','papuser','chapuser']"
        else:
            apnlogin = "['']"

        if not apnpass and sim_info.issuer == "amarisoft":
            apnpass = "['','','','pappwd','chappassword']"
        else:
            apnpass = "['']"


        log.info("Setting network APN username to %s" % apnlogin)
        log.info("Setting network APN password to %s" % apnpass)
        autotest.set_network_apn_username(apnlogin)
        autotest.set_network_apn_password(apnpass)

        log.info("Setting network APN to %s" % apnlist)
        autotest.set_network_apn(str(apnlist))
        log.info("Setting network PDP type to %s" % pdplist)
        autotest.set_network_pdp(str(pdplist))

        autotest.write()

        return [pdplist[0],apnlist[0]]

    if not sim_info:
        log.warning("Unknown SIM type, not setting APN")
        warning_list.append("Unknown SIM type, not setting APN")
        return

    log.info("Detected SIM type %s" % sim_info.issuer)

    cgdcont_params = sset(sim_info)

    if not network_long_name:
        if (sim_info.issuer == "amarisoft"):
            network_long_name = "FW RMD Amarisoft|Legato Lab Amarisoft Network|TWTPE SWAMS1 Net"
    #    if (sim_info.issuer == "amarisoft"):
    #        network_long_name = "FW RMD Amarisoft|Legato Lab Amarisoft Network"
        elif(sim_info.issuer == "sierra"):
            network_long_name = "Sierra Wireless|Rogers Wireless"
        elif(sim_info.issuer == "telus"):
            network_long_name = "TELUS"
        elif(sim_info.issuer == "rogers"):
            network_long_name = "ROGERS ROGERS"
        elif(sim_info.issuer == "ChungHwa"):
            network_long_name = "Chunghwa Telecom"
    log.info("Setting network long name to %s" % network_long_name)
    autotest.set_network_long_name(network_long_name)

    autotest.write()

    apn = sim_info.get_apn(sim_info.default_apn)
    cmd = 'AT+CGDCONT=1,"{pdp}","{apn}"'.format(pdp=cgdcont_params[0], apn=cgdcont_params[1])

    log.info("Setting APN info on module using %s" % cmd)
    response = sendATCMD(cmd)

    if 'OK' in response:
        log.debug("Valid response received")
        return

    raise ValueError("Invalid response received from module: %s" % response)


def set_mbim_data_config(overrides):
    autotest = LeTPAutotestXML()
    target = LeTPTargetXML()
    host = LeTPHostXML()
    module_name = autotest.get_hard_ini()

    if "HL78" in module_name:
        log.warning("MBIM data call test not supported on HL78xx module")
        return

    mbim_path = overrides['target']['uart_mbim']
    wwan = overrides['host']['wwan_if']

    def_conf = os.path.expandvars('$LETP_TESTS/tools/MBPL_SDK_R18_ENG3-lite/settings-simple.conf')
    source = open(def_conf, 'r')
    ipv4_conf = os.path.expandvars('$LETP_TESTS/tools/MBPL_SDK_R18_ENG3-lite/lite-mbim-ipv4-settings.conf')
    file = open(ipv4_conf, 'w')

    while True:
        data = source.readline()
        if not data:
            break
        else:
            if data.startswith('devicePath'):

                if not mbim_path:
                    uart_at = target.get_at()
                    at_port = uart_at.replace("/dev/", "")
                    port = subprocess.getoutput("readlink /sys/class/tty/%s" % at_port)
                    usb_path = port.split("/")[-4].split(":")[0]
                    resp = subprocess.getoutput('dmesg | grep "cdc_mbim %s"' % usb_path).split("\n")

                    for mbim in resp[::-1]:
                        if "USB WDM device" in mbim:
                            mbim_path = '/dev/' + mbim.split(":")[-2].split(" ")[1]
                            break
                file.write("devicePath %s\n" % mbim_path)
                target.set_mbim(mbim_path)

            elif data.startswith('interfaceName'):

                if not wwan:
                    # Set WWAN interface name
                    wwan = get_wwan_iface()
                file.write("interfaceName %s\n" % wwan)
                host.set_wwan_if(wwan)

            elif data.startswith('session 0'):
                # Set the current APN to the conf file
                iccid = autotest.get_sim_ccid()
                sim_info = iccid_to_siminfo(iccid)
                apnlist = []
                for apn in sim_info.apns:
                    apnlist.append(apn.apn)
                apn = sim_info.get_apn(sim_info.default_apn)
                if not apn:
                    apn = apnlist[0]
                else:
                    apn = apn[0]
                data = data.replace(data.split(",")[3], apn)

                # Set MBIM context IP type
                if ipv4_conf:
                    data = data.replace(data.split(",")[6], "MBIMContextIPTypeIPv4")
                else:
                    data = data.replace(data.split(",")[6], "MBIMContextIPTypeIPv4v6")
                file.write(data)

            else:
                file.write(data)

    target.write()
    host.write()

def set_sms_message_storage(overrides):
    autotest = LeTPAutotestXML()
    target = LeTPTargetXML()

    def sset(n):
        log.info("Setting SmsMessageStorage to %s" % n)
        autotest.set_sms_message_storage(n)
        autotest.write()

    o_sms_message_storage = overrides['autotest']['SmsMessageStorage']

    if o_sms_message_storage:
        log.info("sms_message_storage set, skipping detection")
        sset(o_sms_message_storage)
        return

    log.info("Checking SmsMessageStorage from %s using `AT+CPMS=\"SM\"" % autotest.file_path)

    cmd = 'AT+CPMS="SM"'
    response = sendATCMD(cmd)

    if 'OK' in response:
        sms_storage = get_at_return_value(response[1])
        log.debug("Valid response received %s" % response)
        sms_storage = re.match('\d*,(\d*),\d*,(\d*),\d*,(\d*)', sms_storage).group(1)
        sset(sms_storage)
        return sms_storage
    else:
        log.warning((
            "Invalid response received from module "
            "(SIM not detected?)"))
        try:
            log.warning(cms_error_get_info(response))
        except TypeError:
            pass
        sset(0)
        return


def set_amarisoft_address(overrides):
    autotest = LeTPAutotestXML()
    amari_ip = overrides['autotest']['amarisoft_ip']
    amari_addr = overrides['autotest']['amarisoft_address']

    if (not amari_ip or not amari_addr):
        log.warning("############################################")
        log.warning("WARNING")
        log.warning("YOU ARE NOT SET EVERY AMARISOFT SERVER CONFIGURATIONS, TCP ASSOCIATE TEST CASE MAY FAIL")
        warning_list.append("Amarisoft server is not configured, TCP/UDP related test case will fail")
        log.warning("")
        log.warning("############################################")

    if amari_ip:
        log.info("Setting AmarisoftIPAddress to %s" % amari_ip)
        autotest.set_amarisoft_ip_address(amari_ip)

    if amari_addr:
        log.info("Setting AmarisoftAddress to %s" % amari_addr)
        autotest.set_amarisoft_address(amari_addr)

    autotest.write()


def get_release_info(overrides):
    target = LeTPTargetXML()
    release = LeTPReleaseXML()
    autotest = LeTPAutotestXML()
    module_name = autotest.get_hard_ini()
    soft_version = autotest.get_soft_version()

    log.info("Checking release info from %s using `ATI9`" % release.file_path)

    if "HL78" in module_name:

        uart_at = get_uart(target.get_at())
        response = get_ati9(uart_at)
        uart_at.close()
        legato_version = response['legato_version']
        fw_version = response['fw_version']
        atSwi = response['atSwi']
        UBOOT = response['UBOOT']
        MAC = response['MAC']
        PHY = response['PHY']
    else:

        response = soft_version

        legato_version = "N/A"
        fw_version = soft_version.split(" ")[0]
        atSwi = "N/A"
        UBOOT = "N/A"
        MAC = "N/A"
        PHY = "N/A"

    if overrides['release']['legato_version']:
        log.info("legato_version set, overriding")
        legato_version = overrides['release']['legato_version']
    if overrides['release']['fw_version']:
        log.info("fw_version set, overriding")
        fw_version = overrides['release']['fw_version']
    if overrides['release']['atswi']:
        log.info("atswi set, overriding")
        atSwi = overrides['release']['legato_version']
    if overrides['release']['uboot']:
        log.info("uboot set, overriding")
        UBOOT = overrides['release']['legato_version']
    if overrides['release']['mac']:
        log.info("mac set, overriding")
        MAC = overrides['release']['mac']
    if overrides['release']['phy']:
        log.info("phy set, overriding")
        PHY = overrides['release']['phy']

    log.info("Setting legato_version to %s" % legato_version)
    release.set_legato_version(legato_version)
    log.info("Setting fw_version to %s" % fw_version)
    release.set_fw_version(fw_version)
    log.info("Setting atSwi to %s" % atSwi)
    release.set_atswi(atSwi)
    log.info("Setting UBOOT to %s" % UBOOT)
    release.set_uboot(UBOOT)
    log.info("Setting MAC to %s" % MAC)
    release.set_mac(MAC)
    log.info("Setting PHY to %s" % PHY)
    release.set_phy(PHY)

    release.write()

    return response


def get_phase_info(overrides):
    autotest = LeTPAutotestXML()
    release = LeTPReleaseXML()
    module_name = autotest.get_hard_ini()
    soft_version = autotest.get_soft_version()

    def sset(p, k):
        if p is not None:
            log.info("Setting Features_PHASE to %s" % p)
            autotest.set_phase(p)
        if k is not None:
            log.info("Setting Features_AT_KSRAT to %s" % k)
            autotest.set_at_ksrat(k)

        autotest.write()

    log.info("Checking phase information using %s" % release.file_path)

    if "HL78" in module_name:
        firmware_version = firmware_regex.match(release.get_fw_version()).group(2)
        firmware_versions = firmware_version.split(".")
        phase = int(firmware_versions[0]) - 1
    elif "RC51" in module_name:
        firmware_version = soft_version.split(" ")[0]
        firmware_versions = firmware_version.split(".")
        phase = int(firmware_versions[1]) - 4
    elif "EM91" in module_name:
        firmware_version = soft_version.split(" ")[0]
        firmware_versions = firmware_version.split(".")
        phase = int(firmware_versions[0].split("_")[1])

    log.info("Running firmware version %s" % firmware_version)
    if phase < 2:
        enable_ksrat = False
    else:
        enable_ksrat = True

    if overrides['autotest']['phase']:
        log.info("phase set, overriding")
        phase = overrides['autotest']['phase']
    if overrides['autotest']['ksrat']:
        log.info("ksrat set, overriding")
        enable_ksrat = overrides['autotest']['ksrat']

    sset(phase, enable_ksrat)
    return phase

def set_features_info(overrides):
    autotest = LeTPAutotestXML()
    module_name = autotest.get_hard_ini()

    def sset(pccid, ccid, xatt, autoflasher):
        log.info("Setting Features_AT_percent_CCID to %s" % pccid)
        autotest.set_at_percent_ccid(pccid)

        log.info("Setting Features_AT_CCID to %s" % ccid)
        autotest.set_at_ccid(ccid)

        log.info("Setting Features_AT_XATTMODE to %s" % xatt)
        autotest.set_at_xattmode(xatt)

        log.info("Setting Features_Autoflasher to %s" % autoflasher)
        autotest.set_autoflasher(autoflasher)

        autotest.write()

    # Default settings
    XATTMODE = False
    Autoflasher = True
    CCID = True
    percent_CCID = True
    if "RC51" in module_name or "EM91" in module_name:
        log.info("AT%CCID only supported on Altair modules")
        percent_CCID = False

    o_xatt = overrides['autotest']['xatt']
    o_pccid = overrides['autotest']['pccid']
    o_ccid = overrides['autotest']['ccid']
    o_Autoflasher = overrides['autotest']['autoflasher']

    if o_xatt:
        log.info("XATTMODE set, overriding")
        XATTMODE = o_xatt
    if not o_pccid and o_pccid == 0:
        log.info("percent_CCID set, overriding")
        percent_CCID = o_pccid
    if not o_ccid and o_ccid == 0:
        log.info("CCID set, overriding")
        CCID = o_ccid
    if not o_Autoflasher and o_Autoflasher == 0:
        log.info("Autoflasher set, overriding")
        Autoflasher = o_Autoflasher

    sset(percent_CCID, CCID, XATTMODE, Autoflasher)

def get_enabled_gpio(overrides):
    autotest = LeTPAutotestXML()

    def sset(gpio):
        log.info("Setting Enabled_GPIO to %s" % gpio)
        autotest.set_enabled_gpio(gpio)
        autotest.write()

    o_enabled_gpio = overrides['autotest']['enabled_gpio']

    if o_enabled_gpio:
        log.info("enabled_gpio found from config file, skipping detection")
        sset(o_enabled_gpio)
        return

    log.info("Checking Enabled_GPIO from %s using `AT+KGPIOCFG?`" % autotest.file_path)
    resp = sendATCMD("AT+KGPIOCFG?")

    if 'OK' in resp:
        gpio_str = [s for s in resp if ": " in s]
        length = len(gpio_str)
        for i in range(length):
            gpio_str[i] = gpio_str[i].split(': ')[1].split(',')[0].replace("'","")
        enabled_gpio = ",".join(gpio_str)
        log.debug("Valid response received")
        sset(enabled_gpio)
        return enabled_gpio
    elif 'ERROR' in resp:
        log.warning("AT+KGPIOCFG command not supported, not setting enabled GPIO pins")
        return

    raise ValueError("Invalid response received from module: %s" % cme_error_get_info(response))

def set_sim_secrets(overrides):
    autotest = LeTPAutotestXML()
    pin1_code = overrides['autotest']['pin1_code']
    puk1_code = overrides['autotest']['puk1_code']
    pin2_code = overrides['autotest']['pin2_code']
    puk2_code = overrides['autotest']['puk2_code']

    iccid = autotest.get_sim_ccid()
    sim_info = iccid_to_siminfo(iccid)
    if sim_info:
        if pin1_code:
            log.info("Setting PIN1_CODE to %s" % pin1_code)
            autotest.set_pin1(pin1_code)
        else:
            if (sim_info.issuer == "amarisoft"):
                autotest.set_pin1("1111")
            elif(sim_info.issuer == "sierra"):
                autotest.set_pin1("8888")
            elif(sim_info.issuer == "rogers"):
                autotest.set_pin1("1234")
            elif(sim_info.issuer == "ChungHwa"):
                autotest.set_pin1("3699")
            else:
                log.warning("SIM pin not provided, blanking PIN1_CODE")
                log.warning("############################################")
                log.warning("WARNING")
                log.warning("YOU HAVE NOT SET PIN1_CODE")
                warning_list.append("PIN1 code is not set")
                log.warning("")
                log.warning("RUNNING SIM PIN RELATED TESTS MAY FAIL")
                autotest.set_pin1("")

        if puk1_code:
            log.info("Setting PUK1_CODE to %s" % puk1_code)
            autotest.set_puk1(puk1_code)
        else:
            if (sim_info.issuer == "amarisoft"):
                autotest.set_puk1("11111111")
            else:
                log.warning("############################################")
                log.warning("WARNING")
                log.warning("YOU HAVE NOT SET PUK1_CODE")
                warning_list.append("PUK1 code is not set")
                log.warning("")
                log.warning("RUNNING SIM PIN RELATED TESTS MAY LOCK YOUR SIM")
                log.warning("############################################")
                autotest.set_puk1("")

        if pin2_code:
            log.info("Setting PIN2_CODE to %s" % pin2_code)
            autotest.set_pin2(pin2_code)
        else:
            if (sim_info.issuer == "amarisoft"):
                autotest.set_pin2("2222")
            else:
                log.warning("SIM pin not provided, blanking PIN2_CODE")
                log.warning("############################################")
                log.warning("WARNING")
                log.warning("YOU HAVE NOT SET PIN2_CODE")
                warning_list.append("PIN2 code is not set")
                log.warning("")
                log.warning("RUNNING SIM PIN RELATED TESTS MAY FAIL")
                autotest.set_pin2("")

        if puk2_code:
            log.info("Setting PUK2_CODE to %s" % puk2_code)
            autotest.set_puk2(puk2_code)
        else:
            if (sim_info.issuer == "amarisoft"):
                autotest.set_puk2("22222222")
            else:
                log.warning("############################################")
                log.warning("WARNING")
                log.warning("YOU HAVE NOT SET PUK2_CODE")
                warning_list.append("PUK2 code is not set")
                log.warning("")
                log.warning("RUNNING SIM PIN RELATED TESTS MAY LOCK YOUR SIM")
                log.warning("############################################")
                autotest.set_puk2("")
    else:
        log.warning("############################################")
        log.warning("WARNING")
        log.warning("SIM CARD IS NOT VALID")
        warning_list.append("SIM CARD IS NOT VALID")
        log.warning("")
        log.warning("PLEASE CHECK IF SIM IS INSERT")
        log.warning("############################################")

    autotest.write()


def set_sudo(overrides):
    if LEGATO_QA_CONFIGURED:
        ppp = LeTPpppXML()
        host = LeTPHostXML()
    autotest = LeTPAutotestXML()
    sudo = overrides['autotest']['sudo']

    if sudo:
        log.info("Setting Sudo to *")
        if LEGATO_QA_CONFIGURED:
            ppp.set_root_password(sudo)
            host.set_root_password(sudo)
        autotest.set_sudo(sudo)
    else:
        log.warning("############################################")
        log.warning("WARNING")
        log.warning("YOU HAVE NOT SET Sudo password, some PPP test case may fail")
        warning_list.append("sudo password is not set, PPP test case will fail")
        log.warning("")
        log.warning("############################################")

    if LEGATO_QA_CONFIGURED:
        ppp.write()
        host.write()
    autotest.write()


def set_avms_settings(overrides):
    autotest = LeTPAutotestXML()
    avms_url = overrides['autotest']['avms_url']
    avms_client_id = overrides['autotest']['avms_client_id']
    avms_client_secret = overrides['autotest']['avms_client_secret']
    avms_company = overrides['autotest']['avms_company']
    avms_username = overrides['autotest']['avms_username']
    avms_password = overrides['autotest']['avms_password']
    avms_uid = overrides['autotest']['avms_uid']

    if avms_url:
        log.info("Setting avms_url to %s" % avms_url)
        autotest.set_avms_url(avms_url)
    if avms_client_id:
        log.info("Setting avms_client_id to %s" % avms_client_id)
        autotest.set_avms_client_id(avms_client_id)
    if avms_client_secret:
        log.info("Setting avms_client_secret to %s" % avms_client_secret)
        autotest.set_avms_client_secret(avms_client_secret)
    if avms_company:
        log.info("Setting avms_company to %s" % avms_company)
        autotest.set_avms_company(avms_company)
    if avms_username:
        log.info("Setting avms_username to %s" % avms_username)
        autotest.set_avms_username(avms_username)
    if avms_password:
        log.info("Setting avms_password to *")
        autotest.set_avms_password(avms_password)
    if avms_uid:
        log.info("Setting avms_uid to %s" % avms_uid)
        autotest.set_avms_uid(avms_uid)
    else:
        log.info("Trying to get module uid from airvantage")
        log.info("Checking Module Serial Number using `AT+KGSN=3`")
        response = sendATCMD("AT+KGSN=3")
        if "OK" in response:
            serial_num = get_at_return_value(response[1]).split(": ")[0]
            log.debug("Valid response received")
            try:
                token = AVMSClient.get_access_token(avms_url,
                                                     avms_username,
                                                     avms_password,
                                                     avms_client_id,
                                                     avms_client_secret)

                avms_client = AVMSClient(avms_url, token, avms_company, None)
                avms_uid = avms_client.get_module_uid(serial_num)
                log.info("Setting avms_uid to %s" % avms_uid)

                # When UID is None, Initialize the module on AVMS server
                if avms_uid == None:
                    log.info("Initialize the module on AVMS server due to avms_uid is None")
                    # get fsn, IMEI and FW
                    fsn = serial_num
                    imei = sendATCMD("AT+KGSN=0")
                    imei = get_at_return_value(imei[1]).split(": ")[0]
                    firmware = sendATCMD("ATI3")
                    firmware = firmware[1]

                    app_id = avms_client.get_application_uid(firmware)

                    data =  {
                        "name": imei,
                        "state": "INVENTORY",
                        "lifeCycleState": "INVENTORY",
                        "activityState":"ACTIVATED",
                        "gateway":    {
                        "serialNumber": fsn,
                        "imei": imei
                        },
                        "applications" : [{
                            "uid": app_id
                        }]
                    }

                    # Initialize the Moudle on AVMS server
                    log.info("Initialize the module on AVMS server")
                    create_system = avms_client.create_system(data)

                    # HTTP Response '200' is successful addition to server
                    if "200" in str(create_system):
                        log.info("Successfully initialize the module on AVMS server")
                        # return

                    avms_uid = avms_client.get_module_uid(serial_num)
                    log.info("Setting avms_uid to %s" % avms_uid)
                    # Initializing the module finished

                autotest.set_avms_uid(avms_uid)
            except:
                log.warning("Unable to get module uid from AVMS server, skipping avms_uid config")
        else:
            log.warning("AT+KGSN command not supported, skipping avms_uid config")
    autotest.write()

def set_fota_version(overrides):
    autotest = LeTPAutotestXML()
    soft_version = autotest.get_soft_version()
    module_name = autotest.get_hard_ini()

    fota_ver = overrides['autotest']['fota_version']
    fota_sft_up_ver = overrides['autotest']['fota_sft_up_version']
    fota_sft_down_ver = overrides['autotest']['fota_sft_down_version']

    if fota_ver:
        fota_version = str(fota_ver.split(','))
        log.info("Parameter fota_version is configured in autoconfigure")
    else:
        version_len = len(soft_version.split('.'))
        if version_len == 6:
            main_build_version = soft_version.split(".")[1]
            if main_build_version == '3':
                split_soft_version = soft_version.split(".")
                split_soft_version[0] = split_soft_version[0].replace('B','T')
                fota_version = str([".".join(split_soft_version[:5]) + ".99." + split_soft_version[5], soft_version])
            else:
                fota_version = str(['.'.join(soft_version.split('.')[:-1])])
        elif version_len == 5:
            if 'E0' in soft_version:
                fota_version = str([soft_version + ".99", soft_version])
            else:
                if '99' in soft_version.split('.')[-1]:
                    fota_version = str(['.'.join(soft_version.split('.')[:-1]) + '.0'])
                else:
                    fota_version = str(['.'.join(soft_version.split('.')[:-1]) + '.99', soft_version])
        elif "RC51" in module_name:
            #TODO: placeholder for RC51xx development
            fota_version = "['']"
        elif "EM91" in module_name:
            #TODO: placeholder for EM91xx development
            fota_version = "['']"
        else:
            fota_version = "['']"
        log.info("No fota_version is configured in autoconfigure: set default fota_version")
    log.info("Setting SOFT_INI_Fota_Version to %s" % fota_version)
    autotest.set_fota_version(fota_version)

    if fota_sft_up_ver:
        fota_sft_up_version = str(fota_sft_up_ver.split(','))
        log.info("Setting SOFT_INI_Fota_Sft_Up_Version to %s" % fota_sft_up_version)
        autotest.set_fota_sft_up_version(fota_sft_up_version)
    if fota_sft_down_ver:
        fota_sft_down_version = str(fota_sft_down_ver.split(","))
        log.info("Setting SOFT_INI_Fota_Sft_Down_Version to %s" % fota_sft_down_version)
        autotest.set_fota_sft_down_version(fota_sft_down_version)
    autotest.write()

def set_avms_local_delta(overrides):
    autotest = LeTPAutotestXML()
    module_name = autotest.get_hard_ini()

    if "RC51" in module_name or "EM91" in module_name:
        log.warning("FOTA not supported, not setting AVMS settings")
        return

    def sset(local,local99):
        log.info("Setting AVMS_LOCAL_DELTA to %s" % local)
        autotest.set_local_delta_to_test(local)

        log.info("Setting AVMS_LOCAL_DELTA99 to %s" % local99)
        autotest.set_local_delta_from_test(local99)

        autotest.write()


    local_delta = overrides['autotest']['local_avms_path']
    local_delta99 = overrides['autotest']['local_avms99_path']

    if not local_delta or not local_delta99:
        log.info("Fetching AVMS local delta from get-legato")
        module_name = autotest.get_hard_ini()
        soft_version = autotest.get_soft_version()

        sections = soft_version.split(".")

        phase = sections[1]
        major = sections[2]
        minor = sections[3]
        legato = sections[4]

        version = phase+'.'+major+'.'+minor+'.'+legato
        fw = Firmware.from_soft_version(soft_version)

        if fw.signed == HL78FWSigned.UNSIGNED:
            log.warning("Unsigned module don't have local delta")
            log.warning("Skiping setting AVMS_LOCAL_DELTA and AVMS_LOCAL_DELTA99")
            return
        elif fw.signed == HL78FWSigned.SIGNED_RND:
            package_type = "rnd"
        elif fw.signed == HL78FWSigned.SIGNED_SIERRA:
            package_type = "sierra"

        try:
            avms_link = HL78Package.to_full_avms_package_url(module_name.lower(),version,package_type)
            avms_file_name = avms_link.split("/")[-1]
            avms_path = os.path.join(LOCAL_DELTA_DIR, avms_file_name)
            log.info("Downloading %s" % avms_file_name)
            avms_file = requests.get(avms_link)
            open(avms_path,'wb').write(avms_file.content)


            avms99_link = avmslink = HL78Package.to_full_avms_package_url(module_name.lower(),version+".99",package_type)
            avms99_file_name = avms99_link.split("/")[-1]
            avms99_path = os.path.join(LOCAL_DELTA_DIR, avms99_file_name)
            log.info("Downloading %s" % avms99_file_name)
            avms99_file = requests.get(avms99_link)
            open(avms99_path,'wb').write(avms99_file.content)


            avmszipfile=zipfile.ZipFile(avms_path)
            ua99filename=""
            for filename in  avmszipfile.namelist():

                if filename.endswith('.ua'):
                    ua99filename=filename
                    avmszipfile.extract(filename,LOCAL_DELTA_DIR)

            avms99zipfile=zipfile.ZipFile(avms99_path)
            uafilename=""
            for filename in  avms99zipfile.namelist():

                if filename.endswith('.ua'):
                    uafilename=filename
                    avms99zipfile.extract(filename,LOCAL_DELTA_DIR)

            local_delta = os.path.join(LOCAL_DELTA_DIR, uafilename)
            local_delta99 = os.path.join(LOCAL_DELTA_DIR, ua99filename)
        except Exception as e:
            log.warning("Error during get avms file, not setting the path")
            log.error(e)
            local_delta=""
            local_delta99=""


    sset(local_delta,local_delta99)

def set_backup_info(overrides):
    autotest = LeTPAutotestXML()
    module_name = autotest.get_hard_ini()
    if "RC51" in module_name or "EM91" in module_name:
        log.warning("SFT not available on RC51, not downloading sft")
    else:
        sft_link = "http://cgit.legato/altair/1250/tools.git/plain/sft/bin/Linux_x86/sft?h=refs/heads/master"
        sft_path = os.path.join(BACKUP_DIR, 'sft')
        if not os.path.isfile(sft_path):
            log.warning("%s not found, downloading" % sft_path)
            r = requests.get(sft_link)
            with open(sft_path, 'wb') as f:
                f.write(r.content)
            return set_backup_info(overrides)
        os.chmod(sft_path, 755)

    log.info("Setting backupPath to %s" % BACKUP_DIR)
    autotest.set_backup_path(BACKUP_DIR)
    log.info("Setting restorePath to %s" % DOWNLOAD_DIR)
    autotest.set_restore_path(DOWNLOAD_DIR)
    autotest.write()


def set_clac(overrides):
    autotest = LeTPAutotestXML()

    module_name = autotest.get_hard_ini()
    if "RC51" in module_name or "EM91" in module_name:
        log.warning("Clac file not available, test A_HL_INT_GEN_CLAC_0000 will fail.")
        return

    fw = Firmware.from_soft_version(autotest.get_soft_version())
    phase = fw.phase
    major = fw.major
    clac_path = overrides['autotest']['clac_path']
    if clac_path:
        log.info("Setting ClacFilePath to %s" % clac_path)
        autotest.set_clac_file_path(clac_path)
    elif (os.path.isfile(LETP_CLAC_H_PATH) and (phase > 3 or (phase == 3 and major >= 5))):
        log.info("Phase %s, Major %s: Found swiserver_app_clac.h at %s" % (phase, major, LETP_CLAC_H_PATH))
        log.info("Setting ClacFilePath to %s" % LETP_CLAC_H_PATH)
        autotest.set_clac_file_path(LETP_CLAC_H_PATH)
    elif os.path.isfile(LETP_CLAC_H_LEGACY_PATH) and phase >= 3:
        log.info("Phase %s, Major %s: Found swiserver_app_clac_legacy.h at %s" % (phase, major, LETP_CLAC_H_PATH))
        log.info("Setting ClacFilePath to %s" % LETP_CLAC_H_LEGACY_PATH)
        autotest.set_clac_file_path(LETP_CLAC_H_LEGACY_PATH)
    elif os.path.isfile(LETP_CLAC_TXT_PATH) and phase < 3:
        log.info("Phase %s: Found clac.txt at %s" % (phase, LETP_CLAC_TXT_PATH))
        log.info("Setting ClacFilePath to %s" % LETP_CLAC_TXT_PATH)
        autotest.set_clac_file_path(LETP_CLAC_TXT_PATH)
    elif os.path.isfile(autotest.get_clac_file_path()):
        log.info("ClacFilePath in autotest is already set to %s" % autotest.get_clac_file_path())
    else:
        log.warning("Could not find clac file, test A_HL_INT_GEN_CLAC_0000 will fail.")

    autotest.write()


def set_ftp_settings(overrides):
    autotest = LeTPAutotestXML()

    iccid = autotest.get_sim_ccid()
    sim_info = iccid_to_siminfo(iccid)
    if sim_info:
        if (sim_info.issuer == "sierra" or sim_info.issuer == "telus"):
            vm_server_ip = "cnhkg-ev-swtst01.sierrawireless.com"
            ftp_username = "sierra"
            ftp_password = "hisierra"
        else:
            vm_server_ip = overrides['autotest']['IntegrationVMServer']
            ftp_username = overrides['autotest']['ftp_username']
            ftp_password = overrides['autotest']['ftp_passwd']

    if (not ftp_username or not vm_server_ip or not ftp_password):
        log.warning("############################################")
        log.warning("WARNING")
        log.warning("YOU HAVE NOT SET EVERY FTP CONFIGURATIONS, FTP ASSOCIATED TEST CASES MAY FAIL")
        log.warning("")
        log.warning("############################################")

    if vm_server_ip:
        log.info("Setting IntegrationVMServer to %s" % vm_server_ip)
        autotest.set_vm_server_ip(vm_server_ip)
    if ftp_username:
        log.info("Setting ftp_username to %s" % ftp_username)
        autotest.set_ftp_username(ftp_username)
    if ftp_password:
        log.info("Setting ftp_password to %s" % ftp_password)
        autotest.set_ftp_password(ftp_password)

    autotest.write()

def set_external_server(overrides):
    autotest = LeTPAutotestXML()
    flake_server_ip = overrides['autotest']['legato_flake_server']
    flake_echo_port = overrides['autotest']['flake_echo_port']
    flake_ftp_username = overrides['autotest']['flake_ftp_username']
    flake_ftp_passwd = overrides['autotest']['flake_ftp_passwd']

    if (not flake_server_ip or not flake_echo_port or not flake_ftp_username or not flake_ftp_passwd):
        log.warning("############################################")
        log.warning("WARNING")
        log.warning("YOU HAVE NOT SET EXTERNAL SERVER CONFIGURATIONS, 2G TEST CASES MAY FAIL")
        log.warning("")
        log.warning("############################################")

    if flake_server_ip:
        log.info("Setting legato_flake_server to %s" % flake_server_ip)
        autotest.set_legato_flake_server_ip(flake_server_ip)
    if flake_echo_port:
        log.info("Setting flake_echo_port to %s" % flake_echo_port)
        autotest.set_flake_echo_port(flake_echo_port)
    if flake_ftp_username:
        log.info("Setting flake_ftp_username to %s" % flake_ftp_username)
        autotest.set_flake_ftp_username(flake_ftp_username)
    if flake_ftp_passwd:
        log.info("Setting flake_ftp_passwd to %s" % flake_ftp_passwd)
        autotest.set_flake_ftp_password(flake_ftp_passwd)

    autotest.write()


def set_module_network_type(overrides):
    autotest = LeTPAutotestXML()
    network_type = overrides['autotest']['network_type']
    module_name = autotest.get_hard_ini()

    if (network_type == "nb1" and module_name == "HL7800-M") or \
            (network_type == "2g" and module_name not in ["HL7802", "HL7812"]):
        log.warning("Network type %s is not supported by %s module, Setting default network type: M1",
                    network_type.upper(), module_name)
        warning_list.append("Input --network_type is not supported by module, Setting default network type: M1")
        overrides['autotest']['network_type'] = "m1"
        network_type = overrides['autotest']['network_type']

    if network_type in ["m1", "nb1", "2g"]:
        network_type_path = "$LETP_TESTS/sanity/config/network_%s.xml" % network_type
        log.info("Setting network config file to %s" % network_type_path)
        autotest.set_network_type_path(network_type_path)

    # Configure RAT to network type
    if network_type != "m1":

        if network_type == "nb1":
            ksrat = 1
        elif network_type == "2g":
            ksrat = 2
        else:
            raise ValueError("Invalid network type, input must be m1/nb1/2g")

        log.info("Setting KSRAT to %s" % ksrat)
        response = sendATCMD("AT+KSRAT=%s" % ksrat)
        if 'OK' in response:
            log.info("Valid response received")
        else:
            raise ValueError("Invalid response received from module: %s" % response)
        sleep(10)

        response = sendATCMD("AT+CFUN=1,1")
        if 'OK' in response:
            log.info("Valid response received")
        else:
            raise ValueError("Invalid response received from module: %s" % response)
        sleep(15)

    autotest.write()


def set_atip_host_settings(overrides):
    if not LEGATO_QA_CONFIGURED:
        log.info("ATIP testing not configured, skip setting host.xml")
        return

    log.info("Configure host server settings for atip tests")

    host = LeTPHostXML()
    iface = overrides['host']['iface']
    if (overrides['autotest']['network_type'] == '2g'):
        server_check = overrides['host']['2g_server_check']
        tcp_1_internal_url = overrides['host']['2g_tcp_1_internal_url']
        tcp_1_internal_ipv4 = overrides['host']['2g_tcp_1_internal_ipv4']
        tcp_1_internal_port = overrides['host']['2g_tcp_1_internal_port']
        udp_1_internal_url = overrides['host']['2g_udp_1_internal_url']
        udp_1_internal_ipv4 = overrides['host']['2g_udp_1_internal_ipv4']
        udp_1_internal_port = overrides['host']['2g_udp_1_internal_port']
    else:
        server_check = overrides['host']['server_check']
        tcp_1_internal_url = overrides['host']['tcp_1_internal_url']
        tcp_1_internal_ipv4 = overrides['host']['tcp_1_internal_ipv4']
        tcp_1_internal_port = overrides['host']['tcp_1_internal_port']
        udp_1_internal_url = overrides['host']['udp_1_internal_url']
        udp_1_internal_ipv4 = overrides['host']['udp_1_internal_ipv4']
        udp_1_internal_port = overrides['host']['udp_1_internal_port']

    host.set_network_if(iface)
    host.set_server_check(server_check)

    host.set_tcp1_port(tcp_1_internal_port)
    host.set_tcp_internal_1_url(tcp_1_internal_url)
    host.set_tcp_internal_1_ipv4(tcp_1_internal_ipv4)
    host.set_tcp_internal_1_port(tcp_1_internal_port)

    host.set_udp1_port(udp_1_internal_port)
    host.set_udp_internal_1_url(udp_1_internal_url)
    host.set_udp_internal_1_ipv4(udp_1_internal_ipv4)
    host.set_udp_internal_1_port(udp_1_internal_port)

    host.write()


def set_atip_ppp_settings(overrides):
    if not LEGATO_QA_CONFIGURED:
        log.info("ATIP testing not configured, skip setting ppp.xml")
        return

    log.info("Configure ppp settings for ATIP tests")

    ppp = LeTPpppXML()
    sudo = overrides['autotest']['sudo']
    iface = overrides['ppp']['iface']
    ppp_login = overrides['ppp']['ppp_login']
    ppp_password = overrides['ppp']['ppp_password']
    apn = overrides['ppp']['apn']
    apn_auth = overrides['ppp']['apn_auth']
    pdp = overrides['ppp']['pdp']
    pdp_auth = overrides['ppp']['pdp_auth']

    ppp.set_root_password(sudo)
    ppp.set_network_if(iface)
    ppp.set_ppp_login(ppp_login)
    ppp.set_ppp_password(ppp_password)
    ppp.set_apn(apn)
    ppp.set_apn_auth(apn_auth)
    ppp.set_pdp(pdp)
    ppp.set_pdp_auth(pdp_auth)

    ppp.write()


def set_atip_simdb_settings(overrides):
    if not LEGATO_QA_CONFIGURED:
        log.info("ATIP testing not configured, skip setting simdb.xml")
        return

    log.info("Configure SIM settings for ATIP tests")

    simdb = LeTPSimDBXML()
    network_type = overrides['autotest']['network_type']
    if network_type == "nb1":
        amarisoft_band = overrides['simdb']['amarisoft_band_nb1']
    else:
        amarisoft_band = overrides['simdb']['amarisoft_band_m1']
    amarisoft_imsi_prefix = overrides['simdb']['amarisoft_imsi_prefix']
    sierra_apn = overrides['simdb']['sierra_apn']
    sierra_pdp = overrides['simdb']['sierra_pdp']

    simdb.set_amarisoft_band(amarisoft_band)
    simdb.set_amarisoft_imsi_prefix(amarisoft_imsi_prefix)
    simdb.set_sierra_apn(sierra_apn)
    simdb.set_sierra_pdp(sierra_pdp)

    simdb.write()


def check_network_registration(overrides):
    autotest = LeTPAutotestXML()
    iccid = autotest.get_sim_ccid()
    sim_info = iccid_to_siminfo(iccid)
    network_type = overrides['autotest']['network_type']

    if not sim_info:
        log.warning("SIM Card Not Detected")
        warning_list.append("SIM Card is missing")
        return

    log.info("Checking %s Network Registration" % network_type.upper())
    AT_CMD_List_Net_Registration=["AT+CREG?","AT+CEREG?"]
    AT_RESP_List_Net_Registration=['+CREG: 2,1', '+CEREG: 2,1','+CREG: 2,5', '+CEREG: 2,5']

    sendATCMD("AT+CREG=2",False)

    sendATCMD("AT+CEREG=2",False)

    response = sendATCMD("AT+CREG?",False)

    for res in AT_RESP_List_Net_Registration:
        if res in response[1]:
            if network_type == "2g":
                response = sendATCMD("AT+CGACT=1,1")
                if not 'OK' in response:
                    break
            log.info("%s Network Registration Ready" % network_type.upper())
            return

    sendATCMD("AT+CFUN=1,1")
    sleep(20)

    # JLiang: Add for HL7812 module reset cannot register automatic.
    #sendATCMD("AT+CFUN=1")
    #sleep(5)

    #sendATCMD("AT+COPS=0")
    #sleep(5)


    i = 0
    while i< 10:
        log.info("--------Tried network connection number : %s --------" %str(i+1))
        j=0
        while j<len(AT_CMD_List_Net_Registration):
            response = sendATCMD(AT_CMD_List_Net_Registration[j],False)
            for res in AT_RESP_List_Net_Registration:
                result = res in response[1]
                if result:
                    if network_type == "2g":
                        response = sendATCMD("AT+CGACT=1,1")
                        if not 'OK' in response:
                            break
                    log.info("%s Network Registration Ready" % network_type.upper())
                    return
            # Check only CREG for 2G and allow more delay for network registration
            if network_type == "2g":
                sleep(5)
                break
            j=j+1
        sleep(3)
        i=i+1

    log.warning("%s Network Registration NOT Ready" % network_type.upper())
    warning_list.append("%s Network Registration is NOT Ready" % network_type.upper())

def unlock_module():
    global AT_UnlockWarningOn
    log.info("Unlocking module")
    response = sendATCMD("AT!UNLOCK=\"A710\"")
    if "OK" not in response:
        log.warning("AT Unlock not supported on current firmware")
        if not AT_UnlockWarningOn:
            warning_list.append("AT Unlock not supported on current firmware")
            AT_UnlockWarningOn = True

def set_usb_relay(overrides):
    relay = LeTPRelayXML()
    relay_port = overrides['numato']['relay_port']
    relay_num = overrides['numato']['relay_num']
    ctrl_relay_num = overrides['numato']['ctrl_relay_num']
    if relay_port:
        log.info("Setting relay port to %s" %relay_port)
        relay.set_relay_port(relay_port)

    if relay_num:
        log.info("Setting relay num to %s" %relay_num)
        relay.set_relay_num(relay_num)

    if ctrl_relay_num:
        log.info("Setting control relay num to %s" % ctrl_relay_num)
        relay.set_ctrl_relay_num(ctrl_relay_num)

    relay.write()

def check_otii():
    pass

def check_usb_relay():
    autotest = LeTPAutotestXML()
    target = LeTPTargetXML()
    uart_at = target.get_at()
    relay = LeTPRelayXML()
    relay_port = relay.get_relay_port()
    relay_num = relay.get_relay_num()

    if relay_powercycle(relay_port, relay_num, uart_at):
        autotest.set_usb_relay_availability('1')
        log.info("USB relay is available")
    else:
        autotest.set_usb_relay_availability('0')
        log.warning("USB relay is NOT available")

    autotest.write()

def check_otii():
    autotest = LeTPAutotestXML()
    target = LeTPTargetXML()
    uart_at = target.get_at()
    otii_device = create_otii()
    if otii_device:
        if otii_powercycle(otii_device, uart_at):
            autotest.set_otii_availability('1')
            log.info("OTII is available")
        else:
            autotest.set_otii_availability('0')
            log.warning("OTII is NOT available")
    else:
        autotest.set_otii_availability('0')
        log.warning("OTII is NOT available")

    autotest.write()

def sendATCMD(cmd, isstrip = True):
    target = LeTPTargetXML()

    uart_at = get_uart(target.get_at())
    if not uart_at:
        log.warning("AT port is not available for AT command")
        return None

    cmd += "\r\n"
    cmd = cmd.encode()

    uart_at.write(cmd)
    sleep(2)
    ATRsplst = []

    while 1:
        line = uart_at.readline()
        ATRsplst.append(line)
        if ('OK' in line.decode("utf-8") or 'ERROR' in line.decode("utf-8")):
            break

    if isstrip:
        response = strip_at_response(ATRsplst)
    else:
        response = list(map(lambda line: line.decode("utf-8"), ATRsplst))
        response = list(map(lambda line: line.strip(), response))
        response = list(filter(lambda line: len(line), response))
    uart_at.close()
    log.info(response)
    return response

# TODO: replace override boilerplate with a decorator?
def get_overrides():
    config = {
        'autotest': {},
        'target': {},
        'release': {},
        'host': {},
        'network': {},
        'ppp': {},
        'simdb': {},
        'upload': {},
        'numato': {}
    }

    def set_override(path, val):
        path = path.split('/')
        group = path[0]
        name = path[1]
        if val is not None:
            log.info('Overriding %s with %s' % (name, val))

        if name in config[group]:
            # Only overrite preexisting config if val has been set
            if val is not None:
                config[group][name] = val
        else:
            # Ensure config item exists (even if set to None)
            config[group][name] = val

    parser = argparse.ArgumentParser()
    autotest = parser.add_argument_group('autotest')

    log.info("Reading arguments")
    parser.add_argument("--config_file", help="Custom Config File Path")
    autotest.add_argument("--pin1_code", help="PIN1_CODE", type=int)
    autotest.add_argument("--puk1_code", help="PUK1_CODE", type=int)
    autotest.add_argument("--pin2_code", help="PIN2_CODE", type=int)
    autotest.add_argument("--puk2_code", help="PUK2_CODE", type=int)
    autotest.add_argument("--soft_version", help="SOFT_INI_Soft_Version")
    autotest.add_argument("--wdsd_version", help="SOFT_INI_Wdsd_Version")
    autotest.add_argument("--hard_ini", help="HARD_INI")
    autotest.add_argument("--sim_imsi", help="SIM_IMSI")
    autotest.add_argument("--sim_ccid", help="SIM_CCID")
    autotest.add_argument("--sim_voice_number", help="Voice_Number")
    autotest.add_argument("--phase", help="Features_PHASE", type=int)
    autotest.add_argument("--ksrat", help="Features_AT_KSRAT", type=int)
    autotest.add_argument("--ccid", help="Features_AT_CCID", type=int)
    autotest.add_argument("--pccid", help="Features_AT_percent_CCID", type=int)
    autotest.add_argument("--xatt", help="Features_AT_XATTMODE", type=int)
    autotest.add_argument("--autoflasher", help="Features_Autoflasher", type=int)
    autotest.add_argument("--sudo", help="Sudo password")
    autotest.add_argument("--clac_path", help="File path to swiserver_app_clac.h")
    autotest.add_argument("--sms_storage", help="Sms message storage capacity", type=int)
    autotest.add_argument("--amarisoft_address", help="amarisoft server address")
    autotest.add_argument("--amarisoft_ip", help="amarisoft server IP Address")
    autotest.add_argument("--device_ip", help="NDS ip address")
    autotest.add_argument("--local_avms_path", help="Path to local .ua file")
    autotest.add_argument("--local_avms99_path", help="Path to local 99.ua file")
    autotest.add_argument("--IntegrationVMServer", help="Integration VM Server IP")
    autotest.add_argument("--ftp_username", help="FTP server username")
    autotest.add_argument("--ftp_passwd", help="FTP server password")
    autotest.add_argument("--legato_flake_server", help="Legato Flake Server IP")
    autotest.add_argument("--flake_echo_port", help="Legato Flake Echo Port")
    autotest.add_argument("--flake_ftp_username", help="Legato Flake FTP Username")
    autotest.add_argument("--flake_ftp_passwd", help="Legato Flake FTP Password")

    autotest.add_argument("--network_name", help="Name of the sim network")
    autotest.add_argument("--long_network_name", help="Long name of the sim network")
    autotest.add_argument("--network_apn", help="Network APN")
    autotest.add_argument("--network_apn_login", help="Network APN username")
    autotest.add_argument("--network_apn_passwd", help="Network APN password")
    autotest.add_argument("--network_pdp_type", help="Network PDP type")
    autotest.add_argument("--network_max_pdp_context", help="Max Network PDP context")
    autotest.add_argument("--enabled_gpio", help="Enabled_GPIO")

    target = parser.add_argument_group('target')
    target.add_argument("--uart_at", help="AT Port")
    target.add_argument("--uart_cli", help="CLI Port")
    target.add_argument("--uart_mbim", help="MBIM Port")

    release = parser.add_argument_group('release')
    release.add_argument("--legato_version", help="legato_version")
    release.add_argument("--fw_version", help="fw_version")
    release.add_argument("--atswi", help="atSwi")
    release.add_argument("--uboot", help="UBOOT")
    release.add_argument("--mac", help="MAC")
    release.add_argument("--phy", help="PHY")

    host = parser.add_argument_group('host')
    host.add_argument("--ip_address",
                      help="IP of the default host network interface")
    host.add_argument("-iface",
                      help="Default host network interface")

    network = parser.add_argument_group('network')
    network.add_argument("--m1_bands", nargs="+",
                         help="List of m1 bands")
    network.add_argument("--nb1_bands", nargs="+",
                         help="List of nb1 bands")
    network.add_argument("--network_type", help="Type of the network: nb1/m1/2g")

    avms = parser.add_argument_group('avms')
    avms.add_argument("--avms_url",
                      help="AVMS URL")
    avms.add_argument("--avms_client_id",
                      help="AVMS client ID")
    avms.add_argument("--avms_client_secret",
                      help="AVMS client secret")
    avms.add_argument("--avms_company",
                      help="AVMS company")
    avms.add_argument("--avms_username", help="AVMS username")
    avms.add_argument("--avms_password", help="AVMS password")
    avms.add_argument("--avms_uid",
                      help="AVMS module UID")

    fota = parser.add_argument_group('fota')
    fota.add_argument("--fota_version", help="SOFT_INI_Fota_Version")
    fota.add_argument("--fota_sft_up_version", help="SOFT_INI_Fota_Sft_Up_Version")
    fota.add_argument("--fota_sft_down_version", help="SOFT_INI_Fota_Sft_Down_Version")

    fota.add_argument("--ref_version",
                      help="AutoAVMS_refVersion")
    fota.add_argument("--avms_zip_path",
                      help=("AVMSZipPath "
                            "(path to AVMS zip package to your current"
                            "firmware version)"))
    fota.add_argument("--avms_zip_path_to_test",
                      help=("AVMSZipPathToTest "
                            "(path to AVMS zip package to your current"
                            "firmware's test version)"))
    fota.add_argument("--avms_zip_path_from_test",
                      help=("AVMSZipPathFromTest "
                            "(path to AVMS zip package to your current"
                            "firmware from its test version)"))

    upload = parser.add_argument_group('upload')
    upload.add_argument("--host",
                        help=("Database for test uploads "
                              "(used to query FOTA information"))

    numato = parser.add_argument_group('numato')
    numato.add_argument("--relay_port", help="USB relay port")
    numato.add_argument("--relay_num", help="USB relay port number")
    numato.add_argument("--ctrl_relay_num", help="USB relay port number for PIN control")

    args = parser.parse_args()


    if (args.config_file):
        custome_config_path = os.path.expandvars('$LETP_WRAPPER_ROOT/%s' % args.config_file)
        if os.path.isfile(custome_config_path):
            log.info("Config file found at %s" % custome_config_path)
            log.info("Reading config yaml file for path %s" % LETP_CONFIG_PATH)
            config.update(yaml.load(open(custome_config_path, 'r'),
                                    Loader=yaml.BaseLoader))
    else:
        if os.path.isfile(LETP_CONFIG_PATH):
            log.info("Config file found at %s" % LETP_CONFIG_PATH)
            log.info("Reading config yaml file for path %s" % LETP_CONFIG_PATH)
            config.update(yaml.load(open(LETP_CONFIG_PATH, 'r'),
                                    Loader=yaml.BaseLoader))

    if LEGATO_QA_CONFIGURED:
        if os.path.isfile(LEGATO_QA_CONFIG_PATH):
            log.info("ATIP config file found at %s" % LEGATO_QA_CONFIG_PATH)
            log.info("Reading ATIP config yaml file for path %s" % LEGATO_QA_CONFIG_PATH)
            config.update(yaml.load(open(LEGATO_QA_CONFIG_PATH, 'r'),
                                    Loader=yaml.BaseLoader))

    set_override('autotest/pin1_code', args.pin1_code)
    set_override('autotest/puk1_code', args.puk1_code)
    set_override('autotest/pin2_code', args.pin2_code)
    set_override('autotest/puk2_code', args.puk2_code)
    set_override('autotest/soft_version', args.soft_version)
    set_override('autotest/wdsd_version', args.wdsd_version)
    set_override('autotest/hard_ini', args.hard_ini)
    set_override('autotest/sim_imsi', args.sim_imsi)
    set_override('autotest/sim_ccid', args.sim_ccid)
    set_override('autotest/sim_voice_number', args.sim_voice_number)
    set_override('autotest/phase', args.phase)
    set_override('autotest/ksrat', args.ksrat)
    set_override('autotest/ccid', args.ccid)
    set_override('autotest/pccid', args.pccid)
    set_override('autotest/xatt', args.xatt)
    set_override('autotest/autoflasher', args.autoflasher)
    set_override('autotest/SmsMessageStorage', args.sms_storage)
    set_override('autotest/amarisoft_address', args.amarisoft_address)
    set_override('autotest/amarisoft_ip', args.amarisoft_ip)
    set_override('autotest/sudo', args.sudo)
    set_override('autotest/device_ip', args.device_ip)
    set_override('autotest/local_avms_path', args.local_avms_path)
    set_override('autotest/local_avms99_path', args.local_avms99_path)
    set_override('autotest/IntegrationVMServer', args.IntegrationVMServer)
    set_override('autotest/ftp_username', args.ftp_username)
    set_override('autotest/ftp_passwd', args.ftp_passwd)
    set_override('autotest/legato_flake_server', args.legato_flake_server)
    set_override('autotest/flake_echo_port', args.flake_echo_port)
    set_override('autotest/flake_ftp_username', args.flake_ftp_username)
    set_override('autotest/flake_ftp_passwd', args.flake_ftp_passwd)
    set_override('autotest/clac_path', args.clac_path)

    set_override('autotest/network_name', args.network_name)
    set_override('autotest/long_network_name', args.long_network_name)
    set_override('autotest/network_apn', args.network_apn)
    set_override('autotest/network_apn_login', args.network_apn_login)
    set_override('autotest/network_apn_passwd', args.network_apn_passwd)
    set_override('autotest/network_pdp_type', args.network_pdp_type)
    set_override('autotest/network_max_pdp_context', args.network_max_pdp_context)
    set_override('autotest/enabled_gpio', args.enabled_gpio)

    set_override('target/uart_at', args.uart_at)
    set_override('target/uart_cli', args.uart_cli)
    set_override('target/uart_mbim', args.uart_mbim)

    set_override('release/legato_version', args.legato_version)
    set_override('release/fw_version', args.fw_version)
    set_override('release/atswi', args.atswi)
    set_override('release/uboot', args.uboot)
    set_override('release/mac', args.mac)
    set_override('release/phy', args.phy)

    set_override('host/ip_address', args.ip_address)
    set_override('host/network_if', args.iface)
    set_override('host/wwan_if', args.iface)

    set_override('network/m1_bands', args.m1_bands)
    set_override('network/nb1_bands', args.nb1_bands)
    set_override('autotest/network_type', args.network_type)

    set_override('autotest/avms_url', args.avms_url)
    set_override('autotest/avms_client_id', args.avms_client_id)
    set_override('autotest/avms_client_secret', args.avms_client_secret)
    set_override('autotest/avms_company', args.avms_company)
    set_override('autotest/avms_username', args.avms_username)
    set_override('autotest/avms_password', args.avms_password)
    set_override('autotest/avms_uid', args.avms_uid)

    set_override('autotest/fota_version', args.fota_version)
    set_override('autotest/fota_sft_up_version', args.fota_sft_up_version)
    set_override('autotest/fota_sft_down_version', args.fota_sft_down_version)
    set_override('autotest/ref_version', args.ref_version)
    set_override('autotest/avms_zip_path', args.avms_zip_path)
    set_override('autotest/avms_zip_path_to_test', args.avms_zip_path_to_test)
    set_override('autotest/avms_zip_path_from_test', args.avms_zip_path_from_test)

    set_override('upload/host', args.host)

    set_override('numato/relay_port', args.relay_port)
    set_override('numato/relay_num', args.relay_num)
    set_override('numato/ctrl_relay_num', args.ctrl_relay_num)

    return config


def main():
    overrides = get_overrides()
    set_uart_at(overrides)
    print("")
    set_usb_relay(overrides)
    print("")
    check_otii()
    print("")
    check_usb_relay()
    print("")
    # restore_default_settings(overrides)
    # print("")
    get_hard_ini(overrides)
    print("")
    unlock_module()
    print("")
    set_switracemode(overrides)
    print("")
    set_uart_cli(overrides)
    print("")
    get_soft_version(overrides)
    print("")
    set_wdsd_version(overrides)
    print("")
    set_fota_version(overrides)
    print("")
    get_imsi(overrides)
    print("")
    get_ccid(overrides)
    print("")
    set_sim_secrets(overrides)
    print("")
    set_unlock_sim(overrides)
    print("")
    get_release_info(overrides)
    print("")
    get_phase_info(overrides)
    print("")
    set_features_info(overrides)
    print("")
    set_default_kcarriercfg()
    print("")
    set_band_info(overrides)
    print("")
    set_module_network_type(overrides)
    print("")
    set_apn_info(overrides)
    print("")
    set_mbim_data_config(overrides)
    print("")
    set_clac(overrides)
    print("")
    set_ip_info(overrides)
    print("")
    set_sms_message_storage(overrides)
    print("")
    set_voice_number(overrides)
    print("")
    set_service_center_num(overrides)
    print("")
    set_avms_local_delta(overrides)
    print("")
    set_backup_info(overrides)
    print("")
    set_sudo(overrides)
    print("")
    set_avms_settings(overrides)
    print("")
    set_ftp_settings(overrides)
    print("")
    set_external_server(overrides)
    print("")
    set_amarisoft_address(overrides)
    print("")
    set_atip_host_settings(overrides)
    print("")
    set_atip_ppp_settings(overrides)
    print("")
    set_atip_simdb_settings(overrides)
    print("")
    check_network_registration(overrides)
    print("")
    set_sim_dns(overrides)
    print("")
    get_enabled_gpio(overrides)
    print("")
    unlock_module()
    print("")

if __name__ == '__main__':
    main()
    print("A SUMMARY OF SIM/NETWORK/MODULE WARNING AND ERROR ")
    for w in warning_list:
        log.warning(w)
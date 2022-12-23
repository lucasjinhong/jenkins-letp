from integration_libs.otii_tcp_client import otii_connection, otii_exception, otii
from integration_libs.hl78_uart import is_valid_at, get_uart
import os

from time import sleep
import logging

log = logging.getLogger("hl78_power_control")
log.setLevel(logging.DEBUG)
c_handler = logging.StreamHandler()
c_handler.setFormatter(
        logging.Formatter("[%(name)s][%(levelname)s]: %(message)s"))
log.addHandler(c_handler)

def relay_powercycle(relay_port, relay_num='0', uart_at=None):
    if not relay_port:
        log.error("Not able to power cycle with relay: relay not provided")
        return False

    if uart_at:
        log.info("USB Relay(%s num: %s): Power cycle the module and check AT port %s" %(relay_port, relay_num, uart_at))
        result = True
        for _ in range(3):
            run_relay_command(relay_port,relay_num, 'on')
            if is_valid_at(uart_at):
                log.error("AT port %s is still on after the module poweroff" %uart_at)
                log.error("Retry module power off...")
                result = False
            else:
                log.info("Module is powered off successfully")
                result = True
                break
    
        for _ in range(3):
            run_relay_command(relay_port,relay_num, 'off')
            if not is_valid_at(uart_at):
                log.error("AT port %s is still off after module poweron" %uart_at)
                log.error("Retry module power on...")
                result = False
            else:
                log.info("Module is powered on successfully")
                result = True
                break

        return result
    else:
        log.info("USB Relay(%s num: %s): Power cycle the module without AT port check" %(relay_port, relay_num))
        run_relay_command(relay_port,relay_num, 'on')
        run_relay_command(relay_port,relay_num, 'off')
        return False

# def run_relay_command(relay_port, relay_num='0', action='on'):
#     if action not in ["on", "off"]:
#         log.warning("incorrect usb relay action %s " %action )
#         return False
#     log.info("Turn %s USB relay (%s:%s)" %(action, relay_port, relay_num))
#     try:
#         for _ in range(5):
#             ser = get_uart(relay_port, at=False)
#             if not ser:
#                 sleep(5)
#                 continue

#             ser.write(b'\r')
#             if action == 'on':
#                 ser.write(b'relay on %d\r' %int(relay_num))
#                 sleep(10)
#             elif action == 'off':
#                 ser.write(b'relay off %d\r' %int(relay_num))
#                 sleep(35)
#             ser.close()
#             log.info("Successfully turn %s USB relay (%s:%s)" %(action, relay_port, relay_num))
#             return True
#         log.warning("Couldn't get valid USB relay (%s:%s)" %(relay_port, relay_num))
#         return False
#     except:
#         log.warning("Couldn't turn %s USB relay (%s:%s)" %(action, relay_port, relay_num))
#         pass
#     return False


def run_relay_command(relay_port, relay_num='0', action='on'):
    print("\nhl78_power_control.py This is run_relay_command action: ", action, "\n")
    if action not in ["on", "off"]:
        log.warning("incorrect usb relay action %s " %action )
        return False
    log.info("Turn %s USB relay (%s:%s)" %(action, relay_port, relay_num))
    try:
        for _ in range(5):
            print("This is for loop")
            # ser = get_uart(relay_port, at=False)
            # if not ser:
            #     print("\tStart to sleep\t")
            #     sleep(5)
            #     continue
            # ser.write(b'\r')
            
            if action == 'on':
                print("\t\taction is on\t\t")
                # ser.write(b'relay on %d\r' %int(relay_num))
                os.system('usbrelay A0001_1=1')
                sleep(10)
            elif action == 'off':
                print("\t\taction is off\t\t")
                # ser.write(b'relay off %d\r' %int(relay_num))
                os.system('usbrelay A0001_1=0')
                sleep(35)
            # ser.close()
            log.info("Successfully turn %s USB relay (%s:%s)" %(action, relay_port, relay_num))
            return True
        log.warning("Couldn't get valid USB relay (%s:%s)" %(relay_port, relay_num))
        return False
    except:
        log.warning("Couldn't turn %s USB relay (%s:%s)" %(action, relay_port, relay_num))
        pass
    return False


def create_otii(host = "127.0.0.1", port = 1905):
    connection = otii_connection.OtiiConnection(host, port)
    try:
        connect_response = connection.connect_to_server()
    except Exception as err:
        log.warning("OTII fails to connect to server")
        return None

    if connect_response["type"] == "error":
        log.warning("OTII receive response code with error code (%s:%s)" %(connect_response["errorcode"], connect_response["data"]["message"]))
        return None

    otii_object = otii.Otii(connection)
    devices = otii_object.get_devices()
    if len(devices) == 0:
        log.warning("OTII: No Arc connected!")
        return None

    my_arc = devices[0]
    my_arc.set_main_voltage(3.7)
    my_arc.set_exp_voltage(1.8)
    my_arc.set_main(True)
    my_arc.set_gpo(2, True)

    return my_arc

def otii_powercycle(otii_device, uart_at=None):

    if not otii_device:
        log.warning("OTII device is not available")
        return False

    if uart_at:
        log.info("OTII: Power cycle the module and check AT port %s" % uart_at)
        result = True
        # otii_device.set_main(False)
        otii_device.set_gpo(2, False)
        sleep(2)
        if is_valid_at(uart_at):
            log.error("AT port %s is still on after module poweroff" %uart_at)
            result = False
        # otii_device.set_main(True)
        otii_device.set_gpo(2, True)
        sleep(25)
        if not is_valid_at(uart_at):
            log.error("AT port %s is still off after module poweron" %uart_at)
            result = False
        return result
    else:
        log.info("OTII: Power cycle the module without AT port check")
        otii_device.set_main(False)
        sleep(2)
        otii_device.set_main(True)
        sleep(25)
        return False

def powercycle(relay_port, relay_num='0', uart_at=None):
    otii_device = create_otii()
    if not otii_device:
        log.info("Use USB relay to power cycle module")
        return relay_powercycle(relay_port, relay_num, uart_at)
    log.info("Use OTII to power cycle module")
    return otii_powercycle(otii_device, uart_at)
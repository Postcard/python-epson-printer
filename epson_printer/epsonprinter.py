import signal
from contextlib import contextmanager
import usb.core
import usb.util
import time



ESC = 27
GS = 29
FULL_PAPER_CUT = [
    GS,
    86,  # V
    0]   # \0
UNDERLINE_OFF = [
    ESC,
    45,    # -
    0]
BOLD_ON = [
    ESC,
    69,      # E
    1]
BOLD_OFF = [
    ESC,
    69,      # E
    0]
DEFAULT_LINE_SPACING = [
    ESC,
    50]   # 2
CENTER = [
    ESC,
    97,    # a
    1]
LEFT_JUSTIFIED = [
    ESC,
    97,    # a
    0]
RIGHT_JUSTIFIED = [
    ESC,
    97,    # a
    2]


def linefeed(lines=1):
    return [
        ESC,  # ESC
        100,  # d
        lines]


def underline_on(weight):
    return [
        ESC,
        45,    # -
        weight]


def set_line_spacing(dots):
    return [
        ESC,
        51,  # 3
        dots]


def set_text_size(width_magnification, height_magnification):
    if width_magnification < 0 or width_magnification > 7:
        raise Exception("Width magnification should be between 0(x1) and 7(x8)")
    if height_magnification < 0 or height_magnification > 7:
        raise Exception("Height magnification should be between 0(x1) and 7(x8)")
    n = 16 * width_magnification + height_magnification
    byte_array = [
        GS,
        33,   # !
        n]
    return byte_array


def set_print_speed(speed):
    byte_array = [
        GS,  # GS
        40,  # (
        75,  # K
        2,
        0,
        50,
        speed]
    return byte_array


def send_command_to_device(timeout=5000):
    """ decorator used to send the result of a command to the usb device"""
    def _send_command_to_device(func):
        def wrapper(*args, **kwargs):
            printer = args[0]
            byte_array = func(*args, **kwargs)
            printer.write_bytes(byte_array, timeout)
        return wrapper
    return _send_command_to_device


class TimeoutException(Exception): pass

@contextmanager
def time_limit(seconds):
    def signal_handler(signum, frame):
        raise TimeoutException, "Timed out!"
    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)



class EpsonPrinter:
    """ An Epson thermal printer based on ESC/POS"""

    printer = None

    def __init__(self, id_product):

        id_vendor = 0x04b8

        # Search device on USB tree and set is as printer
        self.device = usb.core.find(idVendor=id_vendor, idProduct=id_product)
        if self.device is None:
            raise ValueError("Printer not found. Make sure the cable is plugged in.")

        if self.device.is_kernel_driver_active(0):
            try:
                self.device.detach_kernel_driver(0)
            except usb.core.USBError as e:
                print("Could not detach kernel driver: %s" % str(e))

        configuration = self.device.get_active_configuration()
        interface = configuration[(0, 0)]

        def out_endpoint_match(ep):
            return usb.util.endpoint_direction(ep.bEndpointAddress) == usb.util.ENDPOINT_OUT

        self.out_endpoint = usb.util.find_descriptor(interface, custom_match=out_endpoint_match)

        def in_endpoint_match(ep):
            return usb.util.endpoint_direction(ep.bEndpointAddress) == usb.util.ENDPOINT_IN

        self.in_endpoint = usb.util.find_descriptor(interface, custom_match=in_endpoint_match)


    def write_bytes(self, byte_array, timeout=5000):
        msg = ''.join([chr(b) for b in byte_array])
        self.write(msg, timeout)

    def write(self, msg, timeout=5000):
        self.out_endpoint.write(msg, timeout=timeout)

    def read(self):
        try:
            return self.in_endpoint.read(self.in_endpoint.wMaxPacketSize)
        except usb.core.USBError as e:
            return None

    def blocking_read(self):
        while True:
            data = self.read()
            if len(data) > 0:
                return data[0]

    def flush_read(self):
        while True:
            data = self.read()
            if not data or len(data) == 0:
                break

    def print_text(self, msg):
        self.write(msg)

    @send_command_to_device()
    def linefeed(self, lines=1):
        """Feed by the specified number of lines."""
        return linefeed(lines)

    @send_command_to_device()
    def cut(self):
        """Full paper cut."""
        return FULL_PAPER_CUT

    @send_command_to_device()
    def underline_on(self, weight=1):
        """ Activate underline
         weight = 0     1-dot-width
         weight = 1     2-dots-width
        """
        return underline_on(weight)

    @send_command_to_device()
    def underline_off(self):
        return UNDERLINE_OFF

    @send_command_to_device()
    def bold_on(self):
        return BOLD_ON

    @send_command_to_device()
    def bold_off(self):
        return BOLD_OFF

    @send_command_to_device()
    def set_line_spacing(self, dots):
        """Set line spacing with a given number of dots.  Default is 30."""
        return set_line_spacing(dots)

    @send_command_to_device()
    def set_default_line_spacing(self):
        return DEFAULT_LINE_SPACING

    @send_command_to_device()
    def set_text_size(self, width_magnification, height_magnification):
        """Set the text size.  width_magnification and height_magnification can
        be between 0(x1) and 7(x8).
        """
        return set_text_size(width_magnification, height_magnification)

    @send_command_to_device()
    def center(self):
        return CENTER

    @send_command_to_device()
    def left_justified(self):
        return LEFT_JUSTIFIED

    @send_command_to_device()
    def right_justified(self):
        return RIGHT_JUSTIFIED

    @send_command_to_device()
    def set_print_speed(self, speed):
        return set_print_speed(speed)

    @send_command_to_device(timeout=1)
    def transmit_real_time_status(self, n):
        return [16, 4, n]

    def paper_present(self):
        self.flush_read()
        try:
            self.transmit_real_time_status(4)
            with time_limit(1):
                data = self.blocking_read()
                return data == 18
        except:
            return False








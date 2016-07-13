import usb.core
from functools import wraps


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

class EpsonPrinter:
    """ An Epson thermal printer based on ESC/POS"""

    printer = None

    def __init__(self, id_vendor, id_product, out_ep=0x01):
        """
        @param id_vendor  : Vendor ID
        @param id_product : Product ID
        @param interface : USB device interface
        @param in_ep     : Input end point
        @param out_ep    : Output end point
        """

        self.out_ep = out_ep

        # Search device on USB tree and set is as printer
        self.printer = usb.core.find(idVendor=id_vendor, idProduct=id_product)
        if self.printer is None:
            raise ValueError("Printer not found. Make sure the cable is plugged in.")

        if self.printer.is_kernel_driver_active(0):
            try:
                self.printer.detach_kernel_driver(0)
            except usb.core.USBError as e:
                print("Could not detatch kernel driver: %s" % str(e))

        try:
            self.printer.set_configuration()
            self.printer.reset()
        except usb.core.USBError as e:
            print("Could not set configuration: %s" % str(e))

    def write_this(func):
        """
        Decorator that writes the bytes to the wire
        """
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            byte_array = func(self, *args, **kwargs)
            self.write_bytes(byte_array)
        return wrapper

    def write_bytes(self, byte_array):
        msg = ''.join([chr(b) for b in byte_array])
        self.write(msg)

    def write(self, msg):
        self.printer.write(self.out_ep, msg, timeout=20000)

    def print_text(self, msg):
        self.write(msg)

    @write_this
    def linefeed(self, lines=1):
        """Feed by the specified number of lines."""
        return linefeed(lines)

    @write_this
    def cut(self):
        """Full paper cut."""
        return FULL_PAPER_CUT

    @write_this
    def underline_on(self, weight=1):
        """ Activate underline
         weight = 0     1-dot-width
         weight = 1     2-dots-width
        """
        return underline_on(weight)

    @write_this
    def underline_off(self):
        return UNDERLINE_OFF

    @write_this
    def bold_on(self):
        return BOLD_ON

    @write_this
    def bold_off(self):
        return BOLD_OFF

    @write_this
    def set_line_spacing(self, dots):
        """Set line spacing with a given number of dots.  Default is 30."""
        return set_line_spacing(dots)

    @write_this
    def set_default_line_spacing(self):
        return DEFAULT_LINE_SPACING

    @write_this
    def set_text_size(self, width_magnification, height_magnification):
        """Set the text size.  width_magnification and height_magnification can
        be between 0(x1) and 7(x8).
        """
        return set_text_size(width_magnification, height_magnification)

    @write_this
    def center(self):
        return CENTER

    @write_this
    def left_justified(self):
        return LEFT_JUSTIFIED

    @write_this
    def right_justified(self):
        return RIGHT_JUSTIFIED

    @write_this
    def set_print_speed(self, speed):
        return set_print_speed(speed)

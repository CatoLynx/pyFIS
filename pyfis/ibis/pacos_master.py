"""
Copyright (C) 2026 Julian Metzler

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

from .ibis_protocol import IBISProtocol
from ..utils.serial import ensure_serial_port


class PACOSMaster(IBISProtocol):
    """
    A PACOS bus master, sending and receiving telegrams. Defaults to serial port backend.
    """

    ATTR_ALIGN_RIGHT = 1
    ATTR_ALIGN_CENTER = 2
    ATTR_ALIGN_LEFT = 3
    ATTR_SCROLL_SLOW = 4
    ATTR_SWITCH_SLOW = 5
    ATTR_ROLL_SLOW = 6
    ATTR_SCROLL_FAST = 7
    ATTR_SWITCH_FAST = 8
    ATTR_ROLL_FAST = 9
    ATTR_SCROLL_VERTICAL_SLOW_ALIGN_RIGHT = 10
    ATTR_SCROLL_VERTICAL_SLOW_ALIGN_CENTER = 11
    ATTR_SCROLL_VERTICAL_SLOW_ALIGN_LEFT = 12
    ATTR_SCROLL_VERTICAL_FAST_ALIGN_RIGHT = 13
    ATTR_SCROLL_VERTICAL_FAST_ALIGN_CENTER = 14
    ATTR_SCROLL_VERTICAL_FAST_ALIGN_LEFT = 15

    INLINE_CHARSET = 0
    INLINE_SIZE = 1
    INLINE_CHAR_SPACING_ONCE = 2
    INLINE_CHAR_SPACING = 3
    INLINE_INVERT = 4
    INLINE_BOLD = 5
    INLINE_BLINK = 6
    INLINE_COLOR = 7
    INLINE_SPECIAL_CHAR = 8

    INLINE_DISABLE = 0
    INLINE_ENABLE = 1
    INLINE_BLINK_FAST = 1
    INLINE_BLINK_SLOW = 2
    
    def __init__(self, port, address, baudrate = 4800, bytesize = 7, parity = 'E',
                 stopbits = 1, timeout = 2.0, exclusive = True, *args, **kwargs):
        """
        port:
        The serial port to use for communication
        """
        
        super().__init__(*args, encoding='iso-8859-1', **kwargs)
        self.device = ensure_serial_port(port,
            baudrate = baudrate,
            bytesize = bytesize,
            parity = parity,
            stopbits = stopbits,
            timeout = timeout,
            exclusive=exclusive)
        self.address = address
        self.command_collection_active = False
        self.current_message = ""
    
    def _send(self, telegram):
        self.device.write(telegram)
    
    def _receive(self, length):
        return self.device.read(length)

    def __del__(self):
        self.device.close()
    
    def DS021_PACOS(self, message, reply_length = -1):
        """
        PACOS derivative of DS021
        
        message:
        The PACOS message

        reply_length:
        How many payload bytes to expect in the response. Defaults to -1 to read all available data.
        """
        
        length = len(message)
        return self.parse_DS120_PACOS(self.send_telegram("aA{}{:>02}{}"
            .format(self.vdv_hex(self.address),
                self.vdv_hex(length),
                message), reply_length=reply_length))

    def parse_DS120_PACOS(self, telegram):
        if not telegram:
            return None
        if len(telegram) > 3:
            reply = {'value': telegram[2:]}
        else:
            status = telegram[2]
            statuses = {
                '0': 'ok',
                '1': 'unknown_text_or_graphics_id',
                '2': 'unknown_attribute_or_mode_or_submode',
                '3': 'invalid_position',
                '4': 'text_cut_off',
                '5': 'message_format_error',
                '6': 'receive_buffer_full',
                '7': 'general_error',
                '8': 'error',
                '9': '',
                ':': 'parity_error',
                ';': 'incorrect_configuration',
                '<': 'overload',
                '=': 'custom_character_buffer_full',
                '>': '',
                '?': 'bootup',
            }
            reply = {
                'status': statuses.get(status, status)
            }
        return reply
    
    def read_status(self):
        """
        Display status query
        Reply: DS120 PACOS
        """
        
        return self.parse_DS120_PACOS(self.send_telegram("aA{}"
            .format(self.vdv_hex(self.address)), reply_length = -1))

    def _escape(self, text):
        """
        Replace block start character % with %%
        NOTE: $ also needs to be escaped to be displayed, but since
        we want to allow the user to use it as inline format control,
        we can't do that. This is the user's responsibility.
        """
        return text.replace("%", "%%")

    def pacos_message(self, message):
        if self.command_collection_active:
            if len(self.current_message + message) > 255:
                raise ValueError("Message length would exceed 255 characters")
            self.current_message += message
        else:
            return self.DS021_PACOS(message)

    def inline_format(self, text, format, value):
        """
        Apply inline format to the given text
        format: what to change, see INLINE_ definitions in this class
        value: specific to format, 0 to 15, or one of the INLINE_ definitions of this class
               For the INLINE_SPECIAL_CHAR format, value can be 128 to 255.

        NOTE: The format stays active until it is reset, even across text fields!

        Examples:
        inline_format("test", INLINE_BOLD, INLINE_ENABLE)
        inline_format("test", INLINE_INVERT, INLINE_DISABLE)
        inline_format("test", INLINE_CHAR_SPACING, 4)
        inline_format("test", INLINE_BLINK, INLINE_BLINK_FAST)
        """
        if format == self.INLINE_SPECIAL_CHAR:
            return f"${self.vdv_hex(format)}{self.vdv_hex(value, pad=True)}{text}"
        else:
            return f"${self.vdv_hex(format)}{self.vdv_hex(value)}{text}"

    def begin_command_list(self):
        self.command_collection_active = True
        self.current_message = ""

    def send_command_list(self):
        self.command_collection_active = False
        return self.DS021_PACOS(self.current_message)

    def define_field_simple(self, x_start, x_end, y_end, attribute):
        """
        Define a text field with pixel-based coordinates,
        giving left and right X coordinates and the bottom Y coordinate
        Coordinate range: 1 to 999
        attribute: see ATTR_ definitions in this class
        """
        message = f"%00{x_start:03d}{x_end:03d}{y_end:03d}{self.vdv_hex(attribute)}"
        return self.pacos_message(message)

    def define_field_row_based(self, row, field, attribute):
        """
        Define a text field with row-based coordinates,
        giving the row and field number
        Row range: 1 to 99
        Field range: 1 to 9
        attribute: see ATTR_ definitions in this class
        """
        message = f"%01{row:02d}{field}{self.vdv_hex(attribute)}"
        return self.pacos_message(message)

    def set_text_start_position(self, x, y):
        """
        Set start position for the following text, pixel-based
        Coordinate range: 1 to 999
        """
        message = f"%02{x:03d}{y:03d}"
        return self.pacos_message(message)

    def define_field_char_based(self, x_start, x_end, y_end, attribute):
        """
        Define a text field with character-based coordinates,
        giving left and right X coordinates and the bottom Y coordinate
        Coordinate range: 1 to 999
        attribute: see ATTR_ definitions in this class
        """
        message = f"%03{x_start:03d}{x_end:03d}{y_end:03d}{self.vdv_hex(attribute)}"
        return self.pacos_message(message)

    def define_field(self, x_start, x_end, y_start, y_end, attribute):
        """
        Define a text field with pixel-based coordinates,
        giving left and right X coordinates and the top and bottom Y coordinates
        Coordinate range: 1 to 999
        attribute: see ATTR_ definitions in this class
        """
        message = f"%04{x_start:03d}{x_end:03d}{y_start:03d}{y_end:03d}{self.vdv_hex(attribute)}"
        return self.pacos_message(message)

    def set_text_start_position_char_based(self, x, y):
        """
        Set start position for the following text, character-based
        Coordinate range: 1 to 999
        """
        message = f"%05{x:03d}{y:03d}"
        return self.pacos_message(message)

    def text(self, text):
        """
        Send text information
        Max text length: 245 characters
        """
        text = self._escape(text)
        if len(text) > 245:
            raise ValueError("Maximum text length is 245 characters")
        message = f"%10{text}"
        return self.pacos_message(message)

    def predefined_text(self, text_id):
        """
        Recall predefined text based on ID (1 to 999)
        """
        message = f"%11{text_id:03d}"
        return self.pacos_message(message)

    def predefined_graphics(self, graphics_id):
        """
        Recall predefined graphics based on ID (1 to 99)
        """
        message = f"%12{graphics_id:02d}"
        return self.pacos_message(message)

    def clock(self, mode):
        """
        Display current time
        Mode: 1="hh:mm", 2="hh.mm", 3="hh:mm.ss", 4="hh:mm:ss"
        """
        message = f"%13{mode}"
        return self.pacos_message(message)

    def clear_area(self, x_start, y_start, x_end, y_end):
        """
        Clear a rectangular area,
        giving left and right X coordinates and the top and bottom Y coordinates
        Coordinate range: 1 to 999
        """
        message = f"%20{x_start:03d}{y_start:03d}{x_end:03d}{y_end:03d}"
        return self.pacos_message(message)

    def clear_row_based(self, row, field):
        """
        Clear a row,
        giving the row and field number
        Row range: 1 to 99
        Field range: 1 to 9, or 0 to clear the entire row
        """
        message = f"%21{row:02d}{field}"
        return self.pacos_message(message)

    def clear_row(self, y_end):
        """
        Clear an entire row,
        giving the bottom Y coordinate.
        Coordinate range: 1 to 999
        """
        message = f"%22{y_end:03d}"
        return self.pacos_message(message)

    def clear_display(self):
        """
        Clear the entire display
        This does not reset active format attributes!
        """
        message = "%23"
        return self.pacos_message(message)

    def clear_area_char_based(self, x_start, y_start, x_end, y_end):
        """
        Clear a rectangular area with character-based coordinates,
        giving left and right X coordinates and the bottom Y coordinate
        Coordinate range: 1 to 999
        """
        message = f"%24{x_start:03d}{y_start:03d}{x_end:03d}{y_end:03d}"
        return self.pacos_message(message)

    def set_time(self, time):
        """
        Set system time.
        time must be something that implements strftime()
        """
        message = f"%30{time.strftime('%H%M%S')}"
        return self.pacos_message(message)

    def set_background_buffer(self, mode):
        """
        Control writing to the background buffer.
        0 = Everything up to the next CR will be written to the background buffer
            (only makes sense if combined with other messages in the same telegram)
        1 = Display background buffer
        2 = Everything from now on will be written to the background buffer
        """
        message = f"%31{mode}"
        return self.pacos_message(message)

    def init_display(self):
        """
        Initialize the display
        Clears the display and sets default attributes
        """
        message = "%32"
        return self.pacos_message(message)

    def set_standby_mode(self, mode):
        """
        Switch between standby or normal mode.
        True = Standby, False = Normal
        """
        message = f"%33{int(mode)}"
        return self.pacos_message(message)

    def set_night_mode(self, mode):
        """
        Switch between night or day mode.
        True = Night, False = Day
        """
        message = f"%34{int(mode)}"
        return self.pacos_message(message)

    def show_special_screen(self):
        """
        Show the special screen
        Clears the display, sets default attributes and shows the special screen
        """
        message = "%35"
        return self.pacos_message(message)

    def set_default_attributes(self, text):
        """
        Sets the default text attributes
        It's unclear how exactly this is used!
        """
        message = f"%36{text}"
        return self.pacos_message(message)

    def horizontal_line(self, x_start, x_end, y, width):
        """
        Show a horizontal line,
        giving left and right X coordinates, the Y coordinate and the width in pixels
        Coordinate range: 1 to 999
        """
        message = f"%40{x_start:03d}{x_end:03d}{y:03d}{width}"
        return self.pacos_message(message)

    def vertical_line(self, x, y_start, y_end, width):
        """
        Show a vertical line,
        giving the X coordinate, the top and bottom Y coordinates and the width in pixels
        Coordinate range: 1 to 999
        """
        message = f"%41{x:03d}{y_start:03d}{y_end:03d}{width}"
        return self.pacos_message(message)

    def rectangle(self, x_start, x_end, y_start, y_end):
        """
        Show an outlined rectangle with 1 pixel width,
        giving the left and right X coordinates and the top and bottom Y coordinates
        Coordinate range: 1 to 999
        """
        message = f"%42{x_start:03d}{x_end:03d}{y_start:03d}{y_end:03d}"
        return self.pacos_message(message)

    def recall_configuration(self, config_id):
        """
        Recall a predefined configuration with the given ID (1 to 999)
        """
        message = f"%50{config_id:03d}"
        return self.pacos_message(message)

    def recall_configuration_with_blank_field_0(self, config_id):
        """
        Recall a predefined configuration with the given ID (1 to 999)
        and set a blank text in field 0
        """
        message = f"%51{config_id:03d}"
        return self.pacos_message(message)

    def check_config_availability(self, config_id, version):
        """
        Check if a configuration with the given ID (1 to 999)
        and the given version (1 to 99) is available
        """
        message = f"%60{config_id:03d}{version:02d}"
        return self.pacos_message(message)

    def send_config(self, config_id, version, block, data):
        """
        Send a configuration with the given ID (1 to 999)
        and the given version (1 to 99) and block number (1 to 999)
        to the display
        Max data length: 246 characters
        """
        if len(data) > 246:
            raise ValueError("Maximum data length is 246 characters")
        message = f"%61{config_id:03d}{version:02d}{block:03d}{data}"
        return self.pacos_message(message)

    def set_master_timeout(self, timeout):
        """
        Set the master timeout in seconds (1 to 999, or 0 to disable)
        After this timeout, the display will show its fallback text
        """
        message = f"%70{timeout:03d}"
        return self.pacos_message(message)

    def set_protocol_timeout(self, timeout):
        """
        Set the protocol timeout in milliseconds (1 to 999)
        """
        message = f"%71{timeout:03d}"
        return self.pacos_message(message)

    def set_page_switch_interval(self, interval):
        """
        Set page switch interval in seconds (0 to 999)
        """
        message = f"%72{interval:03d}"
        return self.pacos_message(message)

    def set_parameters(self, slow_scroll_speed, fast_scroll_speed, slow_switch_interval, fast_switch_interval, *params):
        """
        Set parameters
        The first 4 parameters are the scroll speeds for slow and fast scroll texts
        and the switch intervals for slow and fast switching texts.
        Further parameters are manufacturer specific and can be specified using the params parameter.
        All parameters must be in the range 0 to 255!
        """
        parameters = [slow_scroll_speed, fast_scroll_speed, slow_switch_interval, fast_switch_interval] + params
        message = f"%74{len(parameters):02d}"
        for parameter in parameters:
            message += self.vdv_hex(parameter, pad=True)
        return self.pacos_message(message)

    def delete_data(self, mode):
        """
        Delete stored data
        0 = delete texts, fields and custom characters
        1 = delete texts
        2 = delete fields
        3 = delete custom characters
        """
        message = f"%80{mode}"
        return self.pacos_message(message)

    def store_text(self, text_id, text):
        """
        Store a text (ID 1 to 999) to be recalled later
        """
        message = f"%81{text_id:03d}{self._escape(text)}"
        return self.pacos_message(message)

    def store_field(self, field_id, x_start, x_end):
        """
        Store a field (ID 1 to 9) to be recalled later
        """
        message = f"%82{field_id}{x_start:03d}{x_end:03d}"
        return self.pacos_message(message)

    def store_custom_character(self, font_id, size, char_id, data):
        """
        Store a custom character for the given font ID (1 to 9), size (1 to 15)
        and character ID (32 to 255)
        Data is a series of 1 to 98 bytes, the format of which is manufacturer specific.
        """
        message = f"%83{font_id}{self.vdv_hex(size)}00{char_id:03d}{len(data):02d}"
        for byte in data:
            message += self.vdv_hex(byte, pad=True)
        return self.pacos_message(message)

    def delete_fallback_slot(self, slot):
        """
        Delete a single storage slot of the fallback data (1 to 8, or 0 to delete all slots)
        This command must be at the beginning of a message!
        """
        message = f"%84{slot}"
        return self.pacos_message(message)

    def read_fallback_slot(self, slot):
        """
        Read a single storage slot of the fallback data
        This command must be at the beginning of a message!
        To read the actual response value, call read_status() after sending this message.
        """
        if self.command_collection_active:
            raise NotImplementedError("read_storage_cell can not be combined with other commands")
        message = f"%85{slot}"
        return self.DS021_PACOS(message, reply_length=-1)

    def write_fallback_slot(self, slot, message):
        """
        Write into a single storage slot of the fallback data (1 to 8)
        message is a PACOS message consisting of block modes %0, %1, %2 or %4 only.
        This command must be at the beginning of a message!
        """
        _message = f"%86{slot}{message}"
        return self.pacos_message(_message)

    def read_version(self):
        """
        Read the software version of the display
        To read the actual response value, call read_status() after sending this message.
        """
        if self.command_collection_active:
            raise NotImplementedError("read_version can not be combined with other commands")
        message = f"%90"
        return self.DS021_PACOS(message, reply_length=-1)

    def self_test(self):
        """
        Run a display self-test
        """
        message = "%:0"
        return self.pacos_message(message)

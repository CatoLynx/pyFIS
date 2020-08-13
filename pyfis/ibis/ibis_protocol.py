"""
Copyright (C) 2016 - 2020 Julian Metzler

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

import math

class IBISProtocol:
    """
    All the logic related to the IBIS protocol
    """
    
    def __init__(self, debug = False):
        """
        debug:
        Whether to print the sent and received telegrams
        """
        
        self.debug = debug
        
        # Simple telegram definitions
        self.DS001 = self._tg("l{:>03}")        # Line number, 1-4 digits
        self.DS001neu = self._tg("q{:0>4}")     # Line number, alphanumeric, 1-4 chars
        self.DS001a = self._tg("qE{:02d}")      # Line number symbol ID, 1-2 digit
        self.DS001b = self._tg("lF{:05d}")      # Radio
        self.DS001c = self._tg("lP{:03d}")      # Line tape reel position ID, 1-3 digit
        self.DS001d = self._tg("lC{:0>4}")      # Line number, alphanumeric, 1-4 chars
        self.DS001e = self._tg("lC{:0>8}")      # Line number, alphanumeric, 1-8 chars
        self.DS001f = self._tg("lB{:0>7}")      # Line number, alphanumeric, 1-7 chars
        self.DS002 = self._tg("k{:02d}")        # Course number, 1-2 digits
        self.DS002a = self._tg("k{:05d}")       # Train number, 1-5 digits
        self.DS003 = self._tg("z{:03d}")        # Destination text ID, 1-3 digit
        self.DS003b = self._tg("zR{:03d}")      # Destination ID for IMU, 1-3 digits
        self.DS003d = self._tg("zN{:03d}")      # Route number, 1-3 digits
        self.DS003e = self._tg("zP{:03d}")      # Destination tape reel position ID, 1-3 digit
        self.DS003f = self._tg("zN{:06d}")      # Route number, 1-6 digits
        self.DS003g = self._tg("zL{:04d}")      # Line number, 1-4 digits
        self.DS004 = self._tg("e{:06d}")        # Ticket validator attributes, 6 digits
        self.DS004a = self._tg("eA{:04d}")      # Additional ticket validator attributes, 4 digits
        self.DS004b = self._tg("eH{:07d}")      # Ticket validator stop number, 1-7 digits
        self.DS005 = self._tg("u{:04d}")        # Time, HHMM
        self.DS006 = self._tg("d{:05d}")        # Date, DDMMY
        self.DS007 = self._tg("w{:01d}")        # Train length, 1 digit
        self.DS009 = self._tg("v{: <16}")       # Next stop text, 16 characters
        self.DS009a = self._tg("v{: <20}")      # Next stop text, 20 characters
        self.DS009b = self._tg("v{: <24}")      # Next stop text, 24 characters
        self.DS010 = self._tg("x{:04d}")        # Line progress display stop ID, 1-4 digits
        self.DS010a = self._tg("xH{:04d}")      # Line progress display stop ID, 1-4 digits
        self.DS010b = self._tg("xI{:02d}")      # Line progress display stop ID, 1-2 digits
        self.DS010d = self._tg("xJ{:04d}")      # Year, YYYY
        self.DS010e = self._tg("xV{}{:03d}")    # Delay, +/-, 1-3 digits
    
    def _send(self, telegram):
        """
        Actually send the telegram.
        This varies depending on implementation and needs to be overridden
        """
        pass
    
    def _receive(self, length):
        """
        Actually receive data.
        This varies depending on implementation and needs to be overridden
        """
        pass

    def _printable(self, char):
        """
        Replace non-printable chars with printable variants.
        """
        if char in range(0, 32):
            return "<{:02X}>".format(char)
        else:
            return chr(char)
    
    def debug_telegram(self, telegram, receive = False):
        """
        Print a telegram to standard output if the debug flag is set.
        
        telegram:
        The telegram to print
        
        receive:
        Whether to print the telegram as sent or received
        """
        
        if self.debug:
            action = "Received" if receive else "Sending"
            telegram_debug = "\n".join("{:02X} {}".format(
                byte, self._printable(byte)) for byte in telegram)
            print("{} telegram:\n".format(action))
            print(telegram_debug)
    
    def process_special_characters(self, telegram):
        """
        Replace IBIS special characters and strip unsupported characters.
        
        telegram:
        The telegram as a string
        
        Returns:
        The processed telegram
        """
        
        telegram = telegram.replace("ä", "{")
        telegram = telegram.replace("ö", "|")
        telegram = telegram.replace("ü", "}")
        telegram = telegram.replace("ß", "~")
        telegram = telegram.replace("Ä", "[")
        telegram = telegram.replace("Ö", "\\")
        telegram = telegram.replace("Ü", "]")
        telegram = telegram.encode('ascii', errors = 'replace')
        return telegram
    
    def wrap_telegram(self, telegram):
        """
        Append the checksum and the end byte to the given telegram.
        
        telegram:
        The telegram (as a bytearray) to wrap
        
        Returns:
        The wrapped telegram (as a bytearray)
        """
        
        telegram.append(0x0D)
        checksum = 0x7F
        for byte in telegram:
            checksum ^= byte
        telegram.append(checksum)
        return telegram
    
    def send_telegram(self, telegram, reply_length = 0):
        """
        Send an arbitrary telegram. Checksum and end byte will be added.
        
        telegram:
        The telegram to send
        
        reply_length:
        How many bytes to expect as a reply
        
        Returns:
        The received telegram OR None
        
        TODO: Actually check the checksum
        """
        
        if type(telegram) is str:
            telegram = self.process_special_characters(telegram)
            telegram = bytearray(telegram)
        elif type(telegram) is bytes:
            telegram = bytearray(telegram)
        
        telegram = self.wrap_telegram(telegram)
        self.debug_telegram(telegram)
        self._send(telegram)
        if reply_length:
            reply = self._receive(reply_length + 2)
            self.debug_telegram(reply, receive = True)
            reply = reply[:-2]
            return reply.decode('latin1')
    
    def vdv_hex(self, value):
        """
        Convert a numerical value into the VDV hexadecimal representation
        
        value:
        The value to convert (0 to 255) OR a VDV Hex value to convert back
        
        Returns:
        The VDV Hex value OR the integer for the VDV Hex value
        """
        
        vdvhex = "0123456789:;<=>?"
        if type(value) is int:
            assert 0 <= value <= 255
            if value > 15:
                high_nibble = value >> 4
                low_nibble = value % 16
                return vdvhex[high_nibble] + vdvhex[low_nibble]
            else:
                return vdvhex[value]
        else:
            assert 1 <= len(value) <= 2
            if len(value) == 2:
                high_nibble = vdvhex.index(value[0])
                low_nibble = vdvhex.index(value[1])
                return high_nibble << 4 + low_nibble
            else:
                return vdvhex.index(value)
    
    def _tg(self, fmt, reply_length = 0):
        """
        Wrapper for simple telegrams with just variables
        
        fmt:
        The format string for the telegram
        
        reply_length:
        As in send_telegram
        """
        
        def _send(*args):
            return self.send_telegram(fmt.format(*args),
                reply_length = reply_length)
        
        return _send
    
    def DS003a(self, text):
        """
        Destination text
        
        text:
        The destination text
        """
        
        num_blocks = math.ceil(len(text) / 16)
        return self.send_telegram("zA{}{}"
            .format(self.vdv_hex(num_blocks), text.ljust(num_blocks*16)))
    
    def DS003aUESTRA(self, front_text, side_text = "", line_text = "",
        display_line_text_front = True, display_line_text_side = True,
        display_interval_front = 3.0, display_interval_side = 3.0,
        text_align_front = "M", text_align_side = "M",
        bold_text_front = True, bold_text_side = True):
        """
        Destination text for ÜSTRA displays
        
        front_text:
        The destination text for the front display
        (string or array of up to 4 strings to be displayed sequentially)

        side_text:
        The destination text for the side display
        (string or array of up to 4 strings to be displayed sequentially)

        line_text:
        The line number (string, alphanumerical)

        display_line_text_front:
        Whether to display line number on the front display
        (bool or array of up to 4 bools to set line number display
        per text block)

        display_line_text_side:
        Whether to display line number on the side display
        (bool or array of up to 4 bools to set line number display
        per text block)
        
        display_interval_front:
        Interval for switching between sequential text blocks in seconds
        on the front display (1.0 ... 8.5 seconds, in 0.5 second steps)
        
        display_interval_side:
        Interval for switching between sequential text blocks in seconds
        on the side display (1.0 ... 8.5 seconds, in 0.5 second steps)
        
        text_align_front:
        Text align for front text. (L=Left, M=Middle, R=Right)
        
        text_align_side:
        Text align for side text. (L=Left, M=Middle, R=Right)
        
        bold_text_front:
        Whether text should be bold or thin on the front display.
        (bool or array of bools for block 1 line 1, block 1 line 2,
        block 2 line 1, block 2 line 2, etc. up to block 4 line 2)
        
        bold_text_side:
        Whether text should be bold or thin on the side display.
        (bool or array of bools for block 1 line 1, block 1 line 2,
        block 2 line 1, block 2 line 2, etc. up to block 4 line 2)
        """

        def _insert_case_switch_control_chars(text):
            """
            Insert the case-switching control character 0x06 in the given text
            to switch between upper and lower case
            """
            if not text:
                return ""
            ret_text = ""
            is_lower = False # Keep track of the current case
            for char in text:
                if not is_lower and ord(char) in range(0x60, 0x80):
                    ret_text += chr(0x06)
                    is_lower = True
                if is_lower and ord(char) in range(0x40, 0x60):
                    ret_text += chr(0x06)
                    is_lower = False
                if char == "\n":
                    is_lower = False
                ret_text += char.upper()
            if is_lower:
                # Make sure we are back to upper
                ret_text += chr(0x06)
            return ret_text
        
        def _array_to_byte(array):
            """
            Convert a bool array to a byte with the corresponding bits set
            """
            byte = 0x00
            for i, val in enumerate(array):
                byte |= (int(val) << i)
            return byte
        
        if type(front_text) in (bytes, str):
            front_text = [front_text]
        if type(side_text) in (bytes, str):
            side_text = [side_text]
        if type(display_line_text_front) is bool:
            display_line_text_front = [display_line_text_front] * 4
        if type(display_line_text_side) is bool:
            display_line_text_side = [display_line_text_side] * 4
        if type(bold_text_front) is bool:
            bold_text_front = [bold_text_front] * 8
        if type(bold_text_side) is bool:
            bold_text_side = [bold_text_side] * 8
        
        display_interval_front = max(1.0, display_interval_front)
        display_interval_front = min(display_interval_front, 8.5)
        display_interval_front = round(display_interval_front * 2) - 2 # 0 to 15
        
        display_interval_side = max(1.0, display_interval_side)
        display_interval_side = min(display_interval_side, 8.5)
        display_interval_side = round(display_interval_side * 2) - 2 # 0 to 15
        
        front_text_lines = [a + [""] * (2-len(a)) for a in [_insert_case_switch_control_chars(t).splitlines() for t in front_text]]
        side_text_lines = [a + [""] * (2-len(a)) for a in [_insert_case_switch_control_chars(t).splitlines() for t in side_text]]
        line_text = _insert_case_switch_control_chars(line_text)
        
        data = ""
        for lines in front_text_lines:
            data += "\n.W{}\n{}\n".format(lines[0], lines[1])
        for lines in side_text_lines:
            data += "\n.X{}\n{}\n".format(lines[0], lines[1])
        data += "\n.Y{}\n".format(line_text)
        data += "\n.C"
        data += chr(0x30 + _array_to_byte(display_line_text_front))
        data += chr(0x30 + _array_to_byte(display_line_text_side))
        data += chr(0x30 + display_interval_front)
        data += chr(0x30 + display_interval_side)
        data += text_align_front
        data += text_align_side
        data += "M"
        data += chr(0x20 + _array_to_byte(bold_text_front[0:6]))
        data += chr(0x20 + _array_to_byte(bold_text_front[6:8] + bold_text_side[0:4]))
        data += chr(0x20 + _array_to_byte(bold_text_side[4:8]))
        
        num_blocks = math.ceil(len(data) / 4)
        return self.send_telegram("zA{:>02}{}"
            .format(self.vdv_hex(num_blocks), data.ljust(num_blocks*4)))
    
    def DS003c(self, text):
        """
        Next stop text
        
        text:
        The next stop text
        """
        
        num_blocks = math.ceil(len(text) / 4)
        return self.send_telegram("zI{}{}"
            .format(self.vdv_hex(num_blocks), text.ljust(num_blocks*4)))
    
    def DS004c(self, text):
        """
        Stop text for ticket validators / ticket vending machines
        
        text:
        The stop text
        """
        
        num_blocks = math.ceil(len(text) / 4)
        return self.send_telegram("eT{}{}"
            .format(self.vdv_hex(num_blocks), text.ljust(num_blocks*4)))
    
    def DS010c(self, stop_id):
        """
        Next stop ID for line progress display
        
        stop_id:
        The ID of the next stop, 1-2 digits
        """
        
        stop_id_high_nibble = stop_id >> 4
        stop_id_low_nibble = stop_id & 0x0F
        return self.send_telegram("xZ{}{}"
            .format(self.vdv_hex(stop_id_high_nibble),
                self.vdv_hex(stop_id_low_nibble)))
    
    def DS010f(self, stop_id, change_text):
        """
        Connection information for line progress display
        
        stop_id:
        The ID of the next stop, 1-2 digits
        
        change_text:
        Connection information
        """
        
        stop_id_high_nibble = stop_id >> 4
        stop_id_low_nibble = stop_id & 0x0F
        length_high_nibble = len(change_text) >> 4
        length_low_nibble = len(change_text) & 0x0F
        return self.send_telegram("xU{}{}{}{}{}"
            .format(self.vdv_hex(stop_id_high_nibble),
                self.vdv_hex(stop_id_low_nibble),
                self.vdv_hex(length_high_nibble),
                self.vdv_hex(length_low_nibble),
                change_text))
    
    def DS020(self, address):
        """
        Display status query
        Reply: DS120
        
        address:
        The address of the display
        """
        
        return self.parse_DS120(self.send_telegram("a{}"
            .format(self.vdv_hex(address)), reply_length = 2))
    
    def parse_DS120(self, telegram):
        if not telegram:
            return None
        status = telegram[1]
        statuses = {
            '0': 'ok',
            '1': 'displaying',
            '2': 'searching',
            '3': 'error',
            '6': 'input_implausible'
        }
        reply = {
            'status': statuses.get(status, status)
        }
        return reply
    
    def DS201(self, address):
        """
        Display version query
        Reply: DS1201
        
        address:
        The address of the display
        """
        
        return self.parse_DS1201(self.send_telegram("aV{}"
            .format(self.vdv_hex(address)), reply_length = 8))
    
    def parse_DS1201(self, telegram):
        if not telegram:
            return None
        version = telegram[2:]
        reply = {
            'version': version
        }
        return reply
    
    def DS021(self, address, text):
        """
        Destination text
        
        address:
        The address of the display
        
        text:
        The destination text
        """
        
        num_blocks = math.ceil(len(text) / 16)
        return self.send_telegram("aA{}{}{}"
            .format(self.vdv_hex(address),
                self.vdv_hex(num_blocks),
                text.ljust(num_blocks*16)))
    
    def DS021a(self, address, stop_id, stop_text, change_text):
        """
        Line progress display texts
        
        address:
        The address of the display
        
        stop_id:
        The ID of the stop to send data for
        
        stop_text:
        The name of the stop
        
        change_text:
        Connection information
        """
        
        data = "\x03{:>02}\x04{}\x05{}".format(
            stop_id, stop_text, change_text)
        num_blocks, remainder = divmod(len(data), 16)
        return self.send_telegram("aL{}{}{}{}"
            .format(self.vdv_hex(address),
                self.vdv_hex(num_blocks),
                self.vdv_hex(remainder),
                data))

    def DS021t(self, address, text):
        """
        Destination text

        address:
        The address of the display

        text:
        The destination text
        """

        num_blocks = math.ceil(len(text) / 16)
        if '\n' not in text:
            text = text + '\n'
        return self.send_telegram("aA{}{}A0{}\n\n  "
            .format(self.vdv_hex(address),
                self.vdv_hex(num_blocks),
                text))
    
    def DS060(self, direction):
        """
        Query locating device status
        Reply: DS160
        
        direction:
        Either A, B or C
        """
        
        return self.parse_DS160(self.send_telegram("o{}S"
            .format(direction), reply_length = 3))
    
    def parse_DS160(self, telegram):
        if not telegram:
            return None
        status = telegram[2]
        statuses = {
            '0': 'ok_no_information',
            '1': 'information_read',
            '2': 'new_information'
        }
        reply = {
            'status': statuses.get(status, status)
        }
        return reply
    
    def DS601(self, direction):
        """
        Query locating device version
        Reply: DS1601
        
        direction:
        Either A, B or C
        """
        
        return self.parse_DS1201(self.send_telegram("o{}V"
            .format(direction), reply_length = 18))
    
    def parse_DS1601(self, telegram):
        if not telegram:
            return None
        version = int(telegram[2:])
        reply = {
            'version': version
        }
        return reply
    
    def DS061(self, direction):
        """
        Query locating device data
        Reply: DS161
        
        direction:
        Either A, B or C
        """
        
        return self.parse_DS161(self.send_telegram("o{}D"
            .format(direction), reply_length = 10))
    
    def parse_DS161(self, telegram):
        if not telegram:
            return None
        beacon_id_vdvhex = telegram[2:]
        beacon_id = 0x00
        for n in range(8):
            char = beacon_id_vdvhex[n]
            beacon_id |= self.vdv_hex(char) << ((7 - n) * 4)
        reply = {
            'beacon_id': beacon_id
        }
        return reply
    
    def DS068(self, channel, radio_telegram_type, delay, reporting_point_id, hand, line_number, course_number, destination_id, train_length):
        """
        Send an LSA radio telegram
        """
        
        radio_telegram = "{}{}{:02d}{}{}{:0>4}{}{:03d}{:02d}{:03d}{}".format(
            self.vdv_hex(channel),
            self.vdv_hex(0),
            radio_telegram_type,
            self.vdv_hex(delay),
            self.vdv_hex(6), # Number of extra bytes
            reporting_point_id,
            self.vdv_hex(hand),
            line_number,
            course_number,
            destination_id,
            self.vdv_hex(train_length)
        )
        return self.parse_DS160(self.send_telegram("oFM{}{}"
            .format(self.vdv_hex(math.ceil(len(radio_telegram) / 2)),
                radio_telegram), reply_length = 3))
    
    def GSP(self, address, line1 = "", line2 = ""):
        """
        Send GSP display data
        Reply: DS120
        
        address:
        The address of the display
        
        line1:
        The top line text
        
        line2:
        The bottom line text
        """
        
        lines = ""
        if line2:
            line1 += "\x0a" # Line feed (LF)
        lines += line1
        lines += line2
        lines += "\x0a\x0a"
        
        num_blocks = math.ceil(len(lines) / 16)
        remainder = len(lines) % 16
        if remainder:
            filler = " " * (16 - remainder)
        else:
            filler = ""
        
        data = "aA{address}{num_blocks}{lines}{filler}".format(
            address = self.vdv_hex(address),
            num_blocks = self.vdv_hex(num_blocks),
            lines = lines,
            filler = filler)
        
        return self.parse_DS120(self.send_telegram(data, reply_length = 2))
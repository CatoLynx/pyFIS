"""
Copyright (C) 2020 Julian Metzler

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


import socket


class MigraTCP:
    """
    microSYST migra industrial LED sign with Ethernet and TCP/IP connection
    """
    
    COLOR_BLACK = "0"
    COLOR_GREEN = "1"
    COLOR_RED = "2"
    COLOR_YELLOW = "3"
    COLOR_TRANSPARENT = "T"
    COLOR_NAMES = {
        COLOR_BLACK: ["black", "off"],
        COLOR_GREEN: ["green"],
        COLOR_RED: ["red"],
        COLOR_YELLOW: ["yellow", "orange"],
        COLOR_TRANSPARENT: ["transparent", "transparency", "alpha"],
    }
    
    DIR_OFF = "0"
    DIR_UP = "1"
    DIR_DOWN = "2"
    DIRECTIONS = (DIR_OFF, DIR_UP, DIR_DOWN)
    
    TRIG_NORMAL = "="
    TRIG_HISTORY = "#"
    TRIGGER_MODES = (TRIG_NORMAL, TRIG_HISTORY)
    
    def __init__(self, host, port=10001, timeout=2.0, debug=False):
        """
        host:
          The hostname or IP to connect to
        
        port:
          The TCP port to use for communication
        
        timeout:
          The socket timeout in seconds
        """
        
        self.debug = debug
        self.command_queue_enabled = False
        self.command_queue = []
        
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))
        self.socket.settimeout(timeout)

    def __del__(self):
        self.socket.close()
    
    def _printable(self, char):
        """
        Replace non-printable chars with printable variants.
        """
        
        if char in range(0, 32):
            return "<{:02X}>".format(char)
        else:
            return chr(char)
    
    def debug_telegram(self, telegram, receive=False):
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
    
    def _send(self, telegram):
        self.debug_telegram(telegram)
        self.socket.send(telegram)
    
    def _receive(self, length):
        data = self.socket.recv(length)
        self.debug_telegram(data, receive=True)
        return data
    
    def send_telegram(self, payload, response=True, checksum=True, response_length=1):
        """
        Send a raw telegram. Header and trailer will be added.
        
        payload:
          The data to be sent
        
        response:
          Whether to request and read a response from the display
        
        checksum:
          Whether to use checksum and length bytes
        
        response_length:
          The length of the payload of the expected response
        """
        
        length = len(payload)
        if length > 230:
            raise ValueError("Telegram is too long (max. 230 bytes)")
        
        frame_ctrl = 0x80
        if response:
            frame_ctrl |= 0x01
        if checksum:
            frame_ctrl |= 0x02
        dest_addr = 0x81
        src_addr = 0x80
        telegram = bytearray([0x02, dest_addr, src_addr, frame_ctrl])
        if checksum:
            len_h = 0xF0 | ((length & 0xF0) >> 4)
            len_l = 0xF0 | (length & 0x0F)
            telegram.extend([len_h, len_l])
        telegram.extend(payload)
        if checksum:
            chk_sum = sum(telegram[1:]) % 256
            chk_h = 0xF0 | ((chk_sum & 0xF0) >> 4)
            chk_l = 0xF0 | (chk_sum & 0x0F)
            telegram.extend([chk_h, chk_l])
        telegram.append(0x03)
        
        self._send(telegram)
        
        if response:
            return self.receive_response(payload_length=response_length)
    
    def receive_response(self, payload_length=1):
        """
        Read the response from the display.
        
        payload_length:
          The expected length of the payload (usually 1 byte for status code)
        """
        
        telegram = bytearray()
        telegram.extend(self._receive(5 + payload_length))
        payload = telegram[4:-1]
        return payload
    
    def get_color_flag(self, color):
        """
        Return the character used to describe the given color
        """
        
        color = color.lower()
        choices = [inner for outer in self.COLOR_NAMES.values() for inner in outer]
        if color not in choices:
            raise ValueError(f"Invalid color name '{color}'. Choices are: {', '.join(choices)}")
        return [key for key, value in self.COLOR_NAMES.items() if color in value][0]
    
    def send_command(self, command, escape=True, *args, **kwargs):
        """
        Send a command (consisting of an escape character and some ASCII chars)
        
        command:
          The command to be sent (string)
        
        escape:
          Whether to prepend an escape character (0x1B) - not needed for text
        
        *args, **kwargs:
          Passed to send_telegram
        """
        
        payload = bytearray()
        if escape:
            payload.append(0x1B)
        if not escape and self.command_queue_enabled:
            # Separate non-escaped commands (texts) by 0x1F when queueing
            payload.append(0x1F)
        payload.extend(command.encode('ascii'))
        if self.command_queue_enabled:
            self.command_queue.append(payload)
        else:
            return self.send_telegram(payload, *args, **kwargs)
    
    def start_command_queue(self):
        """
        Causes subsequent calls to send_command() to queue up telegrams
        for sending them as one unit when send_command_queue() is called.
        """
        
        self.command_queue_enabled = True
    
    def send_command_queue(self, *args, **kwargs):
        """
        Send all queued commands.
        
        *args, **kwargs:
          Passed to send_command
        """
        
        try:
            telegram = b"".join(self.command_queue)
            response = self.send_telegram(telegram, *args, **kwargs)
            return response
        finally:
            self.command_queue_enabled = False
            self.command_queue = []
    
    def text(self, text):
        """
        Print a text at the current cursor position with the current attributes
        """
        
        return self.send_command(text, escape=False)
        
    def select_font(self, font_id, monospace=False):
        """
        Select a font for all subsequent texts
        
        font_id:
          ID of the font to be selected (0 to 99)
        
        monospace:
          Whether to force equal character widths
        """
        
        mono_flag = "z" if monospace else "Z"
        return self.send_command(f"{mono_flag}{font_id:02}")
        
    def set_cursor_pos(self, x, y):
        """
        Set the cursor to the specified X and Y coordinates
        """
        
        return self.send_command(f"C{x:03}{y:03}")
        
    def set_attributes(self, fg_color, bg_color, blink):
        """
        Set foreground color, background color and blink attributes
        for subsequent texts
        
        fg_color:
          One of self.COLORS
        
        bg_color:
          One of self.COLORS or 'transparent'
        
        blink:
          True for blinking text, False for static text
        """
        
        fg_flag = self.get_color_flag(fg_color)
        bg_flag = self.get_color_flag(bg_color)
        return self.send_command(f"A{fg_flag}{bg_flag}{str(int(blink))}")
    
    def set_scroll_speed(self, speed):
        """
        Set the scroll interval for all scrolling texts
        
        speed:
          0 - stopped
          1 - 1.8 seconds
          2 - 1.6 seconds
          3 - 1.4 seconds
          4 - 1.2 seconds
          5 - 1 second
          6 - 0.8 seconds
          7 - 0.6 seconds
          8 - 0.4 seconds
          9 - 0.2 seconds
        """
        
        return self.send_command(f"L{speed}")
    
    def show_text(self, text_id):
        """
        Show the stored text with the given ID
        """
        
        return self.send_command(f"T+{text_id:03}")
    
    def hide_text(self, text_id):
        """
        Hide the stored text with the given ID
        """
        
        return self.send_command(f"T-{text_id:03}")
    
    def show_image(self, image_id):
        """
        Show the stored image with the given ID
        """
        
        return self.send_command(f"G+{image_id:03}")
    
    def hide_image(self, image_id):
        """
        Hide the stored image with the given ID
        """
        
        return self.send_command(f"G-{image_id:03}")
    
    def show_variable(self, var_id):
        """
        Show the stored variable with the given ID
        """
        
        return self.send_command(f"V+{var_id:03}")
    
    def hide_variable(self, var_id):
        """
        Hide the stored variable with the given ID
        """
        
        return self.send_command(f"V-{var_id:03}")
    
    def set_variable_value(self, var_id, value):
        """
        Set the value of the stored variable with the given ID
        """
        
        return self.send_command(f"V={var_id:03}{value}")
    
    def increment_variable(self, var_id):
        """
        Increment the stored variable with the given ID
        """
        
        return self.send_command(f"VI{var_id:03}")
    
    def decrement_variable(self, var_id):
        """
        Decrement the stored variable with the given ID
        """
        
        return self.send_command(f"VD{var_id:03}")
    
    def set_variable_pos(self, var_id, x, y):
        """
        Set the display position of the stored variable with the given ID
        to the given X and Y coordinates
        """
        
        return self.send_command(f"VP{var_id:03}{x:03}{y:03}")
    
    def show_bargraph(self, bg_id):
        """
        Show the stored bargraph with the given ID
        """
        
        return self.send_command(f"W+{bg_id:03}")
    
    def hide_bargraph(self, bg_id):
        """
        Hide the stored bargraph with the given ID
        """
        
        return self.send_command(f"W-{bg_id:03}")
    
    def set_bargraph_value(self, bg_id, value):
        """
        Set the value of the stored variable with the given ID
        """
        
        # Alternative command format: raw signed integer
        # f"W={bg_id:03}I{high_byte}{low_byte}"
        
        sign = "+" if value >= 0 else "-"
        return self.send_command(f"W={bg_id:03}A{sign}{abs(value):05}")
    
    def fill(self, color):
        """
        Fill the entire display with one color
        
        color:
          One of self.COLORS
        """
        
        color_flag = self.get_color_flag(color)
        return self.send_command(f"F{color_flag}")
    
    def set_pixel(self, x, y, color):
        """
        Set the given pixel to the given color
        
        color:
          One of self.COLORS
        """
        
        color_flag = self.get_color_flag(color)
        return self.send_command(f"P{color_flag}{x:03}{y:03}")
    
    def get_pixel(self, x, y):
        """
        Get the color of the given pixel
        """
        
        response = self.send_command(f"P?{x:03}{y:03}", response_length=3)
        color = self.COLORS[response[2] - ord("0")]
        return color
    
    def rectangle(self, x1, y1, x2, y2, fg_color, bg_color):
        """
        Draw a rectangle with the given colors.
        
        x1, y1:
          Coordinates of the top left corner
        
        x2, y2:
          Coordinates of the bottom right corner
        
        fg_color:
          One of self.COLORS
        
        bg_color:
          One of self.COLORS or 'transparent'
        """
        
        fg_flag = self.get_color_flag(fg_color)
        bg_flag = self.get_color_flag(bg_color)
        return self.send_command(f"R{fg_flag}{bg_flag}{x1:03}{y1:03}{x2:03}{y2:03}")
    
    def scroll_area_vertical(self, direction, speed, step, y1, y2, extended_range=False):
        """
        Scroll the area between lines y1 and y2 in the given direction,
        at the given scroll interval, with the given step size.
        
        direction:
          One of self.DIRECTIONS
        
        speed:
          See set_scroll_speed
        
        step:
          0 - No movement
          1 to 9 - 1 to 9 pixels
        
        extended_range:
          If True, use three characters for y1 and y2 (for displays with more than 64 rows)
        """
        
        if extended_range:
            return self.send_command(f"S{direction}{speed}{step}{y1:03}{y2:03}")
        else:
            return self.send_command(f"S{direction}{speed}{step}{y1:02}{y2:02}")
    
    def set_blink_period(self, period):
        """
        Set the blink period for all blinking texts
        
        period:
          0 - 2 seconds
          1 - 1.8 seconds
          2 - 1.6 seconds
          3 - 1.4 seconds
          4 - 1.2 seconds
          5 - 1 second
          6 - 0.8 seconds
          7 - 0.6 seconds
          8 - 0.4 seconds
          9 - 0.2 seconds
        """
        
        return self.send_command(f"B{period}")
    
    def set_brightness(self, color, brightness):
        """
        Set the brightness for all LEDs of the given color
        
        color:
          self.COLOR_RED or self.COLOR_GREEN
        
        brightness:
          0 to 100
        """
        
        color_flag = self.get_color_flag(color)
        if color_flag not in (self.COLOR_RED, self.COLOR_GREEN):
            raise ValueError("Color for set_brightness can only be red or green")
        if color_flag == self.COLOR_GREEN:
            color_flag = "1"
        elif color_flag == self.COLOR_RED:
            color_flag = "2"
        return self.send_command(f"H{color_flag}{brightness:03}")
    
    def set_and_get_gpio(self, outputs):
        """
        Set the 16 general purpose outputs and return the state of the 16 inputs
        
        outputs:
          List of 16 values:
            True - Turn output on
            False - Turn output off
            None - Don't change output
        
        Returns:
          A list in the same form as the outputs parameter
        """
        
        def _get_output_flag(value):
            if value is True:
                return "1"
            elif value is False:
                return "0"
            else:
                return "N"
        
        output_flags = "".join(map(_get_output_flag, outputs))
        response = self.send_command(f"D{output_flags}", response_length=18)
        inputs = [(v == ord("1")) for v in response[2:]]
        return inputs
    
    def run_macros(self, macro_id):
        """
        Run macros starting at the given ID
        """
        
        return self.send_command(f"M{macro_id:03}")
    
    def run_macro_conditional(self, macro_id, input_channel, trigger_mode, trigger_state):
        """
        Run the macro with the given ID if the given digital input (0 to 15)
        is currently in the given state (trigger mode NORMAL)
        or has been in the given state at least once since the last call of this command
        (trigger mode HISTORY)
        
        trigger_mode:
          self.TRIG_NORMAL or self.TRIG_HISTORY
        
        trigger_state:
          True or False (on or off)
        """
        
        return self.send_command(f"M{macro_id:03}E{input_channel:1X}{trigger_mode}{trigger_state:1}")
    
    def wait(self, duration):
        """
        Pause macro execution for the given duration.
        
        duration:
          Time to wait in seconds (0 to 99.9)
        """
        
        duration_flag = int(duration * 10)
        return self.send_command(f"w{duration_flag:03}")
    
    def stop_macros(self):
        """
        Stop macro execution.
        """
        
        return self.send_command("E")

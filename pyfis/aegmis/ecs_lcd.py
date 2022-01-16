"""
Copyright (C) 2022 Julian Metzler

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

import datetime
import socket
import time

from io import BytesIO
from PIL import Image


class ECSLCDisplay:
    """
    ERROR / STATUS CODES
    """

    CMD_STATUS_DICT = {
        -1: "ERR_NO_RESPONSE",
        0:  "ECS_LCD_OK",
        1:  "ECS_LCD_EFONTSIZE",
        2:  "ECS_LCD_CLIPPED",
        3:  "ECS_LCD_ENOTFOUND",
        4:  "ECS_LCD_EDEVICECMD",
        5:  "ECS_LCD_ECHAR_ATTRIBUTE",
        6:  "ECS_LCD_EINIT_DISPLAY",
        7:  "ECS_LCD_EINIT_SECTOR",
        8:  "ECS_LCD_ERANGE",
        9:  "ECS_LCD_EOPTION_CONVERT",
        10: "ECS_LCD_EOPTION_LEN",
        11: "ECS_LCD_EOPTION",
        12: "ECS_LCD_EMISOPTION",
        13: "ECS_LCD_EHWDISPLAY",
        14: "ECS_LCD_DISPLAY",
        15: "ECS_LCD_ESECTOR",
        16: "ECS_LCD_EPAGE",
        17: "ECS_LCD_EPAGE_SEQ",
        18: "ECS_LCD_ECOMMUNICATION",
        19: "ECS_LCD_EBITMAP",
        20: "ECS_LCD_ELINE",
        21: "ECS_LCD_ESYNTAX",
        22: "ECS_LCD_EDELTEXT",
        23: "ECS_LCD_ENOPAGEACT",
        24: "ECS_LCD_ESECTORNR",
        25: "ECS_LCD_EPAGENR",
        26: "ECS_LCD_ESECX",
        27: "ECS_LCD_ESECY",
        28: "ECS_LCD_EFONT_MISS",
        29: "ECS_LCD_ESECLIN",
        30: "ECS_LCD_ENOSECACT",
        31: "ECS_LCD_EFEWPARS",
        32: "ECS_LCD_EOPTION1",
        33: "ECS_LCD_EOPTION2",
        34: "ECS_LCD_EOPTION3",
        35: "ECS_LCD_EOPTION4",
        36: "ECS_LCD_EFONTNR",
        37: "ECS_LCD_EFONTMISS",
        38: "ECS_LCD_ESECTTYPE",
        39: "ECS_LCD_EMUCHPARS",
        40: "ECS_LCD_EDEC_MISS",
        41: "ECS_LCD_COMMAND",
        42: "ECS_LCD_ENOEND",
        43: "ECS_LCD_EPREFIX",
        44: "ECS_LCD_EPOSTFIX",
        45: "ECS_LCD_EALIGN",
        46: "ECS_LCD_EATTRIB",
        47: "ECS_LCD_ECOLOR",
        48: "ECS_LCD_ESAMECOLORS",
        49: "ECS_LCD_ENOSPACE",
        50: "ECS_LCD_ENOANZPAGE",
        51: "ECS_LCD_EOUTOFRANGE",
        52: "ECS_LCD_ENOPAGENOTIME",
        53: "ECS_LCD_ECASE",
        54: "ECS_LCD_EONOFF",
        55: "ECS_LCD_EBIT",
        56: "ECS_LCD_EVALUE",
        57: "ECS_LCD_EALLOC",
        58: "ECS_LCD_EFILE",
        59: "ECS_LCD_EADRDOUBLE",
        60: "ECS_LCD_EGMFC",
        61: "ECS_LCD_EBLOCK",
        62: "ECS_LCD_EFONT",
        63: "ECS_LCD_EGLASTAB",
        64: "ECS_LCD_EHWNOTSUPPORTED",
        254: "ECS_LCD_ECONFIG",
        255: "ECS_LCD_EGENERAL"
    }

    OP_STATUS_DICT = {
        0: "OP_STAT_READY",
        1: "OP_STAT_LAMP_FAULT",
        2: "OP_STAT_LCD_FAULT",
        3: "OP_STAT_LAMP_LCD_FAULT"
    }


    def __init__(self, host, port=7487, timeout=10.0, double_sided=True, debug=False):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.double_sided = double_sided
        self.debug = debug
        self.socket = None
        self.socket_rfile = None
        self.socket_wfile = None
        socket.setdefaulttimeout(timeout)
        self._init_socket()
        device_cfg = self.get_device_cfg()
        self.width = device_cfg['xPixel']
        if self.double_sided:
            # Double-sided displays have the back side mapped below the front side
            self.height = device_cfg['yPixel'] // 2
        else:
            self.height = device_cfg['yPixel']


    """
    SOCKET I/O
    """

    def _init_socket(self):
        if self.socket is not None:
            try:
                self.socket.close()
            except:
                pass
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))
        self.socket_rfile = self.socket.makefile('r')
        self.socket_wfile = self.socket.makefile('w')

    def write(self, data):
        self.socket_wfile.write(data)
        self.socket_wfile.flush()

    def read_response(self):
        try:
            response = self.socket_rfile.readline()
            if self.debug:
                print("Received response: " + response.strip())
            return response
        except (socket.timeout, OSError):
            self._init_socket()
            return None

    def parse_response(self):
        response = self.read_response()
        if response is None:
            return {'status': -1, 'status_text': self.CMD_STATUS_DICT.get(-1, "UNKNOWN")}

        # Stupid bug, some replies have a space before the equals sign
        response = response.replace(" =", "=")

        parts = response.split()
        command = parts[0][:-1] # -1 to remove the trailing colon

        resp_dict = {}
        for part in parts[1:]:
            subparts = part.split("=")
            resp_dict[subparts[0]] = "=".join(subparts[1:])

        for int_key in ('status', 'operative', 'xPixel', 'yPixel'):
            if int_key in resp_dict:
                resp_dict[int_key] = int(resp_dict[int_key])

        if 'status' in resp_dict:
            resp_dict['status_text'] = self.CMD_STATUS_DICT.get(resp_dict['status'], "UNKNOWN")
        if 'operative' in resp_dict:
            resp_dict['operative_text'] = self.OP_STATUS_DICT.get(resp_dict['operative'], "UNKNOWN")

        if command == "ECS_LCD_GetTime":
            if 'time' in resp_dict:
                resp_dict['time'] = datetime.datetime.strptime(resp_dict['time'], "%H:%M:%S").time()
            if 'date' in resp_dict:
                resp_dict['date'] = datetime.datetime.strptime(resp_dict['date'], "%Y-%m-%d").date()
            if 'time' in resp_dict and 'date' in resp_dict:
                resp_dict['datetime'] = datetime.datetime.combine(resp_dict['date'], resp_dict['time'])
        elif command == "ECS_LCD_GetResetTime":
            if 'time' in resp_dict:
                resp_dict['time'] = int(resp_dict['time'])

        return resp_dict

    def send_command(self, command, *args, **kwargs):
        kwargs_list = []
        for key, value in kwargs.items():
            if value is None:
                continue

            if type(value) in (tuple, list):
                value_str = " ".join(map(str, value))
            elif type(value) in (bytes, bytearray):
                value_str = " ".join(["{:02X}".format(b) for b in value])
            else:
                value_str = str(value)
            kwargs_list.append("-" + key + " " + value_str)

        args_str = " ".join(map(str, args))
        kwargs_str = " ".join(kwargs_list)
        command_str = command.strip()
        if args_str:
            command_str += " " + args_str
        if kwargs_str:
            command_str += " " + kwargs_str
        command_str = command_str.strip() + "\r\n"
        if self.debug:
            print("Sending command:   " + command_str.strip())
        self.write(command_str)
        return self.parse_response()


    """
    COMMANDS
    """

    def define_normal_page(self, page):
        """
        Sets up a normal page with the given page ID.
        Normal pages are exactly the same size as the display.
        
        page: page ID, 0...255
        """
        return self.send_command("ECS_LCD_DefineNormalPage", page=page)

    def define_virtual_page(self, page, cols, rows):
        """
        Sets up a virtual page with the given page ID.
        Virtual pages can be larger than the display size and support
        vertical scrolling of rows.
        
        page: page ID, 0...255
        cols: Page width in columns
        rows: Page height in rows
        """
        return self.send_command("ECS_LCD_DefineVirtualPage", page=page, size=(cols, rows))

    def delete_page(self, page):
        """
        Deletes the page with the given ID.
        
        page: page ID, 0...255
        """
        return self.send_command("ECS_LCD_DeletePage", page=page)

    def select_page(self, page):
        """
        Selects the page with the given ID for editing.
        
        page: page ID, 0...255
        """
        return self.send_command("ECS_LCD_SelectPage", page=page)

    def change_sector(self, sector, col, row, cols, rows, type, font=None, lines=None, bg_color=None):
        """
        Updates the currently selected sector on the currently
        selected page with the given configuration.
        
        sector: sector ID, 0...255
        col: sector origin column, 0...65024
        row: sector origin row, 0...65024
        cols: sector width in columns, 0...65024
        rows: sector height in rows, 0...65024 (for virtual pages, only height 1 is valid)
        type: sector type, text or graphic
        font: font ID, 0...255 (only for sector type text)
        lines: number of lines of text in the sector, 0...255 (only for sector type text)
        bg_color: background color of the sector, 3-tuple, (0, 0, 0)...(255, 255, 255) (only for displays with RGB backlight)
        """
        return self.send_command("ECS_LCD_ChangeSector", sector=(sector, col, row, cols, rows), sectortype=type, font=font, lines=lines, bkcolor=bg_color)

    def select_sector(self, sector):
        """
        Selects the sector with the given ID on the currently selected page for editing.
        
        sector: sector ID, 0...255
        """
        return self.send_command("ECS_LCD_SelectSector", sector=sector)

    def chr_out_text(self, row, text, align, attribute, textcode=None):
        """
        Outputs text in the currently selected sector on the currently selected page.
        
        row: line index inside the current sector, 0...255
        text: text to output
        align: text alignment (left, center, right, flow) (flow: scroll text if it doesn't fit into the sector)
        attribute: text display attribute (normal, blink, compblink, invers) (compblink: inverted and blinking)
        textcode: index of pre-defined text for split-flap style control, 0...65535
        """
        text = "\"" + text.replace("\"", "") + "\""
        return self.send_command("ECS_LCD_ChrOutText", row, text=text, align=align, textcode=textcode, attribute=attribute)

    def put_image(self, col, row, image, filename=None):
        """
        Outputs the given image in the currently selected sector on the currently selected page.
        
        col: X position of the image in columns, 0...65024
        row: Y position of the image in rows, 0...65024
        image: image to output (path to image file, PIL Image object, or raw BMP image data)
        filename: filename to save the image as on the display (max. 31 characters)
        """
        if isinstance(image, Image.Image):
            bio = BytesIO()
            image.convert('1')
            image.save(bio, 'BMP')
            bio.seek(0)
            img_data = bio.read()
        elif type(image) is str:
            bio = BytesIO()
            image = Image.open(image)
            image.convert('1')
            image.save(bio, 'BMP')
            bio.seek(0)
            img_data = bio.read()
        else:
            img_data = image
        return self.send_command("ECS_LCD_PutImage", col, row, imagefilename=filename, image=img_data)

    def insert_line(self, line):
        """
        Inserts a line of text into the currently selected sector,
        below the line with the specified index.
        The remaining lines will be shifted downwards.
        
        line: line ID, 0...255
        """
        return self.send_command("ECS_LCD_InsertLine", line=line)

    def delete_line(self, line):
        """
        Deletes a line of text from the currently selected sector.
        The remaining lines will be shifted upwards.
        
        line: line ID, 0...255
        """
        return self.send_command("ECS_LCD_DeleteLine", line=line)

    def chr_clr_txt(self, line):
        """
        CLears a line of text in the currently selected sector.
        
        line: line ID, 0...255
        """
        return self.send_command("ECS_LCD_ChrClrTxt", line)

    def clr_sector(self):
        """
        Deletes the contents of the currently selected sector.
        """
        return self.send_command("ECS_LCD_ClrSector")

    def clr_page(self):
        """
        Deletes the contents of the currently selected page.
        """
        return self.send_command("ECS_LCD_ClrPage")

    def show_page(self, page):
        """
        Displays the page with the given ID on the display.
        
        page: page ID, 0...255
        """
        return self.send_command("ECS_LCD_ShowPage", page=page)

    def prog_page_sequence(self, page, duration):
        """
        Appends an entry to the current list of pages to show.
        Each entry comprises the page ID to be shown and a duration.
        
        page: page ID, 0...255
        duration: duration is milliseconds, 0...65024
        """
        return self.send_command("ECS_LCD_ProgPageSequence", page=page, time=duration)

    def activate_page_sequence(self):
        """
        Activates the previously programmed page seqneuce.
        """
        return self.send_command("ECS_LCD_ActivatePageSequence")

    def scroll_page(self, mode, lines=None, pause=None):
        """
        Scrolls the display contents up by the given amount of lines of text
        with the given pause between lines.
        
        mode: scroll mode (off, line, cont)
                off:  disable scrolling
                line: scroll row by row
                cont: scroll pixel by pixel
        lines: the number of lines to scroll, 0...255
        pause: the pause between lines in seconds, 0...255
        """
        return self.send_command("ECS_LCD_ScrollPage", scroll=mode, lines=lines, pausetime=pause)

    def switch_background_light(self, state):
        """
        Turns the background light on or off.
        
        state: light state (on, off)
        """
        if type(state) in (bool, int):
            state = 'on' if state else 'off'
        return self.send_command("ECS_LCD_SwitchBackgroundLight", light=state)

    def get_operative_status(self):
        """
        Get the operative status of the display.
        """
        return self.send_command("ECS_LCD_GetOperativeStatus")

    def get_reset_time(self):
        """
        Get the number of seconds since the last reset.
        """
        return self.send_command("ECS_LCD_GetResetTime")

    def get_time(self):
        """
        Get the system time.
        """
        return self.send_command("ECS_LCD_GetTime")

    def get_software_version(self):
        """
        Get the software version.
        """
        return self.send_command("ECS_LCD_GetSoftwareVersion")

    def get_device_cfg(self):
        """
        Get the device configuration.
        """
        return self.send_command("ECS_LCD_GetDeviceCfg")

    def get_page_content(self, page):
        """
        Get the contents of the specified page.

        page: page ID, 0...255
        """
        return self.send_command("ECS_LCD_GetPageContent", page=page)


    """
    CONVENIENCE FUNCTIONS
    """

    def display_text(self, page, text, font, align='center', attribute='normal'):
        """
        Displays a text on the given page.

        page: page ID, 0...255
        text: the text to display
        font: font ID, 0...255
        align: text alignment (left, center, right, flow)
        attribute: text display attribute (normal, blink, compblink, invers) (compblink: inverted and blinking)
        """
        lines = text.splitlines()
        self.define_normal_page(page)
        self.select_page(page)
        self.change_sector(0, 0, 0, self.width, self.height, 'text', font, lines=len(lines))
        self.select_sector(0)
        for i, row in enumerate(lines):
            self.chr_out_text(i, row, align, attribute)

        if self.double_sided:
            self.change_sector(1, 0, self.height, self.width, self.height, 'text', font, lines=len(lines))
            self.select_sector(1)
            for i, row in enumerate(lines):
                self.chr_out_text(i, row, align, attribute)
        
        self.show_page(page)

    def display_image(self, page, image, halign='center', valign='middle'):
        """
        Displays an image on the given page.

        page: page ID, 0...255
        image: the image to display (PIL Image object or path to image)
        halign: horizontal image alignment (left, center, right)
        valign: vertical image alignment (top, middle, bottom)
        """
        if not isinstance(image, Image.Image):
            image = Image.open(image)
        width, height = image.size

        if halign == 'center':
            x = (self.width - width) // 2
        elif halign == 'right':
            x = self.width - width
        else:
            x = 0

        if valign == 'middle':
            y = (self.height - height) // 2
        elif valign == 'bottom':
            y = self.height - height
        else:
            y = 0

        self.define_normal_page(page)
        self.select_page(page)
        self.change_sector(0, 0, 0, self.width, self.height, 'graphic')
        self.select_sector(0)
        self.put_image(x, y, image)

        if self.double_sided:
            self.change_sector(1, 0, self.height, self.width, self.height, 'graphic')
            self.select_sector(1)
            self.put_image(x, y, image)
        
        self.show_page(page)
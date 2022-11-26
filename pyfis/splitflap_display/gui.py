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

HAS_TKINTER = False
try:
    import tkinter as tk
    import tkinter.font as tkFont
    HAS_TKINTER = True
except ModuleNotFoundError:
    pass

from .fields import *


"""
This module can build a GUI based on a SplitFlapDisplay instance.
This can be used to easily build a manual control tool for a display.
"""

class SplitFlapGUI:
    def __init__(self, display, parent):
        if not HAS_TKINTER:
            raise RuntimeError("Tkinter could not be loaded. Please make sure the tkinter module exists.")
        
        self.display = display
        self.parent = parent
        self.field_widgets = {}
        self.frame = tk.Frame(parent)
        self.build_gui()

    @staticmethod
    def _set_optionmenu_width(widget, choices):
        f = tkFont.nametofont(widget.cget("font"))
        zerowidth = f.measure("0")
        w = round(max([f.measure(i) for i in choices]) / zerowidth)
        widget.config(width=w)

    @staticmethod
    def _validate_entry(allowed_chars, max_length, text):
        if len(text) > max_length:
            return False
        if allowed_chars:
            for char in text:
                if char not in (allowed_chars + [" "]):
                    return False
        return True

    def build_gui(self):
        fields = self.display.get_fields()
        for name, field in fields:
            if isinstance(field, TextField):
                if field.display_mapping:
                    allowed_chars = list(set([c.lower() for c in field.display_mapping.values()] + [c.upper() for c in field.display_mapping.values()]))
                else:
                    allowed_chars = None
                _len = field.length # Required! If you use field.length in the lambda directly, it'll give the wrong value!
                _validate_func = lambda text: self._validate_entry(allowed_chars, _len, text)
                _vcmd = (self.frame.register(_validate_func), "%P")
                entry = tk.Entry(self.frame, validate='key', validatecommand=_vcmd)
                entry.grid(column=field.x, row=field.y, columnspan=field.module_width*field.length, rowspan=field.module_height, sticky=tk.NSEW, padx=2, pady=2)
                self.field_widgets[name] = (entry, None, None)
            elif isinstance(field, CustomMapField):
                choices = list(field.display_mapping.values())
                var = tk.StringVar(self.frame)
                var.set(choices[0])
                opt = tk.OptionMenu(self.frame, var, *choices)
                opt.configure(indicatoron=False, anchor=tk.W)
                self._set_optionmenu_width(opt, choices)
                opt.grid(column=field.x, row=field.y, columnspan=field.module_width, rowspan=field.module_height, sticky=tk.NSEW, padx=2, pady=2)
                self.field_widgets[name] = (opt, var, choices)

    def update_display(self):
        for name, widget_data in self.field_widgets.items():
            widget, var, choices = widget_data
            if var:
                getattr(self.display, name).set(var.get())
            else:
                getattr(self.display, name).set(widget.get())
        #self.display.update()

    def clear_display(self):
        self.display.clear()
        for name, widget_data in self.field_widgets.items():
            widget, var, choices = widget_data
            if choices:
                var.set("")
            else:
                widget.delete(0, tk.END)
        #self.display.update()
"""
Copyright (C) 2019 - 2020 Julian Metzler

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

from .ascii_graphics import AsciiGraphics

class SplitFlapDisplay:
    def __init__(self, backend):
        self.backend = backend
        self.check_address_collisions()
    
    def get_fields(self):
        fields = []
        for name in dir(self):
            candidate = getattr(self, name)
            if hasattr(candidate, '_is_field') and candidate._is_field == True:
                fields.append((name, candidate))
        return fields
    
    def clear(self):
        """
        Clear all fields
        """
        for name, field in self.get_fields():
            field.clear()
    
    def check_address_collisions(self):
        """
        Checks if any of the addresses used by the fields are occupied
        by more than one field and raises an exception is necessary
        """
        addresses = []
        for name, field in self.get_fields():
            addresses += field.address_mapping
        if len(addresses) != len(set(addresses)):
            raise ValueError("Some addresses are occupied by more than one field")
    
    def get_module_data(self):
        """
        Returns all addresses and associated codes of the modules
        making up the display
        """
        module_data = []
        fields = self.get_fields()
        for name, field in fields:
            module_data += field.get_module_data()
        module_data.sort(key=lambda d:d[0])
        return module_data
    
    def update(self):
        self.backend.d_set_module_data(self.get_module_data())
        self.backend.d_update()
    
    def get_size(self):
        """
        Calculates the size of the display based on the position and size
        of its fields
        """
        width = 0
        height = 0
        for name, field in self.get_fields():
            f_params = field.get_ascii_render_parameters()
            x = f_params['x']
            y = f_params['y']
            f_end_x = x + f_params['width']
            f_end_y = y + f_params['height']
            if f_end_x > width:
                width = f_end_x
            if f_end_y > height:
                height = f_end_y
        return (width, height)
    
    def render_ascii(self):
        """
        Renders the display layout as ASCII graphics using ASCII frame symbols
        """
        width, height = self.get_size()
        graphics = AsciiGraphics(width, height)
        for name, field in self.get_fields():
            f_params = field.get_ascii_render_parameters()
            x = f_params['x']
            y = f_params['y']
            graphics.draw_rectangle(x, y, f_params['width'], f_params['height'])
            f_value = field.get()
            if type(f_value) in (list, tuple):
                for i, text in enumerate(f_value):
                    rendered_text = text[:f_params['text_max_length']]
                    if field.text_align == 'left':
                        rendered_text = rendered_text.ljust(f_params['text_max_length'])
                    elif field.text_align == 'center':
                        rendered_text = rendered_text.center(f_params['text_max_length'])
                    elif field.text_align == 'right':
                        rendered_text = rendered_text.rjust(f_params['text_max_length'])
                    graphics.draw_text(x + f_params['x_offset'] + i * f_params['spacing'], y + f_params['y_offset'], rendered_text, f_params['text_spacing'])
            else:
                graphics.draw_text(x + f_params['x_offset'], y + f_params['y_offset'], field.get(), f_params['text_spacing'])
            for i in range(field.length - 1):
                graphics.draw_line(x + f_params['spacing'] * (i+1), y, f_params['height'], 'v', t_ends=True)
        return graphics.render()

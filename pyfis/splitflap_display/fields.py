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

class BaseField:
    # This is needed so Form.get_fields() will know what to include
    _is_field = True
    
    def __init__(self, start_address = None, length = 1, descending = False,
                 text_align = 'left',
                 address_mapping = None, display_mapping = None,
                 x = 0, y = 0, module_width = 1, module_height = 1, home_pos = 0):
        """
        start_address: the address of the first module in this field
        length: How many modules make up this field
        descending: If using start_address, select descending addresses
        text_align: Alignment of the text (left, center, right)
        address_mapping: If modules have non-sequential addresses, the list of
                         addresses corresponding to the digits in this field
        display_mapping: Optional mapping of split-flap card numbers to
                         displayed text or symbols for all modules in this field
        x: Horizontal offset of the field in multiples of the smallest unit size
        y: Vertical offset of the field in multiples of the smallest unit size
        module_width: Width of the modules making up the field in multiples
                       of the smallest unit size
        module_height: Height of the modules making up the field in multiples
                       of the smallest unit size
        home_pos: ID of the home position. Should be 0, but is different in some cases
        """
        if start_address is None and address_mapping is None:
            raise AttributeError("Either start_address or address_mapping must be present")
        if type(length) is not int or length <= 0:
            raise ValueError("length must be a positive integer")
        if start_address is not None:
            if start_address not in range(256):
                raise ValueError("start_address must be an int between 0 and 255")
            if descending:
                if start_address - length < 0:
                    raise ValueError("Field is too long for given start address")
            else:
                if start_address + length > 256:
                    raise ValueError("Field is too long for given start address")
        if address_mapping is not None:
            if len(address_mapping) != length:
                raise ValueError("Length of address_mapping doesn't match field length")
        self.start_address = start_address
        self.length = length
        self.descending = descending
        if text_align not in ('left', 'center', 'right'):
            raise ValueError("text_align must be left, center or right")
        self.text_align = text_align
        if address_mapping is not None:
            self.address_mapping = address_mapping
        else:
            if self.descending:
                self.address_mapping = list(range(start_address, start_address-length, -1))
            else:
                self.address_mapping = list(range(start_address, start_address+length))
        self.display_mapping = display_mapping
        if display_mapping is not None:
            self.inverse_display_mapping = {v: k for k, v in display_mapping.items()}
        else:
            self.inverse_display_mapping = None
        self.x = x
        self.y = y
        self.module_width = module_width
        self.module_height = module_height
        self.home_pos = home_pos
        self.value = " " * self.length
        self.mirrors = []
    
    def set(self, value):
        self.value = value
    
    def get(self):
        return self.value
    
    def clear(self):
        self.value = " " * self.length
    
    def get_single_module_data(self, pos):
        raise NotImplementedError
    
    def get_module_data(self):
        module_data = []
        for i in range(self.length):
            module_data.append(self.get_single_module_data(i))
        return module_data
    
    def get_ascii_render_parameters(self):
        """
        Calculate the parameters needed to render the field as ASCII graphics
        """
        parameters = {
            'x': self.x * 2,
            'y': self.y * 2,
            'width': self.length * 2 * self.module_width + 1,
            'height': 2 * self.module_height + 1,
            'spacing': 2 * self.module_width,
            'text_spacing': 2 * self.module_width,
            'x_offset': self.module_width,
            'y_offset': self.module_height,
            'text_max_length': 2 * self.module_width - 1,
        }
        return parameters

    def add_mirror(self, field):
        """
        Add a field to the list of mirror fields
        """
        if field not in self.mirrors:
            self.mirrors.append(field)

    def remove_mirror(self, field):
        """
        Remove a field from the list of mirror fields
        """
        while field in self.mirrors:
            self.mirrors.remove(field)

    def update_mirrors(self):
        """
        Update all mirror fields of this field
        """
        for field in self.mirrors:
            if type(self.value) is list:
                field.value = self.value.copy()
            else:
                field.value = self.value


class MirrorField(BaseField):
    """
    This special field is set up so it mirrors an existing field.
    """
    def __init__(self, source_field, *args, **kwargs):
        if not isinstance(source_field, BaseField):
            raise ValueError("source_field must be an instance of a Field subclass")
        if 'start_address' not in kwargs:
            kwargs['start_address'] = source_field.start_address
        if 'length' not in kwargs:
            kwargs['length'] = source_field.length
        if 'descending' not in kwargs:
            kwargs['descending'] = source_field.descending
        if 'text_align' not in kwargs:
            kwargs['text_align'] = source_field.text_align
        if 'display_mapping' not in kwargs:
            kwargs['display_mapping'] = source_field.display_mapping
        if 'x' not in kwargs:
            kwargs['x'] = source_field.x
        if 'y' not in kwargs:
            kwargs['y'] = source_field.y
        if 'module_width' not in kwargs:
            kwargs['module_width'] = source_field.module_width
        if 'module_height' not in kwargs:
            kwargs['module_height'] = source_field.module_height
        if 'home_pos' not in kwargs:
            kwargs['home_pos'] = source_field.home_pos
        super().__init__(*args, **kwargs)
        self.source_field = source_field
        source_field.add_mirror(self)

    def set(self, value):
        pass

    def get(self):
        return self.source_field.get()

    def clear(self):
        pass

    def get_single_module_data(self, pos):
        addr, code, dummy_x, dummy_y = self.source_field.get_single_module_data(pos)
        x = self.x + pos * self.module_width
        return self.address_mapping[pos], code, x, self.y

    def get_module_data(self):
        module_data = []
        for i in range(self.length):
            module_data.append(self.get_single_module_data(i))
        return module_data

    def get_ascii_render_parameters(self):
        """
        Get the base parameters from the source field,
        but change the x and y values to allow for different placement
        """
        parameters = self.source_field.get_ascii_render_parameters()
        parameters.update({
            'x': self.x * 2,
            'y': self.y * 2,
        })
        return parameters


class TextField(BaseField):
    def __init__(self, *args, value = "", upper_only = True, **kwargs):
        super().__init__(*args, **kwargs)
        self.upper_only = upper_only
        self.set(value)
    
    def set(self, value):
        if type(value) is not str:
            raise ValueError("value must be str")
        if self.upper_only:
            value = value.upper()
        self.value = value[:self.length]
        if self.text_align == 'left':
            self.value = self.value.ljust(self.length)
        elif self.text_align == 'center':
            self.value = self.value.center(self.length)
        elif self.text_align == 'right':
            self.value = self.value.rjust(self.length)
        self.update_mirrors()
    
    def get_single_module_data(self, pos):
        """
        Returns the split-flap module address and code for the given position
        in the field with the current field value
        """
        if pos >= self.length:
            raise ValueError("pos must be inside field boundaries")
        addr = self.address_mapping[pos]
        char = self.value[pos]
        if self.display_mapping is not None:
            code = self.inverse_display_mapping.get(char, self.home_pos)
        else:
            code = ord(char.encode('iso-8859-1'))
        x = self.x + pos * self.module_width
        return addr, code, x, self.y


class CustomMapField(BaseField):
    def __init__(self, display_mapping, *args, value = [], **kwargs):
        super().__init__(*args, display_mapping=display_mapping, **kwargs)
        self.value = [""] * self.length
        self.set(value)

    def set(self, value):
        if type(value) not in (list, tuple):
            value = [value] * self.length
        value = value[:self.length] + [""] * (self.length - len(value))
        for i, module_value in enumerate(value):
            if module_value not in self.inverse_display_mapping:
                self.value[i] = ""
            else:
                self.value[i] = module_value
        self.update_mirrors()
    
    def clear(self):
        self.value = [""] * self.length
        self.update_mirrors()
    
    def get_single_module_data(self, pos):
        """
        Returns the split-flap module address and code for the given position
        in the field with the current field value
        """
        if pos >= self.length:
            raise ValueError("pos must be inside field boundaries")
        addr = self.address_mapping[pos]
        display_value = self.value[pos]
        code = self.inverse_display_mapping.get(display_value, self.home_pos)
        x = self.x + pos * self.module_width
        return addr, code, x, self.y
    
    def get_ascii_render_parameters(self):
        parameters = super().get_ascii_render_parameters()
        parameters['x_offset'] = 1
        parameters['text_spacing'] = 1
        return parameters
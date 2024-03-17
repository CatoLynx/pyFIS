"""
Copyright (C) 2019 - 2024 Julian Metzler

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

import io
import json
import random
import time

from .ascii_graphics import AsciiGraphics
from .fields import *

class SplitFlapDisplay:
    TRANSITION_LEFT_TO_RIGHT = 'ltr'
    TRANSITION_RIGHT_TO_LEFT = 'rtl'
    TRANSITION_TOP_TO_BOTTOM = 'ttb'
    TRANSITION_BOTTOM_TO_TOP = 'btt'
    TRANSITION_MIDDLE_OUT_HORIZONTAL = 'moh'
    TRANSITION_MIDDLE_OUT_VERTICAL = 'mov'
    TRANSITION_MIDDLE_IN_HORIZONTAL = 'mih'
    TRANSITION_MIDDLE_IN_VERTICAL = 'miv'
    TRANSITION_SEQUENTIAL = 'seq'
    TRANSITION_SEQUENTIAL_REVERSE = 'seq-rev'
    TRANSITION_RANDOM = 'rnd'
    TRANSITION_RANDOM_CHOICE = 'rndc'
    
    TRANSITIONS = [
        TRANSITION_LEFT_TO_RIGHT,
        TRANSITION_RIGHT_TO_LEFT,
        TRANSITION_TOP_TO_BOTTOM,
        TRANSITION_BOTTOM_TO_TOP,
        TRANSITION_MIDDLE_OUT_HORIZONTAL,
        TRANSITION_MIDDLE_OUT_VERTICAL,
        TRANSITION_MIDDLE_IN_HORIZONTAL,
        TRANSITION_MIDDLE_IN_VERTICAL,
        TRANSITION_SEQUENTIAL,
        TRANSITION_SEQUENTIAL_REVERSE,
        TRANSITION_RANDOM
    ]

    def __init__(self, backend):
        self.backend = backend
        self.check_address_collisions()
    
    @classmethod
    def from_json(cls, json_data, backend):
        # data can be a dict, open file or JSON string
        if type(json_data) is dict:
            data = json_data
        elif isinstance(json_data, io.IOBase):
            data = json.load(json_data)
        else:
            data = json.loads(json_data)
        
        units = data['units']
        maps = data['maps']
        display = SplitFlapDisplay(backend)
        
        for unit in units:
            if unit['type'] == 'map':
                _map = dict([(int(key), value) for key, value in maps[unit['map']].items()])
                field = CustomMapField(
                    display_mapping=_map,
                    start_address=unit['addr'],
                    length=unit['len'],
                    x=unit['x'],
                    y=unit['y'],
                    module_width=unit['width'],
                    module_height=unit['height'],
                    home_pos=unit['home']
                )
                setattr(display, unit['name'], field)
            elif unit['type'] == 'text':
                _map = dict([(int(key), value) for key, value in maps[unit['map']].items()]) if 'map' in unit else None
                field = TextField(
                    display_mapping=_map,
                    start_address=unit['addr'],
                    length=unit['len'],
                    x=unit['x'],
                    y=unit['y'],
                    module_width=unit['width'],
                    module_height=unit['height'],
                    home_pos=unit['home']
                )
                setattr(display, unit['name'], field)
        return display

    def _group(self, data, key):
        sorted_data = sorted(data, key=key)
        prev_group = None
        output = {}
        for item in sorted_data:
            group = key(item)
            if group != prev_group:
                prev_group = group
                output[group] = [item]
            else:
                output[group].append(item)
        return output
    
    def _interleave(self, list1, list2):
        newlist = []
        a1 = len(list1)
        a2 = len(list2)
        for i in range(max(a1, a2)):
            if i < a1:
                newlist.append(list1[i])
            if i < a2:
                newlist.append(list2[i])
        return newlist
    
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
        Check if any of the addresses used by the fields are occupied
        by more than one field and raise an exception if necessary
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
    
    def update(self, transition = None, interval = 0.1):
        fields = self.get_fields()
        module_data = self.get_module_data()
        
        if transition == self.TRANSITION_RANDOM_CHOICE:
            transition = random.choice(self.TRANSITIONS)

        if transition == self.TRANSITION_LEFT_TO_RIGHT:
            module_data_by_x = self._group(module_data, lambda i: i[2])
            min_x = min(module_data_by_x.keys())
            max_x = max(module_data_by_x.keys())
            for x in range(min_x, max_x+1):
                if x in module_data_by_x:
                    self.backend.d_set_module_data([md[:2] for md in module_data_by_x[x]])
                    self.backend.d_update()
                time.sleep(interval)
        elif transition == self.TRANSITION_RIGHT_TO_LEFT:
            module_data_by_x = self._group(module_data, lambda i: i[2])
            min_x = min(module_data_by_x.keys())
            max_x = max(module_data_by_x.keys())
            for x in range(max_x, min_x-1, -1):
                if x in module_data_by_x:
                    self.backend.d_set_module_data([md[:2] for md in module_data_by_x[x]])
                    self.backend.d_update()
                time.sleep(interval)
        elif transition == self.TRANSITION_TOP_TO_BOTTOM:
            module_data_by_y = self._group(module_data, lambda i: i[3])
            min_y = min(module_data_by_y.keys())
            max_y = max(module_data_by_y.keys())
            for y in range(min_y, max_y+1):
                if y in module_data_by_y:
                    self.backend.d_set_module_data([md[:2] for md in module_data_by_y[y]])
                    self.backend.d_update()
                time.sleep(interval)
        elif transition == self.TRANSITION_BOTTOM_TO_TOP:
            module_data_by_y = self._group(module_data, lambda i: i[3])
            min_y = min(module_data_by_y.keys())
            max_y = max(module_data_by_y.keys())
            for y in range(max_y, min_y-1, -1):
                if y in module_data_by_y:
                    self.backend.d_set_module_data([md[:2] for md in module_data_by_y[y]])
                    self.backend.d_update()
                time.sleep(interval)
        elif transition == self.TRANSITION_MIDDLE_OUT_HORIZONTAL:
            module_data_by_x = self._group(module_data, lambda i: i[2])
            min_x = min(module_data_by_x.keys())
            max_x = max(module_data_by_x.keys())
            mid_x = min_x + (max_x - min_x) // 2
            pair_complete = True
            for x in self._interleave(range(mid_x, min_x-1, -1), range(mid_x+1, max_x+1)):
                if x in module_data_by_x:
                    self.backend.d_set_module_data([md[:2] for md in module_data_by_x[x]])
                    self.backend.d_update()
                pair_complete = not pair_complete
                if pair_complete:
                    time.sleep(interval)
        elif transition == self.TRANSITION_MIDDLE_IN_HORIZONTAL:
            module_data_by_x = self._group(module_data, lambda i: i[2])
            min_x = min(module_data_by_x.keys())
            max_x = max(module_data_by_x.keys())
            mid_x = min_x + (max_x - min_x) // 2
            pair_complete = True
            for x in self._interleave(range(mid_x, min_x-1, -1), range(mid_x+1, max_x+1))[::-1]:
                if x in module_data_by_x:
                    self.backend.d_set_module_data([md[:2] for md in module_data_by_x[x]])
                    self.backend.d_update()
                pair_complete = not pair_complete
                if pair_complete:
                    time.sleep(interval)
        elif transition == self.TRANSITION_MIDDLE_OUT_VERTICAL:
            module_data_by_y = self._group(module_data, lambda i: i[3])
            min_y = min(module_data_by_y.keys())
            max_y = max(module_data_by_y.keys())
            mid_y = min_y + (max_y - min_y) // 2
            pair_complete = True
            for y in self._interleave(range(mid_y, min_y-1, -1), range(mid_y+1, max_y+1)):
                if y in module_data_by_y:
                    self.backend.d_set_module_data([md[:2] for md in module_data_by_y[y]])
                    self.backend.d_update()
                pair_complete = not pair_complete
                if pair_complete:
                    time.sleep(interval)
        elif transition == self.TRANSITION_MIDDLE_IN_VERTICAL:
            module_data_by_y = self._group(module_data, lambda i: i[3])
            min_y = min(module_data_by_y.keys())
            max_y = max(module_data_by_y.keys())
            mid_y = min_y + (max_y - min_y) // 2
            pair_complete = True
            for y in self._interleave(range(mid_y, min_y-1, -1), range(mid_y+1, max_y+1))[::-1]:
                if y in module_data_by_y:
                    self.backend.d_set_module_data([md[:2] for md in module_data_by_y[y]])
                    self.backend.d_update()
                pair_complete = not pair_complete
                if pair_complete:
                    time.sleep(interval)
        elif transition == self.TRANSITION_SEQUENTIAL:
            addrs = [md[0] for md in module_data]
            codes = [md[1] for md in module_data]
            min_addr = min(addrs)
            max_addr = max(addrs)
            for addr in range(min_addr, max_addr+1):
                if addr in addrs:
                    self.backend.d_set_module_data([(addr, codes[addrs.index(addr)])])
                    self.backend.d_update()
                time.sleep(interval)
        elif transition == self.TRANSITION_SEQUENTIAL_REVERSE:
            addrs = [md[0] for md in module_data]
            codes = [md[1] for md in module_data]
            min_addr = min(addrs)
            max_addr = max(addrs)
            for addr in range(max_addr, min_addr-1, -1):
                if addr in addrs:
                    self.backend.d_set_module_data([(addr, codes[addrs.index(addr)])])
                    self.backend.d_update()
                time.sleep(interval)
        elif transition == self.TRANSITION_RANDOM:
            random.shuffle(module_data)
            for addr, pos, x, y in module_data:
                self.backend.d_set_module_data([(addr, pos)])
                self.backend.d_update()
                time.sleep(interval)
        else:
            self.backend.d_set_module_data([md[:2] for md in module_data])
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
    
    def export_json(self, prettify = False):
        """
        Exports the display configuration in a JSON format
        that can be used with the xatLabs Cheetah display controller
        """
        data = {
            'units': [],
            'maps': {}
        }
        
        for name, field in self.get_fields():
            f_type_str = 'unknown'
            if isinstance(field, MirrorField):
                if isinstance(field.source_field, TextField):
                    f_type_str = 'text'
                elif isinstance(field.source_field, CustomMapField):
                    f_type_str = 'map'
            else:
                if isinstance(field, TextField):
                    f_type_str = 'text'
                elif isinstance(field, CustomMapField):
                    f_type_str = 'map'
            
            mapping = field.display_mapping
            map_name = f"map_{name}"
            map_found = False
            if mapping:
                # Check if this map already exists
                for _name, _map in data['maps'].items():
                    if hash(frozenset(_map.items())) == hash(frozenset(mapping.items())):
                        map_found = True
                        map_name = _name
                        break
            
            # Add map if it didn't exist
            if not map_found:
                data['maps'][map_name] = mapping.copy()
            
            unit = {
                'name': name,
                'flags': [],
                'type': f_type_str,
                'addr': field.start_address,
                'x': field.x,
                'y': field.y,
                'width': field.module_width,
                'height': field.module_height,
                'len': field.length,
                'home': field.home_pos,
                'map': map_name
            }
            data['units'].append(unit)
            
        if prettify:
            return json.dumps(data, indent=4, sort_keys=True)
        else:
            return json.dumps(data)

"""
Copyright (C) 2023 Julian Metzler

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

import json
import os


def get_text_width(text, font):
    """
    Get the width of the given text using the given font.
    """
    
    if not text:
        return 0
    
    try:
        with open(os.path.join(os.path.dirname(__file__), "dimensions-{}.json".format(font)), 'r') as f:
            dimensions = json.load(f)
        width = 0
        for char in text:
            dims = dimensions.get(char, (0, 0))
            w = dims[0]
            if w is None:
                w = 0
            width += w
        width += dimensions.get('spacing', 0) * (len(text) - 1)
        return width
    except FileNotFoundError:
        raise NotImplementedError("Width calculation not available for this font")
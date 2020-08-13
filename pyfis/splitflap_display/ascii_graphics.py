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

class AsciiGraphics:
    PIECES = ["━", "┃", "┏", "┗", "┓", "┛", "┣", "┳", "┫", "┻", "╋"]
    PIECES_2_POINTS = ["━", "┃", "┏", "┗", "┓", "┛"]
    PIECES_3_POINTS = ["┣", "┳", "┫", "┻"]
    PIECES_4_POINTS = ["╋"]
    PIECE_COMBINATIONS = {
        "━": {
            "┃": "╋",
            "┏": "┳",
            "┗": "┻",
            "┓": "┳",
            "┛": "┻",
            "┣": "╋",
            "┫": "╋",
        },
        "┃": {
            "━": "╋",
            "┏": "┣",
            "┗": "┣",
            "┓": "┫",
            "┛": "┫",
            "┳": "╋",
            "┻": "╋",
        },
        "┏": {
            "━": "┳",
            "┃": "┣",
            "┗": "┣",
            "┓": "┳",
            "┛": "╋",
            "┫": "╋",
            "┻": "╋",
        },
        "┗": {
            "━": "┻",
            "┃": "┣",
            "┏": "┣",
            "┓": "╋",
            "┛": "┻",
            "┳": "╋",
            "┫": "╋",
        },
        "┓": {
            "━": "┳",
            "┃": "┫",
            "┏": "┳",
            "┗": "╋",
            "┛": "┫",
            "┻": "╋",
            "┣": "╋",
        },
        "┛": {
            "━": "┻",
            "┃": "┫",
            "┏": "╋",
            "┗": "┻",
            "┓": "┫",
            "┣": "╋",
            "┳": "╋",
        },
        "┣": {
            "━": "╋",
            "┓": "╋",
            "┛": "╋",
            "┳": "╋",
            "┫": "╋",
            "┻": "╋",
        },
        "┳": {
            "┃": "╋",
            "┛": "╋",
            "┗": "╋",
            "┣": "╋",
            "┫": "╋",
            "┻": "╋",
        },
        "┫": {
            "━": "╋",
            "┏": "╋",
            "┗": "╋",
            "┣": "╋",
            "┳": "╋",
            "┻": "╋",
        },
        "┻": {
            "┃": "╋",
            "┏": "╋",
            "┓": "╋",
            "┣": "╋",
            "┳": "╋",
            "┫": "╋",
        }
    }
    
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.clear()
    
    def render(self):
        output = "\n".join(["".join(row) for row in self.canvas])
        return output
    
    def clear(self):
        self.canvas = []
        for y in range(self.height):
            row = []
            for x in range(self.width):
                row.append(" ")
            self.canvas.append(row)
    
    def get_num_points(self, piece):
        """
        Return how many points a piece has
        """
        if piece in self.PIECES_2_POINTS:
            return 2
        if piece in self.PIECES_3_POINTS:
            return 3
        if piece in self.PIECES_4_POINTS:
            return 4
        return 0
    
    def combine_piece(self, piece1, piece2):
        """
        Adds piece2 to the canvas,
        combining it with piece1
        """
        if piece1 in self.PIECES and piece2 not in self.PIECES:
            # Frame pieces take precedence, ignore anything else
            return piece1
        if piece1 not in self.PIECES and piece2 not in self.PIECES:
            # Just overwrite if neither piece is a frame piece
            return piece2
        if piece1 == " ":
            # No piece present, so just put the new one there
            return piece2
        else:
            combination = self.PIECE_COMBINATIONS.get(piece1, {}).get(piece2)
            if combination is None:
                combination = self.PIECE_COMBINATIONS.get(piece2, {}).get(piece1)
                if combination is None:
                    # If no combination can be found, the piece with more points takes precedence
                    # In case of equal numbers, the newer piece takes precedence
                    if self.get_num_points(piece1) > self.get_num_points(piece2):
                        return piece1
                    else:
                        return piece2
            return combination
    
    def draw_text(self, x, y, text, spacing = 1):
        for i, char in enumerate(text):
            self.draw_piece(x+(i*spacing), y, char)
    
    def draw_piece(self, x, y, piece):
        existing_piece = self.canvas[y][x]
        new_piece = self.combine_piece(existing_piece, piece)
        self.canvas[y][x] = new_piece
    
    def draw_line(self, x, y, length, direction, t_ends = False):
        """
        The t_ends parameter controls whether a line
        just ends straight or in a T cross
        """
        if length <= 0:
            return
        if direction == 'h':
            if t_ends:
                self.draw_piece(x, y, "┣")
                self.draw_piece(x+length-1, y, "┫")
                if length > 2:
                    for i in range(length-2):
                        self.draw_piece(x+i+1, y, "━")
            else:
                for i in range(length):
                    self.draw_piece(x+i, y, "━")
        elif direction == 'v':
            if t_ends:
                self.draw_piece(x, y, "┳")
                self.draw_piece(x, y+length-1, "┻")
                if length > 2:
                    for i in range(length-2):
                        self.draw_piece(x, y+i+1, "┃")
            else:
                for i in range(length):
                    self.draw_piece(x, y+i, "┃")
    
    def draw_rectangle(self, x, y, width, height):
        self.draw_piece(x, y, "┏")
        self.draw_piece(x+width-1, y, "┓")
        self.draw_piece(x, y+height-1, "┗")
        self.draw_piece(x+width-1, y+height-1, "┛")
        if width > 2:
            self.draw_line(x+1, y, width-2, 'h')
            self.draw_line(x+1, y+height-1, width-2, 'h')
        if height > 2:
            self.draw_line(x, y+1, height-2, 'v')
            self.draw_line(x+width-1, y+1, height-2, 'v')

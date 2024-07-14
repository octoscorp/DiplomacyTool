"""
Utils for View objects
"""
from PIL import Image, ImageTk
import math

def fix_offset(points, amount):
    """
    Adds offset of amount to the points
    Data is expected in 0-based format; this may not look quite right (e.g. borders not showing).
    """
    output = []
    for i in range(len(points)):
        output.append([points[i][0] + amount, points[i][1] + amount])
    return output

def blend(colour1, colour2, weight_colour1=1, weight_colour2=1):
    """Accepts two colours in the format '#rgb' and returns the blended version."""
    col1 = [col * weight_colour1 for col in rgb_from_string(colour1)]
    col2 = [col * weight_colour2 for col in rgb_from_string(colour2)]

    # Average the two
    divisor = weight_colour1 + weight_colour2
    
    red = hex(int((col1[0] + col2[0]) / divisor))
    green = hex(int((col1[1] + col2[1]) / divisor))
    blue = hex(int((col1[2] + col2[2]) / divisor))

    return f'#{red[2:]}{green[2:]}{blue[2:]}'

def _hex_to_num(letters):
    hex_rep = f'0x{letters}'
    return int(hex_rep, 0)

def rgb_from_string(colour_str):
    """Extracts r,g,b values from a string of format '#rrggbb' or '#rgb'"""
    # Remove leading #
    if len(colour_str) == 0:
        return
    colour = colour_str[1:] if colour_str[0] == '#' else colour_str
    
    # Lengthen string if length 3
    if len(colour) == 3:
        colour = f'{colour[0]}{colour[0]}{colour[1]}{colour[1]}{colour[2]}{colour[2]}'
    
    red = _hex_to_num(colour[0:2])
    green = _hex_to_num(colour[2:4])
    blue = _hex_to_num(colour[4:])

    return (red, green, blue)

def get_circle_bounding_box(centre, radius, offset=0):
    return [
        centre[0] - radius + offset,
        centre[1] - radius + offset,
        centre[0] + radius + offset,
        centre[1] + radius + offset
    ]

def get_fleet_triangle_points(location):
    """Defines points of a triangle for the fleet"""
    return [
        location[0] - 10, location[1] - 5,
        location[0] + 10, location[1] - 5,
        location[0], location[1] + 5
    ]

def get_convoy_symbol_points(fleet_position):
    return [
        fleet_position[0] - 10, fleet_position[1] - 12,
        fleet_position[0] - 6, fleet_position[1] - 8,
        fleet_position[0] - 2, fleet_position[1] - 12,
        fleet_position[0] + 2, fleet_position[1] - 8,
        fleet_position[0] + 6, fleet_position[1] - 12,
        fleet_position[0] + 10, fleet_position[1] - 8,
    ]

def get_support_points(support_from, start, end):
    return [
        *support_from,
        start[0] + ((end[0] - start[0]) * 0.2), start[1] + ((end[1] - start[1]) * 0.2),
        start[0] + ((end[0] - start[0]) * 0.7), start[1] + ((end[1] - start[1]) * 0.7),
        start[0] + ((end[0] - start[0]) * 0.9), start[1] + ((end[1] - start[1]) * 0.9),
    ]

def create_transparent_image(size, fill, alpha):
    img_fill = rgb_from_string(fill) + (alpha,)
    return ImageTk.PhotoImage(Image.new('RGBA', (size[0], size[1]), img_fill))
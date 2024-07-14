"""
Display objects for a Tkinter Canvas
Author: G Hampton
"""
from view_utils import fix_offset, get_circle_bounding_box, get_fleet_triangle_points, create_transparent_image

class DisplayObject():
    """Wrapper class for shapes on a canvas"""
    def __init__(self, canvas, shape):
        self.shape = shape
        self.canvas = canvas

        self.fill_colour = ""
        self.outline_colour = ""
        self.active_colour = ""
        self.is_active = False
    
    def set_fill_colour(self, fill_colour):
        self.fill_colour = fill_colour
    
    def set_outline_colour(self, outline_colour):
        self.outline_colour = outline_colour
    
    def set_active_colour(self, active_colour):
        self.active_colour = active_colour
    
    def toggle_active(self, active):
        self.is_active = active
        self.recolour()
    
    def recolour(self):
        fill_col = self.fill_colour
        if self.is_active:
            fill_col = self.active_colour
        self.canvas.itemconfig(self.shape, fill=fill_col, outline=self.outline_colour)
        
class Territory():
    """Helper class"""
    def __init__(self, canvas, name, border_points, data, is_test=False):
        # Data
        self.short_name = name
        self.type = data["type"]
        self.full_name = data["full_name"]
        self.is_supply_centre = data["is_supply_centre"]
        self.buildable_for = None
        self.owned_by = None

        # Graphical Data
        self.unit_position = fix_offset([data["location"]["unit"]], 2)[0]
        self.name_location = fix_offset([data["location"]["name"]], 2)[0]
        
        self.coasts = {}
        if "coasts" in data.keys():
            self._add_coasts(canvas, data["coasts"], is_test)
        
        if is_test:
            return

        # Display
        self.shape = DisplayObject(canvas, canvas.create_polygon(*border_points, tags=(name,  "territory_layer")))
        self.name = canvas.create_text(self.name_location, text=name, anchor="nw", tags=(name, "text", "territory_decoration_layer"))

        self.canal_layer = None
        if self.type == "canal" and "canal_points" in data.keys():
            self._add_canal_layer(canvas, fix_offset(data["canal_points"], 2))
        if self.is_supply_centre:
            self.supply_location = fix_offset([data["location"]["supply"]], 2)[0]
            self.supply_centre_shape = canvas.create_oval(get_circle_bounding_box(self.supply_location, 3, 4))
        
        # UI
        self.tooltip = Tooltip(canvas, f'{name} ({self.full_name})')

        self.ui = canvas.create_polygon(*border_points, fill='', tags=(name, "ui_layer"))
    
    def _add_coasts(self, canvas, coast_data, is_test):
        for coast in coast_data:
            location = [self.name_location[i] + coast["rel_location"][i] for i in [0, 1]]
            self.coasts[coast["label"]] = location
            if is_test:
                continue
            canvas.create_text(location, text=coast["label"], anchor="nw", tags=("text", "territory_decoration_layer"))
            points = get_circle_bounding_box([location[0] + 5, location[1] + 8], 10)
            canvas.create_polygon(points[0], points[1], points[2], points[1], points[2], points[3], points[0], points[3], \
                                  fill='', width='2', state="hidden", tags=(f'{self.short_name}-{coast["label"]}', "coast_layer", f'{self.short_name}-coast'))

    def make_home_centre(self, canvas, team):
        """Makes this province into a home centre for team"""
        self.buildable_for = team
        self.owned_by = team

        canvas.delete(self.supply_centre_shape)
        self.supply_centre_shape = canvas.create_rectangle(get_circle_bounding_box(self.supply_location, 3))
    
    def capture(self, team):
        if self.is_supply_centre:
            self.owned_by = team
    
    def is_army_accessible(self):
        """Note that there are also canal and coast types; these are accessible to both"""
        return self.type != "ocean"

    def is_fleet_accessible(self):
        """Note that there are also canal and coast types; these are accessible to both"""
        return self.type != "land"
    
    def _add_canal_layer(self, canvas, points):
        """Adds an overlay showing the canal"""
        self.canal_layer = canvas.create_polygon(*points, tags="territory_decoration_layer")

class Unit():
    """Helper class"""
    def __init__(self, canvas, team, location, position, unit_type, is_test=False):
        self.location = location
        self.position = position
        self.type = unit_type
        self.team = team
        self.pending_order = None

        if is_test:
            return
        self.canvas = canvas

    def draw_shape(self):
        match self.type:
            case "Army":
                self.shape = self.canvas.create_oval(get_circle_bounding_box(self.position, 7), tags=('units', self.team, self.location))
            case "Fleet":
                self.shape = self.canvas.create_polygon(get_fleet_triangle_points(self.position), tags=('units', self.team, self.location))
            case _:
                print(f'Apparently, {self.type} is neither Army nor Fleet.')

    def delete(self):
        self.canvas.delete(self.shape)

    def give_order(self, type, location_1, location_2):
        """Pass None to location_1 for a move"""
        if self.pending_order:
            for shape in self.pending_order.shapes:
                self.canvas.delete(shape)

        if type == "move":
            location_1 = self.location
        if type == "hold":
            location_1 = self.location
            location_2 = self.location
        
        self.pending_order = Order(self, type, location_1, location_2)
        return self.pending_order
        
    def move(self, canvas, new_location, new_position):
        self.location = new_location
        pos_change = [new_position[0] - self.position[0], new_position[1] - self.position[1]]
        canvas.move(self.shape, *pos_change)
        self.position = new_position

class Order():
    def __init__(self, unit, type, location_1, location_2):
        self.unit = unit
        self.type = type
        self.supported_order = None
        self.build_type = None
        self.location_1 = location_1
        self.location_2 = location_2
        self.shapes = []
        self.strength = 1
        self.convoy_routes = []
    
    def __str__(self):
        rep = ""
        if self.unit:
            rep += f"{self.unit.type[0]} {self.unit.location} "
        else:
            return f"Build {self.build_type[0]} {self.location_1}"
        match self.type:
            case "hold":
                rep += "H"
            case "move":
                rep += f"-> {self.location_2}"
            case "support":
                rep += f"S {self.location_1} -> {self.location_2}"
            case "convoy":
                rep += f"C A {self.location_1} -> {self.location_2}"
        return rep
    
    def add_shape(self, shape):
        self.shapes.append(shape)
    
    def add_strength(self):
        self.strength += 1
    
    def remove_strength(self):
        self.strength -= 1
    
    def erase(self, canvas):
        for shape in self.shapes:
            canvas.delete(shape)
        self.shapes = []

class Tooltip():
    def __init__(self, canvas, display_text):
        self.padding = 5

        self.shown = "hidden"
        self.bg = None
        self.canvas = canvas
        self.position = [0,0]
        self.text = canvas.create_text([dim + self.padding for dim in self.position], text=display_text, anchor="nw", tags=('tooltip', 'tooltip_text'), state="hidden")
    
    def set_bg_colour(self, colour):
        img = create_transparent_image([80, 40], colour, 255 * 0.6)
        if self.bg:
            self.canvas.delete(self.bg)
        self.bg = self.canvas.create_image(self.position, image=img, anchor='nw', tags=('tooltip', 'tooltip_bg'), state = self.shown)
    
    def show(self):
        self.shown = "normal"
        self.canvas.itemconfig('tooltip', state=self.shown)
    
    def hide(self):
        self.shown = "hidden"
        self.canvas.itemconfig('tooltip', state=self.shown)
    
    def move(self, new_position):
        pos_change = [new_position[0] - self.position[0], new_position[1] - self.position[1]]
        if self.bg:
            self.canvas.move(self.bg, pos_change)
        self.canvas.move(self.text, [dim + self.padding for dim in pos_change])
        self.position = new_position
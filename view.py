"""
View class for a Diplomacy application.
Date: 5/06/24
Author: G Hampton
"""
import tkinter as tk

from view_utils import blend, fix_offset, get_circle_bounding_box, get_convoy_symbol_points, get_fleet_triangle_points, get_support_points
from display_object import Unit, Territory, Order
from diplomacy_adjudicator import DiplomacyAdjudicator, split_coast

# Palettes MUST have water, land, border, blank, players, tooltip, tooltip_text and supply.
# Optional extras: canal, coast, canal_water, active
DEFAULT_PALETTE = { # Copied from BackStabbr
    "water": "#ccf",
    "canal_water": "#bbe",
    "land": "#ddd",
    "border": "#111",
    "blank": "#fff",
    "supply": "#fff",
    "active": "#888",   # Averaged with existing colour
    "tooltip": "#444",
    "tooltip_text": "#eee",
    "players": [
        "#bb0",
        "#c00",
        "#0a0",
        "#99f",
        "#00a",
        "#000",
        "#b0b",
    ]
}

class DiplomacyWindow():
    def __init__(self, border_points, map_data, starting_builds, adjacency):
        # Data
        self.borders = fix_offset(border_points, 2)
        self.territories = {}
        self.units = {}
        self.team_indices = {}
        self.orders = []

        # GUI
        self.palette = DEFAULT_PALETTE
        self.root = tk.Tk()
        self.root.attributes("-fullscreen", True)
        self.canvas = tk.Canvas(self.root, height=800, width=900)
        self.highlighted = None
        self.ordering = None
        self.ordering_secondary = None
        self.order_type = None
        self.require_coast = []
        self.awaiting_coast = False

        self._fill_and_layout(map_data, starting_builds)
        self.adjudicator = DiplomacyAdjudicator(adjacency, self.territories, self.units)

        # And away we go
        self.redraw()
        self.root.mainloop()
    
    def redraw(self):
        # Territories
        self.canvas.tag_lower("territory_layer")
        self.canvas.tag_raise("territory_decoration_layer")
        self.canvas.tag_raise("coast_layer")

        # Units
        self.canvas.tag_raise("units")

        self.canvas.tag_raise("order_layer")
        self.canvas.tag_raise("ui_layer")

    def _fill_and_layout(self, map_data, starting_builds):
        self.canvas.grid(row=0, column=0, columnspan=2, rowspan=5)
        adjudicate_button = tk.Button(self.root, text="Adjudicate Orders", command=self._on_submit)
        adjudicate_button.grid(row=0, column=2)

        self._create_territories(map_data)
        self.create_units(starting_builds, starting=True)
        self.apply_colour_palette()
        self.bind_inputs()
    
    def _create_territories(self, map_data):
        for name in map_data.keys():
            border_points = [self.borders[i] for i in map_data[name]["borders"]]
            if "canal_points" in map_data[name].keys():
                map_data[name]["canal_points"] = [self.borders[i] for i in map_data[name]["canal_points"]]
            self.territories[name] = Territory(self.canvas, name, border_points, map_data[name])
    
    def create_units(self, builds, starting=False):
        """
        Create units. builds is expected to be a list of items with following structure:
        {
        "team_name": "Turkey",
        "builds": [
            {
            "location": "ANK",
            "unit_type": "Fleet"
            },
        ]
        }
        """
        i = 0
        for team in builds:
            if starting:
                self.units[team["team_name"]] = []
                self.team_indices[team["team_name"]] = i
                i += 1
            for unit in team["builds"]:
                position = self.get_unit_position(unit["location"])
                created = Unit(self.canvas, team["team_name"], unit["location"], position, unit["unit_type"])
                created.draw_shape()
                self.units[team["team_name"]].append(created)

                if starting:
                    self.territories[self.get_territory_name(unit["location"])].make_home_centre(self.canvas, team["team_name"])

    def apply_colour_palette(self):
        self.canvas.configure(bg=self.palette["blank"])

        # Territories
        for name in self.territories.keys():
            territory = self.territories[name]
            fill_colour = 'red' # Default, should be overridden
            match territory.type:
                case "ocean":
                    fill_colour = self.palette["water"]
                
                case "canal":
                    # Fill land
                    fill_colour = self.palette["land"]
                    if "canal" in self.palette.keys():
                        fill_colour = self.palette["canal"]
                    
                    # Fill the water in the canal
                    canal_fill=self.palette["water"]
                    if "canal_water" in self.palette.keys():
                        canal_fill=self.palette["canal_water"]
                    self.canvas.itemconfig(territory.canal_layer, fill=canal_fill)
                
                case "coast":
                    fill_colour = self.palette["land"]
                    if "coast" in self.palette.keys():
                        fill_colour = self.palette["coast"]
                
                case "land":
                    fill_colour = self.palette["land"]
            
            if territory.owned_by != None:
                fill_colour = blend(fill_colour, self.palette["players"][self.team_indices[territory.owned_by]], 3, 1)

            territory.shape.set_fill_colour(fill_colour)
            territory.shape.set_outline_colour(self.palette["border"])
            territory.shape.set_active_colour(blend(fill_colour, self.palette["active"], 2, 1))
            territory.shape.recolour()

            self.canvas.itemconfig("text", fill=self.palette["border"])
            self.canvas.itemconfig("coast_layer", outline=self.palette["border"])
            self.canvas.itemconfig("ui_layer", outline=self.palette["border"])
        
        # Units
        for team in self.units.keys():
            team_colour = self.palette['players'][self.team_indices[team]]
            for unit in self.units[team]:
                tile_colour = self.territories[self.get_territory_name(unit.location)].shape.fill_colour
                self.canvas.itemconfig(team, outline=team_colour, width=3, fill=blend(team_colour, tile_colour, 1, 1))
    
    def bind_inputs(self):
        self.root.bind("<Motion>", self._on_motion)
        self.root.bind("<Button>", self._on_click)
        self.root.bind("<Escape>", self._on_escape_press)
        self.root.bind("<s>", self._on_s_press)
        self.root.bind("<c>", self._on_c_press)

    def _on_escape_press(self, _event):
        self.ordering = None
        self.ordering_secondary = None
        self.order_type = None

    def _on_s_press(self, _event):
        self.ordering_secondary = None
        self.order_type = "support" if self.order_type != "support" else None
    
    def _on_c_press(self, _event):
        self.ordering_secondary = None
        self.order_type = "convoy" if self.order_type != "convoy" else None

    def _on_motion(self, event):
        mouse_location = [self.root.winfo_pointerx() - self.root.winfo_rootx(), self.root.winfo_pointery() - self.root.winfo_rooty()]
        if mouse_location[0] < 0 or mouse_location[0] > 900 or mouse_location[1] < 0 or mouse_location[1] > 800:
            if self.highlighted:
                self.territories[self.highlighted].shape.toggle_active(False)
                self.highlighted = None
            return
        tags = self.canvas.gettags(self.canvas.find_closest(*mouse_location))
        name = tags[0]
        if tags[1] != 'ui_layer':
            if tags[1] == 'coast_layer':
                self.highlighted = name
            return
        if self.highlighted != name:
            if self.highlighted:
                self.territories[self.get_territory_name(self.highlighted)].shape.toggle_active(False)
            self.highlighted = name
        territory = self.territories[name]
        territory.shape.toggle_active(True)
    
    def _on_click(self, _event):
        if not self.highlighted:
            return
        if self.adjudicator.get_current_phase() == "winter":
            if self.build_phase_click():
                self.draw_last_order()
            return
        if not self.ordering:
            for team in self.units.keys():
                for unit in self.units[team]:
                    if self.get_territory_name(unit.location) == self.highlighted:
                        self.ordering = unit
                        self.toggle_valid_moves(True)
                        return
        elif self.awaiting_coast:
            self.determine_coast()
        else:
            self.toggle_valid_moves(False)
            if self.order_type == None:
                _, location_1, unit_from_coast = split_coast(self.ordering.location)
                location_2 = self.highlighted
                
                if location_1 == self.highlighted:
                    self.order_type = "hold"
                    if unit_from_coast:
                        location_2 = f'{location_2}-{unit_from_coast}'

                else:
                    self.order_type = "move"
                    if self.highlighted in self.require_coast:
                        self.awaiting_coast = True
                        self.toggle_coast_choice(self.territories[self.highlighted], True)
                        return
                    if self.territories[self.highlighted].coasts and self.ordering.type == "Fleet":
                        location_2 = f'{location_2}-{self.adjudicator.get_legal_coast(self.ordering.location, self.highlighted)}'
                if self.ordering.pending_order:
                    self.orders.remove(self.ordering.pending_order)
                self.orders.append(self.ordering.give_order(self.order_type, location_1, location_2))
                self.ordering = None
                self.order_type = None
                self.draw_last_order()
            else:   # Convoy or support
                if self.ordering_secondary == None:
                    for team in self.units.keys():
                        for unit in self.units[team]:
                            if self.get_territory_name(unit.location) == self.highlighted:
                                self.ordering_secondary = unit
                                return
                else:
                    if self.ordering.pending_order:
                        self.orders.remove(self.ordering.pending_order)
                    self.orders.append(self.ordering.give_order(self.order_type, self.ordering_secondary.location, self.highlighted))
                    self.ordering = None
                    self.ordering_secondary = None
                    self.order_type = None
                    self.draw_last_order()
    
    def build_phase_click(self):
        territory = self.territories[self.highlighted]
        for team in self.units.keys():
            for unit in self.units[team]:
                if self.get_territory_name(unit.location) == territory.short_name:
                    if unit.pending_order:
                        unit.pending_order.erase(self.canvas)
                        unit.pending_order = None
                        return False
                    else:
                        order = unit.give_order("disband", unit.location, unit.location)
                        self.orders.append(order)
                        return True
        if not territory.buildable_for or territory.buildable_for != territory.owned_by:
            return False
        for order in self.orders:
            if order.location_1 == territory.short_name and order.type == "build":
                order.erase(self.canvas)
                if order.build_type == "Army":
                    order.build_type = "Fleet"
                    return True
                self.orders.remove(order)
                return False
        order = Order(None, "build", self.highlighted, self.highlighted)
        order.build_type = "Army"
        self.orders.append(order)
        return True

    def determine_coast(self):
        parts = self.highlighted.split('-')
        if len(parts) <= 1:
            return
        territory = self.territories[parts[0]]
        self.toggle_coast_choice(territory, False)
        if self.ordering.pending_order:
            self.orders.remove(self.ordering.pending_order)
        self.orders.append(self.ordering.give_order(self.order_type, self.ordering.location, self.highlighted))
        self.ordering = None
        self.order_type = None
        self.awaiting_coast = False
        self.draw_last_order()
    
    def toggle_coast_choice(self, territory, show):
        tag = f'{territory.short_name}-coast'
        if show:
            self.canvas.itemconfig(tag, state='normal')
            self.canvas.tag_raise(tag)
        else:
            self.canvas.tag_lower(tag)
            self.canvas.itemconfig(tag, state='hidden')

    def capture_centres(self):
        for team in self.units.keys():
            for unit in self.units[team]:
                territory = self.territories[self.get_territory_name(unit.location)]
                if territory.is_supply_centre:
                    territory.capture(team)
        self.apply_colour_palette()

    def _on_submit(self):
        moves_completed = self.adjudicator.adjudicate_moveset(self.orders)
        match self.adjudicator.get_current_phase():
            case "spring":
                for move in moves_completed:
                    move.unit.move(self.canvas, move.location_2, self.get_unit_position(move.location_2))
            case "autumn":
                for move in moves_completed:
                    move.unit.move(self.canvas, move.location_2, self.get_unit_position(move.location_2))
                self.capture_centres()
            case "winter":
                builds = []
                for build in moves_completed:
                    team = self.territories[build.location_1].owned_by
                    found = False
                    if build.type == "disband":
                        self.units[build.unit.team].remove(build.unit)
                        build.unit.delete()
                    else:   # build.type == "build":
                        for i in range(len(builds)):
                            if builds[i]["team_name"] == team:
                                index = i
                                found = True
                                break

                        if found == False:
                            builds.append({"team_name": team, "builds": []})
                            index = -1
                        
                        builds[index]["builds"].append({
                            "location": build.location_1,
                            "unit_type": build.build_type,
                        })
                self.create_units(builds)
                self.redraw()
                self.apply_colour_palette()
        self.adjudicator.update_territories(self.territories)
        self.adjudicator.update_units(self.units)
        self.adjudicator.step_phase()
        # Remove old orders
        self.canvas.delete('order')
        for order in self.orders:
            if order.unit:
                order.unit.pending_order = []
        self.orders = []
    
    def toggle_valid_moves(self, show):
        thickness = 1
        require_coast = []
        if show:
            thickness = 2
        moves = self.adjudicator.get_legal_moves_for_unit(self.ordering.type, self.ordering.location)
        for move in moves + [self.ordering.location]:
            parts = move.split('-')
            name = parts[0]
            if len(parts) > 1 and show:
                require_coast.append(name)
            territory = self.territories[name]
            self.canvas.itemconfig(territory.ui, width=thickness)
        
        require_coast = list({coast for coast in require_coast if require_coast.count(coast) > 1})
        if show:
            self.require_coast = require_coast

    def get_territory_name(self, location_str):
        parts = location_str.split("-")
        return parts[0]

    def get_unit_position(self, location_str):
        """Handles some location strings having -<coast>"""
        parts = location_str.split("-")
        territory = self.territories[parts[0]]
        if len(parts) == 1:
            return territory.unit_position
        return territory.coasts[parts[1]]

    def draw_last_order(self):
        implied_order = '#aa1'
        last = self.orders[-1]
        start_position = self.get_unit_position(last.location_1)
        end_position = self.get_unit_position(last.location_2)
        match last.type:
            case "move":
                last.add_shape(self.canvas.create_line(start_position, end_position, arrow="last", arrowshape=(15, 15, 7), fill='#111', width='2', tags=("order", "order_layer")))
            case "hold":
                last.add_shape(self.canvas.create_oval(*get_circle_bounding_box(start_position, 14), outline='#111', width='2', tags=("order", 'order_layer')))
            case "convoy":
                last.add_shape(self.canvas.create_line(start_position, end_position, arrow="last", fill=implied_order, tags=("order", 'order_layer')))
                last.add_shape(self.canvas.create_line(*get_convoy_symbol_points(last.unit.position), fill='#111', width='2', tags=("order", 'order_layer')))
            case "support":
                points = get_support_points(last.unit.position, start_position, end_position)
                last.add_shape(self.canvas.create_line(*points, smooth="bezier", dash=(4,6), fill='#111', width=2, tags=("order", 'order_layer')))
                last.add_shape(self.canvas.create_oval(*get_circle_bounding_box(points[-2:], 4), fill='', outline='#111', tags=("order", 'order_layer')))
            case "build":
                if last.build_type == "Army":
                    last.add_shape(self.canvas.create_oval(get_circle_bounding_box(start_position, 7), fill='', width='3', outline='#111', dash=(16,2), tags=("order", "order_layer")))
                else:
                    last.add_shape(self.canvas.create_polygon(get_fleet_triangle_points(start_position), fill='', width='3', outline='#111', dash=(16,2), tags=("order", "order_layer")))
            case "disband":
                points = get_circle_bounding_box(start_position, 9)
                last.add_shape(self.canvas.create_line(points[0], points[1], [points[2], points[3]], *last.unit.position, points[2], points[1], points[0], points[3], \
                                                       fill='#c11', width=3, tags=("order", 'order_layer')))

def run_tests():
    ROOT_ATTRIBUTES = ["adjacency", "map_data", "starting_builds"]
    NODE_ATTRIBUTES = ["type", "is_supply_centre", "full_name", "location"]
    import map_loader
    data = map_loader.load_from_JSON("./Maps/default.json", ROOT_ATTRIBUTES)

    DiplomacyWindow(data["border_points"], data["map_data"], data["starting_builds"], data["adjacency"])

if __name__ == "__main__":
    run_tests()
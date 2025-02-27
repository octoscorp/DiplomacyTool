"""
file: diplomacy_utils.py
Backend utils for diplomacy.

Implements stub classes for Phase, Order, Unit, and Territory. This should allow
implementations to abstract away some of the basic functionality, and draw on base
enums for type.
  Phase: WINTER, SPRING, AUTUMN
  Order: DISBAND, BUILD, HOLD, MOVE, SUPPORT, CONVOY
  Unit: ARMY, FLEET
  Territory: LAND, OCEAN, COAST, CANAL
"""

class Phase:
    # Types of phase
    WINTER = _first_phase = 0
    SPRING = 1
    AUTUMN = _last_phase = 2

    @staticmethod
    def get_next_phase(current_phase):
        if current_phase == Phase._last_phase:
            return Phase._first_phase
        return current_phase + 1

class Order:
    # Types of order
    DISBAND = 0
    BUILD = 1
    HOLD = 2
    MOVE = 3
    SUPPORT = 4
    CONVOY = 5

    @staticmethod
    def from_string(order_string):
        """
        Create an order from the given string.
        
        Example order strings:
        - Hold: "A SMY H"
        - Move: "A BUL -> CON"
        - Support: "F BLA S A BUL -> CON"
        - Convoy: "F AEG C A BUL -> CON"
        - Build: "build F CON"
        - Disband: "disband A BUL"

        Counterpart accomplished with __str__
        """

        parts = order_string.split()
        if parts[0] in ["disband", "build"]:
            return Order(Order._type_from_string(parts[0]), (Unit.type_from_string(parts[1]), parts[2]))
        
        ord_unit = (Unit.type_from_string(parts[0]), parts[1])
        ord_type = Order._type_from_string(parts[2])

        if ord_type == Order.HOLD:
            return Order(ord_type, ord_unit)
        if ord_type == Order.MOVE:
            return Order(ord_type, ord_unit, end_destination=parts[3])
        
        helped_unit = (Unit.type_from_string(parts[3]), parts[4])
        helped__ord_type = Order._type_from_string(parts[5])
        end_destination = parts[4]

        if helped__ord_type == Order.MOVE:
            end_destination = parts[6]
        
        return Order(ord_type, ord_unit, end_destination=end_destination, helped_unit=helped_unit)
    
    @staticmethod
    def _type_from_string(order_partial_string):
        match order_partial_string:
            case 'disband':
                return Order.DISBAND
            case 'build':
                return Order.BUILD
            case 'H':
                return Order.HOLD
            case '->':
                return Order.MOVE
            case 'S':
                return Order.SUPPORT
            case 'C':
                return Order.CONVOY
            case _:
                return Order.HOLD
    
    @staticmethod
    def _string_from_type(order_type):
        match order_type:
            case Order.BUILD:
                return 'build'
            case Order.DISBAND:
                return 'disband'
            case Order.HOLD:
                return 'H'
            case Order.MOVE:
                return '->'
            case Order.SUPPORT:
                return 'S'
            case Order.CONVOY:
                return 'C'
            case _:
                raise ValueError('This implementation only handles orders for: BUILD, HOLD, MOVE, SUPPORT, and CONVOY. That was none of these.')
    
    def __str__(self):
        """ Create the string representation of this order """
        if self.type in [Order.BUILD, Order.DISBAND]:
            return f"{Order._string_from_type(self.type)} {Unit.string_from_type(self.unit_type)} {self.unit_location}"
        order = f"{self.unit_type} {self.unit_location} {self.type}"
        if self.type == Order.MOVE:
            order += f" {self.end_dest}"
        if self.type <= Order.MOVE:
            # Hold and move
            return order
        
        order += f" {self.helped_u_type} {self.helped_u_location} {Order._string_from_type(self.type)}"
        if self.type == Order.SUPPORT and self.end_dest == self.helped_u_location:
            # Support-hold
            return order
        # Support-move, convoy
        return order + f" {self.end_dest}"
        

    def __init__(self, ord_type, unit, end_destination=None, helped_unit=None):
        """
        unit and helped_unit should be (type, location) tuples.
        If supporting a unit to hold, set end_destination the same as helped_unit location
        """
        # Set on all orders
        self.unit_type = unit[0]
        self.unit_location = unit[1]
        self.type = ord_type
        
        # Optional args
        # End destination of move, support, or convoy
        self._end_dest = end_destination
        self._helped_u_type = helped_unit[0]
        self._helped_u_location = helped_unit[1]

        # Fancy rubbish - different names for the same function. This feels a little silly for
        # get methods in python (since the variables are all public anyway), but would be a
        # great format for set methods.
        self.get_move_destination = self._get_end_dest
        self.get_supported_unit_destination = self._get_end_dest
        self.get_convoyed_unit_destination = self._get_end_dest

        self.get_supported_unit_type = self._get_helped_u_type
        self.get_convoyed_unit_type = self._get_helped_u_type

        self.get_supported_unit_start_location = self._get_helped_u_location
        self.get_convoyed_unit_start_location = self._get_helped_u_location
    
    # The following get function groups are effectively overloaded definitions, where the
    # function name is changed instead of the arguments. Ideal syntax would be some
    def _get_end_dest(self):
        """
        Return the destination of the move being made/supported/convoyed
        """
        return self._end_dest
    
    def _get_helped_u_type(self):
        """
        Return the type of the unit being supported/convoyed
        """
        return self._helped_u_type
    
    def _get_helped_u_location(self):
        """
        Return the location of the unit being supported/convoyed
        """
        return self._helped_u_location

class Unit:
    # Type enumeration
    ARMY = 0
    FLEET = 1

    @staticmethod
    def type_from_string(type_string):
        match type_string:
            case 'A':
                return Unit.ARMY
            case 'F':
                return Unit.FLEET
            case _:
                return Unit.ARMY
    
    @staticmethod
    def string_from_type(unit_type):
        match unit_type:
            case Unit.ARMY:
                return 'A'
            case Unit.FLEET:
                return 'F'
            case _:
                raise ValueError("This class only implements Army and Fleet types, and that was neither!")

    def __init__(self, unit_type, unit_location, unit_team):
        self.type = unit_type
        self.location = unit_location
        self.team = unit_team

        self._order = None
    
    def set_order(self, order):
        self._order = order
    
    def get_order(self):
        return self._order

class Territory:
    """
    Stub class which territory implementations should inherit (or emulate, if you like re-inventing wheels).

    Implements:
    - Type enumeration for LAND, OCEAN, COAST, CANAL
    """

    # Type enumeration
    LAND = 0
    OCEAN = 1
    COAST = 2
    CANAL = 3

    @staticmethod
    def type_from_string(type_string):
        match type_string:
            case 'land':
                return Territory.LAND
            case 'ocean':
                return Territory.OCEAN
            case 'coast':
                return Territory.COAST
            case 'canal':
                return Territory.CANAL
            case _:
                raise ValueError("This only implements types LAND, OCEAN, CANAL, and COAST. That was none of these")
    
    # I see no use case for this method (especially in the adjudication end). Leaving it around for completeness.

    # @staticmethod
    # def string_from_type(territory_type):
    #     match territory_type:
    #         case Territory.LAND:
    #             return 'land'
    #         case Territory.OCEAN:
    #             return 'ocean'
    #         case Territory.COAST:
    #             return 'coast'
    #         case Territory.CANAL:
    #             return 'canal'
    #         case _:
    #             raise ValueError("This only implements types LAND, OCEAN, CANAL, and COAST. That was none of these")


    def __init__(self,
            name,
            supply_centre=False,
            adjacency={
                Unit.FLEET: [],
                Unit.ARMY: []},
            type=LAND,
            full_name=None
            ):
        """
        Note that name should functionally be an index; full_name is decorative
        """
        # Arg handling
        self.name = name
        self._supply_centre = supply_centre
        self._army_adjacent = adjacency[Unit.ARMY]
        self._fleet_adjacent = adjacency[Unit.ARMY]
        self._type = type
        self.full_name = full_name if full_name != None else name
    
    def is_supply_centre(self):
        """ Returns bool of whether this territory is a supply centre """
        return self._supply_centre
""" Backend utils for diplomacy """

# Enums
class Phase:
    # Types of phase
    WINTER = 0
    SPRING = 1
    AUTUMN = 2

# Stub classes
class Order:
    # Types of order
    BUILD = 0
    HOLD = 1
    MOVE = 2
    SUPPORT = 3
    CONVOY = 4

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
        """

        parts = order_string.split()
        if parts[0] == "build":
            return Order(Order.BUILD, (Unit.type_from_string(parts[1]), parts[2]))
        
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
    def to_string(order):
        pass

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

    def __init__(self,
            name,
            supply_centre=False,
            adjacency={
                Unit.FLEET: [],
                Unit.ARMY: []},
            type=Territory.LAND,
            full_name=None
            ):
        """
        Note that name should functionally be an index; full_name is decorative
        """
        # Arg handling
        self.name
        self._supply_centre
        self._army_adjacent
        self._fleet_adjacent
        self._type
        self.full_name = full_name if full_name !== None else name
    
    def is_supply_centre(self):
        """ Returns bool of whether this territory is a supply centre """
        return self._supply_centre
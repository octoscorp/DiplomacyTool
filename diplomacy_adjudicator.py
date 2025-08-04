"""
Class for adjudicating Diplomacy moves

Date: 10/6/2024
Author: G Hampton
"""
from diplomacy_utils import Order, Phase, Unit, Territory, TerritoryMap


class BaseAdjudicator():
    """
    An interface, which adjudicators should extend. Implements stubs of all test-interfacing methods and
    some bare-minimum methods and attributes to interact with them
    """
    def __init__(self, starting_units: dict[str, list[Unit]]):
        self.phase = Phase.SPRING
        self.units = starting_units
        self._update_unit_locations()

    def adjudicate_moveset(self, moveset):
        """
        Return a set of the moves which succeed.
        If your adjudicator returns other moves (e.g. valid supports), override
        the test_adjudicate_moveset to filter only moves before returning
        """
        # Override this method!
        raise NotImplementedError

    def set_units(self, new_units: dict[str, list[Unit]]):
        """ Replace existing unit dict with new_units """
        self.units = new_units
        self._update_unit_locations()

    def add_unit(self, unit):
        if unit.team not in self.units.keys():
            self.units[unit.team] = []
        self.units[unit.team].append(unit)
        self._update_unit_locations(unit)

    def _update_unit_locations(self, added_unit: Unit=None):
        """
        (Re)populates _units_by_location based on current units. If
        added_unit is passed, adds that unit without regenerating.
        """
        if added_unit != None:
            # Don't regenerate in this circumstance
            self._units_by_location[added_unit.location] = added_unit
            return
        self._units_by_location = {}
        for unit_list in self.units.values():
            for unit in unit_list:
                self._units_by_location[unit.location] = unit

    def apply_moves(self, moves: list[Order]):
        """
        Move units based on the moveset. This should already have been validated.
        """
        pass

    def get_unit_at_location(self, location_str):
        try:
            return self._units_by_location[location_str]
        except KeyError:
            if Territory.get_coast(location_str):
                return self.get_unit_at_location(Territory.remove_coast(location_str))
        return None

    # Tester interface
    def test_remove_all_units(self):
        self.set_units({})

    def test_create_unit(self, unit):
        self.add_unit(Unit(
            Unit.type_from_string(unit["type"]),
            unit["location"],
            unit["team"]
        ))

    def test_set_phase(self, phase):
        self.phase = phase

    def test_string_to_order(self, string):
        return Order.from_string(string)

    def test_order_to_string(self, order):
        # Verify that the tester has given an actual Order (isinstance should allow for subclasses too)
        assert(isinstance(order, Order))
        return str(order)

    def test_adjudicate_moveset(self, moveset):
        # Check that the tester has sent the moveset in a structure we expect, i.e.
        # {
        #     "TEAM": [
        #         "Order1",
        #         "..."
        #     ]
        # }
        for team in moveset.keys():
            assert(type(moveset[team]) is list)
            for order in moveset[team]:
                assert(isinstance(order, Order))
        return self.adjudicate_moveset(moveset)

    # Optionally override to define your own intentional failures.
    def test_get_intentional_failures(self):
        """
        This function returns a list of the test cases which this adjudicator fails intentionally.
        Format:
        {
            MODULE_NAME: [
                (index, reason)
            ]
        }
        """
        return {}


class DiplomacyAdjudicator(BaseAdjudicator):
    def __init__(self, territories: TerritoryMap, starting_units):
        super(starting_units)
        self.territories = territories

        # TODO: implement retreats
        self.retreats = []

        # TODO: Reimplement build turn validation
        # self.counts_last_round = {team: 0 for team in starting_units.keys()}
        # for name in self.territories.keys():
        #     team = self.territories[name].owned_by
        #     if team:
        #         self.counts_last_round[team] += 1

    def step_phase(self):
        self.phase = Phase.get_next_phase(self.phase)

    def get_changes(self):
        """Really well-formatted way to get the change in number of SCs for each team"""
        return {
            team_name: len([self.territories[name] for name in self.territories.keys() if self.territories[name].owned_by == team_name]) - self.counts_last_round[team_name]
            for team_name in self.units.keys()}

    def adjudicate_builds(self, orders):
        valid = []
        changes = self.get_changes()

        # TODO: get str-manipulating splits out of this functionality, decouple
        for build in orders:
            location = build.unit_location
            team = self.territories[Territory.remove_coast(location)].owned_by if not build.unit else build.unit.team

            if not team:
                continue

            if changes[team] > 0:
                if build.type != Order.BUILD:
                    continue
                # Fleets cannot be build inland
                if self.territories[location].type == Territory.LAND and build.unit_type == Unit.FLEET:
                    continue
                if team == self.territories[location].buildable_for:
                    # Do not allow building where there is already a unit
                    flag = False
                    for unit_team in self.units.keys():
                        for unit in self.units[unit_team]:
                            if unit.location.split('-')[0] == location:
                                flag = True
                                break
                    if flag:
                        continue
                    valid.append(build)
            if changes[team] < 0:
                if build.type != Order.DISBAND:
                    continue
                # Disband
                # TODO: Check if team has a unit where it has ordered to disband.
                valid.append(build)
        return valid

    def adjudicate_moveset(self, orders):
        # Overriding abstract implementation
        match Phase.get_phase_type(self.get_current_phase()):
            case Phase.BUILD:
                return self.adjudicate_builds(orders)
            case Phase.RETREAT:
                return self._adjudicate_retreat(orders)
            case Phase.STANDARD | \
                 _:
                return self._adjudicate_standard(orders)

    def _adjudicate_standard(self, orders):
        """
        Non-build and non-retreat turn
        """
        check_for_convoys = []
        moves = []
        holds = []
        supports = []
        convoys = []
        self.retreats = []

        for order in orders:
            is_valid = self.validate_order(order)
            if not is_valid:
                if order.type == Order.MOVE and order.unit_type == Unit.ARMY:
                    # A unit can't move to its own location
                    if order.get_move_start() != order.get_move_destination():
                        check_for_convoys.append(order)
                continue
            match order.type:
                case Order.MOVE:
                    moves.append(order)
                case Order.SUPPORT:
                    supports.append(order)
                case Order.CONVOY:
                    convoys.append(order)
                case Order.HOLD | \
                     _:
                    holds.append(order)

        convoyed = self.check_convoys(check_for_convoys, convoys)
        moves += convoyed
        
        self.add_support(supports, moves, holds, convoys)
        retreats = self.compare_strength(supports, moves, holds, convoys)
        self.remove_broken_convoys(convoyed, moves, convoys)
        return moves

    def _adjudicate_retreat(self, orders):
        pass

    def remove_broken_convoys(self, convoyed, moves, convoys):
        """
        For each convoyed move, remove all convoy routes which are not possible
        due to not having a convoying unit on that route.
        """
        convoying_locations = [convoy.unit.location for convoy in convoys]
        for move in convoyed:
            to_delete = []
            for route in move.convoy_routes:
                for space in route:
                    if space not in convoying_locations:
                        to_delete = route
                        break
            if len(to_delete) >= len(move.convoy_routes):
                moves.remove(move)

    def add_support(self, supports, moves, holds, convoys):
        """Add support to moves, holds, and convoys"""
        # For each support order
        for support in supports:
            # Set a flag "cut" to False
            support_is_cut = False
            # For each move order
            for move in moves:
                if move.get_move_destination() == support.get_supporting_unit_location() and
                        support.get_supported_unit_destination() != move.get_move_start() and
                        move.team != support.team:
                # If move destination == support origin and support destination != move origin and support team != move team
                    # If support has a supported order
                        # Remove strength 1 from that order
                    # Add a hold order for this unit
                    # Set cut to true
                    # Stop searching through moves
                # Elif move origin == supported origin and move dest == support dest
                    # Set the support's supported order
                    # Add strength 1 to that order
            # If cut is raised
                # Exit now
            # For each hold order:
                # If hold location = supported hold location
                    # Set support's supported order
                    # Add strength 1 to hold
                    # break
            # For each convoy
                # If support start == convoy unit location and support is to hold
                    # Set supported order; add strength 1
        pass

    def compare_strength(self, supports, moves, holds, convoys):
        """Compare the strength of all orders"""
        # Create a dict of contested locations called contests
        # For each move
            # if destination not in contests
                # init to empty list

            # add this move to contests for destination
            # For each other move
                # If it goes to the same destination, or attempts a direct swap with this move
                    # Add it to opposed contests

        # Handle the "opposed" moves
        # For each hold (/support/convoy)
            # If the location is in contests
                # Add the hold order to the list

        # Determine which units win

        # For each contested space
            # for each order listed for that space
                # create an individual list?
                # if hold, add to own var?

            # self._get_successful_move (moves)

            # if that is not empty
                # winning = True
                # If there is still a hold
                    # If hold strength < move strength
                        # Remove hold from successful orders

                        # Add hold to retreats
                    # else:
                        # winning = False
                # if winning:
                    # Remove winning move from local list
            # For remaining local moves, enter a hold
            
            # Return retreats
        pass


    def _get_successful_move(self, move_list):
        """Return the move of `move_list` which is most successful"""
        # If empty return None
        # If len 1 return first
        # sort by strength
        # if first strength > second strength
            # Return first
        # return none
        pass

    def _handle_opposed(self, contests, retreats, moves, holds):
        # While there are opposing moves
            # pop one
            # For each other move
                # If other start = move dest and move start = other dest
                    # Remove from opposed; break
            # if move strength > other strength:
                # add move to success, other to retreats
            # same other way around
            # else:   # Bounce
                # Remove move, other from successful moves
                # add hold orders for both units
        pass

    def check_convoys(self, moves_to_check, convoys):
        """
        Check `moves_to_check` for convoys. Remove any with no convoy support.
        """
        convoyed_moves = []
        convoys_by_move = {}

        # Collate convoys by the move that they are trying to convoy
        for convoy in convoys:
            if (convoy.location_1, convoy.location_2) not in convoys_by_move.keys():
                convoys_by_move[(convoy.location_1, convoy.location_2)] = []
            convoys_by_move[(convoy.location_1, convoy.location_2)].append(convoy)

        # For each move, check if it's being convoyed.
        for move in moves_to_check:
            transport = (move.location_1, move.location_2)
            if transport not in convoys_by_move.keys():
                break

            # Get the relevant convoys and possible routes
            used_convoys = convoys_by_move[transport]
            routes = self.get_connecting_routes(move, used_convoys)
            if len(routes) > 0:
                convoyed_moves.append(move)

            # Add each route to the move order for future evaluation
            for route in routes:
                move.convoy_routes.append(route)

        # Return all moves which get convoyed
        return convoyed_moves

    def get_connecting_routes(self, move, convoys):
        """Get all possible convoy routes which connect move start to end"""
        convoy_locations = [convoy.unit.location for convoy in convoys]
        routes = []
        self.get_all_paths(move.location_1, move.location_2, [], [], routes, convoy_locations + [move.location_2])
        return routes

    def get_all_paths(self, current, destination, visited, path, routes, convoy_locations):
        """
        Get all paths connecting start to end in fleet adjacency
        TODO: Is this valid? Do we need to check that a coastal fleet cannot convoy?
        """
        visited.append(current)
        path.append(current)
        if current == destination:
            # Sliced to avoid last one
            routes.append(path[1:-1])
        else:
            for vertex in self.adjacency["fleet"][current]:
                if vertex not in visited and vertex in convoy_locations:
                    self.get_all_paths(vertex, destination, visited, path, routes, convoy_locations)
        visited.remove(current)
        path.remove(current)

    def validate_order(self, order: Order):
        """Return a boolean of whether an order is valid or not."""
        is_valid = False
        unit = self.get_ordered_unit(order)
        if unit == None:
            return is_valid

        match order.type:
            case Order.MOVE | \
                 Order.SUPPORT:
                is_valid = self._validate_move_or_support(order, unit)
            case Order.CONVOY:
                is_valid = self._validate_convoy(order)
            case Order.HOLD:
                is_valid = True
        return is_valid

    def get_ordered_unit(self, order: Order):
        """Consult with storage of unit locations"""
        return self.get_unit_at_location(order.get_ordered_unit_location())

    def _validate_move_or_support(self, order: Order, unit: Unit):
        """
        Helper for validate_order. Check that the order destination is valid.
        This exploits the fact that get_move_destination and
        get_supported_unit_destination wrap the same function, so move and
        support are validated the same way.
        """
        # Cannot move/support to own location
        if order.get_ordered_unit_location() == order.get_order_destination():
            return False

        # Check the end point is on the legal list
        legal_dests = self.get_legal_destinations_for_order(order, unit)
        for dest in legal_dests:
            if dest == order.get_order_destination():
                return True
        return False

    def _validate_convoy(self, order):
        """
        Helper for validate_order. Check that the convoying unit is in Ocean, and the
        convoyed unit start/destination are on the shore.
        """
        shared_types = [Territory.CANAL, Territory.COAST]
        return self.territories[order.get_convoying_unit_location].type == Territory.OCEAN and \
            self.territories[order.get_convoyed_unit_start].type in shared_types and \
            self.territories[order.get_convoyed_unit_destination].type in shared_types

    def get_legal_destinations_for_order(self, order: Order, unit: Unit):
        """
        Return the set of legal locations for this unit to move given its type and starting location.
        This set is stripped of coast.
        """
        # Supports CAN go to an unreachable coast, Moves CANNOT

        # TerritoryMap.getneighbours(unit) gives adjacencies to the unit

        legal_moves = []
        if unit_type == Unit.ARMY:
            valid_types = [Territory.CANAL, Territory.COAST, Territory.LAND]
        if unit_type == Unit.FLEET:
            valid_types = [Territory.CANAL, Territory.COAST, Territory.OCEAN]

        start_terr = Territory.remove_coast(unit_location)
        start_coast = Territory.get_coast(unit_location)

        for location in self.adjacency[unit_type][start_terr]:
            from_coast, location, to_coast = split_coast(location)
            if unit_from_coast != None:
                if from_coast == None or from_coast != unit_from_coast:
                    continue
            territory = self.territories[location]
            if territory.type in valid_spaces:    
                if to_coast:
                    # TODO: str-format
                    location = f'{location}-{to_coast}'
                legal_moves.append(location)

        return legal_moves

    def get_legal_coast(self, unit_location, unit_destination):
        _, unit_location, unit_from_coast = split_coast(unit_location)
        if unit_destination == unit_location:
            if not unit_from_coast:
                return ''
            return unit_from_coast
        for location in self.adjacency["fleet"][unit_location]:
            from_coast, location, to_coast = split_coast(location)
            if location != unit_destination:
                continue
            if unit_from_coast != None:
                if from_coast == None or from_coast != unit_from_coast:
                    continue
            return to_coast

    # Overriding!
    def test_get_intentional_failures(self):
        """ This function returns a list of the test cases which this adjudicator fails intentionally. """
        return {
            "DATC_3.1": [
                ("6.A.6", "This is intended for a sandbox environment"),    # Ordering a unit of another country - this is intended for a sandbox environment.
                ("6.B.7", "Usage in face-to-face play should be a little more generous"),    # Supporting own unit with unspecified coast - this is intended for use in face-to-face play, so is a little more generous.
            ],
        }


class DefaultAdjudicator():
    """
    A wrapper to allow instantiation with no init arguments. Useful in decoupling tests.
    Does NOT have any units loaded to start with.
    """
    def __init__(self):
        import json_loader
        data = json_loader.load_from_JSON("./data/maps/default.json")

        # Create territories
        territories = {}
        for name in data["map_data"].keys():
            territory = data["map_data"][name]
            territories[name] = Territory(name,
                                          supply_centre=territory["is_supply_centre"],
                                          type=Territory.type_from_string(territory["type"]),
                                          # TODO: add adjacencies here, or remove from territories
                                          full_name=territory["full_name"])

        return DiplomacyAdjudicator(data["adjacency"], territories, units={})

def run_tests():
    '''Acceptance testing'''
    # Default test case is latest DATC
    import diplomacy_test
    diplomacy_test.main()

if __name__ == "__main__":
    run_tests()
"""
Class for adjudicating Diplomacy moves

Date: 10/6/2024
Author: G Hampton
"""
import diplomacy_utils


class BaseAdjudicator():
    """
    An interface, which adjudicators should extend. Implements stubs of all test-interfacing methods
    """
    def __init__(self):
        self.phase = Phase.SPRING
        self.units = {}

    # Override this!
    def adjudicate_moveset(self, moveset):
        raise NotImplementedError
    
    def set_units(self, new_units):
        """ Replace existing unit dict with new_units """
        self.units = new_units
    
    def add_unit(self, unit):
        if unit.team not in self.units.keys():
            self.units[unit.team] = []
        self.units[unit.team].append(unit)

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
        # Check that the tester has sent the moveset in a structure we expect
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
    def __init__(self, adjacency, territories, units):
        super()
        self.adjacency = adjacency
        self.territories = territories
        self.set_units(units)

        self.retreats = []
        self.counts_last_round = {team: 0 for team in units.keys()}
        for name in self.territories.keys():
            team = self.territories[name].owned_by
            if team:
                self.counts_last_round[team] += 1
    
    def step_phase(self):
        self.phase = Phase.get_next_phase(self.phase)
    
    def get_changes(self):
        return {
            team_name: len([self.territories[name] for name in self.territories.keys() if self.territories[name].owned_by == team_name]) - self.counts_last_round[team_name]
        for team_name in self.units.keys()}

    def adjudicate_builds(self, orders):
        valid = []
        changes = self.get_changes()

        # TODO: get str-manipulating splits out of this functionality, decouple
        for build in orders:
            name = build.location_1.split('-')[0]
            team = self.territories[name].owned_by if not build.unit else build.unit.team

            if not team:
                continue

            if changes[team] > 0:
                if build.type != Order.BUILD:
                    continue
                # Build
                if self.territories[name].type == Territory.LAND and build.build_type == Unit.FLEET:
                    continue
                if team == self.territories[name].buildable_for:
                    flag = False
                    for unit_team in self.units.keys():
                        for unit in self.units[unit_team]:
                            if unit.location.split('-')[0] == name:
                                flag = True
                                break
                    if flag:
                        continue
                    valid.append(build)
            if changes[team] < 0:
                if build.type != Order.DISBAND:
                    continue
                # Disband
                valid.append(build)
        return valid

    def adjudicate_moveset(self, orders, allow_retreats=True):
        if self.get_current_phase() == Phase.WINTER:
            return self.adjudicate_builds(orders)
        check_for_convoys = []
        moves = []
        holds = []
        supports = []
        convoys = []
        self.retreats = []

        for order in orders:
            is_valid = self.validate_order(order)
            if not is_valid:
                if order.type == Order.MOVE and order.location_1 != order.location_2 and order.unit.type == Unit.ARMY:
                    check_for_convoys.append(order)
                continue
            match order.type:
                case Order.MOVE:
                    moves.append(order)
                case Order.SUPPORT:
                    supports.append(order)
                case Order.CONVOY:
                    convoys.append(order)
                case ORDER.HOLD:
                    holds.append(order)
        
        convoyed = self.check_convoys(check_for_convoys, convoys)
        moves += convoyed
        
        self.add_support(supports, moves, holds, convoys)
        retreats = self.compare_strength(supports, moves, holds, convoys)
        self.remove_broken_convoys(convoyed, moves, convoys)
        if allow_retreats:
            self.retreats = retreats
        return moves

    def remove_broken_convoys(self, convoyed, moves, convoys):
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
        for i in range(len(supports)):
            support = supports[i]
            cut = False
            for move in moves:
                if move.location_2 == support.unit.location:
                    if support.location_2 != move.location_1 and support.unit.team != move.unit.team:
                        # This support is cut!
                        if support.supported_order:
                            support.supported_order.remove_strength()
                        holds.append(support.unit.give_order(Order.HOLD, support.unit.location, support.unit.location))
                        cut = True
                        break
                elif move.location_1 == support.location_1 and move.location_2 == support.location_2:
                    support.supported_order = move
                    move.add_strength()
            if cut:
                break
            for hold in holds:
                if hold.location_1 == support.location_1:
                    if hold.location_2 == support.location_2:
                        support.supported_order = hold
                        hold.add_strength()
                    break
            for convoy in convoys:
                if support.location_1 == convoy.unit.location and support.location_2 == convoy.unit.location:
                    convoy.add_strength()

    def compare_strength(self, supports, moves, holds, convoys):
        contests = {"opposed": []}
        retreats = []
        for move in moves:
            if move.location_2 not in contests.keys():
                contests[move.location_2] = []
            contests[move.location_2].append(move)
            for move_2 in moves:
                if move == move_2:
                    continue
                if (move_2.location_1 == move.location_2 and move_2.location_2 == move.location_1) or move.location_2 == move_2.location_2:
                    contests["opposed"].append(move)
        self._handle_opposed(contests, retreats, moves, holds)
        for hold in holds + supports + convoys:
            if hold.unit.location in contests.keys():
                contests[hold.unit.location].append(hold)
        
        # Determine which units win
        for name in [key for key in contests.keys() if len(contests[key]) > 1]:
            m = []
            h = None
            for order in contests[name]:
                if order.type == Order.MOVE and order in moves:
                    moves.remove(order)
                    m.append(order)
                else:
                    h = order
            
            best_move = self._get_successful_move(m)
            if best_move:
                winning = True
                if h:
                    if h.strength < best_move.strength:
                        match h.type:
                            case Order.HOLD:
                                holds.remove(h)
                            case Order.SUPPORT:
                                print("Support gets broken here, but still detected as move?")
                                supports.remove(h)
                            case Order.CONVOY:
                                convoys.remove(h)
                        retreats.append(h)
                    else:
                        winning = False
                if winning:
                    m.remove(best_move)
                    moves.append(best_move)
            for move in m:
                holds.append(move.unit.give_order(Order.HOLD, move.unit.location, move.unit.location))
            return retreats
        
            
    def _get_successful_move(self, move_list):
        if not move_list:
            return None
        if len(move_list) == 1:
            return move_list[0]
        order = sorted(move_list, reverse=True, key=lambda x: x.strength)
        if order[0].strength > order[1].strength:
            return order[0]
        else:
            return None
            
    def _handle_opposed(self, contests, retreats, moves, holds):
        while len(contests['opposed']) > 0:
            move = contests['opposed'].pop()
            for i in range(len(contests['opposed'])):
                counterpart = contests['opposed'][i]
                if counterpart.location_1 == move.location_2 and counterpart.location_2 == move.location_1:
                    del contests['opposed'][i]
                    break
            if move.strength > counterpart.strength:
                retreats.append(counterpart)
                moves.remove(counterpart)
            elif move.strength < counterpart.strength:
                retreats.append(move)
                moves.remove(move)
            else:   # Bounce
                if move in moves:
                    moves.remove(move)
                if counterpart in moves:
                    moves.remove(counterpart)
                holds.append(move.unit.give_order(Order.HOLD, move.unit.location, move.unit.location))
                holds.append(counterpart.unit.give_order(Order.HOLD, counterpart.unit.location, counterpart.unit.location))
        del contests['opposed']

    def check_convoys(self, moves_to_check, convoys):
        convoyed_moves = []
        convoys_by_move = {}
        for convoy in convoys:
            if (convoy.location_1, convoy.location_2) not in convoys_by_move.keys():
                convoys_by_move[(convoy.location_1, convoy.location_2)] = []
            convoys_by_move[(convoy.location_1, convoy.location_2)].append(convoy)
        
        for move in moves_to_check:
            transport = (move.location_1, move.location_2)
            if transport not in convoys_by_move.keys():
                break
            used_convoys = convoys_by_move[transport]
            routes = self.get_connecting_routes(move, used_convoys)
            if len(routes) > 0:
                convoyed_moves.append(move)
            for route in routes:
                move.convoy_routes.append(route)

        return convoyed_moves
    
    def get_connecting_routes(self, move, convoys):
        convoy_locations = [convoy.unit.location for convoy in convoys]
        routes = []
        self.get_all_paths(move.location_1, move.location_2, [], [], routes, convoy_locations + [move.location_2])
        return routes
    
    def get_all_paths(self, current, destination, visited, path, routes, convoy_locations):
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

    def validate_order(self, order):
        legal_moves = self.get_legal_moves_for_unit(order.unit.type, order.unit.location)
        is_valid = False
        match order.type:
            case Order.MOVE:
                is_valid = self._validate_move(order, legal_moves)
            case Order.SUPPORT:
                # Conveniently, supports have the same validation criteria as moves
                is_valid = self._validate_move(order, legal_moves)
            case Order.CONVOY:
                is_valid = self._validate_convoy(order)
            case Order.HOLD:
                is_valid = True
        return is_valid
    
    def _validate_move(self, order, legal_moves):
        if order.location_1 == order.location_2:
            return False
        for move in legal_moves:
            if move == order.location_2:
                return True
        return False
    
    def _validate_convoy(self, order):
        shared_types = [Territory.CANAL, Territory.COAST]
        return self.territories[order.unit.location].type == Territory.OCEAN and \
            self.territories[order.location_1].type in shared_types and \
            self.territories[order.location_2].type in shared_types

    def get_legal_moves_for_unit(self, unit_type, unit_location):
        legal_moves = []
        if unit_type == Unit.ARMY:
            valid_spaces = [Territory.CANAL, Territory.COAST, Territory.LAND]
        if unit_type == Unit.FLEET:
            valid_spaces = [Territory.CANAL, Territory.COAST, Territory.OCEAN]

        _, unit_location, unit_from_coast = split_coast(unit_location)

        for location in self.adjacency[unit_type.lower()][unit_location]:
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
    
    # Override!
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
    __init__(self):
        import json_loader
        from display_object import Territory
        data = json_loader.load_from_JSON("./data/maps/default.json", True)

        # Create territories
        territories = {}
        for name in data["map_data"].keys():
            # TODO: Fix territory definition
            territories[name] = Territory(None, name, [], data["map_data"][name], is_test=True)

        return DiplomacyAdjudicator(data["adjacency"], territories, units={})

def split_coast(location):
    from_coast = None
    to_coast = None
    if "-" in location:
        parts = location.split("-")
        if len(parts[0]) != 3:
            from_coast = parts[0]
            location = parts[1]
            if len(parts[-1]) != 3:
                to_coast = parts[-1]
        else:
            location = parts[0]
            to_coast = parts[1]
    return from_coast, location, to_coast

def run_tests():
    '''Acceptance testing'''
    # Default test case is latest DATC
    import diplomacy_test
    diplomacy_test.main()

if __name__ == "__main__":
    run_tests()
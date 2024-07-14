"""
Class for adjudicating Diplomacy moves

Date: 10/6/2024
Author: G Hampton
"""
PHASES = [
    "spring",
    "autumn",
    "winter",
]

class DiplomacyAdjudicator():
    def __init__(self, adjacency, territories, units):
        self.adjacency = adjacency
        self.territories = territories
        self.units = units
        self.retreats = []
        self.phase = 0
        self.counts_last_round = {team: 0 for team in units.keys()}
        for name in self.territories.keys():
            team = self.territories[name].owned_by
            if team:
                self.counts_last_round[team] += 1
    
    def get_intentional_DATC_failures(self):
        """ This function returns a list of the DATC test cases which this adjudicator fails intentionally. """
        return [
            "6.A.6",    # Ordering a unit of another country - this is intended for a sandbox environment.
            "6.B.7",    # Supporting own unit with unspecified coast - this is intended for use in face-to-face play, so is a little more generous.
        ]

    def update_units(self, units):
        self.units = units
    
    def update_territories(self, territories):
        self.territories = territories
    
    def get_current_phase(self):
        return PHASES[self.phase]
    
    def step_phase(self):
        self.phase = (self.phase + 1) % len(PHASES)
    
    def set_phase(self, phase):
        """ Allows for setting the phase directly. Used in testing. """
        self.phase = PHASES.index(phase.lower())
    
    def get_changes(self):
        return {
            team_name: len([self.territories[name] for name in self.territories.keys() if self.territories[name].owned_by == team_name]) - self.counts_last_round[team_name]
        for team_name in self.units.keys()}

    def adjudicate_builds(self, orders):
        valid = []
        changes = self.get_changes()

        for build in orders:
            name = build.location_1.split('-')[0]
            team = self.territories[name].owned_by if not build.unit else build.unit.team

            if not team:
                continue

            if changes[team] > 0:
                if build.type != "build":
                    continue
                # Build
                if self.territories[name].type == "land" and build.build_type == "Fleet":
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
                if build.type != "disband":
                    continue
                # Disband
                valid.append(build)
        return valid

    def adjudicate_moveset(self, orders, allow_retreats=True):
        if self.get_current_phase() == "winter":
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
                if order.type == "move" and order.location_1 != order.location_2 and order.unit.type == "Army":
                    check_for_convoys.append(order)
                continue
            match order.type:
                case "move":
                    moves.append(order)
                case "support":
                    supports.append(order)
                case "convoy":
                    convoys.append(order)
                case "hold":
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
                        holds.append(support.unit.give_order("hold", support.unit.location, support.unit.location))
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
                if order.type == "move"and order in moves:
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
                            case "hold":
                                holds.remove(h)
                            case "support":
                                print("Support gets broken here, but still detected as move?")
                                supports.remove(h)
                            case "convoy":
                                convoys.remove(h)
                        retreats.append(h)
                    else:
                        winning = False
                if winning:
                    m.remove(best_move)
                    moves.append(best_move)
            for move in m:
                holds.append(move.unit.give_order("hold", move.unit.location, move.unit.location))
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
                holds.append(move.unit.give_order("hold", move.unit.location, move.unit.location))
                holds.append(counterpart.unit.give_order("hold", counterpart.unit.location, counterpart.unit.location))
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
            case "move":
                is_valid = self._validate_move(order, legal_moves)
            case "support":
                # Conveniently, supports have the same validation criteria as moves
                is_valid = self._validate_move(order, legal_moves)
            case "convoy":
                is_valid = self._validate_convoy(order)
            case "hold":
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
        return self.territories[order.unit.location].type == "ocean" and \
            self.territories[order.location_1].type in ["canal", "coast"] and \
            self.territories[order.location_2].type in ["canal", "coast"]

    def get_legal_moves_for_unit(self, unit_type, unit_location):
        legal_moves = []
        if unit_type == "Army":
            valid_spaces = ["land", "canal", "coast"]
        if unit_type == "Fleet":
            valid_spaces = ["coast", "ocean", "canal"]

        _, unit_location, unit_from_coast = split_coast(unit_location)

        for location in self.adjacency[unit_type.lower()][unit_location]:
            from_coast, location, to_coast = split_coast(location)
            if unit_from_coast != None:
                if from_coast == None or from_coast != unit_from_coast:
                    continue
            territory = self.territories[location]
            if territory.type in valid_spaces:    
                if to_coast:
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

#=============================================================
# Test cases
def run_tests():
    from DATC import DATC_Tester
    adj = setup_test_adjudicator()
    tester = DATC_Tester(adj)
    tester.display_test_results()

def setup_test_adjudicator():
    import map_loader
    from display_object import Territory
    data = map_loader.load_from_JSON("./Maps/default.json", True)

    # Create territories
    territories = {}
    for name in data["map_data"].keys():
        territories[name] = Territory(None, name, [], data["map_data"][name], is_test=True)

    return DiplomacyAdjudicator(data["adjacency"], territories, units={})

if __name__ == "__main__":
    run_tests()
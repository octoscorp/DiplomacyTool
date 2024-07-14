""" Holds the Diplomacy Adjudicator Test Cases (3.0) """
from display_object import Unit, Order
from colorama import init as colorama_init
from colorama import Fore, Back, Style

POS = [0,0]
ORD = "  Orders:\n"

class DATC_Tester():
    def __init__(self, adjudicator):
        self.adjudicator = adjudicator

        colorama_init()

        # Check that the adjudicator implements all the required functions
        required_methods = ["update_units", "set_phase", "adjudicate_moveset"]
        for name in required_methods:
            required_method = getattr(self.adjudicator, name, None)
            assert callable(required_method), f"Adjudicator does not have a method called {name}. Implement it, or wrap the appropriate method."

    def unit_list_to_team_set(self, unit_list):
        units = {}
        for unit in unit_list:
            if unit.team not in units.keys():
                units[unit.team] = []
            units[unit.team].append(unit)
        return units

    def display_test_results(self):
        """ Run all cases in DATC and show output """
        all_cases = [
            # Test cases A - basic checks
            tc_a_1, tc_a_2, tc_a_3, tc_a_4, tc_a_5, tc_a_7, tc_a_8, tc_a_9, tc_a_10, tc_a_11, tc_a_12,
            # Test cases B - coastal issues
            tc_b_1, tc_b_2, tc_b_3, tc_b_4, tc_b_5, tc_b_6, tc_b_7, tc_b_8, tc_b_9, tc_b_10, tc_b_11, tc_b_12, tc_b_13, tc_b_14, tc_b_15
            # Test cases C - circular movement
            # Test cases D - supports and dislodges
            # Test cases E - head-to-head battles and beleaguered garrison
            # Test cases F - convoys
            # Test cases G - convoying to adjacent provinces
            # Test cases H - retreating
            # Test cases I - building
            # Test cases J - civil disorder and disbands
        ]
        total = 0
        fail_count = 0
        warning_count = 0
        for test_case in all_cases:
            total += 1
            failed = 0
            successful_moves = []

            units, orders, results, msgs = test_case()
            self.adjudicator.units = self.unit_list_to_team_set(units)
            if orders[0].type == "build":
                self.adjudicator.set_phase("winter")
            else:
                self.adjudicator.set_phase("spring")
            try:
                successful_moves = self.adjudicator.adjudicate_moveset(orders)
                assert self.is_same_moves(set(successful_moves), set(results))
            except AssertionError:
                if msgs["title"] not in self.adjudicator.get_intentional_DATC_failures():
                    failed = 2
                    fail_count += 1
                else:
                    failed = 1
                    warning_count += 1
            finally:
                self.show_test_case(msgs, failed, successful_moves, results)
        
        self.show_summary(total, fail_count, warning_count)
    
    def is_same_moves(self, set_1, set_2):
        if len(set_1) != len(set_2):
            return False
        strings_1 = [str(move) for move in set_1]
        strings_2 = [str(move) for move in set_2]
        strings_1.sort()
        strings_2.sort()
        for i in range(len(strings_1)):
            if strings_1[i] != strings_2[i]:
                return False
        return True

    def show_test_case(self, msgs, failed, successful_moves, results):
        if "section_title" in msgs.keys():
            print()
            print("=" * 50)
            print(msgs["section_title"])
        print("-" * 50)
        back_colour = Back.GREEN
        if failed == 1:
            back_colour = Back.YELLOW
        elif failed == 2:
            back_colour = Back.RED
        print(f"{back_colour}{msgs['title']}{Style.RESET_ALL}")
        print(msgs["orders"])
        print()
        print(msgs["err"] if failed == 2 else msgs["success"])
        if failed > 0:
            print(f"  Expected results: {[str(move) for move in results]}")
            print(f"  Actual results: {[str(move) for move in successful_moves]}")
        print()
    
    def show_summary(self, total, fails, warnings):
        colour = Fore.RED if fails > 0 else Fore.GREEN
        print(f"{colour}{'=' * 50}{Style.RESET_ALL}")
        print(f"{colour}SUMMARY{Style.RESET_ALL}")
        print()
        print(f"{colour}{total - fails - warnings} of {total} test cases passed.{Style.RESET_ALL}")
        if warnings > 0:
            print(f"  - {Fore.YELLOW}Of which {warnings} were intentional.{Style.RESET_ALL}")
        print(f"{colour}{'=' * 50}{Style.RESET_ALL}")

# 6.A BASIC CHECKS
def tc_a_1():
    """ Check that an illegal move (without convoy) will fail """
    units = [
        Unit(None, "England", "NTH", POS, "Fleet", is_test=True),
    ]
    orders = [
        units[0].give_order("move", "NTH", "PIC"),
    ]
    results = []
    msgs = {
        "section_title": "6.A - BASIC CHECKS",
        "title": "6.A.1",
        "orders": ORD + f"    {Back.WHITE}{Fore.BLACK}F NTH -> PIC{Style.RESET_ALL}",
        "success": f"  {Fore.GREEN}Illegal move correctly failed.{Style.RESET_ALL}",
        "err": f"  {Fore.RED}Illegal move without convoy succeeded!{Style.RESET_ALL}",
    }
    return (units, orders, results, msgs)
def tc_a_2():
    """ Check that an army cannot be moved to open sea """
    units = [
        Unit(None, "England", "LVP", POS, "Army", is_test=True),
    ]
    orders = [
        units[0].give_order("move", "LVP", "IRI"),
    ]
    results = []
    msgs = {
        "title": "6.A.2",
        "orders": ORD + f"    {Back.WHITE}{Fore.BLACK}A LVP -> IRI{Style.RESET_ALL}",
        "success": f"  {Fore.GREEN}Illegal move correctly failed.{Style.RESET_ALL}",
        "err": f"  {Fore.RED}Army walked into the ocean!{Style.RESET_ALL}",
    }
    return (units, orders, results, msgs)
def tc_a_3():
    """ Check that a fleet cannot be moved to land (non-coastal) """
    units = [
        Unit(None, "Germany", "KIE", POS, "Fleet", is_test=True),
    ]
    orders = [
        units[0].give_order("move", "KIE", "MUN"),
    ]
    results = []
    msgs = {
        "title": "6.A.3",
        "orders": ORD + f"    {Back.WHITE}{Fore.BLACK}F KIE -> MUN{Style.RESET_ALL}",
        "success": f"  {Fore.GREEN}Illegal move correctly failed.{Style.RESET_ALL}",
        "err": f"  {Fore.RED}Fleet climbed into a landlocked area!{Style.RESET_ALL}",
    }
    return (units, orders, results, msgs)
def tc_a_4():
    """ Check that a unit cannot be moved to its own space """
    units = [
        Unit(None, "Germany", "KIE", POS, "Fleet", is_test=True),
        Unit(None, "Germany", "HOL", POS, "Army", is_test=True),
    ]
    orders = [
        units[0].give_order("move", "KIE", "KIE"),
        units[1].give_order("move", "HOL", "HOL"),
    ]
    results = []
    msgs = {
        "title": "6.A.4",
        "orders": ORD + f"    {Back.WHITE}{Fore.BLACK}A HOL -> HOL{Style.RESET_ALL}\n" + \
            f"    {Back.WHITE}{Fore.BLACK}F KIE -> KIE{Style.RESET_ALL}",
        "success": f"  {Fore.GREEN}Illegal moves correctly failed.{Style.RESET_ALL}",
        "err": f"  {Fore.RED}Move that goes nowhere should be illegal!{Style.RESET_ALL}",
    }
    return (units, orders, results, msgs)
def tc_a_5():
    """ Check that a unit cannot be moved to its own space with a convoy """
    units = [
        Unit(None, "England", "NTH", POS, "Fleet", is_test=True),
        Unit(None, "England", "YOR", POS, "Army", is_test=True),
        Unit(None, "England", "LVP", POS, "Army", is_test=True),

        Unit(None, "Germany", "LON", POS, "Fleet", is_test=True),
        Unit(None, "Germany", "WAL", POS, "Army", is_test=True),
    ]
    orders = [
        units[0].give_order("convoy", "YOR", "YOR"),
        units[1].give_order("move", "YOR", "YOR"),
        units[2].give_order("support", "YOR", "YOR"),

        units[3].give_order("move", "LON", "YOR"),
        units[4].give_order("support", "LON", "YOR"),
    ]
    results = [
        units[3].pending_order
    ]
    msgs = {
        "title": "6.A.5",
        "orders": ORD + f"    {Back.WHITE}{Fore.BLUE}A YOR -> YOR{Style.RESET_ALL}\n" + \
            f"    {Back.WHITE}{Fore.BLUE}F NTH C YOR -> YOR{Style.RESET_ALL}\n" + \
            f"    {Back.WHITE}{Fore.BLUE}A LVP S YOR -> YOR{Style.RESET_ALL}\n" + \
            f"    {Back.WHITE}{Fore.BLACK}F LON -> YOR{Style.RESET_ALL}\n" + \
            f"    {Back.WHITE}{Fore.BLACK}A WAL S LON -> YOR{Style.RESET_ALL}",
        "success": f"  {Fore.GREEN}Illegal move correctly failed.{Style.RESET_ALL}",
        "err": f"  {Fore.RED}Move to own territory should be illegal, even if it's convoyed!{Style.RESET_ALL}",
    }
    return (units, orders, results, msgs)
# Test case 6.A.6 is skipped here. It concerns ordering other countries' units (Ger orders F LON -> NTH), current implementation does not support this.
def tc_a_7():
    """ Check that a fleet cannot be convoyed """
    units = [
        Unit(None, "England", "LON", POS, "Fleet", is_test=True),
        Unit(None, "England", "NTH", POS, "Fleet", is_test=True),
    ]
    orders = [
        units[0].give_order("move", "LON", "BEL"),
        units[1].give_order("convoy", "LON", "BEL"),
    ]
    results = []
    msgs = {
        "title": "6.A.7",
        "orders": ORD + f"    {Back.WHITE}{Fore.BLACK}F LON -> BEL{Style.RESET_ALL}\n" + \
            f"    {Back.WHITE}{Fore.BLACK}F NTH C LON -> BEL{Style.RESET_ALL}",
        "success": f"  {Fore.GREEN}Illegal move correctly failed.{Style.RESET_ALL}",
        "err": f"  {Fore.RED}Fleet was convoyed (only armies can get convoyed)!{Style.RESET_ALL}",
    }
    return (units, orders, results, msgs)
def tc_a_8():
    """ Check that a unit cannot support itself to gain an extra hold power """
    units = [
        Unit(None, "Italy", "VEN", POS, "Army", is_test=True),
        Unit(None, "Italy", "TYR", POS, "Army", is_test=True),

        Unit(None, "Austria", "TRI", POS, "Fleet", is_test=True),
    ]
    orders = [
        units[0].give_order("move", "VEN", "TRI"),
        units[1].give_order("support", "VEN", "TRI"),
    
        units[2].give_order("support", "TRI", "TRI"),
    ]
    results = [
        units[0].pending_order
    ]
    msgs = {
        "title": "6.A.8",
        "orders": ORD + f"    {Back.WHITE}{Fore.BLACK}A VEN -> TRI{Style.RESET_ALL}\n" + \
            f"    {Back.WHITE}{Fore.BLACK}A TYR S VEN -> TRI{Style.RESET_ALL}\n" + \
            f"    {Back.WHITE}{Fore.BLUE}F TRI S F TRI H{Style.RESET_ALL}",
        "success": f"  {Fore.GREEN}Defend strength correctly determined.{Style.RESET_ALL}",
        "err": f"  {Fore.RED}Units cannot get an additional hold power by supporting themself!{Style.RESET_ALL}",
    }
    return (units, orders, results, msgs)
def tc_a_9():
    """ If two provinces are adjacent, that does not mean that a fleet can move between those two provinces. """
    units = [
        Unit(None, "Italy", "ROM", POS, "Fleet", is_test=True),
    ]
    orders = [
        units[0].give_order("move", "ROM", "VEN"),
    ]
    results = []
    msgs = {
        "title": "6.A.9",
        "orders": ORD + f"    {Back.WHITE}{Fore.BLACK}F ROM -> VEN{Style.RESET_ALL}",
        "success": f"  {Fore.GREEN}Illegal move correctly failed.{Style.RESET_ALL}",
        "err": f"  {Fore.RED}Fleets need to follow the coast!{Style.RESET_ALL}",
    }
    return (units, orders, results, msgs)
def tc_a_10():
    """ Destination of supported move must be reachable by supporting unit. """
    units = [
        Unit(None, "Austria", "VEN", POS, "Army", is_test=True),

        Unit(None, "Italy", "ROM", POS, "Fleet", is_test=True),
        Unit(None, "Italy", "APU", POS, "Army", is_test=True),
    ]
    orders = [
        units[0].give_order("hold", "VEN", "VEN"),
    
        units[1].give_order("support", "APU", "VEN"),
        units[2].give_order("move", "APU", "VEN"),
    ]
    results = []
    msgs = {
        "title": "6.A.10",
        "orders": ORD + f"    {Back.WHITE}{Fore.BLUE}A VEN H{Style.RESET_ALL}\n" + \
            f"    {Back.WHITE}{Fore.BLACK}A APU -> VEN{Style.RESET_ALL}\n" + \
            f"    {Back.WHITE}{Fore.BLACK}F ROM S APU -> VEN{Style.RESET_ALL}",
        "success": f"  {Fore.GREEN}Illegal support correctly failed.{Style.RESET_ALL}",
        "err": f"  {Fore.RED}Unit supported move to a territory they can't reach!{Style.RESET_ALL}",
    }
    return (units, orders, results, msgs)
def tc_a_11():
    """ Simple bounce. """
    units = [
        Unit(None, "Austria", "VIE", POS, "Army", is_test=True),

        Unit(None, "Italy", "VEN", POS, "Army", is_test=True),
    ]
    orders = [
        units[0].give_order("move", "VIE", "TYR"),
    
        units[1].give_order("move", "VEN", "TYR"),
    ]
    results = []
    msgs = {
        "title": "6.A.11",
        "orders": ORD + f"    {Back.WHITE}{Fore.BLACK}A VIE -> TYR{Style.RESET_ALL}\n" + \
        f"    {Back.WHITE}{Fore.BLUE}A VEN -> TYR{Style.RESET_ALL}",
        "success": f"  {Fore.GREEN}Two units with equal strength correctly bounced.{Style.RESET_ALL}",
        "err": f"  {Fore.RED}Units moving with equal strength should bounce!{Style.RESET_ALL}",
    }
    return (units, orders, results, msgs)
def tc_a_12():
    """ Three-unit bounce """
    units = [
        Unit(None, "Austria", "VIE", POS, "Army", is_test=True),

        Unit(None, "Italy", "VEN", POS, "Army", is_test=True),

        Unit(None, "Germany", "MUN", POS, "Army", is_test=True),
    ]
    orders = [
        units[0].give_order("move", "VIE", "TYR"),
    
        units[1].give_order("move", "VEN", "TYR"),

        units[2].give_order("move", "MUN", "TYR"),
    ]
    results = []
    msgs = {
        "title": "6.A.12",
        "orders": ORD + f"    {Back.WHITE}{Fore.YELLOW}A VIE -> TYR{Style.RESET_ALL}\n" + \
            f"    {Back.WHITE}{Fore.BLUE}A VEN -> TYR{Style.RESET_ALL}\n" + \
            f"    {Back.WHITE}{Fore.BLACK}A MUN -> TYR{Style.RESET_ALL}",
        "success": f"  {Fore.GREEN}Three units with equal strength correctly bounced.{Style.RESET_ALL}",
        "err": f"  {Fore.RED}All equal units moving into the same territory should bounce!{Style.RESET_ALL}",
    }
    return (units, orders, results, msgs)

# 6.B COASTAL ISSUES
def tc_b_1():
    """ Check that a move which requires a coast fails when not specified """
    units = [
        Unit(None, "France", "POR", POS, "Fleet", is_test=True),
    ]
    orders = [
        units[0].give_order("move", "POR", "SPA"),
    ]
    results = []
    msgs = {
        "section_title": "6.B - COASTAL ISSUES",
        "title": "6.B.1",
        "orders": ORD + f"    {Back.WHITE}{Fore.BLACK}F POR -> SPA{Style.RESET_ALL}",
        "success": f"  {Fore.GREEN}Illegal move correctly failed.{Style.RESET_ALL}",
        "err": f"  {Fore.RED}Move requiring coast was completed with no coast specified!{Style.RESET_ALL}",
    }
    return (units, orders, results, msgs)
def tc_b_2():
    """ Check that a move which can only go to one coast succeeds when not specified """
    units = [
        Unit(None, "France", "GAS", POS, "Fleet", is_test=True),
    ]
    orders = [
        units[0].give_order("move", "GAS", "SPA"),
    ]
    results = [
        Order(units[0], "move", "GAS", "SPA-nc")
    ]
    msgs = {
        "title": "6.B.2",
        "orders": ORD + f"    {Back.WHITE}{Fore.BLACK}F GAS -> SPA{Style.RESET_ALL}",
        "success": f"  {Fore.GREEN}Only coast correctly chosen.{Style.RESET_ALL}",
        "err": f"  {Fore.RED}Move with only one possible coast could not decide on coast!{Style.RESET_ALL}",
    }
    return (units, orders, results, msgs)
def tc_b_3():
    """ Check that a move which can only go to one coast fails when another coast is specified """
    units = [
        Unit(None, "France", "GAS", POS, "Fleet", is_test=True),
    ]
    orders = [
        units[0].give_order("move", "GAS", "SPA-sc"),
    ]
    results = []
    msgs = {
        "title": "6.B.3",
        "orders": ORD + f"    {Back.WHITE}{Fore.BLACK}F GAS -> SPA-sc{Style.RESET_ALL}",
        "success": f"  {Fore.GREEN}Move with wrong coast correctly fails.{Style.RESET_ALL}",
        "err": f"  {Fore.RED}Move with wrong coast specified should fail!{Style.RESET_ALL}",
    }
    return (units, orders, results, msgs)
def tc_b_4():
    """ Check that a fleet can support an unreachable coast """
    units = [
        Unit(None, "France", "GAS", POS, "Fleet", is_test=True),
        Unit(None, "France", "MAR", POS, "Fleet", is_test=True),

        Unit(None, "Italy", "WES", POS, "Fleet", is_test=True),
    ]
    orders = [
        units[0].give_order("move", "GAS", "SPA-nc"),
        units[1].give_order("support", "GAS", "SPA"),

        units[2].give_order("move", "WES", "SPA"),
    ]
    results = [
        Order(units[0], "move", "GAS", "SPA-nc")
    ]
    msgs = {
        "title": "6.B.4",
        "orders": ORD + f"    {Back.WHITE}{Fore.BLACK}F GAS -> SPA-nc{Style.RESET_ALL}\n" + \
            f"    {Back.WHITE}{Fore.BLACK}F MAR S GAS -> SPA-nc{Style.RESET_ALL}\n" + \
            f"    {Back.WHITE}{Fore.BLUE}F WES -> SPA-sc{Style.RESET_ALL}",
        "success": f"  {Fore.GREEN}Fleet supports unreachable coast of reachable territory.{Style.RESET_ALL}",
        "err": f"  {Fore.RED}Fleet support to unreachable coast of reachable territory failed!{Style.RESET_ALL}",
    }
    return (units, orders, results, msgs)
def tc_b_5():
    """ Check that a fleet cannot support a territory reachable from the other coast """
    units = [
        Unit(None, "France", "SPA-nc", POS, "Fleet", is_test=True),
        Unit(None, "France", "MAR", POS, "Fleet", is_test=True),

        Unit(None, "Italy", "LYO", POS, "Fleet", is_test=True),
    ]
    orders = [
        units[0].give_order("support", "MAR", "LYO"),
        units[1].give_order("move", "MAR", "LYO"),

        units[2].give_order("hold", "LYO", "LYO"),
    ]
    results = []
    msgs = {
        "title": "6.B.5",
        "orders": ORD + f"    {Back.WHITE}{Fore.BLACK}F SPA-nc S MAR -> LYO{Style.RESET_ALL}\n" + \
            f"    {Back.WHITE}{Fore.BLACK}F MAR -> LYO{Style.RESET_ALL}\n" + \
            f"    {Back.WHITE}{Fore.BLUE}F LYO H{Style.RESET_ALL}",
        "success": f"  {Fore.GREEN}Coastal fleet did not support a territory it could not reach.{Style.RESET_ALL}",
        "err": f"  {Fore.RED}Fleet on coast achieved a support only legal from the other coast!{Style.RESET_ALL}",
    }
    return (units, orders, results, msgs)
def tc_b_6():
    """ Support can be cut from the other coast """
    units = [
        Unit(None, "England", "IRI", POS, "Fleet", is_test=True),
        Unit(None, "England", "NAO", POS, "Fleet", is_test=True),

        Unit(None, "France", "SPA-nc", POS, "Fleet", is_test=True),
        Unit(None, "France", "MAO", POS, "Fleet", is_test=True),

        Unit(None, "Italy", "LYO", POS, "Fleet", is_test=True),
    ]
    orders = [
        units[0].give_order("support", "NAO", "MAO"),
        units[1].give_order("move", "NAO", "MAO"),

        units[2].give_order("support", "MAO", "MAO"),
        units[3].give_order("hold", "MAO", "MAO"),

        units[4].give_order("move", "LYO", "SPA-sc"),
    ]
    results = [
        units[1].pending_order,
    ]
    msgs = {
        "title": "6.B.6",
        "orders": ORD + f"    {Back.WHITE}{Fore.BLACK}F IRI S NAO -> MAO{Style.RESET_ALL}\n" + \
            f"    {Back.WHITE}{Fore.BLACK}F NAO -> MAO{Style.RESET_ALL}\n" + \
            f"    {Back.WHITE}{Fore.BLUE}F SPA-nc S MAO H{Style.RESET_ALL}\n" + \
            f"    {Back.WHITE}{Fore.BLUE}F MAO H{Style.RESET_ALL}\n" + \
            f"    {Back.WHITE}{Fore.YELLOW}F LYO -> SPA-sc{Style.RESET_ALL}",
        "success": f"  {Fore.GREEN}Fleet cut support provided by opposite coast{Style.RESET_ALL}",
        "err": f"  {Fore.RED}Fleet on coast was not cut by the other coast!{Style.RESET_ALL}",
    }
    return (units, orders, results, msgs)
def tc_b_7():
    """ Supporting own unit without specifying the coast should fail """
    units = [
        Unit(None, "France", "POR", POS, "Fleet", is_test=True),
        Unit(None, "France", "MAO", POS, "Fleet", is_test=True),

        Unit(None, "Italy", "LYO", POS, "Fleet", is_test=True),
        Unit(None, "Italy", "WES", POS, "Fleet", is_test=True),
    ]
    orders = [
        units[0].give_order("support", "MAO", "SPA"),
        units[1].give_order("move", "MAO", "SPA-nc"),

        units[2].give_order("support", "WES", "SPA-sc"),
        units[3].give_order("move", "WES", "SPA-sc"),
    ]
    results = [
        units[3].pending_order,
    ]
    msgs = {
        "title": "6.B.7",
        "orders": ORD + f"    {Back.WHITE}{Fore.BLACK}F POR S MAO -> SPA{Style.RESET_ALL}\n" + \
            f"    {Back.WHITE}{Fore.BLACK}F MAO -> SPA-nc{Style.RESET_ALL}\n" + \
            f"    {Back.WHITE}{Fore.BLUE}F LYO S WES -> SPA-sc H{Style.RESET_ALL}\n" + \
            f"    {Back.WHITE}{Fore.BLUE}F WES -> SPA-sc{Style.RESET_ALL}",
        "success": f"  {Fore.GREEN}Support with unspecified coast fails correctly.{Style.RESET_ALL}",
        "err": f"  {Fore.RED}Support with unspecified coast succeeds!{Style.RESET_ALL}",
    }
    return (units, orders, results, msgs)
def tc_b_8():
    """ Supporting with unspecified coast when only one coast is possible should succeed """
    units = [
        Unit(None, "France", "POR", POS, "Fleet", is_test=True),
        Unit(None, "France", "GAS", POS, "Fleet", is_test=True),

        Unit(None, "Italy", "LYO", POS, "Fleet", is_test=True),
        Unit(None, "Italy", "WES", POS, "Fleet", is_test=True),
    ]
    orders = [
        units[0].give_order("support", "GAS", "SPA"),
        units[1].give_order("move", "GAS", "SPA-nc"),

        units[2].give_order("support", "WES", "SPA-sc"),
        units[3].give_order("move", "WES", "SPA-sc"),
    ]
    results = []
    msgs = {
        "title": "6.B.8",
        "orders": ORD + f"    {Back.WHITE}{Fore.BLACK}F POR S GAS -> SPA{Style.RESET_ALL}\n" + \
            f"    {Back.WHITE}{Fore.BLACK}F GAS -> SPA-nc{Style.RESET_ALL}\n" + \
            f"    {Back.WHITE}{Fore.BLUE}F LYO S WES -> SPA-sc H{Style.RESET_ALL}\n" + \
            f"    {Back.WHITE}{Fore.BLUE}F WES -> SPA-sc{Style.RESET_ALL}",
        "success": f"  {Fore.GREEN}Support with implied coast (only choice) determines coast correctly.{Style.RESET_ALL}",
        "err": f"  {Fore.RED}Support with implied coast does not determine a coast!{Style.RESET_ALL}",
    }
    return (units, orders, results, msgs)
def tc_b_9():
    """ Supporting to wrong coast should be possible. """
    units = [
        Unit(None, "France", "POR", POS, "Fleet", is_test=True),
        Unit(None, "France", "MAO", POS, "Fleet", is_test=True),

        Unit(None, "Italy", "LYO", POS, "Fleet", is_test=True),
        Unit(None, "Italy", "WES", POS, "Fleet", is_test=True),
    ]
    orders = [
        units[0].give_order("support", "MAO", "SPA-nc"),
        units[1].give_order("move", "MAO", "SPA-sc"),

        units[2].give_order("support", "WES", "SPA-sc"),
        units[3].give_order("move", "WES", "SPA-sc"),
    ]
    results = [
        units[3].pending_order,
    ]
    msgs = {
        "title": "6.B.9",
        "orders": ORD + f"    {Back.WHITE}{Fore.BLACK}F POR S MAO -> SPA-nc{Style.RESET_ALL}\n" + \
            f"    {Back.WHITE}{Fore.BLACK}F MAO -> SPA-sc{Style.RESET_ALL}\n" + \
            f"    {Back.WHITE}{Fore.BLUE}F LYO S WES -> SPA-sc H{Style.RESET_ALL}\n" + \
            f"    {Back.WHITE}{Fore.BLUE}F WES -> SPA-sc{Style.RESET_ALL}",
        "success": f"  {Fore.GREEN}Support to wrong coast does not strengthen move.{Style.RESET_ALL}",
        "err": f"  {Fore.RED}Support to wrong coast still strengthens move!{Style.RESET_ALL}",
    }
    return (units, orders, results, msgs)
def tc_b_10():
    """ If a unit's starting coast is specified incorrectly, but the order is otherwise valid, the move will still be attempted. """
    units = [
        Unit(None, "France", "SPA-sc", POS, "Fleet", is_test=True),
    ]
    orders = [
        units[0].give_order("move", "SPA-nc", "LYO"),
    ]
    results = [
        units[0].pending_order,
    ]
    msgs = {
        "title": "6.B.10",
        "orders": ORD + f"    {Back.WHITE}{Fore.BLACK}F SPA-nc -> LYO (actually in SPA-sc){Style.RESET_ALL}",
        "success": f"  {Fore.GREEN}Move with wrong starting coast still succeeds.{Style.RESET_ALL}",
        "err": f"  {Fore.RED}Move with incorrect starting coast fails despite no other issues!{Style.RESET_ALL}",
    }
    return (units, orders, results, msgs)
def tc_b_11():
    """ Coast cannot change just by ordering other coast """
    units = [
        Unit(None, "France", "SPA-nc", POS, "Fleet", is_test=True),
    ]
    orders = [
        units[0].give_order("move", "SPA-sc", "LYO"),
    ]
    results = []
    msgs = {
        "title": "6.B.11",
        "orders": ORD + f"    {Back.WHITE}{Fore.BLACK}F SPA-sc -> LYO (actually in SPA-nc){Style.RESET_ALL}",
        "success": f"  {Fore.GREEN}Fleet does not change coast just because of order format.{Style.RESET_ALL}",
        "err": f"  {Fore.RED}Fleet changes coast magically due to wrong coast order!{Style.RESET_ALL}",
    }
    return (units, orders, results, msgs)
def tc_b_12():
    """ Armies should ignore coasts specified on their movement """
    units = [
        Unit(None, "France", "GAS", POS, "Army", is_test=True),
    ]
    orders = [
        units[0].give_order("move", "GAS", "SPA-nc"),
    ]
    results = [
        Order(units[0], "move", "GAS", "SPA"),
    ]
    msgs = {
        "title": "6.B.12",
        "orders": ORD + f"    {Back.WHITE}{Fore.BLACK}A GAS -> SPA-nc{Style.RESET_ALL}",
        "success": f"  {Fore.GREEN}Army move correctly ignores coast.{Style.RESET_ALL}",
        "err": f"  {Fore.RED}Army move still considers coast!{Style.RESET_ALL}",
    }
    return (units, orders, results, msgs)
def tc_b_13():
    """ Coastal crawl not allowed (coasts don't stop movements from being head-to-head) """
    units = [
        Unit(None, "Turkey", "BUL-sc", POS, "Fleet", is_test=True),
        Unit(None, "Turkey", "CON", POS, "Fleet", is_test=True),
    ]
    orders = [
        units[0].give_order("move", "BUL-sc", "CON"),
        units[1].give_order("move", "CON", "BUL-ec"),
    ]
    results = []
    msgs = {
        "title": "6.B.13",
        "orders": ORD + f"    {Back.WHITE}{Fore.BLACK}F BUL-sc -> CON{Style.RESET_ALL}\n" + \
            f"    {Back.WHITE}{Fore.BLACK}F CON -> BUL-ec{Style.RESET_ALL}",
        "success": f"  {Fore.GREEN}Coasts do not prevent head-to-head.{Style.RESET_ALL}",
        "err": f"  {Fore.RED}Coastal crawl (coasts not preventing head-to-head) is possible!{Style.RESET_ALL}",
    }
    return (units, orders, results, msgs)
def tc_b_14():
    """ Coast must be specified in certain build cases """
    units = []
    orders = [
        Order(None, "build", "STP", "STP"),
    ]
    results = []
    msgs = {
        "title": "6.B.14",
        "orders": ORD + f"    {Back.WHITE}{Fore.BLACK}Build F STP{Style.RESET_ALL}",
        "success": f"  {Fore.GREEN}Build order requiring coast is not valid without coast.{Style.RESET_ALL}",
        "err": f"  {Fore.RED}Build order requiring coast ignored coast requirement!{Style.RESET_ALL}",
    }
    return (units, orders, results, msgs)
def tc_b_15():
    """ Supporting foreign unit with unspecified coast - support should be valid """
    units = [
        Unit(None, "France", "POR", POS, "Fleet", is_test=True),
        
        Unit(None, "England", "MAO", POS, "Fleet", is_test=True),

        Unit(None, "Italy", "LYO", POS, "Fleet", is_test=True),
        Unit(None, "Italy", "WES", POS, "Fleet", is_test=True),
    ]
    orders = [
        units[0].give_order("support", "MAO", "SPA"),

        units[1].give_order("move", "MAO", "SPA-nc"),

        units[2].give_order("support", "WES", "SPA-sc"),
        units[3].give_order("move", "WES", "SPA-sc"),
    ]
    results = []
    msgs = {
        "title": "6.B.15",
        "orders": ORD + f"    {Back.WHITE}{Fore.BLACK}F POR S MAO -> SPA{Style.RESET_ALL}\n" + \
            f"    {Back.WHITE}{Fore.BLUE}F MAO -> SPA-nc{Style.RESET_ALL}\n" + \
            f"    {Back.WHITE}{Fore.YELLOW}F LYO S WES -> SPA-sc{Style.RESET_ALL}\n"
            f"    {Back.WHITE}{Fore.YELLOW}F WES -> SPA-sc{Style.RESET_ALL}\n",
        "success": f"  {Fore.GREEN}Supporting a foreign unit to an unspecified coast works.{Style.RESET_ALL}",
        "err": f"  {Fore.RED}Supporting a foreign unit to an unspecified coast fails!{Style.RESET_ALL}",
    }
    return (units, orders, results, msgs)

# 6.C. CIRCULAR MOVEMENT
def tc_c_1():
    """ Three units can move in a circle """
    pass
def tc_c_2():
    """ Three units can move in a circle when one is supported (more a computer issue) """
    pass
def tc_c_3():
    """ When one of the units bounces, the whole circular movement will hold """
    pass
def tc_c_4():
    """ When circular movement contains an attacked (not dislodged) convoy, the circular movement succeeds. """
    pass
def tc_c_5():
    """ When circular movement contains a dislodged convoy, the circular movement is disrupted. """
    pass
def tc_c_6():
    """ Two armies with two convoys can swap places """
    pass
def tc_c_7():
    """ If in a swap one unit bounces, the swap fails. """
    pass
def tc_c_8():
    """ Self dislodgement is prohibited in circular movement """
    pass
def tc_c_9():
    """ Support of dislodging own unit is prohibited in circular movement """
    pass

def tc_d_1():
    """ Supported hold prevents dislodgement """
    pass
def tc_d_2():
    """ Move cuts a hold support """
    pass
def tc_d_3():
    """ Move cuts a move support """
    pass
def tc_d_4():
    """ Unit supporting a hold can receive support hold. """
    pass
def tc_d_5():
    """ Unit supporting a move can receive support hold. """
    pass
def tc_d_6():
    """ Convoying unit can receive support hold. """
    pass
def tc_d_7():
    """ Moving unit cannot receive support hold if move fails. """
    pass
def tc_d_8():
    """ Failed convoyed unit cannot receive hold support """
    pass
def tc_d_9():
    """ Unit which is holding cannot be supported by a move support """
    pass
def tc_d_10():
    """ A unit may not dislodge a unit from the same nation """
    pass
def tc_d_11():
    """ A unit may not dislodge a bounced unit from the same nation """
    pass
def tc_d_12():
    """ Supporting another nation to dislodge own unit is illegal. """
    pass
def tc_d_13():
    """ Supporting another nation to dislodge own bounced unit is illegal. """
    pass
def tc_d_14():
    """ Supporting a foreign attack does not prevent dislodgement. """
    pass
def tc_d_15():
    """ Unit cannot cut support to attack on itself """
    pass
def tc_d_16():
    """ Convoying a unit which would dislodge your own unit is allowed """
    pass
def tc_d_17():
    """ Dislodgement of own attacker cuts support """
    pass
def tc_d_18():
    """ A surviving unit will sustain support """
    pass
def tc_d_19():
    """ Support not cut when nation's own support would cause dislodgement. """
    pass
def tc_d_20():
    """ Unit cannot cut support of its own country """
    pass
def tc_d_21():
    """ Unit can cut (failing to dislodge), then be dislodged """
    pass
def tc_d_22():
    """ Impossible fleet move cannot be supported. """
    pass
def tc_d_23():
    """ Impossible coast move cannot be supported """
    pass
def tc_d_24():
    """ Impossible army move cannot be supported """
    pass
def tc_d_25():
    """ Failed hold support can be supported to hold """
    pass
def tc_d_26():
    """ Failed move support can be supported to hold """
    pass
def tc_d_27():
    """ Failed convoy can be supported to hold """
    pass
def tc_d_28():
    """ Illegal move can be supported to hold """
    pass
def tc_d_29():
    """ Illegal move due to wrong coast can be supported to hold """
    pass
def tc_d_30():
    """ Illegal move due to missing coast can be supported to hold """
    pass
def tc_d_31():
    """ Illegal move due to missing convoy cannot be supported into destination """
    pass
def tc_d_32():
    """ Illegal move due to missing convoy can be supported to hold """
    pass
def tc_d_33():
    """ A self-bounce can be broken by an unwanted support """
    pass
def tc_d_34():
    """ Support targeting own territory not allowed """
    pass

def tc_e_1():
    pass
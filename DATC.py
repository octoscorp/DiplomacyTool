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
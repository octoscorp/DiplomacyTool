"""
Test Case runner and interface for matching with adjudicator.

Adjudicators should only need to mesh with AdjudicatorTestInterface; whatever test
suite they wish to use can interface with TestRunner.

Author: G Hampton
Date: 24/02/2025
"""
from colorama import init as colorama_init
from colorama import Fore, Back, Style
import json_loader 

FAIL = 0
WARN = 1
SUCCESS = 2
CONTEXT = 4
HIGHLIGHT = 8
# These two should always be the highest; adding them together ensures no collision
NORMAL = HIGHLIGHT + CONTEXT

class Order:
    BUILD = 0
    HOLD = 1
    MOVE = 2
    SUPPORT = 3
    CONVOY = 4

class Phase:
    WINTER = 0
    SPRING = 1
    AUTUMN = 2

def load_test_cases(filepath):
    required_structure = []
    json_loader.load_from_JSON(filepath, required_structure)

    return json_data

def format_text(text, format):
    """
    Permit format keywords. The keywords allowed are:
    - success: bold green text, default bg
    """
    tags = ""
    match color:
        case FAIL:
            tags += Fore.RED
        case WARN:
            tags += Fore.YELLOW
        case SUCCESS:
            tags += Fore.GREEN
        case HIGHLIGHT + FAIL:
            tags += Back.RED + Style.BRIGHT
        case HIGHLIGHT + WARN:
            tags += Back.YELLOW + Style.BRIGHT
        case HIGHLIGHT + SUCCESS:
            tags += Back.GREEN + Style.BRIGHT
        case CONTEXT:
            tags += Style.DIM
        case _:
            # Don't tag meaninglessly
            return text
    return f"{tags}{text}{Style.RESET_ALL}"

class AdjudicatorTestInterface():
    def __init__(self, adjudicator):
        self.adjudicator = adjudicator

        # Check that the adjudicator implements all the required functions
        required_methods = [
            "test_remove_all_units",
            "test_create_unit",
            "test_set_phase",
            "test_string_to_order",
            "test_order_to_string",
            "test_adjudicate_moveset"
        ]
        for name in required_methods:
            required_method = getattr(self.adjudicator, name, None)
            assert callable(required_method), f"Adjudicator does not have a method called {name}. Implement it, or wrap the appropriate method."
        
        # Check for optionally defined intentional failures
        self.int_fails = {}
        intentional_failures = getattr(self.adjudicator, "test_get_intentional_failures", None)
        if callable(intentional_failures):
            fails = intentional_failures()
            for fail in fails:
                self.int_fails[fail[0]] = fail[1]
        else:
            print("No intentional failures.")
        
        # To define tests to intentionally fail for your adjudicator, create a method named "test_get_intentional_failures".
        # The method should return a list of (test_number, reason) tuples. Examples:
        # [
        #     ("6.A.1", "I think illegal moves should succeed"),
        #     ("6.A.6", "Implementation is for sandbox"),
        #     ("6.B.1", "")
        # ]

    def get_order_type(self, order_string):
        parts = order_string.split()
        if parts[0] == "build":
            return Order.BUILD
        match parts[2]:
            case "->":
                return Order.MOVE
            case "S":
                return Order.SUPPORT
            case "C":
                return Order.CONVOY
            _:
                return Order.HOLD

    def setup(self, test_case):
        """ Setup beginning state with the starting units. Check whether it should be winter (first order should be enough). """
        for unit in test_case["start_units"]:
            # Processing required?
            self.adjudicator.test_create_unit(unit)

        if self.get_order_type(test_case["orders"][0]["moveset"][0]) == Order.BUILD:
            self.adjudicator.test_set_phase(Phase.WINTER)
        else:
            self.adjudicator.test_set_phase(Phase.SPRING)

    def enter_orders_and_run(self, test_case):
        """ Enter orders for each team of units, return the result of adjudicating them all """
        moveset = []
        for team_orderset in test_case["orders"]:
            team_name = team_orderset["team"]
            for order_string in team_orderset["moveset"]:
                moveset.append(self.adjudicator.test_string_to_order(team, order_string))
        
        return [self.adjudicator.test_order_to_string(o) for o in self.adjudicator.test_adjudicate_moveset(moveset)]

    def check_for_intentional_fail(self, test_case):
        if test_case["title"] in self.int_fails.keys():
            return self.int_fails[test_case["title"]]
        return False


class TestRunner():
    def __init__(self, adjudicator, test_case_file):
        self.adj_int = AdjudicatorTestInterface(adjudicator)
        self.test_cases = load_test_cases(test_case_file)

        colorama_init()

    def _evaluate_test_case(self, test_case, quiet):
        reason = ''
        try:
            self.adj_int.setup(test_case)
            result_moveset = self.adj_int.enter_orders_and_run(test_case)
            assert self.is_same_moves(test_case["result_moves"], result_moveset)
            state = SUCCESS
        except AssertionError:
            # Check for test cases intentionally failed
            state = FAIL
            reason = self.adj_int.check_for_intentional_fail(test_case)
            if reason !== False:
                # Intentional, mitigate failure
                state = WARN
        finally:
            if !quiet:
                self.show_test_case(test_case, state, reason, moves)
        return state

    def display_test_results(self, quiet=False):
        """ Run all cases given and show output """
        total = 0
        fail_count = 0
        warning_count = 0
        for section in self.test_cases["sections"]:
            self._show_section_header(section["title"])
            for test_case in section["test_cases"]:
                total += 1
                match self._evaluate_test_case(test_case, quiet):
                    case FAIL:
                        fail_count += 1
                    case WARNING:
                        warning_count += 1
        
        self.show_summary(total, fail_count, warning_count)
    
    def is_same_moves(self, expected, result):
        if len(expected) != len(result):
            return False
        expected.sort()
        result.sort()
        for i in range(len(expected)):
            if expected[i] != result[i]:
                return False
        return True

    def _show_section_header(self, section_title):
        print()
        print("=" * 50)
        print(section_title)

    def _print_orders(self, orders, state=NORMAL):
        for orderset in orders:
            team_name = orders["team"]
            moves = orders["moveset"]
            
            print(format_text(f"{team_name}:", state))
            for move in moves:
                print(format_text(f"  {move}", state))
            print()

    def show_test_case(self, test_case, state, reason, moves_made):
        print("-" * 50)
        # Header
        print(format_text(test_case["title"], state + HIGHLIGHT))

        # Orders for context
        self._print_orders(test_case["orders"], CONTEXT)
        if state < SUCCESS:
            print("!" * 8)
            print("Expected results:")
            self._print_orders(test_case["result_moves"])
            print("-")
            print("Actual results:")
            self._print_orders(moves_made, state)
            if state == WARN:
                reason = reason if reason else "No reason given."
                print("-" * 3)
                print(format_text(f"Reason: {reason}", WARN))
        print()
    
    def show_summary(self, total, fails, warnings):
        overall_state = FAIL if fails > 0 else SUCCESS
        print(format_text('=' * 50 + "\nSUMMARY", overall_state))
        print()
        print(format_text(f"{total - fails - warnings} of {total} test cases passed.", overall_state))
        if warnings > 0:
            print(format_text(f"  - Of which {warnings} were intentional.", WARN))
        print(format_text('=' * 50), overall_state)

def main():
    from diplomacy_adjudicator import DefaultAdjudicator
    import sys

    silenced = False
    test_file = "./data/test_cases/DATC_3.1.json"

    # Very rough command-line parsing
    if len(sys.argv) > 1:
        silenced = sys.argv.index("-q")
        if silenced != -1:
            sys.argv.pop(silenced)
            silenced = True
        # If silenced, must have filename
        test_file = sys.argv[1]

    # DefaultAdjudicator is a shortcut which allows test interfaces to ignore implementation details and needs no arguments
    test_adj = DefaultAdjudicator()
    runner = TestRunner(test_adj, test_file)

    runner.display_test_results(silenced)

# Tests
if __name__ == "__main__":
    main()
""" Holds the Diplomacy Adjudicator Test Cases (3.0) """
from display_object import Unit, Order
from colorama import init as colorama_init
from colorama import Fore, Back, Style
import json_loader 

FAIL = 0
WARN = 1
SUCCESS = 2

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
        case "success":
            tags += Fore.GREEN
        case "warning":
            tags += Fore.YELLOW
        case "failure":
            tags += Fore.RED
        case "highlight_success":
            tags += Back.GREEN + Style.BRIGHT
        case "highlight_warning":
            tags += Back.YELLOW + Style.BRIGHT
        case "highlight_failure":
            tags += Back.RED + Style.BRIGHT
        case "context":
            tags += Style.DIM
        case _:
            # Don't tag meaninglessly
            return text
    return f"{tags}{text}{Style.RESET_ALL}"

class Adjudicator_Test_Interface():
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


class Test_Runner():
    def __init__(self, adjudicator, test_case_file):
        self.adj_int = Adjudicator_Test_Interface(adjudicator)
        self.test_cases = load_test_cases(test_case_file)

        colorama_init()

    def evaluate_test_case(self, test_case):
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
            self.show_test_case(test_case, state, reason)
        return state

    def display_test_results(self):
        """ Run all cases in DATC and show output """
        total = 0
        fail_count = 0
        warning_count = 0
        for section in self.test_cases["sections"]:
            for test_case in section["test_cases"]:
                total += 1
                match self.evaluate_test_case(test_case):
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

    def show_test_case(self, test_case, state, reason):
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
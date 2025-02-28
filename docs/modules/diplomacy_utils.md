# Diplomacy Utils

This is equivalent to the "Model" layer of MVC. 

## Class Stubs

These are simplistic implementations of the classes, designed to provide some base functionality which is required by most things. In particular, they make use of static methods to define string conversions for the types. Additionally, by definining all-caps constants within classes, enums can be provided along with the class stubs. These can then be used by other classes to keep a consistent communication around these types (e.g. Order.DISBAND).

### Phase

This defines the game phase cycle.

#### Enum Values

* WINTER
* SPRING
* AUTUMN

#### Static Methods

* `get_next_phase(current_phase)`
    * Step along the phase enum by adding 1. Of note are the class attributes `_first_phase` and `_last_phase`, which point to their respective enum values. If you add more phases, override these to include them in this function's stepping.

### Order

This defines orders issued and provides the capacity to convert between Order objects and string codes for them: "F ANK S A BUL -> CON"

#### Enum Values

* DISBAND
* BUILD
* HOLD
* MOVE
* SUPPORT
* CONVOY

#### Static Methods

* `from_string(order_string)`
    
    Create an order from the given string.
    Example order strings:
    * Hold: "A SMY H"
    * Move: "A BUL -> CON"
    * Support: "F BLA S A BUL -> CON"
    * Convoy: "F AEG C A BUL -> CON"
    * Build: "build F CON"
    * Disband: "disband A BUL"
    
    The counterpart of this is the non-static `__str__` inbuilt function.
    
* `_type_from_string(order_partial_string)`
    
    Convert from a partial string to a value in the enum. This looks for the following string segments:
    * `H` (hold)
    * `->` (move)
    * `S` (support)
    * `C` (convoy)
    * `disband`
    * `build`

    The counterpart of this is `_string_from_type`.
    
* `_string_from_type(order_type)`
    
    Convert from a value in the enum to a partial string representing an order type. This is the counterpart of `_type_from_string`, see that function for the string segments.

#### Non-static Methods
* `__str__()`
    
    This is the inbuilt function that `str(object)` calls. By overriding it, we set our own definition of how the order converts to a string.

    The counterpart of this function is the static method `from_string`.

### Unit

#### Enum values

* FLEET
* ARMY

#### Static Methods
`string_from_type`
Converts between strings and unit types: 'F' and 'A' become Unit.FLEET and Unit.ARMY 

`type_from_string`

### Territory

#### Enum values

* LAND
* OCEAN
* COAST
* CANAL

#### Static Methods

`type_from_string`
Converts between the string (expects one of "land", "ocean", "coast", "canal") and the corresponding enum value.
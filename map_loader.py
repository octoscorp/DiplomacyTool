"""
Loads a diplomacy map from a JSON file.
The format of the file must include details to outline the adjacencies and relative positions, and ideally will contain outlines too.

Date: 3/06/2024
Author: G Hampton

=============================================================
File format:
{
  "adjacency": {
    "NAO": ["NWG", "CLY", "LIV", "IRI", "MAO"],
    "NWG": ["BAR", "NWY", "NTH", "EDI", "CLY", "NAO"]
  },
  "map_data": {
    "NAO": {
      "type": "ocean",
      "is_supply_centre": false,
      "full_name": "North Atlantic Ocean",
      "location": [0,0],
      "borders": [
        [0,0],
        [10,0],
        [10,10]
      ]
    }
  },
  "starting_builds": [
    {
      "team_name": "Turkey",
      "builds": [
        {
          "location": "ANK",
          "unit_type": "Fleet"
        },
        {
          "location": "CON",
          "unit_type": "Army"
        },
        {
          "location": "SMY",
          "unit_type": "Army"
        }
      ]
    },
  ]
}
"""

import json

ROOT_ATTRIBUTES = ["adjacency", "map_data", "starting_builds"]
NODE_ATTRIBUTES = ["type", "is_supply_centre", "full_name", "location"]

def _read_file_to_JSON(filepath, require_borders):
    """Checks that file exists, is openable, and is valid JSON. Returns the JSON object."""
    file = open(filepath, "r")
    lines = file.read()
    file.close()
    json_data = json.loads(lines)

    _check_attributes(json_data, ROOT_ATTRIBUTES)
    if require_borders:
        _check_attributes(json_data, ["border_points"])
      
    return json_data

def _check_attributes(json_data, attributes):
    """Checks that the data has the required attributes, otherwise raises KeyError"""
    for attribute in attributes:
        if attribute not in json_data.keys():
            raise KeyError(f"Key \"{attribute}\" expected in JSON data but could not be found.")

def load_from_JSON(filepath, require_borders=False):
    """Attempts to parse the JSON file supplied by the rules provided above."""
    data = _read_file_to_JSON(filepath, require_borders)

    return data
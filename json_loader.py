"""
Loads a JSON file and has the ability to check for top-level keys.
Ideally would be extended to check against a schema.

Date: 21/02/2025
Author: G Hampton

=============================================================
Map file format:
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

def load_from_JSON(filepath, required_attributes=[]):
    """
    Checks that file exists, is openable, and is valid JSON. Returns the JSON object.
      filepath: filepath to attempt to open.
      required_attributes: checked against top-level json keys.
    """
    file = open(filepath, "r")
    lines = file.read()
    file.close()
    json_data = json.loads(lines)

    _check_attributes(json_data, required_attributes)
      
    return json_data

def _check_attributes(json_data, attributes):
    """Checks that the data has the required attributes, otherwise raises KeyError"""
    for attribute in attributes:
        if attribute not in json_data.keys():
            raise KeyError(f"Key \"{attribute}\" expected in JSON data but could not be found.")
from . import *

parse_classes['func_ladder'] = {
    "classname": parse_string,
    "model": parse_string,

    "targetname": parse_string,

    # Exporting settings
    "_export_geo": False,
    "_export_col": True,
}

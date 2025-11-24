from . import *

parse_classes['multi_manager'] = {
    "classname": parse_string,
    "model": parse_string,

    "targetname": parse_string,
    "spawnflags": parse_int,

    # Exporting settings
    "_export_geo": False,
    "_export_col": False,
}

from . import *

parse_classes['info_teleport_destination'] = {
    "classname": parse_string,
    "model": parse_string,

    "targetname": parse_string,
    "angles": parse_angles,
    "spawnflags": parse_int,

    # Exporting settings
    "_export_geo": False,
    "_export_col": False,
}

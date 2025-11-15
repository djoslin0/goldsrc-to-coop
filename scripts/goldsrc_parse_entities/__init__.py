import pkgutil
import importlib

parse_classes = {}

def parse_string(entity, field, iscalar):
    pass

def parse_position(entity, field, iscalar):
    if entity == None or field == None or field not in entity:
        return
    x, y, z = map(float, entity[field].split())
    entity[field] = (x * iscalar, y * iscalar, z * iscalar)

def parse_angles(entity, field, iscalar):
    if entity == None or field == None or field not in entity:
        return
    x, y, z = map(float, entity[field].split())
    entity[field] = (x, y, z)

def parse_color(entity, field, iscalar):
    if entity == None or field == None or field not in entity:
        return
    x, y, z = map(int, entity[field].split())
    entity[field] = (x, y, z)

def parse_int(entity, field, iscalar):
    if entity == None or field == None or field not in entity:
        return
    entity[field] = int(entity[field])

def parse_float(entity, field, iscalar):
    if entity == None or field == None or field not in entity:
        return
    entity[field] = float(entity[field])

def parse_float_scaled(entity, field, iscalar):
    if entity == None or field == None or field not in entity:
        return
    entity[field] = float(entity[field]) * iscalar

__all__ = [name for name in globals() if not name.startswith('_')]

for loader, module_name, is_pkg in pkgutil.iter_modules(__path__):
    module = importlib.import_module(f"{__name__}.{module_name}")
    __all__.append(module_name)

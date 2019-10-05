

from sc2.constants import UnitTypeId


# Zerg units can burrow but not listed here explicitly
# All protoss unit can cloak if near Mothership, also not listed explicitly
CAN_CLOAK = {
    UnitTypeId.LURKER,
    UnitTypeId.GHOST,
    UnitTypeId.WIDOWMINE,
    UnitTypeId.BANSHEE,
    UnitTypeId.DARKTEMPLAR,
    UnitTypeId.OBSERVER
}


from sc2.constants import UnitTypeId

CREEP_BUFF_DEFAULT = 1.3

CREEP_BUFF_FACTOR = {
    UnitTypeId.DRONE : 1.0,
    UnitTypeId.BROODLING : 1.0,
    UnitTypeId.CHANGELING : 1.0,
    UnitTypeId.QUEEN : 1.667,
    UnitTypeId.HYDRALISK : 1.5,
    UnitTypeId.SPORECRAWLER : 1.5,
    UnitTypeId.SPINECRAWLER : 1.5
}

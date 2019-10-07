


from sc2.constants import UnitTypeId
from sc2.constants import *

# This dictionary map the amount of extra damage units gain per attack upgrade

ATTACK_UPGRADE_DEFAULT = (1, 1)

# (Ground, air)
ATTACK_UPGRADE_INC = {
    UnitTypeId.DRONE : (0, 0),
    UnitTypeId.PROBE : (0, 0),
    UnitTypeId.SCV : (0, ),

    #ZERG:
    UnitTypeId.BANELING : (2, 0),
    UnitTypeId.ROACH : (2, 0),
    UnitTypeId.RAVAGER : (2, 0),
    UnitTypeId.LURKER : (2, 0),
    UnitTypeId.ULTRALISK : (3, 0), #33% splash
    #Note: Mutalisk is: +1 / +0.3 / +0.1
    UnitTypeId.BROODLORD : (2, 2),

    #TERRAN:
    UnitTypeId.HELLIONTANK : (2, 0),
    UnitTypeId.SIEGETANK : (2, 0), 
    UnitTypeId.SIEGETANKSIEGED : (4, 0), 
    UnitTypeId.CYCLONE : (2, 2),
    UnitTypeId.THOR : (3 , 1),  #this is thor in explosive mode
    UnitTypeId.THORAP : (3, 4), # TODO: this is for thor in high impact mode??
    UnitTypeId.LIBERATOR : (5, 1),

    #PROTOSS:
    UnitTypeId.DARKTEMPLAR : (5, 0),
    UnitTypeId.IMMORTAL : (2, 0),
    UnitTypeId.ORACLE : (0, 0),
    UnitTypeId.CARRIER : (8, 8), # Effective increase for 8 interceptors! (special case)
    UnitTypeId.ARCHON : (3, 3),
    UnitTypeId.TEMPEST : (4, 3),

}

# Bonus damage units does against enemies (type, damage, upgrade_inc)
ATTACK_BONUS_DAMAGE = {
    #ZERG:
    UnitTypeId.BANELING : (IS_LIGHT, 15, 2), # Note: banelings does 80+5 damage versus buildings 
    UnitTypeId.LURKER : (IS_ARMORED, 10, 1),
    UnitTypeId.CORRUPTOR : (IS_MASSIVE, 6, 1),
    UnitTypeId.SPORECRAWLER : (IS_BIOLOGICAL, 15, 0),

    #TERRAN:
    UnitTypeId.MARAUDER : (IS_ARMORED, 10, 1),
    UnitTypeId.GHOST : (IS_LIGHT, 10, 1),
    UnitTypeId.HELLION : (IS_LIGHT, 6, 1), # 11+1 with Infernal Pre-igniter aka blue-flame
    UnitTypeId.HELLIONTANK : (IS_LIGHT, 0, 1), #12+1 with Infernal Pre-igniter aka blue-flame
    UnitTypeId.SIEGETANK : (IS_ARMORED, 10, 1),
    UnitTypeId.SIEGETANKSIEGED : (IS_ARMORED, 30, 1),
    UnitTypeId.THOR : (IS_LIGHT, 6, 1), # Explosive mode
    UnitTypeId.THORAP : (IS_MASSIVE, 15, 2), # High impact mode
    UnitTypeId.VIKINGFIGHTER : (IS_MECHANICAL, 8, 1),
    UnitTypeId.VIKINGASSAULT : (IS_ARMORED, 4, 0),

    #PROTOSS:
    UnitTypeId.STALKER : (IS_ARMORED, 5, 1),
    UnitTypeId.ADEPT : (IS_LIGHT, 12, 1),
    UnitTypeId.IMMORTAL : (IS_ARMORED, 30, 3),
    UnitTypeId.COLOSSUS : (IS_LIGHT, 5, 1),
    UnitTypeId.PHOENIX : (IS_LIGHT, 5, 0),
    UnitTypeId.VOIDRAY : (IS_ARMORED, 4, 0), # +10 in primatic alignment
    UnitTypeId.ORACLE : (IS_LIGHT, 7, 0),
    UnitTypeId.TEMPEST : (IS_MASSIVE , 22, 2), #TODO: ONLY versus AIR
    UnitTypeId.ARCHON : (IS_BIOLOGICAL, 10, 1),

}

ATTACK_SPLASH_RANGE = {
    UnitTypeId.BANELING : 2.2,
    UnitTypeId.ULTRALISK : 2.5, # 33% over 180 degree arc
    # Purification nova : 1.5,
    UnitTypeId.ARCHON : 0.5, # ??

}

def get_attack_upgrade_increase(id, vs_air:bool = False) -> int:
    tmp = ATTACK_UPGRADE_INC.get(id, ATTACK_UPGRADE_DEFAULT)
    return tmp[1] if vs_air else tmp[0]






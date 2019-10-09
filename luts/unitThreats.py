
from sc2.constants import UnitTypeId




#this list is a hand crafted threat list for units that is used to help the Agents make decisions
#the reason is that certain aspects of unit information is very hard to dedude directly from stats and attributes
# all values are between 0 and 1.0 for the network

DEFAULT_UNIT_THREAT_VALUE = 0.0

UNIT_THREAT_VALUE = {
    UnitTypeId.QUEEN : 0.2,
    UnitTypeId.BANELING : 0.1,
    UnitTypeId.RAVAGER : 0.1,
    UnitTypeId.LURKER : 0.3,
    UnitTypeId.INFESTOR : 0.75,
    UnitTypeId.SWARMHOSTMP : 0.5,
    UnitTypeId.ULTRALISK : 0.1,
    UnitTypeId.BROODLORD : 0.4,
    UnitTypeId.VIPER : 0.75,

    UnitTypeId.MARINE : 0.1,
    UnitTypeId.MARAUDER : 0.1,
    UnitTypeId.REAPER : 0.1,
    UnitTypeId.GHOST : 0.75,
    UnitTypeId.SIEGETANK : 0.15,
    UnitTypeId.CYCLONE : 0.1,
    UnitTypeId.WIDOWMINE : 0.4,
    UnitTypeId.MEDIVAC : 0.7,
    UnitTypeId.LIBERATOR : 0.2,
    UnitTypeId.RAVEN : 0.75,
    UnitTypeId.BANSHEE : 0.3,
    UnitTypeId.BATTLECRUISER : 0.2,

    UnitTypeId.SENTRY : 0.4,
    UnitTypeId.ADEPT : 0.1,
    UnitTypeId.HIGHTEMPLAR : 0.75,
    UnitTypeId.DARKTEMPLAR : 0.3,
    UnitTypeId.IMMORTAL : 0.1,
    UnitTypeId.DISRUPTOR : 0.3,
    UnitTypeId.OBSERVER : 0.3,
    UnitTypeId.WARPPRISM : 0.7,
    UnitTypeId.VOIDRAY : 0.1,
    UnitTypeId.ORACLE : 0.3,
    UnitTypeId.CARRIER : 0.5,
    UnitTypeId.MOTHERSHIP : 1.0,
}



#TODO: improve my list of counters - a lot of improvement is still required
# I think I have way to much stuff here, and should thin it out.

# This list contains unit counters to also help in some calculations and so forth
UNIT_HARD_COUNTERS = {
    UnitTypeId.ZERGLING : {UnitTypeId.BANELING, UnitTypeId.COLOSSUS, UnitTypeId.HELLION, UnitTypeId.HELLIONTANK},
    UnitTypeId.ROACH : {UnitTypeId.SIEGETANK, UnitTypeId.IMMORTAL, UnitTypeId.ULTRALISK},
    UnitTypeId.LURKER : {UnitTypeId.SIEGETANK, UnitTypeId.ULTRALISK, UnitTypeId.DISRUPTOR},
    UnitTypeId.INFESTOR : {UnitTypeId.GHOST, UnitTypeId.HIGHTEMPLAR},
    UnitTypeId.BROODLORD : {UnitTypeId.CORRUPTOR, UnitTypeId.VOIDRAY, UnitTypeId.VIKING},
    UnitTypeId.VIPER : {UnitTypeId.GHOST, UnitTypeId.HIGHTEMPLAR},

    UnitTypeId.MARINE : {UnitTypeId.BANELING, UnitTypeId.COLOSSUS, UnitTypeId},
    UnitTypeId.MARAUDER : {UnitTypeId.ZEALOT},
    UnitTypeId.REAPER : {UnitTypeId.STALKER},
    UnitTypeId.GHOST : {UnitTypeId.STALKER, UnitTypeId.ZERGLING},
    UnitTypeId.HELLION : {UnitTypeId.ROACH, UnitTypeId.STALKER, UnitTypeId.MARAUDER, UnitTypeId.SIEGETANK},
    UnitTypeId.SIEGETANK : {UnitTypeId.BANSHEE, UnitTypeId.MUTALISK, UnitTypeId.IMMORTAL },
    UnitTypeId.CYCLONE : {UnitTypeId.SIEGETANK},
    UnitTypeId.THOR : {UnitTypeId.INFESTOR},
    UnitTypeId.MEDIVAC : {UnitTypeId.CORRUPTOR, UnitTypeId.VIKING, UnitTypeId.VOIDRAY},
    UnitTypeId.LIBERATOR : {UnitTypeId.CORRUPTOR, UnitTypeId.VIKING, UnitTypeId.VOIDRAY},
    UnitTypeId.RAVEN : {UnitTypeId.GHOST, UnitTypeId.HIGHTEMPLAR},
    UnitTypeId.BATTLECRUISER : {UnitTypeId.INFESTOR},

    UnitTypeId.ZEALOT : {UnitTypeId.COLOSSUS, UnitTypeId.HELLIONTANK},
    UnitTypeId.SENTRY : {UnitTypeId.GHOST, UnitTypeId.HIGHTEMPLAR, UnitTypeId.ULTRALISK, UnitTypeId.THOR, UnitTypeId.ARCHON},
    UnitTypeId.ADEPT : {UnitTypeId.STALKER},
    UnitTypeId.HIGHTEMPLAR : {UnitTypeId.GHOST},
    UnitTypeId.DARKTEMPLAR : {UnitTypeId.OVERSEER, UnitTypeId.OBSERVER, UnitTypeId.RAVEN, UnitTypeId.PHOTONCANNON},
    UnitTypeId.COLOSSUS : {UnitTypeId.CORRUPTOR, UnitTypeId.VIKING, UnitTypeId.TEMPEST},
    UnitTypeId.ARCHON : {UnitTypeId.GHOST},
    UnitTypeId.OBSERVER : {UnitTypeId.OVERSEER, UnitTypeId.OBSERVER, UnitTypeId.RAVEN},
    UnitTypeId.WARPPRISM : {UnitTypeId.CORRUPTOR, UnitTypeId.VIKING, UnitTypeId.VOIDRAY},
    UnitTypeId.PHOENIX : {UnitTypeId.CORRUPTOR, UnitTypeId.CARRIER, UnitTypeId.BATTLECRUISER},
    UnitTypeId.ORACLE : {UnitTypeId.VIKING, UnitTypeId.CORRUPTOR, UnitTypeId.GHOST, UnitTypeId.HIGHTEMPLAR},
    UnitTypeId.CARRIER : {UnitTypeId.INFESTOR, UnitTypeId.CORRUPTOR, UnitTypeId.TEMPEST, UnitTypeId.VIKING},
    UnitTypeId.TEMPEST : {UnitTypeId.CORRUPTOR, UnitTypeId.VIKING, UnitTypeId.VOIDRAY},
    UnitTypeId.MOTHERSHIP : {UnitTypeId.TEMPEST}
}


UNIT_SOFT_COUNTERS = {
    UnitTypeId.QUEEN : {UnitTypeId.ZERGLING, UnitTypeId.MARINE, UnitTypeId.ZEALOT},
    UnitTypeId.ZERGLING : {UnitTypeId.ADEPT, UnitTypeId.ZEALOT, UnitTypeId},
    UnitTypeId.BANELING : {UnitTypeId.MARAUDER, UnitTypeId.ROACH, UnitTypeId.STALKER},
    UnitTypeId.ROACH : {UnitTypeId.MARAUDER, UnitTypeId.VOIDRAY },
    UnitTypeId.LURKER : {UnitTypeId.OVERSEER, UnitTypeId.OBSERVER, UnitTypeId.RAVEN, UnitTypeId.PHOTONCANNON, UnitTypeId.RAVAGER},
    UnitTypeId.INFESTOR : {UnitTypeId.SIEGETANK, UnitTypeId.TEMPEST, UnitTypeId.ULTRALISK},
    UnitTypeId.SWARMHOSTMP : {UnitTypeId.HELLIONTANK, UnitTypeId.COLOSSUS, UnitTypeId.ULTRALISK},
    UnitTypeId.ULTRALISK : {UnitTypeId.VOIDRAY, UnitTypeId.BROODLORD, UnitTypeId.BATTLECRUISER, UnitTypeId.IMMORTAL},
    UnitTypeId.MUTALISK : {UnitTypeId.CORRUPTOR, UnitTypeId.SPORECRAWLER, UnitTypeId.THOR, UnitTypeId.PHOENIX},
    UnitTypeId.CORRUPTOR : {UnitTypeId.VOIDRAY, UnitTypeId.HYDRALISK, UnitTypeId.VIKING},
    UnitTypeId.BROODLORD : {UnitTypeId.THOR, UnitTypeId.INFESTOR, UnitTypeId.VIPER, UnitTypeId.BATTLECRUISER},
    UnitTypeId.VIPER : {UnitTypeId.VIKING, UnitTypeId.PHOENIX, UnitTypeId.ULTRALISK},

    UnitTypeId.MARINE : {UnitTypeId.INFESTOR, UnitTypeId.HELLION, UnitTypeId.ARCHON},
    UnitTypeId.MARAUDER : {UnitTypeId.ZERGLING, UnitTypeId.MARINE, UnitTypeId.IMMORTAL},
    UnitTypeId.REAPER : {UnitTypeId.QUEEN, UnitTypeId.MARAUDER, UnitTypeId.ROACH, UnitTypeId.ADEPT},
    UnitTypeId.GHOST : {UnitTypeId.HIGHTEMPLAR, UnitTypeId.OVERSEER, UnitTypeId.OBSERVER, UnitTypeId.RAVEN},
    UnitTypeId.HELLION : {UnitTypeId.QUEEN},
    UnitTypeId.SIEGETANK : {UnitTypeId.ZERGLING, UnitTypeId.ZEALOT},
    UnitTypeId.CYCLONE : {UnitTypeId.ZERGLING, UnitTypeId.IMMORTAL},
    UnitTypeId.WIDOWMINE : {UnitTypeId.OVERSEER, UnitTypeId.OBSERVER, UnitTypeId.RAVEN, UnitTypeId.RAVAGER},
    UnitTypeId.THOR : {UnitTypeId.IMMORTAL},
    UnitTypeId.VIKING : {UnitTypeId.MARINE, UnitTypeId.MUTALISK, UnitTypeId.STALKER},
    UnitTypeId.MEDIVAC : {UnitTypeId.INFESTOR, UnitTypeId.GHOST, UnitTypeId.HIGHTEMPLAR},
    UnitTypeId.RAVEN : {UnitTypeId.VIKING, UnitTypeId.CORRUPTOR, UnitTypeId.PHOENIX},
    UnitTypeId.BATTLECRUISER : {UnitTypeId.VOIDRAY, UnitTypeId.CORRUPTOR, UnitTypeId.BATTLECRUISER, UnitTypeId.VIKING},

    UnitTypeId.ZEALOT : {UnitTypeId.ROACH, UnitTypeId.MARAUDER},
    UnitTypeId.STALKER : {UnitTypeId.MARAUDER, UnitTypeId.ZERGLING, UnitTypeId.IMMORTAL},
    UnitTypeId.SENTRY : {UnitTypeId.STALKER, UnitTypeId.REAPER, UnitTypeId.HYDRALISK, UnitTypeId.RAVAGER},
    UnitTypeId.ADEPT : {UnitTypeId.QUEEN, UnitTypeId.ROACH, UnitTypeId.MARAUDER},
    UnitTypeId.HIGHTEMPLAR : {UnitTypeId.ROACH, UnitTypeId.ULTRALISK, UnitTypeId.COLOSSUS, UnitTypeId.TEMPEST},
    UnitTypeId.IMMORTAL : {UnitTypeId.ZEALOT, UnitTypeId.ZERGLING, UnitTypeId.MARINE},
    UnitTypeId.COLOSSUS : {UnitTypeId.VOIDRAY},
    UnitTypeId.DISRUPTOR : {UnitTypeId.THOR, UnitTypeId.THOR, UnitTypeId.IMMORTAL},
    UnitTypeId.ARCHON : {UnitTypeId.THOR, UnitTypeId.ULTRALISK, UnitTypeId.IMMORTAL,UnitTypeId.BROODLORD},
    UnitTypeId.WARPPRISM : {UnitTypeId.RAVAGER, UnitTypeId.INFESTOR},
    UnitTypeId.PHOENIX : {UnitTypeId.QUEEN, UnitTypeId.MISSILETURRET},
    UnitTypeId.VOIDRAY : {UnitTypeId.VIKING, UnitTypeId.PHOENIX, UnitTypeId.MUTALISK, UnitTypeId.HYDRALISK, UnitTypeId.QUEEN},
    UnitTypeId.ORACLE : {UnitTypeId.QUEEN},
    UnitTypeId.MOTHERSHIP : {UnitTypeId.OVERSEER, UnitTypeId.OBSERVER, UnitTypeId.RAVEN, UnitTypeId.CORRUPTOR, UnitTypeId.VIKING, UnitTypeId.VOIDRAY},

}






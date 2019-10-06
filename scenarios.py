


from sc2.constants import UnitTypeId
from sc2 import Race

# These scenarios atm do not include special situations like for harassing drones and defending cannon rush etc.

# TODO: open-map vs defense vs attack scenarios

#each scenario is 3 lists of units that will be spawned for each race
# In a tuple or list type object
RACE_INDEX = {
    Race.Zerg : 0,
    Race.Terran : 1,
    Race.Protoss : 2
}
# every list of units consist of a number of tuples
# will later upgrade to NamedTuple
# Fields are:
# 0 - UnitTypeId
# 1 - Minimum amount
# 2 - Maximum amount

# Upgrade levels will be random by the engine


SCENARIOS1 = {
    "Easy1":(
        [(UnitTypeId.ZERGLING, 8,16)], #Zerg
        [(UnitTypeId.MARINE, 4,8)], #Terran
        [(UnitTypeId.ZEALOT, 2,4)] #Protoss
    ),
    "VeryEarlyGame1":(
        [(UnitTypeId.ZERGLING, 6,12),(UnitTypeId.BANELING, 2,4)], #Zerg
        [(UnitTypeId.MARINE, 3,6), (UnitTypeId.REAPER, 1, 3)], #Terran
        [(UnitTypeId.ZEALOT, 1,2), (UnitTypeId.ADEPT, 1, 3)] #Protoss
    ),
    "SentryDefense1":(
        [(UnitTypeId.ZERGLING, 4,8), (UnitTypeId.ROACH, 1,2)], #Zerg
        [(UnitTypeId.MARINE, 2,4), (UnitTypeId.MARAUDER, 1,2)], #Terran
        [(UnitTypeId.ZEALOT, 1,1), (UnitTypeId.SENTRY, 1,2), (UnitTypeId.STALKER,0,1)] #Protoss
    ),
    "Tier1_A":(
        [(UnitTypeId.ZERGLING,6,12), (UnitTypeId.ROACH, 2, 6)], #Zerg
        [(UnitTypeId.MARINE,3,6), (UnitTypeId.MARAUDER, 2,4), (UnitTypeId.SIEGETANK,0,1)], #Terran
        [(UnitTypeId.ZEALOT,1,3), (UnitTypeId.STALKER, 2, 4), (UnitTypeId.SENTRY, 0, 2)] #Protoss
    ),
    "Rush":(
        [(UnitTypeId.ZERGLING,12,18), (UnitTypeId.BANELING,0,3) ], #Zerg
        [(UnitTypeId.MARINE, 6,10), (UnitTypeId.REAPER,0,3)], #Terran
        [(UnitTypeId.ZEALOT, 4,8), (UnitTypeId.ADEPT,0,3)] #Protoss
    ),
    "EarlyDefense":(
        [(UnitTypeId.QUEEN, 1,2), (UnitTypeId.ZERGLING,2,4), (UnitTypeId.SPINECRAWLER, 0, 1)], #Zerg
        [(UnitTypeId.BUNKER,0,1), (UnitTypeId.MARINE, 2,4), (UnitTypeId.SIEGETANK, 0, 1)], #Terran
        [(UnitTypeId.ZEALOT,1,2), (UnitTypeId.SENTRY,0,2), (UnitTypeId.ADEPT, 0, 1), (UnitTypeId.STALKER,0,1), (UnitTypeId.PHOTONCANNON,0,1)] #Protoss
    ),
    "TimingAttack1":(
        [(UnitTypeId.ROACH,7,12), (UnitTypeId.RAVAGER,0,3)],  # Zerg
        [(UnitTypeId.MARINE,6,12), (UnitTypeId.MARAUDER,3,6)],  # Terran
        [(UnitTypeId.ZEALOT,0,2), (UnitTypeId.STALKER,5,12), (UnitTypeId.SENTRY,0,1)]  # Protoss
    ),
    "AirRush1":(
        [(UnitTypeId.MUTALISK, 4,8)], #Zerg
        [(UnitTypeId.LIBERATOR, 3,5)], #Terran
        [(UnitTypeId.PHOENIX, 3,6)] #Protoss
    ),
    "EarlyMidGame":(
        [(UnitTypeId.ROACH, 4,8), (UnitTypeId.HYDRALISK, 3,6)],  # Zerg
        [(UnitTypeId.MARINE,6,10), (UnitTypeId.MARAUDER, 4,8), (UnitTypeId.SIEGETANK,1,2)],  # Terran
        [(UnitTypeId.STALKER, 5,10), (UnitTypeId.IMMORTAL, 0,1), (UnitTypeId.SENTRY,0,1)]  # Protoss
    ),
    "XYZ":(
        [], #Zerg
        [], #Terran
        [] #Protoss
    )



}


#TODO: a test program that analyze the cost comparison of these setups against each other and prints summary
# this would greatly help me tweak the training setups to be more useful











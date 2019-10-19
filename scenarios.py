


from sc2.constants import UnitTypeId
from sc2 import Race
from collections import namedtuple

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

SCENARIO_TYPE_ANY = 0
SCENARIO_TYPE_OPEN = 1
SCENARIO_TYPE_DEFENSE = 2
SCENARIO_TYPE_ATTACK = 3
SCENARIO_TYPE_HARASS_DEFENSE = 4
SCENARIO_TYPE_HARASS_ATTACK = 5


# scenario_type = one of the above constants
# p1 = RaceTyple for player 1 (under training)
# p2 = RaceTuple for player 2 (protagonist) - or None in which case p1 is used
# networks = List[Network names that gets trained here]
# level = a value between 1 and 10 scaling how advanced this is. (influences some training stuff)

Scenario = namedtuple('Scenario',['scenario_type','p1','p2','networks', 'level'])
RaceTuple = namedtuple('RaceTuple',['zerg','terran','protoss'])
ScUnits = namedtuple('ScUnits',['type_id','min','max'])


def get_race_scunits(sc :Scenario, player_id, race):
    assert isinstance(sc, Scenario)
    rt : RaceTuple = sc.p1 if player_id == 1 else sc.p2
    if not rt:
        rt = sc.p1
    assert isinstance(rt, RaceTuple)
    if race == Race.Zerg:
        u = rt.zerg
    elif race == Race.Terran:
        u = rt.terran
    elif race == Race.Protoss:
        u = rt.protoss
    return u

def get_network_names(sc: Scenario, race):
    assert isinstance(sc, Scenario)
    n : RaceTuple = sc.networks
    assert isinstance(n, RaceTuple)
    if race == Race.Zerg:
        u = n.zerg
    elif race == Race.Terran:
        u = n.terran
    elif race == Race.Protoss:
        u = n.protoss
    assert isinstance(u,list)
    return u


#TODO: banelings!
#TODO: early queen defense!

SCENARIOS2 =[
    Scenario(SCENARIO_TYPE_ANY,
        p1 = RaceTuple(
            zerg = [ScUnits(UnitTypeId.ZERGLING, 8,16)], #Zerg
            terran = [ScUnits(UnitTypeId.MARINE, 4,8)], #Terran
            protoss = [ScUnits(UnitTypeId.ZEALOT, 2,4)]),
        p2 = None,
        networks = RaceTuple(
            zerg= ["melee_move", "melee_attack"],
            terran=["range_move" , "range_attack"],
            protoss=["melee_move", "melee_attack"]),
        level = 1
    ),
    Scenario(SCENARIO_TYPE_ANY,
         p1=RaceTuple(
             zerg=[ScUnits(UnitTypeId.ZERGLING, 8, 16)],  # Zerg
             terran=[ScUnits(UnitTypeId.MARINE, 4, 8)],  # Terran
             protoss=[ScUnits(UnitTypeId.ZEALOT, 2, 4)]),
         p2=RaceTuple(
             zerg=[ScUnits(UnitTypeId.BANELING, 2, 8)],  # Zerg
             terran=None,
             protoss=None),
         networks=RaceTuple(
             zerg=["melee_move", "melee_attack"],
             terran=["range_move", "range_attack"],
             protoss=["melee_move", "melee_attack"]),
         level=1
         ),
    Scenario(SCENARIO_TYPE_ANY,
         p1=RaceTuple(
             zerg=[ScUnits(UnitTypeId.ROACH, 2, 6)],  # Zerg
             terran=[ScUnits(UnitTypeId.MARAUDER, 2, 6)],  # Terran
             protoss=[ScUnits(UnitTypeId.STALKER, 2, 6)]),
         p2=RaceTuple(
             zerg=[ScUnits(UnitTypeId.BANELING, 2, 8)],  # Zerg
             terran=None,
             protoss=None),
         networks=RaceTuple(
             zerg=["range_move", "range_attack"],
             terran=["range_move", "range_attack"],
             protoss=["range_move", "range_attack"]),
         level=1
         ),
    Scenario(SCENARIO_TYPE_ANY,
         p1=RaceTuple(
             zerg=[ScUnits(UnitTypeId.HYDRALISK, 4, 8)],  # Zerg
             terran=[ScUnits(UnitTypeId.MARINE, 6, 12)],  # Terran
             protoss=[ScUnits(UnitTypeId.STALKER, 4, 8)]),
         p2=RaceTuple(
             zerg=[ScUnits(UnitTypeId.ZERGLING, 2, 8), ScUnits(UnitTypeId.ROACH, 2, 4)],  # Zerg
             terran=[ScUnits(UnitTypeId.MARINE, 2, 8), ScUnits(UnitTypeId.MARAUDER,2,4)],
             protoss=[ScUnits(UnitTypeId.ZEALOT, 2, 4), ScUnits(UnitTypeId.STALKER, 4,8)]),
         networks=RaceTuple(
             zerg=["range_move", "range_attack"],
             terran=["range_move", "range_attack"],
             protoss=["range_move", "range_attack"]),
         level=1
         ),
    Scenario(SCENARIO_TYPE_ANY,
        p1 = RaceTuple(
            zerg=[ScUnits(UnitTypeId.ROACH, 4, 12)],
            terran=[ScUnits(UnitTypeId.MARINE, 2, 8), ScUnits(UnitTypeId.MARAUDER, 2,6)],
            protoss=[ScUnits(UnitTypeId.STALKER, 4, 10)]
        ),
        p2 = None,
        networks = RaceTuple(
            zerg=["range_move" , "range_attack"],
            terran=["range_move" , "range_attack"],
            protoss=["range_move" , "range_attack"]),
        level = 1
    ),
    Scenario(SCENARIO_TYPE_ANY,
        p1 = RaceTuple(
            zerg=[ScUnits(UnitTypeId.ZERGLING, 6,12), ScUnits(UnitTypeId.ROACH, 4, 8)],
            terran=[ScUnits(UnitTypeId.MARINE, 4,8), ScUnits(UnitTypeId.MARAUDER, 4,9)],
            protoss=[ScUnits(UnitTypeId.ZEALOT, 2,4), ScUnits(UnitTypeId.STALKER, 4,8)]
        ),
        p2 = None,
        networks = RaceTuple(
            zerg=["range_move", "range_attack", "melee_move", "melee_attack"],
            terran=["range_move" , "range_attack"],
            protoss=["range_move", "range_attack", "melee_move", "melee_attack"]),
        level = 1
    ),
    Scenario(SCENARIO_TYPE_ANY,
        p1 = RaceTuple(
            zerg=[ScUnits(UnitTypeId.ROACH, 6,12), ScUnits(UnitTypeId.HYDRALISK, 4, 8)],
            terran=[ScUnits(UnitTypeId.MARINE, 6,12), ScUnits(UnitTypeId.MARAUDER, 5,10)],
            protoss=[ScUnits(UnitTypeId.STALKER, 6,12), ScUnits(UnitTypeId.IMMORTAL, 2,4)],
        ),
        p2 = None,
        networks=RaceTuple(
            zerg=["range_move", "range_attack"],
            terran=["range_move", "range_attack"],
            protoss=["range_move", "range_attack"]),
        level = 2
    ),
    Scenario(SCENARIO_TYPE_DEFENSE,
         p1=RaceTuple(
             zerg=[ScUnits(UnitTypeId.ZERGLING, 2, 6), ScUnits(UnitTypeId.QUEEN, 1, 2)],
             terran=[ScUnits(UnitTypeId.MARINE, 1, 2), ScUnits(UnitTypeId.REAPER, 0, 1), ScUnits(UnitTypeId.HELLION,0,2)],
             protoss=[ScUnits(UnitTypeId.ZEALOT, 0, 2), ScUnits(UnitTypeId.STALKER, 0, 1), ScUnits(UnitTypeId.SENTRY,1, 1), ScUnits(UnitTypeId.ADEPT,0,1)],
         ),
         p2=RaceTuple(
             zerg=[ScUnits(UnitTypeId.ZERGLING, 4, 12), ScUnits(UnitTypeId.ROACH, 2, 6)],
             terran=[ScUnits(UnitTypeId.MARINE, 4, 8), ScUnits(UnitTypeId.MARAUDER, 2, 4)],
             protoss=[ScUnits(UnitTypeId.ZEALOT, 2, 6), ScUnits(UnitTypeId.STALKER, 2, 4), ScUnits(UnitTypeId.SENTRY, 0,2)],
         ),
         networks=RaceTuple(
         zerg=["range_move", "range_attack", "melee_move", "melee_attack"],
         terran=["range_move", "range_attack"],
         protoss=["range_move", "range_attack"]),
         level=2
         ),
    Scenario(SCENARIO_TYPE_DEFENSE,
         p1=RaceTuple(
             zerg=[ScUnits(UnitTypeId.ZERGLING, 2, 6), ScUnits(UnitTypeId.QUEEN, 1, 2)],
             terran=[ScUnits(UnitTypeId.MARINE, 2, 4), ScUnits(UnitTypeId.SIEGETANK, 1, 1)],
             protoss=[ScUnits(UnitTypeId.ZEALOT, 2, 4), ScUnits(UnitTypeId.SENTRY, 1, 2)],
         ),
         p2=RaceTuple(
             zerg=[ScUnits(UnitTypeId.ZERGLING, 4, 12), ScUnits(UnitTypeId.ROACH, 2, 6)],
             terran=[ScUnits(UnitTypeId.MARINE, 4, 8), ScUnits(UnitTypeId.MARAUDER, 2, 4)],
             protoss=[ScUnits(UnitTypeId.ZEALOT, 2, 6), ScUnits(UnitTypeId.STALKER, 2, 4), ScUnits(UnitTypeId.ADEPT, 1, 2)],
         ),
         networks=RaceTuple(
             zerg=["range_move", "range_attack", "melee_move", "melee_attack"],
             terran=["range_move", "range_attack"],
             protoss=["range_move", "range_attack", "melee_move", "melee_attack"]),
         level=2
         ),
    Scenario(SCENARIO_TYPE_DEFENSE,
         p1=RaceTuple(
             zerg=[ScUnits(UnitTypeId.ZERGLING, 2, 6), ScUnits(UnitTypeId.QUEEN, 1, 3), ScUnits(UnitTypeId.ROACH, 0, 2)],
             terran=[ScUnits(UnitTypeId.MARINE, 2, 4), ScUnits(UnitTypeId.SIEGETANK, 0, 1), ScUnits(UnitTypeId.MARAUDER, 0, 2)],
             protoss=[ScUnits(UnitTypeId.ZEALOT, 2, 4), ScUnits(UnitTypeId.SENTRY, 1, 2), ScUnits(UnitTypeId.STALKER,0, 2)],
         ),
         p2=RaceTuple(
             zerg=[ScUnits(UnitTypeId.ZERGLING, 6, 12), ScUnits(UnitTypeId.ROACH, 2, 6), ScUnits(UnitTypeId.BANELING, 3, 6)],
             terran=None,
             protoss=None,
         ),
         networks=RaceTuple(
             zerg=["range_move", "range_attack", "melee_move", "melee_attack"],
             terran=["range_move", "range_attack"],
             protoss=["range_move", "range_attack", "melee_move", "melee_attack"]),
         level=2
         ),
    Scenario(SCENARIO_TYPE_ATTACK,
         p1=RaceTuple(
             zerg=[ScUnits(UnitTypeId.ZERGLING, 4, 8), ScUnits(UnitTypeId.ROACH, 4, 8)],
             terran=[ScUnits(UnitTypeId.MARINE, 3, 6), ScUnits(UnitTypeId.MARAUDER, 3, 6)],
             protoss=[ScUnits(UnitTypeId.ZEALOT, 2, 5), ScUnits(UnitTypeId.STALKER, 4, 8)]
         ),
         p2=RaceTuple(
             zerg=[ScUnits(UnitTypeId.ZERGLING, 4, 12), ScUnits(UnitTypeId.ROACH, 3, 6), ScUnits(UnitTypeId.QUEEN, 1, 3), ScUnits(UnitTypeId.BANELING, 1, 3)],
             terran=[ScUnits(UnitTypeId.MARINE, 4, 8), ScUnits(UnitTypeId.SIEGETANK, 1, 1), ScUnits(UnitTypeId.MARAUDER, 1, 4)],
             protoss=[ScUnits(UnitTypeId.ZEALOT, 2, 4), ScUnits(UnitTypeId.SENTRY, 1, 4), ScUnits(UnitTypeId.STALKER, 4, 8)]
         ),
         networks=RaceTuple(
             zerg=["range_move", "range_attack", "melee_move", "melee_attack"],
             terran=["range_move", "range_attack"],
             protoss=["range_move", "range_attack", "melee_move", "melee_attack"]),
         level=2
         ),
    Scenario(SCENARIO_TYPE_ANY,
         p1=RaceTuple(
             zerg=[ScUnits(UnitTypeId.ZERGLING, 6, 12), ScUnits(UnitTypeId.ROACH, 4, 8), ScUnits(UnitTypeId.RAVAGER, 2,4)],
             terran=[ScUnits(UnitTypeId.MARINE, 4, 8), ScUnits(UnitTypeId.MARAUDER, 4, 9), ScUnits(UnitTypeId.SIEGETANK,1,2)],
             protoss=[ScUnits(UnitTypeId.ZEALOT, 2, 4), ScUnits(UnitTypeId.STALKER, 4, 8), ScUnits(UnitTypeId.SENTRY, 3, 6)]
         ),
         p2=None,
         networks=RaceTuple(
             zerg=["range_move", "range_attack", "melee_move", "melee_attack"],
             terran=["range_move", "range_attack"],
             protoss=["range_move", "range_attack", "melee_move", "melee_attack"]),
         level=3
         ),
    Scenario(SCENARIO_TYPE_OPEN,
         p1=RaceTuple(
             zerg=[ScUnits(UnitTypeId.ZERGLING, 8, 24)],  # Zerg
             terran=None,
             protoss=[ScUnits(UnitTypeId.ZEALOT, 2, 8)]),
         p2=RaceTuple(
             zerg=[ScUnits(UnitTypeId.BANELING, 4, 10)],  # Zerg
             terran=[ScUnits(UnitTypeId.SIEGETANK, 2, 6)],
             protoss=[ScUnits(UnitTypeId.IMMORTAL, 2, 6)]),
         networks=RaceTuple(
             zerg=["melee_move", "melee_attack"],
             terran=["range_move", "range_attack"],
             protoss=["melee_move", "melee_attack"]),
         level=1
         ),
    Scenario(SCENARIO_TYPE_OPEN,
         p1=RaceTuple(
             zerg=[ScUnits(UnitTypeId.ZERGLING, 8, 24)],  # Zerg
             terran=None,
             protoss=[ScUnits(UnitTypeId.ZEALOT, 4, 12)]),
         p2=RaceTuple(
             zerg=[ScUnits(UnitTypeId.ROACH, 4, 8)],  # Zerg
             terran=[ScUnits(UnitTypeId.REAPER, 4, 12)],
             protoss=[ScUnits(UnitTypeId.ADEPT, 4, 12)]),
         networks=RaceTuple(
             zerg=["melee_move", "melee_attack"],
             terran=["range_move", "range_attack"],
             protoss=["melee_move", "melee_attack"]),
         level=1
         ),
    Scenario(SCENARIO_TYPE_OPEN,
         p1=RaceTuple(
             zerg=[ScUnits(UnitTypeId.ZERGLING, 8, 16)],  # Zerg
             terran=None,
             protoss=[ScUnits(UnitTypeId.ZEALOT, 2, 4)]), # Protoss
         p2=RaceTuple(
             zerg=[ScUnits(UnitTypeId.ZERGLING, 8, 16), ScUnits(UnitTypeId.ROACH, 0, 2)],
             terran=[ScUnits(UnitTypeId.MARINE, 4, 8), ScUnits(UnitTypeId.MARAUDER,0, 2)],
             protoss=[ScUnits(UnitTypeId.ZEALOT, 2,4), ScUnits(UnitTypeId.STALKER, 0, 2)]
         ),
         networks=RaceTuple(
             zerg=["melee_move", "melee_attack"],
             terran=["range_move", "range_attack"],
             protoss=["melee_move", "melee_attack"]),
         level=1
         ),
    Scenario(SCENARIO_TYPE_OPEN,
         p1=RaceTuple(
             zerg=[ScUnits(UnitTypeId.ZERGLING, 4, 4)],  # Zerg
             terran=None,
             protoss=[ScUnits(UnitTypeId.ZEALOT, 2, 4)]),  # Protoss
         p2=RaceTuple(
             zerg=[ScUnits(UnitTypeId.ZERGLING, 1, 1), ScUnits(UnitTypeId.ROACH, 0, 0)],
             terran=[ScUnits(UnitTypeId.MARINE, 3, 3), ScUnits(UnitTypeId.MARAUDER, 0, 0)],
             protoss=[ScUnits(UnitTypeId.ZEALOT, 1, 1), ScUnits(UnitTypeId.STALKER, 0, 0)]
         ),
         networks=RaceTuple(
             zerg=["melee_move", "melee_attack"],
             terran=["range_move", "range_attack"],
             protoss=["melee_move", "melee_attack"]),
         level=1
         ),
]



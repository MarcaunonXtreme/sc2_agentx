


from sc2.constants import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId

from BaseAgentA1 import BaseAgentA1

#This file helps with various upgrade tracking and so forth
from sc2.game_data import UnitTypeData
from sc2 import Race
from sc2.constants import IS_STRUCTURE, IS_MECHANICAL, IS_BIOLOGICAL, IS_LIGHT, IS_ARMORED, IS_MASSIVE, IS_PSIONIC

from sc2 import Optional, Union, List, Set
from sc2.data import TargetType
from sc2.cache import property_immutable_cache

import numpy as np


#Note: movement speed in AI is distance per second - if game is played at normal speed.
# ie unit.movement_speed * 1.4 = speed on wiki
# or speed on wiki / 1.4 = unit.movement_speed
#
# ie how far we move in 16 game ticks?

TARGET_GROUND: Set[int] = {TargetType.Ground.value, TargetType.Any.value}
TARGET_AIR: Set[int] = {TargetType.Air.value, TargetType.Any.value}
TARGET_BOTH = TARGET_GROUND | TARGET_AIR


# Base class for unit info tracking
class UnitInfoBase:
    def __init__(self, agent : BaseAgentA1, type_id : UnitTypeId, upgrades ):
        assert isinstance(agent, BaseAgentA1)
        self.agent = agent
        self.type_id = type_id
        assert isinstance(upgrades, np.ndarray)
        self.upgrades = upgrades

        self._type_data : UnitTypeData = agent._game_data.units[type_id.value]
        assert isinstance(self._type_data, UnitTypeData)

        self.speed_upgrade_counter = 0 # used in derived classes


    @property
    def type_data(self) -> UnitTypeData:
        return self._type_data

    @property
    def name(self) -> str:
        """ Returns the name of the unit. """
        return self._type_data.name

    @property
    def race(self) -> Race:
        """ Returns the race of the unit """
        return Race(self._type_data._proto.race)

    @property
    def is_structure(self) -> bool:
        """ Checks if the unit is a structure. """
        return IS_STRUCTURE in self._type_data.attributes

    @property
    def is_light(self) -> bool:
        """ Checks if the unit has the 'light' attribute. """
        return IS_LIGHT in self._type_data.attributes

    @property
    def is_armored(self) -> bool:
        """ Checks if the unit has the 'armored' attribute. """
        return IS_ARMORED in self._type_data.attributes

    @property
    def is_biological(self) -> bool:
        """ Checks if the unit has the 'biological' attribute. """
        return IS_BIOLOGICAL in self._type_data.attributes

    @property
    def is_mechanical(self) -> bool:
        """ Checks if the unit has the 'mechanical' attribute. """
        return IS_MECHANICAL in self._type_data.attributes

    @property
    def is_massive(self) -> bool:
        """ Checks if the unit has the 'massive' attribute. """
        return IS_MASSIVE in self._type_data.attributes

    @property
    def is_psionic(self) -> bool:
        """ Checks if the unit has the 'psionic' attribute. """
        return IS_PSIONIC in self._type_data.attributes


    @property
    def tech_alias(self) -> Optional[List[UnitTypeId]]:
        """ Building tech equality, e.g. OrbitalCommand is the same as CommandCenter
        For Hive, this returns [UnitTypeId.Hatchery, UnitTypeId.Lair]
        For SCV, this returns None """
        return self._type_data.tech_alias

    @property
    def unit_alias(self) -> Optional[UnitTypeId]:
        """ Building type equality, e.g. FlyingOrbitalCommand is the same as OrbitalCommand
        For flying OrbitalCommand, this returns UnitTypeId.OrbitalCommand
        For SCV, this returns None """
        return self._type_data.unit_alias

    @property_immutable_cache
    def _weapons(self):
        """ Returns the weapons of the unit. """
        try:
            return self._type_data._proto.weapons
        except:
            return None

    @property_immutable_cache
    def can_attack(self) -> bool:
        """ Checks if the unit can attack at all. """
        # TODO BATTLECRUISER doesnt have weapons in proto?!
        return bool(self._weapons) or self.type_id in {UnitTypeId.BATTLECRUISER, UnitTypeId.ORACLE}

    @property_immutable_cache
    def can_attack_both(self) -> bool:
        """ Checks if the unit can attack both ground and air units. """
        if self.type_id == UnitTypeId.BATTLECRUISER:
            return True
        if self._weapons:
            return any(weapon.type in TARGET_BOTH for weapon in self._weapons)
        return False

    @property_immutable_cache
    def can_attack_ground(self) -> bool:
        """ Checks if the unit can attack ground units. """
        if self.type_id in {UnitTypeId.BATTLECRUISER, UnitTypeId.ORACLE}:
            return True
        if self._weapons:
            return any(weapon.type in TARGET_GROUND for weapon in self._weapons)
        return False


    @property_immutable_cache
    def _ground_range(self) -> Union[int, float]:
        """ Returns the range against ground units. Does not include upgrades. """
        if self.type_id == UnitTypeId.ORACLE:
            return 4
        if self.type_id == UnitTypeId.BATTLECRUISER:
            return 6
        if self.can_attack_ground:
            weapon = next((weapon for weapon in self._weapons if weapon.type in TARGET_GROUND), None)
            if weapon:
                return weapon.range
        return 0

    def get_ground_attack_range(self):
        return self._ground_range


    @property_immutable_cache
    def _ground_attack_speed(self) -> Union[int, float]:
        """ Returns the dps against ground units. Does not include upgrades. """
        if self.can_attack_ground:
            weapon = next((weapon for weapon in self._weapons if weapon.type in TARGET_GROUND), None)
            if weapon:
                return weapon.speed
        return 1.0

    @property_immutable_cache
    def _air_attack_speed(self) -> Union[int, float]:
        """ Returns the dps against air units. Does not include upgrades. """
        if self.can_attack_air:
            weapon = next((weapon for weapon in self._weapons if weapon.type in TARGET_AIR), None)
            if weapon:
                return weapon.speed
        return 1.0

    def get_ground_attack_speed(self):
        return self._ground_attack_speed

    def get_air_attack_speed(self):
        return self._air_attack_speed

    @property_immutable_cache
    def can_attack_air(self) -> bool:
        """ Checks if the unit can air attack at all. Does not include upgrades. """
        if self.type_id == UnitTypeId.BATTLECRUISER:
            return True
        if self._weapons:
            return any(weapon.type in TARGET_AIR for weapon in self._weapons)
        return False

    @property_immutable_cache
    def _air_range(self) -> Union[int, float]:
        """ Returns the range against air units. Does not include upgrades. """
        if self.type_id == UnitTypeId.BATTLECRUISER:
            return 6
        if self.can_attack_air:
            weapon = next((weapon for weapon in self._weapons if weapon.type in TARGET_AIR), None)
            if weapon:
                return weapon.range
        return 0

    def get_air_attack_range(self):
        return self._air_range

    @property
    def armor(self) -> Union[int, float]:
        """ Returns the armor of the unit. Does not include upgrades """
        return self._type_data._proto.armor

    @property
    def sight_range(self) -> Union[int, float]:
        """ Returns the sight range of the unit. """
        return self._type_data._proto.sight_range

    @property
    def _movement_speed(self) -> Union[int, float]:
        """ Returns the movement speed of the unit. Does not include upgrades or buffs. """
        return self._type_data._proto.movement_speed

    @property
    def is_mineral_field(self) -> bool:
        """ Checks if the unit is a mineral field. """
        return self._type_data.has_minerals

    @property
    def is_vespene_geyser(self) -> bool:
        """ Checks if the unit is a non-empty vespene geyser or gas extraction building. """
        return self._type_data.has_vespene

    @property
    def cargo_size(self) -> Union[float, int]:
        """ Returns the amount of cargo space the unit needs. """
        return self._type_data.cargo_size

    def get_movement_speed(self):
        return self._movement_speed

    def get_base_armor(self):
        return self.armor 


    #When replaced this function is used to check speeds of enemy units to detect if movement speed upgrades is researched
    def check_speed(self, speed):
        pass



class UnitInfo_Zergling(UnitInfoBase):
    def get_movement_speed(self):
        if self.upgrades[UpgradeId.ZERGLINGMOVEMENTSPEED.value]:
            return self._movement_speed*1.6
        else:
            return self._movement_speed

    def get_ground_attack_speed(self):
        if self.upgrades[UpgradeId.ZERGLINGATTACKSPEED.value]:
            return self._ground_attack_speed-0.15 
        else:    
            return self._ground_attack_speed

    def check_speed(self, speed):
        #TODO: figure out how to not GLITCH on this correctly?
        if self.speed_upgrade_counter < 8:
            if speed > self._movement_speed*1.3:
                self.speed_upgrade_counter += 2
            if self.speed_upgrade_counter >= 8:
                print("Detected Enemy got Zergling MovementSpeed Upgrade!")
                self.upgrades[UpgradeId.ZERGLINGMOVEMENTSPEED.value] = True


class UnitInfo_Baneling(UnitInfoBase):
    def get_movement_speed(self):
        if self.upgrades[UpgradeId.CENTRIFICALHOOKS.value]:
            return self._movement_speed*1.18
        else:
            return self._movement_speed

class UnitInfo_Roach(UnitInfoBase):
    def get_movement_speed(self):
        if self.upgrades[UpgradeId.GLIALRECONSTITUTION.value]:
            return self._movement_speed*1.33
        else:
            return self._movement_speed


class UnitInfo_Hydra(UnitInfoBase):
    def get_movement_speed(self):
        if self.upgrades[UpgradeId.EVOLVEMUSCULARAUGMENTS.value]:
            return self._movement_speed*1.25
        else:
            return self._movement_speed

    def get_ground_attack_range(self):
        if self.upgrades[UpgradeId.EVOLVEGROOVEDSPINES.value]:
            return self._ground_range + 1
        else:
            return self._ground_range

    def get_air_attack_range(self):
        if self.upgrades[UpgradeId.EVOLVEGROOVEDSPINES.value]:
            return self._ground_range + 1
        else:
            return self._ground_range


class UnitInfo_Ultralist(UnitInfoBase):

    def get_movement_speed(self):
        if self.upgrades[UpgradeId.ANABOLICSYNTHESIS.value]:
            return self._movement_speed*1.2
        else:
            return self._movement_speed

    def get_base_armor(self):
        if self.upgrades[UpgradeId.CHITINOUSPLATING.value]:
            return 4
        else:
            return 2

class UnitInfo_Overlord(UnitInfoBase):

    def get_movement_speed(self):
        if self.upgrades[UpgradeId.OVERLORDSPEED.value]:
            return self._movement_speed*2.91
        else:
            return self._movement_speed


class UnitInfo_Overseer(UnitInfoBase):

    def get_movement_speed(self):
        if self.upgrades[UpgradeId.OVERLORDSPEED.value]:
            return self._movement_speed*1.29
        else:
            return self._movement_speed


# Can't actually handle infernal Pre-ignoiter here either currently :(
#class UnitInfo_Hellion(UnitInfoBase):

class UnitInfo_Liberator(UnitInfoBase):
    def get_ground_attack_range(self):
        if self.upgrades[UpgradeId.LIBERATORAGRANGEUPGRADE.value]:
            return 5+4
        else:
            return 5

class UnitInfo_Banshee(UnitInfoBase):
    def get_movement_speed(self):
        if self.upgrades[UpgradeId.BANSHEESPEED.value]:
            return self._movement_speed*1.36
        else:
            return self._movement_speed

class UnitInfo_Zealot(UnitInfoBase):
      def get_movement_speed(self):
        if self.upgrades[UpgradeId.CHARGE.value]:
            return self._movement_speed*1.31
        else:
            return self._movement_speed

class UnitInfo_Adept(UnitInfoBase):
    def get_ground_attack_speed(self):
        if self.upgrades[UpgradeId.ADEPTPIERCINGATTACK.value]:
            return self._ground_attack_speed/1.45
        else:
            return self._ground_attack_speed

class UnitInfo_Colossus(UnitInfoBase):
    def get_ground_attack_range(self):
        if self.upgrades[UpgradeId.EXTENDEDTHERMALLANCE.value]:
            return 9
        else:
            return 7

class UnitInfo_Observer(UnitInfoBase):
     def get_movement_speed(self):
        if self.upgrades[UpgradeId.GRAVITICTHRUSTERS.value]:
            return self._movement_speed*1.5
        else:
            return self._movement_speed

class UnitInfo_WarpPrism(UnitInfoBase):
     def get_movement_speed(self):
        if self.upgrades[UpgradeId.GRAVITICDRIVE.value]:
            return self._movement_speed*1.3
        else:
            return self._movement_speed


class UnitInfo_Phoenix(UnitInfoBase):
    def get_air_attack_range(self):
        if self.upgrades[UpgradeId.PHOENIXRANGEUPGRADE.value]:
            return 7
        else:
            return 5


UNIT_INFO_LIST = {
    UnitTypeId.ZERGLING : UnitInfo_Zergling,
    UnitTypeId.BANELING : UnitInfo_Baneling,
    UnitTypeId.ROACH : UnitInfo_Roach,
    UnitTypeId.HYDRALISK : UnitInfo_Hydra,
    UnitTypeId.ULTRALISK : UnitInfo_Ultralist,
    UnitTypeId.OVERLORD : UnitInfo_Overlord,
    UnitTypeId.OVERSEER : UnitInfo_Overseer,

    UnitTypeId.LIBERATOR : UnitInfo_Liberator,
    UnitTypeId.BANSHEE : UnitInfo_Banshee,

    UnitTypeId.ZEALOT : UnitInfo_Zealot,
    UnitTypeId.ADEPT : UnitInfo_Adept,
    UnitTypeId.COLOSSUS : UnitInfo_Colossus,
    UnitTypeId.OBSERVER : UnitInfo_Observer,
    UnitTypeId.WARPPRISM : UnitInfo_WarpPrism,
    UnitTypeId.PHOENIX : UnitInfo_Phoenix,
}



def get_unit_info(type_id : UnitTypeId) -> type:
    return UNIT_INFO_LIST.get(type_id, UnitInfoBase)














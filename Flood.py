# A flood fill algorithm that is very handy for map based analysis of different things
# PixelMap already has a flood algorithm but the idea is to make something more versatile
# this operates on the PixelMap.data_numpy inside it directly 
# this flood fill creates a whole new map, so for flood fills that would only use a small portion of the map it is not very memory efficient

import numpy as np 


from collections import deque

from sc2.pixel_map import PixelMap
from sc2.position import Point2

#if __name__ == "__main__":
from matplotlib import pyplot

#note all coordinates here are row major like numpy -> (y,x)

# Flood Fill algorithm over 2D numpy array
# map - must be a 2d array
# start - can be either:
#     a) a single tuple/list with 2 elements for a coordinate (y,x) (works with Point2)
#     b) a list of such points
#     c) a single value - in which case all map values matching this value will be a starting location
#      (start coodinates are not ranged checked to fit in the map and must be (int,int))
#     d) a lambda function that takes parameters (y,x,v)
# pred - a lambda that gets values (y,x,d,v) and returns true if this is a valid location or not to flood
#    y,x is the coordinates
#    d is the distance in steps from start location
#    v is the map value at these coordinates
# Result is another 2d array of integers. 
#   0 = values that was never used or was blocked
#   1 = start values
#   2+ = flooded values (indicates how far from start location it was flooded, ie. depth)
# Note: currently returns distances as just number of tiles and not perfect "distance". Diagonals are also counters as "1".
# TODO: experiment and see if manhattan distance is better? Or if we must use np.float32 and use the actual calculations?
def flood_fill(map : np.ndarray, start, pred) -> np.ndarray:

    result = np.zeros(map.shape, dtype=np.int32)
    queue : deque = deque()

    ##START processing:
    if hasattr(start, '__call__'):
        #lambda to decide start values: (slowest method)
        for y in range(map.shape[0]):
            for x in range(map.shape[1]):
                if start(y,x,map[y,x]):
                    result[y,x] = 1
                    queue.append((y,x))

    elif isinstance(start, int) or isinstance(start, float):
        #match value:
        coords = np.where(map == start)
        for y,x in zip(coords[0],coords[1]): # Is this the fastest way to do this?
            result[y,x] = 1
            queue.append((y,x))

    else:
        assert isinstance(start,tuple) or isinstance(start, list)
        if isinstance(start[0], tuple):
            # a list of coordinates is provided:
            for y,x in start:
                result[y,x] = 1
                queue.append((y,x))
        else:
            # a single coordinate is provided
            assert isinstance(start[0],int) and isinstance(start[1],int)
            x = start[0]
            y = start[1]
            result[y,x] = 1
            queue.append((y,x))


    ##FLOOD:
    while queue:
        y0,x0 = queue.popleft()
        d = result[y0,x0] + 1
        
        for y,x in [(y0+a,x0+b) for a in (-1,0,1) for b in (-1,0,1)]:
            #TODO: to improve speed we can ignore the edges of the map? It's unplayable anyways?
            if not (0 <= y < map.shape[0] and 0 <= x < map.shape[1]):
                continue #coordinates outside map
            if result[y,x]:
                continue #already used
            
            v = map[y,x]
            if pred(y,x,d,v):
                #add it:
                result[y,x] = d
                queue.append((y,x))

    return result

# Calculates a new placement_grid that is ONLY the base's plateau 
# Calculates the palcement grid area outwards from the base_location that is placeable and closest thatn max_dist
# Usages: 
#   1. use with start_area to calculate the main base plateau area for building
#   2. use with example the natural (first expansion) to calculate it's area, maybe with max_dist < 24?
def calculate_base_plateau(placement_grid : PixelMap, base_location : Point2, max_dist = 24):
    tmp = flood_fill(placement_grid.data_numpy, base_location.position,
    lambda y,x,d,v: v and d < max_dist)
    tmp.clip(max=1,out=tmp)
    return tmp



#Calculate distance from unpathables 
# this can be usefull for unit movement and so forth to know how close to the wall you are?
# See the choke point calculations function below!
def calculate_distance_from_unpathable(pathing_grid : PixelMap):
    if isinstance(pathing_grid, PixelMap):
        pathing_grid = pathing_grid.data_numpy
    tmp = flood_fill(pathing_grid, 0, lambda y,x,d,v: v)
    tmp -= 1 
    return tmp

#Calculate distances from expansion locations for ground units
# might be usefull?
def calculate_distance_from_expansion(pathing_grid : PixelMap, expansion_locations : dict):
    return flood_fill(pathing_grid.data_numpy, expansion_locations.keys(), lambda y,x,d,v : v)

# Calculate distance from a list of buildings
# examples are from: townhalls only, (mine,enemy,both,
# TODO:
#def calculate_distance_from_buildings(pathing_grid : PixelMap, structures : Units):


# Calculates more or less how far a location is from a non-visible tile
# This calculates isn't that fast obviously as it fills the whole map so best not do it EVERY tick!
# Note: Doesn't take patching into consideration
def calculate_distance_from_not_visible(visibility : PixelMap):
    #TODO: can we make this faster somehow?
    coords = np.where(visibility.data_numpy < 2)
    return flood_fill(visibility.data_numpy, [(y,x) for y in coords[0] for x in coords[1]] , lambda y,x,d,v : v==2)



# Calculates the distance from the creep "edge"
# Creep edge tiles comes out as "1" and are any tile that have an adjacent non-creep tile.
# Set on_creep/off_creep to false to not flood over areas that does/does-not have creep (slightly increases speed)
# If pathing_grid is not None it will also consider ground pathing!
# For zerg ground units this is particularly usefull to know.
# Note: recommended to not do this every tick for performance (creep spreads slowly anyways so 1Hz would be more than fast enough)
def calculate_distance_from_creep_edge(creep : PixelMap, on_creep=True, off_creep=True, pathing_grid : PixelMap = None):
    map : np.ndarray = creep.data_numpy
    start = []
    for y in range(8, map.shape[0]-8):
        for x in range(8, map.shape[0]-8):
            if map[y,x] and not all([map[y+1,x],map[y-1,x],map[y,x+1],map[y,x-1]]):
                start.append((y,x)) # Found creep edge

    if pathing_grid:
        return flood_fill(map, start, lambda y,x,d,v : pathing_grid.data_numpy[y,x] and ((v==1 and on_creep) or (v==0 and off_creep)))
    else:
        return flood_fill(map, start, lambda y,x,d,v : (v==1 and on_creep) or (v==0 and off_creep))



# This algorithm can calculate choke point information on the map!
#   This is usefull for building walls and for setting up defensive tactical positions and for general micro play.
# Warning: This algorithm is SLOW! should probably only be executed once at start of game! approaching O(n**3) 
# Reference: https://pdfs.semanticscholar.org/8d80/6103834ad73cdb2ca2714dd13531dba7d8b0.pdf
#   (Although I had to adapt it quite a bit to work)
# If distance_from is True: Returns a map that calculated the distances from choke point tile 
# If distance_from is False: Returns a map that only has the choke points marked.
# Returns both this choke map and the labels map that is essentially a region map. (might be usefull?)
# TODO: we can add a calculation that calculates the size of each label and output that also?
# TODO: We can simplify each collection of gates into a single gate with a start and end location and calculate the width of the choke point
# TODO: we can then also calculate the distance across the labels between these gates and from here have a relative idea how far regions are from each other from ground units
def calculation_choke_points(pathing_grid : PixelMap, distance_from = True, map : np.ndarray = None):
    if map is None:
        map = calculate_distance_from_unpathable(pathing_grid)
    if isinstance(pathing_grid, PixelMap):
        pathing_grid = pathing_grid.data_numpy

    max_depth = np.max(map)
    labels = np.zeros(map.shape, dtype=np.int32)

    next_label = 1
    gates = []

    #level decomposition:
    for depth in range(max_depth,0,-1):

        queue = deque()
        #first flood what we can on the next level:
        for (y,x) in [(a,b) for a in range(8,map.shape[0]-8) for b in range(8,map.shape[1]-8) if map[a,b] == depth]:
            neighbour_labels = [labels[y+dy,x+dx] for dy in (-1,0,1) for dx in (-1,0,1) if labels[y+dy,x+dx]]
            if len(neighbour_labels) > 0:
                queue.append((y,x,neighbour_labels[0]))
                if any(t != neighbour_labels[0] for t in neighbour_labels):
                    gates.append((y,x))

        while queue:
            ty,tx,l = queue.popleft()
            if not labels[ty,tx]:
                labels[ty,tx] = l
                for ny,nx in [(ty+dy,tx+dx) for dy in (-1,0,1) for dx in (-1,0,1) if not labels[ty+dy,tx+dx] and map[ty+dy,tx+dx] == depth]:
                    queue.append((ny,nx,l))

        #Find new labels:
        for (y,x) in [(a,b) for a in range(8,map.shape[0]-8) for b in range(8,map.shape[1]-8) if map[a,b] == depth]:
            if labels[y,x]:
                continue #already flooded
            l = next_label
            next_label += 1
            labels[y,x] = l
            queue.append((y,x))
            while queue:
                ty,tx = queue.popleft()
                assert labels[ty,tx] == l
                for ny,nx in [(ty+dy,tx+dx) for dy in (-1,0,1) for dx in (-1,0,1) if not labels[ty+dy,tx+dx] and map[ty+dy,tx+dx] == depth]:
                    labels[ny,nx] = l
                    queue.append((ny,nx))

    #print(f"Nr of LAbels = {next_label}")


    if distance_from:
        choke = flood_fill(pathing_grid, gates, lambda y,x,d,v : v)
    else:
        choke = np.zeros(map.shape, dtype=np.uint8)
        for gy,gx in gates:
            for y,x in [(gy+a,gx+b) for a in (-1,0,1) for b in (-1,0,1)]:
                choke[y,x] = 1


    gate_list = []
    if True:
        #Calculate start and end points of gates (aka choke points)
        #Note this would be particularly usefull to determine where to build walls I hope.
        tmp = np.zeros(map.shape, dtype=np.uint8)
        queue = deque()
        for (y,x) in [(a,b) for a in range(8,map.shape[0]-8) for b in range(8,map.shape[1]-8) if choke[a,b] == 1]:
            if tmp[y,x]:
                continue
            tmp[y,x] = 1
            end_points = []
            queue.append((y,x))
            #Flood fill this section of "gates"
            while queue:
                ty,tx = queue.popleft()
                for ny,nx in [(ty+dy,tx+dx) for dy in (-1,0,1) for dx in (-1,0,1) if not tmp[ty+dy,tx+dx] and choke[ty+dy,tx+dx] == 1]:
                    tmp[ny,nx] = 1
                    queue.append((ny,nx))
                #select tiles adjacent to "wall" as end_points
                if any(pathing_grid[ty+dy,tx+dx] == 0 for dy in (-2,-1,0,1,2) for dx in (-2,-1,0,1,2)):
                    end_points.append((ty,tx))
                
            if len(end_points) >= 2:
                p1 = end_points[0]
                dist = [abs(p1[0]-p2[0])+abs(p1[1]-p2[0]) for p2 in end_points[1:]]
                p2 = end_points[np.argmax(dist)+1]
                gate_list.append((p1,p2))
            else:
                print("Warning: Error with gate calculation?")


    return choke, labels, gate_list



if __name__ == "__main__":
    print("Flood testing commences")

    testmap = np.zeros((96,96))
    testmap[10:20,10:20] = 1
    testmap[50:60,10:30] = 1
    testmap[10:60, 15:18] = 1
    testmap[40:70, 25:40] = 1
    testmap[50:60, 40:42] = 1
    testmap[40:70, 42:60] = 1

    testmap[10:36,40:80] = 1
    testmap[18:25,50:60] = 0
    testmap[19:24,65:74] = 0

    pyplot.figure()
    pyplot.title("Basic pathing test-map")
    pyplot.imshow(testmap)

    #distance map
    distance_map = calculate_distance_from_unpathable(testmap)

    pyplot.figure()
    pyplot.title("Distance from unpathable")
    pyplot.imshow(distance_map)

    chokes1,_ , _ = calculation_choke_points(testmap, False, map=distance_map)

    pyplot.figure()
    pyplot.title("Choke Points")
    pyplot.imshow(chokes1)

    chokes2, labels, gate_list = calculation_choke_points(testmap, True, map=distance_map)

    for g in gate_list:
        p1 = g[0]
        p2 = g[1]
        print(f"Gate: {p1[0]},{p1[1]} == {p2[0]},{p2[1]}")

    pyplot.figure()
    pyplot.title("Area Labels")
    pyplot.imshow(labels)

    pyplot.figure()
    pyplot.title("Distance from choke points")
    pyplot.imshow(chokes2)

    pyplot.show()


    



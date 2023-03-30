from enum import Enum 
from dataclasses import dataclass
from typing import TypeAlias, Iterator

###############################
## TYPES
class GamePiece(Enum):
    Cube = 'Cube'
    Cone = 'Cone'

class GridHeight(Enum):
    Low = 'Low'
    Mid = 'Mid'
    High = 'High'

class ChargeAction(Enum):
    Docked = 'Docked'
    Engaged = 'Engaged'
    Park = 'Park'

@dataclass
class GridPlacement:
    type: GamePiece
    auto: bool

Grid: TypeAlias = dict[GridHeight, list[GridPlacement | None]]

###############################
## FUNCTIONS
def score_piece(place: GridPlacement | None, height: GridHeight) -> int:

    if place is None:
        return 0

    auto_bonus = 1 if place.auto else 0

    match height:
        case GridHeight.Low:  return 2 + auto_bonus
        case GridHeight.Mid:  return 3 + auto_bonus
        case GridHeight.High: return 5 + auto_bonus


def link_positions_iter(grid: Grid) -> Iterator[tuple[GridHeight, int]]:

    for height, row in grid.items():

        i = 0

        while i <= len(row) - 3:

            if row[i] is not None and row[i+1] is not None and row[i+2] is not None:
                yield height, i
                i += 3
            else:
                i += 1


def link_positions(grid: Grid) -> list[tuple[GridHeight, int]]:
    return list(link_positions_iter(grid))


def link_bonus(grid: Grid) -> int:
    return len(link_positions(grid)) * 5


def score_grid(grid: Grid) -> int:
    return link_bonus(grid) + sum(map(lambda x: sum(map(lambda y: score_piece(y, x[0]), x[1])), grid.items()))


def score_action(auto: bool, end_action: ChargeAction | None) -> int:

    auto_bonus = 2 if auto else 0

    if auto:
        assert end_action != ChargeAction.Park, "Cannot park in auto!"

    match end_action:
        case None: return 0
        case ChargeAction.Park: return 2
        case ChargeAction.Docked: return 6 + auto_bonus
        case ChargeAction.Engaged: return 10 + auto_bonus


def score(grid: Grid, auto_action: ChargeAction | None, end_action: ChargeAction | None, mobility: bool):
    return score_grid(grid) + score_action(True, auto_action) + score_action(False, end_action) + (3 if mobility else 0)


def new_grid() -> Grid:
    return {GridHeight.Low: [None] * 9, GridHeight.Mid: [None] * 9, GridHeight.High: [None] * 9}

def clone_grid(g: Grid) -> Grid:
    return {k: list(v) for k, v in g.items()}


def grid_to_json(grid: Grid) -> object:

    def grid_placement_to_json(gp: GridPlacement | None) -> object:
        return [
            1 if gp.type == GamePiece.Cone else 0,
            gp.auto
        ] if gp else None

    return [
        list(map(grid_placement_to_json, grid[GridHeight.Low])),
        list(map(grid_placement_to_json, grid[GridHeight.Mid])),
        list(map(grid_placement_to_json, grid[GridHeight.High]))
    ]


def json_to_grid(js: object) -> Grid:
    
    def json_to_grid_placement(js: object) -> GridPlacement | None:
        if js == None:
            return None
        return GridPlacement(GamePiece.Cone if js[0] == 1 else GamePiece.Cube, js[1])
    
    return {
        GridHeight.Low:  list(map(json_to_grid_placement, js[0])),
        GridHeight.Mid:  list(map(json_to_grid_placement, js[1])),
        GridHeight.High: list(map(json_to_grid_placement, js[2]))
    }


def action_to_json(act: ChargeAction | None) -> object:
    match act:
        case None: return None
        case ChargeAction.Park: return 0
        case ChargeAction.Docked: return 1
        case ChargeAction.Engaged: return 2

def json_to_action(js: object) -> ChargeAction | None:
    match js:
        case None: return None
        case 0: return ChargeAction.Park
        case 1: return ChargeAction.Docked
        case 2: return ChargeAction.Engaged
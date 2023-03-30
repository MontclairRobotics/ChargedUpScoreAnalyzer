import math
import pygame as pg
import easygui
import json
import sys
import os
from core import *

#######################################
## Internal data
prev_grid = new_grid()
grid = new_grid()

_teams = ['1', '2', '3']

_auto_actions = [None, None, None]
_end_actions = [None, None, None]
_mobilities = [False, False, False]

_height_map = [GridHeight.High, GridHeight.Mid, GridHeight.Low]
_inv_height_map = {_height_map[i]: i for i in range(len(_height_map))}

_keys_down: set[str] = set()
_keys_up: set[str] = set()
_keys_held: set[str] = set()

_mouse_held = False
_mouse_down = False
_mouse_up = False

_selected_team = 0

def resource_path(rel_path: str) -> str:

    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath('.')
    
    return os.path.join(base_path, rel_path)


#######################################
## Graphics
def color_for_piece(piece: GridPlacement | None) -> tuple[pg.Color, pg.Color]:

    bg_col = pg.Color('#207020') if piece is not None and piece.auto else pg.Color('#A0A0A0')

    if piece is None:
        return pg.Color('#A0A0A0'), bg_col

    match piece.type:
        case GamePiece.Cube: return pg.Color('#AF00FF'), bg_col
        case GamePiece.Cone: return pg.Color('#FFFF00'), bg_col


def state_after_click_at(x: int, h: GridHeight) -> GridPlacement | None:

    prev = prev_grid[h][x]
    auto = held('left shift') or held('right shift')

    if prev is not None and prev.team != _selected_team:
        return prev

    if prev is None: 
        return GridPlacement(
            GamePiece.Cube if _inv_height_map[h] == 2 or x in [1, 4, 7] else GamePiece.Cone, 
            auto,
            _selected_team
        )
    
    if auto:
        return GridPlacement(
            prev.type, not prev.auto, prev.team
        )
    
    return None


def team_color(index: int) -> pg.Color:
    match index:
        case 0: return pg.Color('#a02020')
        case 1: return pg.Color('#20a020')
        case 2: return pg.Color('#2020a0')


def action_name(action: ChargeAction | None) -> str:
    match action:
        case ChargeAction.Park:     return 'Park'
        case ChargeAction.Engaged:  return 'Engaged'
        case ChargeAction.Docked:   return 'Docked'
        case None:                  return 'None'


def blit_centered(surf: pg.Surface, other: pg.Surface, rect: pg.Rect):
    trect = pg.Rect(rect.left + (rect.width - other.get_width())//2, rect.top + (rect.height - other.get_height()) // 2, other.get_width(), other.get_height())
    surf.blit(other, trect)
    return trect
def blit_centered_above(surf: pg.Surface, other: pg.Surface, rect: pg.Rect):
    trect = pg.Rect(rect.left + (rect.width - other.get_width())//2, rect.top - other.get_height(), other.get_width(), other.get_height())
    surf.blit(other, trect)
    return trect
def blit_centered_below(surf: pg.Surface, other: pg.Surface, rect: pg.Rect):
    trect = pg.Rect(rect.left + (rect.width - other.get_width())//2, rect.bottom, other.get_width(), other.get_height())
    surf.blit(other, trect)
    return trect


def split_horizontal(rect: pg.Rect, count: int) -> tuple[pg.Rect, ...]:

    def inner():
        x = rect.left
        w = rect.width / count
        for i in range(count):
            yield pg.Rect(x + int(w * i), rect.top, math.ceil(w), rect.height)
    
    return tuple(inner())


def save_to_json() -> object:
    return {
        'grid': grid_to_json(grid),
        'auto_action': list(map(action_to_json, _auto_actions)),
        'end_action': list(map(action_to_json, _end_actions)),
        'mobility': _mobilities,
        'teams': _teams
    }

def load_from_json(js: object) -> str | None:
    global grid, _auto_actions, _end_actions, _mobilities, _teams

    check_json(js, 'grid', 'auto_action', 'end_action', 'mobility', 'teams')

    grid = json_to_grid(js['grid'])
    _auto_actions = list(map(json_to_action, js['auto_action']))
    _end_actions = list(map(json_to_action, js['end_action']))
    _mobilities = js['mobility']
    _teams = js['teams']


#######################################
## Update functionality
def update(surf: pg.surface.Surface, font_large: pg.font.Font, font_small: pg.font.Font):

    global grid, prev_grid, _auto_actions, _end_actions, _mobilities, _teams, _selected_team

    x = 0
    y = 0

    w = 600 // 9
    h = w

    buf = 10

    mouse_pos = pg.mouse.get_pos()

    ## Clear screen ##
    surf.fill('#D0D0D0')


    ## Handle basic inputs ##
    if mouse_down():
        prev_grid = clone_grid(grid)
    
    if pressed('c'):
        grid = new_grid()
        prev_grid = new_grid()
        _auto_actions = [None, None, None]
        _end_actions = [None, None, None]
        _mobilities = [False, False, False]

    if held('s') and held('left ctrl') and (pressed('s') or pressed('left ctrl')):
        path = easygui.filesavebox(default='match.frc', filetypes=['*.frc', '*.json'])
        if path:
            with open(path, 'w') as fp:
                try:
                    json.dump(save_to_json(), fp)
                except Exception as ex:
                    easygui.msgbox(f'An error occured trying to save to {path}: {ex}', 'Error')
    
    if held('o') and held('left ctrl') and (pressed('o') or pressed('left ctrl')):
        path = easygui.fileopenbox(default='*.frc', filetypes=['*.frc', '*.json'])
        if path:
            with open(path, 'r') as fp:
                try:
                    load_from_json(json.load(fp))
                except Exception as ex:
                    easygui.msgbox(f'An error occured trying to open file {path}: {ex}', 'Error')

    if pressed('t'):
        new_teams = easygui.multenterbox(
            'Enter the names of the teams involved in this match!', 
            'Teams',
            ['Team 1', 'Team 2', 'Team 3'],
            _teams
        )

        if new_teams is not None:
            _teams = new_teams

    if pressed('1'): _selected_team = 0
    if pressed('2'): _selected_team = 1
    if pressed('3'): _selected_team = 2

    if pressed('h'): easygui.msgbox(open(resource_path('help.txt')).read(), 'Help')


    ## Render and edit grid ##
    grid_rect = pg.Rect(0, 0, 600, h*3)
    pg.draw.rect(surf, '#C0C0C0', grid_rect, border_bottom_left_radius=5, border_bottom_right_radius=5)

    author_ren = font_small.render('Made by Team 555', True, '#404040')
    surf.blit(author_ren, (300 - author_ren.get_width() // 2, 400 - author_ren.get_height() - 10))

    lbl_ren = font_small.render('Grid', True, '#404040')
    blit_centered_below(surf, lbl_ren, grid_rect)

    for i in range(9):
        for j in range(3):

            tx = x + i*w
            ty = y + j*h

            bg_rect = pg.Rect(tx + buf, ty + buf, w - buf * 2, h - buf * 2)
            fg_rect = pg.Rect(tx + buf + 5, ty + buf + 5, w - buf * 2 - 10, h - buf * 2 - 10)

            if mouse_held() and bg_rect.collidepoint(mouse_pos):
                grid[_height_map[j]][i] = state_after_click_at(i, _height_map[j])

            placement = grid[_height_map[j]][i]
            fg_col, bg_col = color_for_piece(placement)

            pg.draw.rect(surf, bg_col, bg_rect, border_radius=5)
            pg.draw.rect(surf, fg_col, fg_rect, border_radius=5)

            if placement is not None:
                col = '#202020' if placement.type == GamePiece.Cone else '#E0E0E0'
                team_ren = font_small.render(_teams[placement.team], True, col)
                blit_centered(surf, team_ren, bg_rect)


    ## Render links ##
    for height, index in link_positions_iter(grid):
        
        tx = x + index*w
        ty = y + _inv_height_map[height]*h

        bg_rect = pg.Rect(tx + buf // 2, ty + buf // 2, w*3 - buf, h - buf)

        pg.draw.rect(surf, '#E0E0E0', bg_rect, width=5, border_radius=5)


    ## Render buttons ##
    but_w = 200
    but_h = 100

    auto_action_rect = pg.Rect(10, 400 - 10 - but_h, but_w, but_h - 25)
    mob_rect = pg.Rect(10, 400 - 10 - 25, but_w, 25)

    pg.draw.rect(surf, '#A0A0A0', auto_action_rect, border_radius=buf)

    mob_1_rect, mob_2_rect, mob_3_rect = split_horizontal(mob_rect, 3)
    pg.draw.rect(surf, '#207020' if _mobilities[0] else '#A04040', mob_1_rect, border_top_left_radius=buf, border_bottom_left_radius=buf)
    pg.draw.rect(surf, '#207020' if _mobilities[1] else '#A04040', mob_2_rect)
    pg.draw.rect(surf, '#207020' if _mobilities[2] else '#A04040', mob_3_rect, border_top_right_radius=buf, border_bottom_right_radius=buf)

    if auto_action_rect.collidepoint(mouse_pos) and mouse_down():
        if _auto_actions.count(None) == 3 or _auto_actions[_selected_team] is not None:
            match _auto_actions[_selected_team]:
                case None:                 _auto_actions[_selected_team] = ChargeAction.Docked
                case ChargeAction.Docked:  _auto_actions[_selected_team] = ChargeAction.Engaged
                case ChargeAction.Engaged: _auto_actions[_selected_team] = None
    
    if mob_rect.collidepoint(mouse_pos) and mouse_down():
        _mobilities[_selected_team] = not _mobilities[_selected_team]
        
    aut_act_ren = font_small.render(f'Team 2: {action_name(_auto_actions[1])}', True, '#000000')
    cen = blit_centered(surf, aut_act_ren, auto_action_rect)

    aut_act_ren = font_small.render(f'Team 1: {action_name(_auto_actions[0])}', True, '#000000')
    blit_centered_above(surf, aut_act_ren, cen)
    aut_act_ren = font_small.render(f'Team 3: {action_name(_auto_actions[2])}', True, '#000000')
    blit_centered_below(surf, aut_act_ren, cen)

    
    aut_act_lbl_ren = font_small.render('Auto Actions', True, '#404040')
    blit_centered_above(surf, aut_act_lbl_ren, auto_action_rect)
    mob_lbl_ren = font_small.render('Mobility?', True, '#000000')
    blit_centered(surf, mob_lbl_ren, mob_rect)

            
    end_action_rect = pg.Rect(600 - 10 - but_w, 400 - 10 - but_h, but_w, but_h)

    pg.draw.rect(surf, '#A0A0A0', end_action_rect, border_radius=buf)
    if end_action_rect.collidepoint(mouse_pos) and mouse_down():
        match _end_actions[_selected_team]:
            case None:                 _end_actions[_selected_team] = ChargeAction.Park
            case ChargeAction.Park:    _end_actions[_selected_team] = ChargeAction.Docked
            case ChargeAction.Docked:  _end_actions[_selected_team] = ChargeAction.Engaged
            case ChargeAction.Engaged: _end_actions[_selected_team] = None

    # TODO: fixme

    end_act_ren = font_small.render(f'Team 2: {action_name(_end_actions[1])}', True, '#000000')
    cen = blit_centered(surf, end_act_ren, end_action_rect)

    end_act_ren = font_small.render(f'Team 1: {action_name(_end_actions[0])}', True, '#000000')
    blit_centered_above(surf, end_act_ren, cen)
    end_act_ren = font_small.render(f'Team 3: {action_name(_end_actions[2])}', True, '#000000')
    blit_centered_below(surf, end_act_ren, cen)

    end_act_lbl_ren = font_small.render('End Action', True, '#404040')
    blit_centered_above(surf, end_act_lbl_ren, end_action_rect)


    ## Render score ##
    sc = score(grid, _auto_actions, _end_actions, _mobilities, None)
    sc_ren = font_large.render(str(sc), True, '#000000')

    sc_rect = pg.Rect(300 - sc_ren.get_width() // 2, 250, sc_ren.get_width(), sc_ren.get_height())
    surf.blit(sc_ren, sc_rect)

    sc_buf = 5
    last_y = sc_rect.bottom + sc_buf

    for i in range(3):

        sc = score(grid, _auto_actions, _end_actions, _mobilities, i)
        ren = font_small.render(f'Team {i+1}: {sc}', True, '#404040')

        surf.blit(ren, (300 - ren.get_width() // 2, last_y))
        last_y += ren.get_height() + sc_buf


def begin_frame():
    global _mouse_held, _mouse_up, _mouse_down
    _mouse_down = False
    _mouse_up = False


def handle_mouse_up():
    global _mouse_up, _mouse_held
    _mouse_up = True
    _mouse_held = False
def handle_mouse_down():
    global _mouse_down, _mouse_held
    _mouse_down = True
    _mouse_held = True

def mouse_down():
    return _mouse_down
def mouse_up():
    return _mouse_up
def mouse_held():
    return _mouse_held


def handle_keys(events: list[pg.event.Event]):

    global _keys_down, _keys_up
    _keys_down = set()
    _keys_up = set()

    for event in events:
        if event.type == pg.KEYDOWN:
            kn = pg.key.name(event.key).lower()
            _keys_down.add(kn)
            if kn not in _keys_held:
                _keys_held.add(kn)
        elif event.type == pg.KEYUP:
            kn = pg.key.name(event.key).lower()
            _keys_up.add(kn)
            if kn in _keys_held:
                _keys_held.remove(kn)


def held(key: str) -> bool:
    return key in _keys_held
def pressed(key: str) -> bool:
    return key in _keys_down
def released(key: str) -> bool:
    return key in _keys_up

def main():

    pg.init()
    
    icon = pg.image.load(resource_path('icon.png'))

    pg.display.set_caption('Charged Up Score Analyzer')
    pg.display.set_icon(icon)

    surf = pg.display.set_mode((600, 400))

    font_name = 'Fira Code'

    font_big = pg.font.SysFont(font_name, 50)
    font_sml = pg.font.SysFont(font_name, 20)

    running = True

    while running:

        events = pg.event.get()
        begin_frame()

        for event in events:
            if event.type == pg.QUIT:
                running = False
            elif event.type == pg.MOUSEBUTTONDOWN:
                handle_mouse_down()
            elif event.type == pg.MOUSEBUTTONUP:
                handle_mouse_up()
        
        handle_keys(events)

        update(surf, font_big, font_sml)
        pg.display.update()

    pg.quit()


#######################################
## Main loop
if __name__ == '__main__':
    main()
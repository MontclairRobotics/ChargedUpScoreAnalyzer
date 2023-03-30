import pygame as pg
import easygui
import json
from core import *

#######################################
## Internal data
prev_grid = new_grid()
grid = new_grid()

_auto_action = None
_end_action = None
_mobility = False

_height_map = [GridHeight.High, GridHeight.Mid, GridHeight.Low]
_inv_height_map = {_height_map[i]: i for i in range(len(_height_map))}

_keys_down: set[str] = set()
_keys_up: set[str] = set()
_keys_held: set[str] = set()

_mouse_held = False
_mouse_down = False
_mouse_up = False


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

    if prev is None: 
        return GridPlacement(
            GamePiece.Cube if _inv_height_map[h] == 2 or x in [1, 4, 7] else GamePiece.Cone, 
            auto
        )
    
    if auto:
        return GridPlacement(
            prev.type, not prev.auto
        )
    
    return None


def action_name(action: ChargeAction | None) -> str:
    match action:
        case ChargeAction.Park:     return 'Park'
        case ChargeAction.Engaged:  return 'Engaged'
        case ChargeAction.Docked:   return 'Docked'
        case None:                  return 'None'


def blit_centered(surf: pg.Surface, other: pg.Surface, rect: pg.Rect):
    surf.blit(other, (rect.left + (rect.width - other.get_width())//2, rect.top + (rect.height - other.get_height()) // 2))
def blit_centered_above(surf: pg.Surface, other: pg.Surface, rect: pg.Rect):
    surf.blit(other, (rect.left + (rect.width - other.get_width())//2, rect.top - other.get_height()))
def blit_centered_below(surf: pg.Surface, other: pg.Surface, rect: pg.Rect):
    surf.blit(other, (rect.left + (rect.width - other.get_width())//2, rect.bottom))


def save_to_json() -> object:
    return {
        'grid': grid_to_json(grid),
        'auto_action': action_to_json(_auto_action),
        'end_action': action_to_json(_end_action),
        'mobility': _mobility
    }

def load_from_json(js: object):
    global grid, _auto_action, _end_action, _mobility

    grid = json_to_grid(js['grid'])
    _auto_action = json_to_action(js['auto_action'])
    _end_action = json_to_action(js['end_action'])
    _mobility = js['mobility']


#######################################
## Update functionality
def update(surf: pg.surface.Surface, font_large: pg.font.Font, font_small: pg.font.Font):

    global grid, prev_grid, _auto_action, _end_action, _mobility

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

    if held('s') and held('left ctrl') and (pressed('s') or pressed('left ctrl')):
        path = easygui.filesavebox(default='match.frc', filetypes=['*.frc', '*.json'])
        if path:
            with open(path, 'w') as fp:
                json.dump(save_to_json(), fp)
    
    if held('o') and held('left ctrl') and (pressed('o') or pressed('left ctrl')):
        path = easygui.fileopenbox(default='*.frc', filetypes=['*.frc', '*.json'])
        if path:
            with open(path, 'r') as fp:
                load_from_json(json.load(fp))
    

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


    ## Render links ##
    for height, index in link_positions_iter(grid):
        
        tx = x + index*w
        ty = y + _inv_height_map[height]*h

        bg_rect = pg.Rect(tx + buf // 2, ty + buf // 2, w*3 - buf, h - buf)

        pg.draw.rect(surf, '#E0E0E0', bg_rect, width=5, border_radius=5)


    ## Render buttons ##
    but_w = 200
    but_h = 100

    auto_action_rect = pg.Rect(10, 400 - 10 - but_h, but_w, but_h)
    mob_rect = pg.Rect(10, 400 - 10 - 25, but_w, 25)

    pg.draw.rect(surf, '#A0A0A0', auto_action_rect, border_radius=buf)
    pg.draw.rect(surf, '#207020' if _mobility else '#A04040', mob_rect, border_radius=buf)

    if auto_action_rect.collidepoint(mouse_pos) and mouse_down():
        if mob_rect.collidepoint(mouse_pos):
            _mobility = not _mobility
        else:
            match _auto_action:
                case None:                 _auto_action = ChargeAction.Docked
                case ChargeAction.Docked:  _auto_action = ChargeAction.Engaged
                case ChargeAction.Engaged: _auto_action = None
        
    aut_act_ren = font_large.render(action_name(_auto_action), True, '#000000')
    blit_centered(surf, aut_act_ren, auto_action_rect)
    
    aut_act_lbl_ren = font_small.render('Auto Action', True, '#404040')
    blit_centered_above(surf, aut_act_lbl_ren, auto_action_rect)
    mob_lbl_ren = font_small.render('Mobility?', True, '#000000')
    blit_centered(surf, mob_lbl_ren, mob_rect)

            
    end_action_rect = pg.Rect(600 - 10 - but_w, 400 - 10 - but_h, but_w, but_h)

    pg.draw.rect(surf, '#A0A0A0', end_action_rect, border_radius=buf)
    if end_action_rect.collidepoint(mouse_pos) and mouse_down():
        match _end_action:
            case None:                 _end_action = ChargeAction.Park
            case ChargeAction.Park:    _end_action = ChargeAction.Docked
            case ChargeAction.Docked:  _end_action = ChargeAction.Engaged
            case ChargeAction.Engaged: _end_action = None

    end_act_ren = font_large.render(action_name(_end_action), True, '#000000')
    blit_centered(surf, end_act_ren, end_action_rect)

    end_act_lbl_ren = font_small.render('End Action', True, '#404040')
    blit_centered_above(surf, end_act_lbl_ren, end_action_rect)


    ## Render score ##
    sc = score(grid, _auto_action, _end_action, _mobility)
    sc_ren = font_large.render(str(sc), True, (0, 0, 0))

    surf.blit(sc_ren, (300 - sc_ren.get_size()[0] // 2, 300))


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
    surf = pg.display.set_mode((600, 400))

    icon = pg.image.load('icon.png')

    pg.display.set_caption('Charged Up Score Analyzer')
    pg.display.set_icon(icon)

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
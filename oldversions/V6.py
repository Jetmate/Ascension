from math import sqrt
from random import choice

import pygame as pygame
from pygame.locals import *

pygame.init()


def get_list(l, indexes):
    return [l[i] for i in indexes]


def polarity(n):
    return n / abs(n)


def combine_lists(l1, l2, sign):
    l1 = list(l1)
    for i in range(2):
        if sign == '+':
            l1[i] += l2[i]
        elif sign == '-':
            l1[i] -= l2[i]
        elif sign == '*':
            l1[i] *= l2[i]
        else:
            l1[i] /= l2[i]
    return l1


def opposite(n):
    return abs(n - 1)


def make_tuple(thing):
    if type(thing) not in (list, tuple):
        # noinspection PyRedundantParentheses
        return (thing,)
    return thing


def find_center(d1, d2, c1=(0, 0)):
    return [(c1[i] + (d1[i] / 2 - d2[i] / 2)) for i in range(2)]


def collision(c1, d1, c2, d2, inside_only=False):
    d1 = list(d1)
    d2 = list(d2)
    collisions = [False, False]
    for i in range(2):
        d1[i] -= 1
        d2[i] -= 1
        if (c1[i] <= c2[i] and c1[i] + d1[i] >= c2[i] + d2[i]) or \
                (c1[i] >= c2[i] and c1[i] + d1[i] <= c2[i] + d2[i]):
            collisions[i] = True
        if not inside_only:
            if (c2[i] <= c1[i] <= c2[i] + d2[i]) or \
                    (c2[i] <= c1[i] + d1[i] <= c2[i] + d2[i]):
                collisions[i] = True
    if False not in collisions:
        return True
    elif True in collisions:
        return collisions.index(False)


class SpriteSheet:
    def __init__(self, filename, division_index):
        self.sheet = pygame.image.load(filename).convert_alpha()
        self.division_index = division_index
        self.farthest_y_coordinate = 0

    def get_image(self, coordinates, dimensions):
        # noinspection PyArgumentList
        image = pygame.Surface(dimensions, SRCALPHA).convert_alpha()
        image.blit(self.sheet, (0, 0), (coordinates, dimensions))
        return image

    def get_sprites(self, farthest_x_coordinate=0, farthest_y_coordinate=None, all_coordinates=None, y_constant=None,
                    x_constant=None, update=True,
                    scale=True):
        sprites = []
        if not farthest_y_coordinate:
            farthest_y_coordinate = self.farthest_y_coordinate
        if y_constant and x_constant:
            thing = range(x_constant[1])
        else:
            thing = all_coordinates
        for i in thing:
            coordinates_1 = [0, 0]
            coordinates_1[self.division_index] = farthest_y_coordinate
            coordinates_1[opposite(self.division_index)] = farthest_x_coordinate
            if x_constant:
                farthest_x_coordinate = (i + 1) * x_constant[0] - 1
            elif y_constant:
                farthest_x_coordinate = i
            else:
                farthest_x_coordinate = i[opposite(self.division_index)]
            coordinates_2 = [None, None]
            if x_constant or y_constant:
                if x_constant:
                    coordinates_2[opposite(self.division_index)] = farthest_x_coordinate
                else:
                    coordinates_2[opposite(self.division_index)] = i
                if y_constant:
                    coordinates_2[self.division_index] = farthest_y_coordinate + y_constant - 1
                else:
                    coordinates_2[self.division_index] = i
            else:
                coordinates_2 = i
            farthest_x_coordinate += 1
            dimensions = combine_lists((1, 1), combine_lists(coordinates_2, coordinates_1, '-'), '+')
            sprite = self.get_image(coordinates_1, dimensions)
            if scale:
                sprite = pygame.transform.scale(sprite, combine_lists(sprite.get_size(),
                                                                      (game.scale_factor, game.scale_factor), '*'))
            sprites.append(sprite)
        if update:
            if y_constant:
                self.farthest_y_coordinate += y_constant
            elif x_constant:
                self.farthest_y_coordinate = max(all_coordinates) + 1
            else:
                self.farthest_y_coordinate = max(
                    [coordinates[self.division_index] for coordinates in all_coordinates]) + 1
        return sprites


class Quadratic:
    def __init__(self, sign, y_range, speed):
        self.b = 0
        self.a = 1
        if (sign == 1 and y_range[0] > y_range[1]) or (sign == -1 and y_range[1] > y_range[0]):
            x_solution_index = 0
        else:
            x_solution_index = 1
        self.c = y_range[opposite(x_solution_index)]
        self.x_range = [self.get_x(y_range[i])[x_solution_index] for i in range(2)]
        self.x_change = (self.x_range[1] - self.x_range[0]) / speed
        self.current_x = self.x_range[0]
        self.old_y = y_range[0]

    def execute(self):
        self.current_x += self.x_change
        if self.current_x - .01 > self.x_range[1]:
            # noinspection PyRedundantParentheses
            return (self.y_change,)
        current_y = int(self.get_y(self.current_x))
        self.y_change = current_y - self.old_y
        self.old_y = current_y
        return self.y_change

    def get_y(self, x):
        return self.a * x ** 2 + self.b * x + self.c

    def get_x(self, y):
        return sorted(
            [(-self.b + i * sqrt((self.b ** 2) - (4 * self.a * self.c) + (4 * self.a * y))) / (2 * self.a) for i in
             (1, -1)]
        )


class Game:
    def __init__(self, speed, dimensions, scale_factor, version):
        self.speed = speed
        self.dimensions = dimensions
        self.scale_factor = scale_factor
        self.version = version
        self.clock = pygame.time.Clock()
        self.display = pygame.display.set_mode(self.dimensions)
        self.movement_keys = (K_RIGHT, K_LEFT, K_d, K_a)
        self.font = pygame.font.SysFont("Calibri", 100)
        self.condition = 'victory'
        self.count = 0

    @staticmethod
    def exit():
        pygame.quit()
        quit()


class Background:
    def __init__(self, maps, block_sprites, block_color_values, block_offsets):
        self.maps = maps
        self.block_sprites = block_sprites
        self.block_color_values = block_color_values
        self.block_offsets = block_offsets
        self.block_size = game.scale_factor * 10
        self.level = 0
        self.special_block_types = ('entrance', 'exit')

    def block_type(self, grid_coordinates):
        if grid_coordinates in self.blocks:
            return self.blocks[grid_coordinates].kind

    def convert_to_grid(self, coordinates):
        return tuple([int((coordinates[i] - (coordinates[i] % self.block_size)) / self.block_size) for i in range(2)])

    def find_all_grid_coordinates(self, coordinates, dimensions):
        start = self.convert_to_grid(coordinates)
        end = self.convert_to_grid(combine_lists(combine_lists(coordinates, dimensions, '+'), (1, 1), '-'))
        all_coordinates = []

        for x in range(start[0], end[0] + 1):
            for y in range(start[1], end[1] + 1):
                all_coordinates.append((x, y))

        return all_coordinates

    def get_color(self, coordinates):
        return tuple(self.maps[self.level - 1].get_at(coordinates))

    def analyze_map(self):
        self.blocks = {}
        self.cannons = []
        self.backgrounds = []
        self.level += 1
        self.entrance = None

        for x in range(self.maps[self.level - 1].get_width()):
            for y in range(self.maps[self.level - 1].get_height()):
                color = self.get_color((x, y))

                if color in self.block_color_values:
                    block_type = self.block_color_values[color]

                    if block_type == 'entrance':
                        self.entrance = (x, y)

                    elif block_type == 'exit':
                        self.exit = (x, y)

                    self.blocks[(x, y)] = block_type

                elif color != (0, 0, 0, 0):
                    raise Exception("Unidentified block_color {0} at {1}".format(color, (x, y)))

        if not self.entrance:
            raise Exception("No entrance")

        self.backgrounds = [self.entrance]
        active_coordinates = (self.entrance,)

        while active_coordinates:
            all_new_coordinates = []
            for coordinates in active_coordinates:
                for direction in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                    new_coordinates = tuple(combine_lists(coordinates, direction, '+'))
                    if new_coordinates not in self.backgrounds and (new_coordinates not in self.blocks or self.blocks[
                        new_coordinates] != 'block'):
                        self.backgrounds.append(new_coordinates)
                        all_new_coordinates.append(new_coordinates)

            active_coordinates = tuple(all_new_coordinates)

        for initial_coordinates in self.backgrounds:
            self.backgrounds[self.backgrounds.index(initial_coordinates)] = \
                Block(self.block_sprites['background'], combine_lists(
                    initial_coordinates, (self.block_size, self.block_size), '*'), 'background')

        additional_blocks = []

        for initial_coordinates in self.blocks:
            block_type = self.blocks[initial_coordinates]
            coordinates = combine_lists(initial_coordinates, (self.block_size, self.block_size), '*')

            if block_type in self.block_offsets:
                coordinates = combine_lists(coordinates,
                                            combine_lists(
                                                self.block_offsets[block_type],
                                                (game.scale_factor, game.scale_factor), '*'), '+')

            if block_type == 'cannon':
                direction = 0
                for sign in (1, -1):
                    color = self.get_color(combine_lists(initial_coordinates, (sign, 0), '+'))

                    if color in self.block_color_values:
                        if self.block_color_values[color] == 'block':
                            direction = -1 * sign
                            sprites = dict(self.block_sprites[block_type])
                            if direction == -1:
                                sprites['cannon'] = [
                                    pygame.transform.flip(sprite, True, False) for sprite in
                                    self.block_sprites['cannon']['cannon']
                                    ]
                            break

                if direction == 0:
                    raise Exception("Unsupported cannon at {0}".format(initial_coordinates))

                # noinspection PyUnboundLocalVariable
                block = Cannon(sprites, coordinates, block_type, direction)
                self.cannons.append(block)

            else:
                block = Block(self.block_sprites[block_type], coordinates, block_type)

            if len(block.all_grid_coordinates) > 1:
                additional_blocks.append(block)

            else:
                self.blocks[initial_coordinates] = block

        for block in additional_blocks:
            for grid_coordinates in block.all_grid_coordinates:
                self.blocks[grid_coordinates] = block

    def update_level(self):
        self.analyze_map()
        player.default_coordinates = [
            int(find_center(self.blocks[self.entrance].dimensions(), player.dimensions(),
                        self.blocks[self.entrance].coordinates)[0]),
            self.blocks[self.entrance].coordinates[1] + self.blocks[self.entrance].dimensions()[1] -
            player.dimensions()[1]
        ]
        player.total_reset()


class Thing:
    def __init__(self, sprites, sprites_info=None, coordinates=(0, 0)):
        self.sprites = sprites
        self.sprites_info = sprites_info
        self.coordinates = list(coordinates)
        self.reset()

    def dimensions(self, override=False):
        if self.current_sprite_info('dimensions') and not override:
            return self.current_sprite_info('dimensions')
        else:
            return self.current_sprite().get_size()

    def display_coordinates(self):
        if self.current_sprite_info('offsets'):
            return combine_lists(self.coordinates, self.current_sprite_info('offsets'), '+')
        else:
            return self.coordinates

    def update_sprites(self, speed=4, reset=True):
        self.sprite_count += 1
        if self.sprite_count == speed:
            self.sprite_count = 0
            if self.sprite_index == len(self.current_sprites()) - 1:
                if reset:
                    self.sprite_index = 0
                return 'completed'
            self.sprite_index += 1

    def current_sprites(self):
        return make_tuple(self.sprites)

    def current_sprite(self):
        return self.current_sprites()[self.sprite_index]

    def reset(self):
        self.sprite_count = 0
        self.sprite_index = 0

    def current_sprite_info(self, category):
        if self.sprites_info:
            if category in self.sprites_info:
                if self.current_sprite() in self.sprites_info[category]:
                    return self.sprites_info[category][self.current_sprite()]


class Block(Thing):
    def __init__(self, sprites, coordinates, kind):
        super().__init__(sprites, coordinates=coordinates)
        self.all_grid_coordinates = background.find_all_grid_coordinates(self.coordinates, self.dimensions())
        self.kind = kind


class Cannon(Block):
    def __init__(self, sprites, coordinates, kind, direction):
        super().__init__(sprites['cannon'], coordinates, kind)
        self.direction = direction
        self.shot_sprite = sprites['shot']
        self.shot_coordinates = []
        self.shot_dimensions = self.shot_sprite.get_size()
        if self.direction == 1:
            x = self.coordinates[0] + self.dimensions()[0]
        else:
            x = self.coordinates[0] - self.shot_dimensions[0]
        self.shot_initial_coordinates = (
            x, find_center(self.dimensions(), self.shot_dimensions, self.coordinates)[1])
        self.shot_velocity = [5 * self.direction, 0]
        self.shot_frequency = game.speed * 1


class Mob(Thing):
    def __init__(self, sprites, conditions_info, sprites_info=None, coordinates=list((0, 0)),
                 default_sprite_type='stagnant', visible_direction=True):
        self.conditions_info = conditions_info
        self.default_coordinates = coordinates
        self.default_sprite_type = default_sprite_type
        self.visible_direction = visible_direction
        super().__init__(sprites, sprites_info, coordinates)
        self.total_reset()
        self.velocity = [0, 0]
        self.direction = 1

    def current_sprites(self):
        if self.visible_direction:
            return make_tuple(self.sprites[self.direction][self.current_sprite_type])
        else:
            return make_tuple(self.sprites[self.current_sprite_type])

    def reset(self, conditions=None):
        super().reset()
        if conditions:
            for condition in conditions:
                self.conditions[condition] = False

    def total_reset(self):
        self.reset()
        self.current_sprite_type = self.default_sprite_type
        self.velocity = [0, 0]
        self.conditions = {name: self.conditions_info[name]['active'] for name in self.conditions_info}
        self.coordinates = list(self.default_coordinates)
        self.all_grid_coordinates = background.find_all_grid_coordinates(self.coordinates, self.dimensions())

    def process_keys(self, keys):
        if (keys[K_RIGHT] or keys[K_d]) and self.direction != 1:
            self.direction = 1
        elif (keys[K_LEFT] or keys[K_a]) and self.direction != -1:
            self.direction = -1


class Player(Mob):
    def __init__(self, sprites, conditions_info, sprites_info=None):
        super().__init__(sprites, conditions_info, sprites_info, visible_direction=False)
        self.fake_coordinates = find_center(game.dimensions, self.dimensions())

    def generate_display_coordinates(self, coordinates):
        return combine_lists(
            combine_lists(coordinates, self.fake_coordinates, '+'),
            self.coordinates, '-')

    def display_coordinates(self):
        if self.current_sprite_info('offsets'):
            return combine_lists(self.fake_coordinates, self.current_sprite_info('offsets'), '+')
        else:
            return self.fake_coordinates


game = Game(30, (1000, 800), 3, 5)
# background level_maps processing

background_map_sheet = SpriteSheet('background_map_sheet_V{0}.png'.format(game.version), 1)
background_maps_raw = background_map_sheet.get_sprites(y_constant=100, x_constant=(100, 1), scale=False)

# other sprites processing

sprite_sheet = SpriteSheet('sprite_sheet_V{0}.png'.format(game.version), 1)

# background object processing

background_objects_raw = sprite_sheet.get_sprites(all_coordinates=((9, 9), (19, 9), (27, 9), (37, 5)))

background_block_names = ['lava', 'fire', 'flag']

background_sprites = {name: background_objects_raw[background_block_names.index(name)]
                      for name in background_block_names}

cannon_shot_sprite = sprite_sheet.get_sprites(farthest_x_coordinate=44, update=False, all_coordinates=((47, 13),))

background_sprites['cannon'] = {
    'shot': cannon_shot_sprite[0],
    'cannon': (background_objects_raw[3],)
}

background_block_names.append('cannon')

background_door_signs = sprite_sheet.get_sprites(y_constant=9, all_coordinates=(28, 43))

background_doors = sprite_sheet.get_sprites(y_constant=11, x_constant=(15, 8))

door_types = ('entrance', 'exit')

for door_sign_index in range(2):
    if door_sign_index == 0:
        iterator = background_doors
    else:
        iterator = reversed(background_doors)
    for door_sprite in iterator:
        door_sign_sprite = background_door_signs[door_sign_index]

        surface_size = (max(
            door_sign_sprite.get_width(),
            door_sprite.get_width()
        ), door_sign_sprite.get_height() + door_sprite.get_height())

        # noinspection PyArgumentList
        surface = pygame.Surface(surface_size, SRCALPHA).convert_alpha()

        surface.blit(door_sign_sprite, (find_center(
            surface_size, door_sign_sprite.get_size())[0], 0))
        surface.blit(door_sprite, (find_center(
            surface_size, door_sprite.get_size())[0], door_sign_sprite.get_height()))
        background_sprites.setdefault(door_types[door_sign_index], []).append(surface)
    background_block_names.append(door_types[door_sign_index])

block_sprites_raw = sprite_sheet.get_sprites(y_constant=10, x_constant=(10, 4))

background_sprites['block'] = block_sprites_raw

background_sprites_raw = sprite_sheet.get_sprites(y_constant=10, x_constant=(10, 1))

background_sprites['background'] = background_sprites_raw


def convert_to_color(number, base=6):
    c = int(number / base ** 2)
    number -= (c * base ** 2)
    b = int(number / base)
    number -= (b * base)
    a = number
    return a * 51, b * 51, c * 51, 255


background_block_names.insert(0, 'block')

background_color_values = {color: name for color, name in zip(
    [
        convert_to_color(number) for number in
        range(len(background_block_names))
        ], background_block_names)}

background_offsets = {
    'flag': (2, 0),
    'exit': (2.5, 0),
    'cannon': (0, 2)
}

background = Background(background_maps_raw, background_sprites, background_color_values, background_offsets)

# player sprites processing

player_sprites_raw = sprite_sheet.get_sprites(y_constant=10, x_constant=(10, 7), farthest_y_coordinate=100)

player_sprites = {
    'stagnant': player_sprites_raw[0],
    'dying': get_list(player_sprites_raw, range(1, 7))
}

player = Player(player_sprites, {
    'moving': {'active': False, 'velocity': 5},
    'jumping': {'active': False, 'velocity': -90, 'quadratic': None, 'speed': .5},
    'falling': {'active': False, 'velocity': 180, 'quadratic': None, 'speed': .7},
    'entering': {'active': True},
    'exiting': {'active': False},
    'dying': {'active': False}
})

while True:
    for event in pygame.event.get():
        if event.type == QUIT or (event.type == KEYDOWN and event.key == K_SPACE):
            game.exit()
        elif event.type == KEYDOWN and event.key == K_z:
            if game.speed == 30:
                game.speed = 2
            else:
                game.speed = 30

    if game.condition:
        if game.condition == 'victory':
            background.update_level()
        else:
            player.total_reset()
        game.condition = None

    player.velocity = [0, 0]
    player.on_block = False

    for grid_coordinates in background.find_all_grid_coordinates(
            (player.coordinates[0], player.coordinates[1] + player.dimensions()[1]),
            (player.dimensions()[0], 1)):
        if background.block_type(grid_coordinates) == 'block':
            player.on_block = True

    if player.conditions['entering'] or player.conditions['exiting'] or player.conditions['dying']:
        if player.conditions['entering']:
            if background.blocks[background.entrance].update_sprites(5, False) == 'completed':
                player.conditions['entering'] = False

        elif player.conditions['exiting']:
            if background.blocks[background.exit].update_sprites(5) == 'completed':
                game.condition = 'victory'
                continue

        else:
            if player.update_sprites(3) == 'completed':
                game.condition = 'death'
                continue

    else:
        keys = pygame.key.get_pressed()

        if keys[K_RIGHT] or keys[K_LEFT] or keys[K_d] or [K_a]:
            if not player.conditions['moving']:
                player.conditions['moving'] = True

        if (keys[K_UP] or keys[K_w]) and player.on_block and not (
                    player.conditions['jumping'] or player.conditions['falling']):
            player.conditions['jumping'] = True
            # noinspection PyTypeChecker
            player.conditions_info['jumping']['quadratic'] = Quadratic(1, (0,
                                                                           player.conditions_info['jumping'][
                                                                               'velocity']),
                                                                       player.conditions_info['jumping'][
                                                                           'speed'] * game.speed)

        if not (keys[K_RIGHT] and keys[K_d]) and player.direction == 1 or not (
                    keys[K_LEFT] and keys[K_a]) and player.direction == -1:
            player.direction = 0

        player.process_keys(keys)

        if player.direction == 0:
            player.reset(('moving',))
            player.direction = 1

        if not (player.on_block or player.conditions['falling'] or player.conditions['jumping']):
            player.conditions['falling'] = True
            # noinspection PyTypeChecker
            player.conditions_info['falling']['quadratic'] = Quadratic(1,
                                                                       (0,
                                                                        player.conditions_info['falling'][
                                                                            'velocity']), 21)
            # player.conditions_info['falling'][
            #     'speed'] * game.speed)

        for condition in player.conditions:
            if player.conditions[condition]:
                if condition == 'moving':
                    # noinspection PyTypeChecker
                    player.velocity[0] += player.conditions_info['moving']['velocity'] * player.direction

                if condition == 'jumping':
                    # noinspection PyUnresolvedReferences
                    result = player.conditions_info['jumping']['quadratic'].execute()
                    if type(result) == tuple:
                        player.reset(('jumping',))
                    else:
                        player.velocity[1] += result

                elif condition == 'falling':
                    # noinspection PyUnresolvedReferences
                    result = player.conditions_info['falling']['quadratic'].execute()
                    player.velocity[1] += make_tuple(result)[0]

        if player.velocity != [0, 0]:
            player.all_grid_coordinates = background.find_all_grid_coordinates(
                combine_lists(player.coordinates, player.velocity, '+'),
                player.dimensions())

            for grid_coordinates in player.all_grid_coordinates:
                if background.block_type(grid_coordinates) == 'block':

                    for i in range(2):
                        velocity = [0, 0]
                        velocity[i] = player.velocity[i]
                        if grid_coordinates in background.find_all_grid_coordinates(
                                combine_lists(player.coordinates, velocity, '+'),
                                player.dimensions()):
                            change = polarity(velocity[i])

                            while True:
                                velocity[i] -= change
                                player.all_grid_coordinates = background.find_all_grid_coordinates(
                                    combine_lists(player.coordinates, velocity, '+'),
                                    player.dimensions())
                                # print(player.all_grid_coordinates, combine_lists(player.coordinates, velocity, '+'))

                                if grid_coordinates not in player.all_grid_coordinates:
                                    player.velocity[i] = velocity[i]
                                    if i == 1:
                                        player.reset(('jumping', 'falling'))
                                    break

            for grid_coordinates in player.all_grid_coordinates:
                block_type = background.block_type(grid_coordinates)

                if block_type == 'exit':
                    if collision(
                            combine_lists(player.coordinates, player.velocity, '+'),
                            player.dimensions(),
                            background.blocks[grid_coordinates].coordinates,
                            background.blocks[grid_coordinates].dimensions(),
                            True) is True:
                        player.coordinates = (
                            find_center(
                                background.blocks[grid_coordinates].dimensions(),
                                player.dimensions(),
                                c1=background.blocks[grid_coordinates].coordinates)[0],
                            background.blocks[grid_coordinates].coordinates[1] +
                            background.blocks[grid_coordinates].dimensions()[1] -
                            player.dimensions()[1]
                        )

                        player.conditions['exiting'] = True
                        break

                elif block_type in ('fire', 'lava'):
                    player.conditions['dying'] = True
                    player.current_sprite_type = 'dying'
                    break

                elif block_type == 'flag':
                    player.default_coordinates = background.blocks[grid_coordinates].coordinates

        if not player.conditions['exiting']:
            player.coordinates = combine_lists(player.velocity, player.coordinates, '+')

    for cannon in background.cannons:
        for coordinates in cannon.shot_coordinates:
            coordinates[0] += cannon.shot_velocity[0]
            coordinates[1] += cannon.shot_velocity[1]
            shot_grid_coordinates = background.convert_to_grid(coordinates)

            if shot_grid_coordinates in player.all_grid_coordinates:
                if collision(coordinates, cannon.shot_dimensions, player.coordinates, player.dimensions()) is True:
                    player.conditions['dying'] = True
                    player.current_sprite_type = 'dying'
                    cannon.shot_coordinates.remove(coordinates)
                    break

            elif background.block_type(shot_grid_coordinates) in (
                    'cannon', 'block'):
                cannon.shot_coordinates.remove(coordinates)
                break

        if game.count % cannon.shot_frequency == 0:
            cannon.shot_coordinates.append(list(cannon.shot_initial_coordinates))

    game.display.fill((0, 0, 0, 255))

    for block in background.backgrounds:
        game.display.blit(block.current_sprite(), player.generate_display_coordinates(block.display_coordinates()))

    for coordinates in background.blocks:
        block = background.blocks[coordinates]
        if block.kind not in background.special_block_types:
            game.display.blit(block.current_sprite(),
                              player.generate_display_coordinates(block.display_coordinates()))

            if block.kind == 'cannon':
                for shot_coordinates in block.shot_coordinates:
                    game.display.blit(block.shot_sprite, player.generate_display_coordinates(shot_coordinates))

    if player.conditions['entering'] or player.conditions['exiting']:
        game.display.blit(player.current_sprite(), player.display_coordinates())
        player.display_after = False
    else:
        player.display_after = True

    for coordinates in background.blocks:
        block = background.blocks[coordinates]
        if block.kind in background.special_block_types:
            game.display.blit(block.current_sprite(), player.generate_display_coordinates(block.display_coordinates()))

    if player.display_after:
        game.display.blit(player.current_sprite(), player.display_coordinates())

    pygame.display.update()
    game.clock.tick(game.speed)
    game.count += 1

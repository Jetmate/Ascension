from math import sqrt
# from random import choice

import pygame as pygame
from pygame.locals import *

pygame.init()


def get_list(l, indexes):
    return [l[i] for i in indexes]


def polarity(n):
    if n == 0:
        return n
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

    def get_sprites(self, starting_x_coordinate=0, farthest_y_coordinate=None, all_coordinates=None, y_constant=None,
                    x_constant=None, update=True, scale=True):
        sprites = []
        if not farthest_y_coordinate:
            farthest_y_coordinate = self.farthest_y_coordinate
        if y_constant and x_constant:
            thing = x_constant[1]
        else:
            thing = len(all_coordinates)
        farthest_x_coordinate = starting_x_coordinate

        for i in range(thing):
            coordinates_1 = [0, 0]
            coordinates_1[self.division_index] = farthest_y_coordinate
            coordinates_1[opposite(self.division_index)] = farthest_x_coordinate
            if x_constant:
                farthest_x_coordinate = (i + 1) * x_constant[0] - 1 + starting_x_coordinate
            elif y_constant:
                farthest_x_coordinate = all_coordinates[i]
            else:
                farthest_x_coordinate = all_coordinates[i][opposite(self.division_index)]

            coordinates_2 = [None, None]
            if x_constant or y_constant:
                if x_constant:
                    coordinates_2[opposite(self.division_index)] = farthest_x_coordinate
                else:
                    coordinates_2[opposite(self.division_index)] = all_coordinates[i]
                if y_constant:
                    coordinates_2[self.division_index] = farthest_y_coordinate + y_constant - 1
                else:
                    coordinates_2[self.division_index] = all_coordinates[i]
            else:
                coordinates_2 = all_coordinates[i]

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
        self.a = sign
        if (sign == 1 and y_range[0] > y_range[1]) or (sign == -1 and y_range[1] > y_range[0]):
            x_solution_index = 0
        else:
            x_solution_index = 1
        self.c = y_range[opposite(x_solution_index)]
        self.x_range = [self.get_x(y_range[i])[x_solution_index] for i in range(2)]
        self.x_change = (self.x_range[1] - self.x_range[0]) / (speed * game.speed)
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
        return self.a * x ** 2 + self.c

    def get_x(self, y):
        x = sqrt((-self.c + y) / self.a)
        return sorted((-x, x))


class Game:
    def __init__(self, speed, dimensions, scale_factor, version):
        self.speed = speed
        self.real_speed = self.speed
        self.dimensions = dimensions
        self.scale_factor = scale_factor
        self.version = version
        self.clock = pygame.time.Clock()
        self.display = pygame.display.set_mode(self.dimensions)
        self.movement_keys = (K_RIGHT, K_LEFT, K_d, K_a)
        self.font = pygame.font.SysFont("Calibri", 100)
        self.count = 0

    def blit(self, thing):
        self.display.blit(thing.current_sprite(),
                          player.generate_display_coordinates(thing.coordinates))


class Background:
    def __init__(self, maps, block_sprites, block_color_values, block_offsets, block_info, timer_margins,
                 timer_gap, title_sprite, transition_height, transition_quadratic_speeds, solid_block_types,
                 partial_solid_block_types,
                 switch_pairs):
        self.maps = maps
        self.block_sprites = block_sprites
        self.block_color_values = block_color_values
        self.block_offsets = block_offsets
        for offset_name in self.block_offsets:
            if offset_name not in ('entrance_background', 'exit_background'):
                self.block_offsets[offset_name] = combine_lists(block_offsets[offset_name],
                                                                (game.scale_factor, game.scale_factor), '*')
        self.block_info = block_info
        self.block_size = game.scale_factor * 12
        self.timer_margins = timer_margins
        self.timer_gap = timer_gap
        self.timer_margins[0] -= self.timer_gap

        self.transition_height = transition_height
        self.transition_phase = 1
        self.transition_quadratic = None
        self.transition_quadratic_speeds = transition_quadratic_speeds

        self.title_sprite = title_sprite
        # self.title_coordinates = (
        #     find_center(game.dimensions, self.title_sprite.get_size())[0], self.level_transition_height * 2)

        self.condition = 'title'
        self.solid_block_types = solid_block_types
        self.partial_solid_block_types = partial_solid_block_types
        # self.switch_pairs = switch_pairs
        self.level = 0
        self.block_color = self.block_sprites['block'][0].get_at((0, 0))
        self.background_color = self.block_sprites['background'][0].get_at((0, 0))
        self.directions = ((0, 1), (0, -1), (1, 0), (-1, 0))
        self.number_width = self.block_sprites['number'][0].get_width()

    def block_type(self, grid_coordinates):
        if grid_coordinates in self.blocks:
            return self.blocks[grid_coordinates].kind

    def convert_from_grid(self, grid_coordinates):
        return combine_lists(grid_coordinates, (self.block_size, self.block_size), '*')

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

    def update_level(self):
        self.analyze_map()
        self.player_default_coordinates = [
            find_center(self.blocks[self.entrance].dimensions, player.dimensions,
                        self.blocks[self.entrance].coordinates)[0],
            self.blocks[self.entrance].coordinates[1] +
            self.blocks[self.entrance].dimensions[1] -
            player.dimensions[1]
        ]
        player.default_coordinates = list(self.player_default_coordinates)
        player.total_reset()
        player.update_grid_coordinates()

        player.block = self.blocks[
            self.convert_to_grid((player.coordinates[0], player.coordinates[1] + player.dimensions[1]))]

    def surrounding_blocks(self, initial_coordinates, block_types, blocks, return_coordinates=False):
        result = []
        for direction in self.directions:
            grid_coordinates = tuple(combine_lists(initial_coordinates, direction, '+'))
            if grid_coordinates in blocks and blocks[grid_coordinates] in block_types:
                if return_coordinates:
                    result.append(grid_coordinates)
                else:
                    result.append(direction)
        return result

    def rotate_sprites(self, sprite_type, direction):
        rotation = None
        if direction == (-1, 0):
            rotation = 90
        elif direction == (0, 1):
            rotation = 180
        elif direction == (1, 0):
            rotation = 270

        if rotation:
            sprites = []
            for sprite in self.block_sprites[sprite_type]:
                sprites.append(pygame.transform.rotate(sprite, rotation))

        else:
            sprites = self.block_sprites[sprite_type]
        return sprites

    def add_offset(self, coordinates, block_type, direction):
        offset = self.block_offsets[block_type]
        if direction[0]:
            offset = offset[::-1]
        return tuple(combine_lists(coordinates, offset, '+'))

    @staticmethod
    def exception(exception, coordinates):
        raise Exception(exception + ' at {0}'.format(coordinates))

    def analyze_map(self):
        blocks = {}
        self.level += 1
        self.entrance = None
        self.exit = None
        self.time = 0
        self.count = 0

        for x in range(self.maps[self.level - 1].get_width()):
            for y in range(self.maps[self.level - 1].get_height()):
                color = self.get_color((x, y))

                if color in self.block_color_values:
                    block_type = self.block_color_values[color]
                    if block_type == 'entrance':
                        self.entrance = (x, y)
                    elif block_type == 'exit':
                        self.exit = (x, y)
                    blocks[(x, y)] = block_type

                elif color[3] != 0 and not (color[0] == 0 and color[1] == 0 and color[2] == 0):
                    raise Exception("Unidentified block_color {0} at {1}".format(color, (x, y)))

        if not self.entrance or not self.exit:
            raise Exception("Missing door")

        self.doors = (self.entrance, self.exit)
        self.backgrounds = {}
        active_coordinates = (self.entrance,)

        while active_coordinates:
            all_new_coordinates = []
            for coordinates in active_coordinates:
                for direction in self.directions:
                    new_coordinates = tuple(combine_lists(coordinates, direction, '+'))
                    if new_coordinates not in self.backgrounds and (
                                    new_coordinates not in blocks or blocks[new_coordinates] not in (
                                    'block', 'support_block')):
                        self.backgrounds[new_coordinates] = Block(self.block_sprites['background'],
                                                                  self.convert_from_grid(
                                                                      new_coordinates), 'background')
                        all_new_coordinates.append(new_coordinates)
            active_coordinates = tuple(all_new_coordinates)

        self.blocks = {}
        self.cannons = []
        self.lasers = []
        self.platforms = []
        self.rails = []
        self.gate_heads = []
        processed_rails = []
        gate_switch = None
        gate_head = None

        for initial_coordinates in blocks:
            sprites = None
            block_type = blocks[initial_coordinates]
            coordinates = self.convert_from_grid(initial_coordinates)

            if block_type not in ('entrance', 'exit', 'rail', 'block', 'support_block'):
                direction = self.surrounding_blocks(initial_coordinates, ('support_block',), blocks)
                if not direction:
                    self.exception('Unsupported block', initial_coordinates)
                elif len(direction) > 1:
                    self.exception('Surrounded block', initial_coordinates)

                # directions = self.surrounding_blocks(initial_coordinates, self.solid_block_types, blocks)
                # if not directions:
                #     self.exception('Unsupported block', initial_coordinates)
                #
                # # elif len(directions) == 4:
                #     self.exception('Surrounded block', initial_coordinates)
                #
                # elif len(directions) > 1:
                #     x = []
                #     y = []
                #     for direction in directions:
                #         if direction[0] != 0:
                #             x.append(direction)
                #         else:
                #             y.append(direction)
                #     if len(x) == 1:
                #         direction = x[0]
                #     else:
                #         direction = y[0]
                #
                # else:
                #     direction = directions[0]

                # noinspection PyUnboundLocalVariable
                direction = list(direction[0])
                direction_index = opposite(direction.index(0))
                direction[direction_index] *= -1
                direction = tuple(direction)

                sprites = self.rotate_sprites(block_type, direction)

                if block_type in self.block_offsets:
                    coordinates = self.add_offset(coordinates, block_type, direction)

                if block_type in ('laser', 'cannon', 'gate_head'):
                    if block_type in ('laser', 'gate_head'):
                        entity_sprite = self.rotate_sprites(block_type + '_entity', direction)[0]
                        if block_type == 'laser':
                            block = Weapon(sprites, coordinates, 'laser', entity_sprite, direction, direction_index,
                                           self.block_info['laser']['entity_frequency'])
                            self.lasers.append(block)
                            block.end = None
                            block.active = 1  # choice((0, 1))
                            block.sprite_speed = int(block.entity_frequency / len(block.current_sprites()))
                        else:
                            block = GateHead(sprites, coordinates, 'gate_head', entity_sprite, direction,
                                             direction_index,
                                             self.block_info['gate_head']['speed'])
                            self.gate_heads.append(block)

                    else:
                        block = Cannon(sprites, coordinates, self.block_sprites['cannon_entity'][0], direction,
                                       direction_index,
                                       self.block_info['cannon']['entity_frequency'],
                                       self.block_info['cannon']['entity_speed'])
                        self.cannons.append(block)

                    active_coordinates = list(block.all_grid_coordinates[0])
                    if block_type == 'gate_head':
                        # noinspection PyTypeChecker
                        entity = Thing(block.entity_sprite, self.add_offset(
                            self.convert_from_grid(tuple(active_coordinates)), block_type + '_entity',
                            block.direction))
                        entity.all_grid_coordinates = (tuple(active_coordinates),)
                        block.entities.append(entity)

                    while True:
                        active_coordinates[block.direction_index] += block.direction[block.direction_index]
                        if tuple(active_coordinates) in blocks and blocks[
                            tuple(active_coordinates)
                        ] in self.solid_block_types:
                            if block_type == 'cannon':
                                block.last_coordinates = tuple(active_coordinates)
                            break

                        if block_type in ('laser', 'gate_head'):
                            # noinspection PyTypeChecker
                            entity = Thing(block.entity_sprite, self.add_offset(
                                self.convert_from_grid(tuple(active_coordinates)), block_type + '_entity',
                                block.direction))
                            if block_type == 'laser':
                                entity.all_grid_coordinates = tuple(active_coordinates)
                            else:
                                entity.all_grid_coordinates = (tuple(active_coordinates),)
                                entity.gate_head = block

                            block.entities.append(entity)
                else:
                    block = DirectionBlock(sprites, coordinates, block_type, direction, direction_index)
                if block_type == 'gate_switch':
                    gate_switch = block
                elif block_type == 'gate_head':
                    gate_head = block

            else:
                if block_type == 'rail':
                    directions = self.surrounding_blocks(initial_coordinates, ('rail',), blocks)

                    if len(directions) == 1:
                        block_type = 'end_rail'
                        sprites = self.rotate_sprites('end_rail', directions[0])

                        if initial_coordinates not in processed_rails:
                            current_coordinates = tuple(combine_lists(initial_coordinates, directions[0], '+'))
                            rails = [initial_coordinates, current_coordinates]

                            while current_coordinates:
                                new_coordinates = []
                                surrounding_blocks = self.surrounding_blocks(current_coordinates, ('rail',), blocks,
                                                                             True)
                                for block in surrounding_blocks:
                                    if block not in rails:
                                        rails.append(block)
                                        new_coordinates = block
                                        break
                                current_coordinates = new_coordinates

                            processed_rails.append(rails[-1])
                            self.platforms.append(
                                Platform(self.block_sprites['platform'], rails, self.block_info['platform']['speed']))

                    elif len(directions) == 2:
                        if ((1, 0) in directions and (-1, 0) in directions) or (
                                        (0, 1) in directions and (0, -1) in directions):
                            block_type = 'straight_rail'

                            if (0, 1) in directions:
                                sprites = []
                                for sprite in self.block_sprites['straight_rail']:
                                    sprites.append(pygame.transform.rotate(sprite, 90))
                                    # else:
                                    #     sprites = self.sprites['straight_rail']

                        else:
                            block_type = 'turn_rail'

                            rotation = None
                            if (0, 1) in directions:
                                if (-1, 0) in directions:
                                    rotation = 90
                                else:
                                    rotation = 180
                            elif (1, 0) in directions and (0, -1) in directions:
                                rotation = 270
                            if rotation:
                                sprites = []
                                for sprite in self.block_sprites['turn_rail']:
                                    sprites.append(pygame.transform.rotate(sprite, rotation))
                                    # else:
                                    #     sprites = self.sprites['turn_rail']

                    else:
                        self.exception('Undefined rail', initial_coordinates)

                    self.rails.append(initial_coordinates)

                elif block_type in ('block', 'support_block'):
                    block_type = 'block'
                    sprites = [sprite.copy() for sprite in self.block_sprites['block']]
                    far = self.block_size - game.scale_factor
                    directions = []

                    for direction in self.directions:
                        grid_coordinates = tuple(combine_lists(initial_coordinates, direction, '+'))
                        if (grid_coordinates in blocks and (blocks[
                                                                grid_coordinates] not in background.solid_block_types or
                                                                    blocks[
                                                                        grid_coordinates] in background.partial_solid_block_types)) or (
                                        grid_coordinates not in blocks and grid_coordinates in self.backgrounds):
                            directions.append(direction)

                            rect_coordinates = [0, 0]
                            rect_size = [0, 0]
                            direction_index = opposite(direction.index(0))

                            if direction[direction_index] == 1:
                                rect_coordinates[direction_index] = far

                            rect_size[direction_index] = game.scale_factor
                            rect_size[opposite(direction_index)] = self.block_size

                            for sprite in sprites:
                                pygame.draw.rect(sprite, (0, 0, 0, 255), (rect_coordinates, rect_size))

                    corner_coordinates = []
                    if (-1, 0) in directions:
                        if (0, -1) in directions:
                            corner_coordinates.append((0, 0))
                        if (0, 1) in directions:
                            corner_coordinates.append((0, far))
                    if (1, 0) in directions:
                        if (0, -1) in directions:
                            corner_coordinates.append((far, 0))
                        if (0, 1) in directions:
                            corner_coordinates.append((far, far))

                    for corner in corner_coordinates:
                        for sprite in sprites:
                            pygame.draw.rect(sprite, self.background_color,
                                             (corner, (game.scale_factor, game.scale_factor)))

                if block_type in self.block_offsets:
                    coordinates = self.add_offset(coordinates, block_type, (0, 1))

                if not sprites:
                    sprites = self.block_sprites[block_type]
                block = Block(sprites, coordinates, block_type)

            for grid_coordinates in block.all_grid_coordinates:
                self.blocks[grid_coordinates] = block

            # if initial_coordinates in self.doors:
            #     if block_type == 'entrance':
            #         offset = 'entrance_background'
            #     else:
            #         offset = 'exit_background'
                # block.background_coordinates = combine_lists(self.block_offsets[offset], block.coordinates, '+')

                # for grid_coordinates in self.switch_pairs[self.level - 1]:
                #     self.blocks[grid_coordinates].gate_head = self.blocks[self.switch_pairs[self.level - 1][grid_coordinates]]
        if gate_switch:
            gate_switch.gate_head = gate_head


class Thing:
    def __init__(self, sprites, coordinates=(0, 0)):
        self.sprites = sprites
        self.coordinates = list(coordinates)
        self.reset()
        self.dimensions = self.current_sprite().get_size()

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


class Block(Thing):
    def __init__(self, sprites, coordinates, kind):
        super().__init__(sprites, coordinates=coordinates)
        self.all_grid_coordinates = background.find_all_grid_coordinates(self.coordinates, self.dimensions)
        self.kind = kind
        self.transforming = False


class DirectionBlock(Block):
    def __init__(self, sprites, coordinates, kind, direction, direction_index):
        super().__init__(sprites, coordinates, kind)
        self.direction = direction
        self.direction_index = direction_index


class EntityBlock(DirectionBlock):
    def __init__(self, sprites, coordinates, kind, entity_sprite, direction, direction_index):
        super().__init__(sprites, coordinates, kind, direction, direction_index)
        self.entity_sprite = entity_sprite
        self.direction = direction
        self.direction_index = opposite(self.direction.index(0))
        self.entity_dimensions = self.entity_sprite.get_size()
        self.entities = []


class GateHead(EntityBlock):
    def __init__(self, sprites, coordinates, kind, entity_sprite, direction, direction_index, speed):
        super().__init__(sprites, coordinates, kind, entity_sprite, direction, direction_index)
        self.speed = speed * direction[self.direction_index] * game.scale_factor * -1
        self.retracting = False
        self.final_coordinate = self.coordinates[self.direction_index] - background.block_size * self.direction[
            self.direction_index]

    def retract(self):
        for entity in self.entities:
            entity.coordinates[self.direction_index] += self.speed
            entity.all_grid_coordinates = background.find_all_grid_coordinates(entity.coordinates, entity.dimensions)
            if entity.coordinates[self.direction_index] == self.final_coordinate:
                self.entities.remove(entity)

        if len(self.entities) == 0:
            self.retracting = False


class Weapon(EntityBlock):
    def __init__(self, sprites, coordinates, kind, entity_sprite, direction, direction_index, entity_frequency):
        super().__init__(sprites, coordinates, kind, entity_sprite, direction, direction_index)
        self.entity_frequency = entity_frequency * game.speed


class Cannon(Weapon):
    def __init__(self, sprites, coordinates, entity_sprite, direction, direction_index, entity_frequency,
                 entity_speed):
        super().__init__(sprites, coordinates, 'cannon', entity_sprite, direction, direction_index, entity_frequency)
        if self.direction[self.direction_index] == 1:
            x = self.coordinates[self.direction_index]
        else:
            x = self.coordinates[self.direction_index] + self.dimensions[self.direction_index] - \
                self.entity_dimensions[self.direction_index]

        self.entity_initial_coordinates = find_center(self.dimensions, self.entity_dimensions, self.coordinates)
        self.entity_initial_coordinates[self.direction_index] = x
        self.entity_speed = entity_speed * self.direction[self.direction_index] * game.scale_factor


class Platform(Thing):
    def __init__(self, sprites, rails, speed):
        self.speed = speed * game.scale_factor
        self.rail_coordinates = [background.convert_from_grid(rail) for rail in rails]
        self.current_rail_number = 0
        self.rail_direction = -1
        super().__init__(sprites, coordinates=self.rail_coordinates[self.current_rail_number])

    def move(self):
        if self.coordinates in self.rail_coordinates:
            if self.current_rail_number in (0, len(self.rail_coordinates) - 1):
                self.rail_direction *= -1
            self.current_rail_number += self.rail_direction
            self.direction = [int(polarity(self.rail_coordinates[self.current_rail_number][i] - self.coordinates[i]))
                              for i
                              in range(2)]
            self.direction_index = opposite(self.direction.index(0))

        self.coordinates[self.direction_index] += self.speed * self.direction[self.direction_index]
        self.all_grid_coordinates = background.find_all_grid_coordinates(self.coordinates, self.dimensions)


class Mob(Thing):
    def __init__(self, sprites, conditions_info, coordinates=list((0, 0)),
                 default_sprite_type='stagnant', visible_direction=True, gravity=(0, 1)):
        self.conditions_info = conditions_info
        self.default_coordinates = coordinates
        self.default_sprite_type = default_sprite_type
        self.visible_direction = visible_direction
        self.default_gravity = gravity
        self.current_sprite_type = self.default_sprite_type
        super().__init__(sprites, coordinates)
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
        self.gravity = list(self.default_gravity)
        self.gravity_index = opposite(self.gravity.index(0))
        # self.all_grid_coordinates = background.find_all_grid_coordinates(self.coordinates, self.dimensions)

    def update_grid_coordinates(self, velocity=True):
        if velocity:
            coordinates = combine_lists(self.coordinates, self.velocity, '+')
        else:
            coordinates = self.coordinates
        self.all_grid_coordinates = background.find_all_grid_coordinates(coordinates, self.dimensions)


class Player(Mob):
    def __init__(self, sprites, conditions_info):
        super().__init__(sprites, conditions_info, visible_direction=False)
        self.default_fake_coordinates = find_center(game.dimensions, self.dimensions)
        self.fake_coordinates = list(self.default_fake_coordinates)
        self.gravity_switch = None

    def generate_display_coordinates(self, coordinates):
        return combine_lists(
            combine_lists(coordinates, self.fake_coordinates, '+'),
            self.coordinates, '-')

    def die(self):
        self.current_sprite_type = 'dying'
        background.condition = 'reset'
        if self.gravity_switch:
            self.gravity_switch.sprite_index = 0
        self.gravity_switch = None

    def process_collision(self, thing):
        for i in range(2):
            velocity = [0, 0]
            velocity[i] = self.velocity[i]
            if collision(combine_lists(self.coordinates, velocity, '+'), self.dimensions,
                         thing.coordinates, thing.dimensions) is True:
                player.align_velocity(thing, i)

    def align_velocity(self, thing, i):
        if i == player.gravity_index:
            self.reset(('jumping', 'falling'))
            if (self.gravity[self.gravity_index] == 1 and self.velocity[i] > 0) or (
                            self.gravity[self.gravity_index] == -1 and self.velocity[i] < 0):
                self.block = thing

        if self.velocity[i] > 0:
            self.velocity[i] = thing.coordinates[i] - (
                self.coordinates[i] + self.dimensions[i])
        elif self.velocity[i] < 0:
            self.velocity[i] = (thing.coordinates[i] + thing.dimensions[i]) - \
                               self.coordinates[i]
        else:
            self.velocity = [0, 0]
            self.die()

    def set_gravity(self, thing):
        if self.gravity_switch:
            self.gravity_switch.sprite_index = 0
        self.gravity_switch = thing
        thing.sprite_index = 1
        self.gravity = list(thing.direction)
        self.gravity_index = thing.direction_index
        self.gravity[self.gravity_index] *= -1


game = Game(30, (1200, 900), 3, 12)

# sprite_sheet = SpriteSheet('sprite_sheet_V{0}.png'.format(game.version), 1)
sprite_sheet = SpriteSheet('sprite_sheet_V{0}.png'.format(12.1), 1)
# input

# block_names = (
#     'lava', 'fire', 'block', 'resistent_block', 'background', 'cannon', 'platform', 'straight_rail', 'turn_rail', 'end_rail')
block_names = ('block', 'background')
blocks = sprite_sheet.get_sprites(y_constant=12, x_constant=(12, len(block_names)))
background_sprites = {name: [blocks[block_names.index(name)]]
                      for name in block_names}
player_sprites = sprite_sheet.get_sprites(y_constant=12, x_constant=(12, 1))

# background_sprites['entrance'] = sprite_sheet.get_sprites(y_constant=12, x_constant=(16, 9))
# background_sprites['exit'] = background_sprites['entrance']
# background_sprites['cannon_entity'] = sprite_sheet.get_sprites(starting_x_coordinate=46, update=False,
#                                                                all_coordinates=((49, 13),))

# # misc_object_names = ('cannon_entity', 'laser_entity', 'gate_head_entity')
# # misc_objects = sprite_sheet.get_sprites(starting_x_coordinate=46, update=False,
# #                                         all_coordinates=((49, 13), (59, 13), (69, 15)))
# # misc_object_dict = {name: [misc_objects[misc_object_names.index(name)]]
# #                     for name in misc_object_names}
# # background_sprites.update(misc_object_dict)

background_door_signs = sprite_sheet.get_sprites(y_constant=9, all_coordinates=(29, 45))
background_doors = sprite_sheet.get_sprites(y_constant=12, x_constant=(16, 10))
background_sprites['door_background'] = [background_doors[-1]]
del background_doors[-1]

door_types = ('entrance', 'exit')
door_background_offsets = {}

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
        door_coordinates = (find_center(
            surface_size, door_sprite.get_size())[0], door_sign_sprite.get_height())
        surface.blit(door_sprite, door_coordinates)

        background_sprites.setdefault(door_types[door_sign_index], []).append(surface)

    # noinspection PyUnboundLocalVariable
    door_background_offsets[door_types[door_sign_index]] = door_coordinates

# background_sprites['gate_head'] = sprite_sheet.get_sprites(starting_x_coordinate=24, y_constant=10, x_constant=(10, 2),
#                                                            update=False)

# background_sprites['gravity_switch'] = sprite_sheet.get_sprites(starting_x_coordinate=44, y_constant=10,
#                                                                 x_constant=(10, 2),
#                                                                 update=False)

# background_sprites['laser_entity'] = sprite_sheet.get_sprites(starting_x_coordinate=64, y_constant=10,
#                                                               x_constant=(4, 1),
#                                                               update=False)

# background_sprites['gate_head_entity'] = sprite_sheet.get_sprites(starting_x_coordinate=68, y_constant=10,
#                                                                   x_constant=(6, 1),
#                                                                   update=False)

# background_sprites['flag'] = sprite_sheet.get_sprites(y_constant=10, x_constant=(8, 3))

# background_sprites['laser'] = sprite_sheet.get_sprites(y_constant=10, x_constant=(8, 4))



# player_sprites = sprite_sheet.get_sprites(y_constant=10, x_constant=(10, 8))


background_sprites['number'] = sprite_sheet.get_sprites(y_constant=40, x_constant=(20, 10))
# title_sprite = sprite_sheet.get_sprites(y_constant=52, x_constant=(318, 1))[0]

# background_sprites['gate_switch'] = sprite_sheet.get_sprites(y_constant=10, x_constant=(9, 4))

# background_spritews

# processing

player_sprites = {
    'stagnant': player_sprites[0],
    # 'dying': get_list(player_sprites, range(1, 8))
}

player = Player(player_sprites, {
    'moving': {'active': False, 'velocity': int(1.7 * game.scale_factor)},
    'jumping': {'active': False, 'velocity': 30 * game.scale_factor, 'quadratic': None, 'speed': .5},
    'falling': {'active': False, 'velocity': 60 * game.scale_factor, 'quadratic': None, 'speed': .7},
})

background_map_sheet = SpriteSheet('background_map_sheet_V{0}.png'.format(game.version), 1)
# background_map_sheet = SpriteSheet('Ivan\'s_levels.png', 1)
background_maps = background_map_sheet.get_sprites(y_constant=25, x_constant=(25, 10), scale=False)


def convert_to_color(number, base):
    c = int(number / base ** 2)
    number -= (c * base ** 2)
    b = int(number / base)
    number -= (b * base)
    factor = 255 / (base - 1)
    return number * factor, b * factor, c * factor, 255


background_block_names = (
    'block', 'lava', 'fire', 'flag', 'cannon', 'entrance', 'exit', 'laser', 'rail', 'gate_head', 'gate_switch',
    'gravity_switch', 'support_block'
)

background_color_values = {color: name for color, name in zip(
    [
        convert_to_color(number, 6) for number in
        range(len(background_block_names))
        ], background_block_names)}

background_offsets = {
    'flag': (1, 0),
    'exit': (2, 3),
    'entrance': (0, 3),
    'laser': (1, 0),
    'laser_entity': (3, 0),
    # 'entrance_background': door_background_offsets['entrance'],
    # 'exit_background': door_background_offsets['exit'],
    'gate_head_entity': (2, 0),
    # 'button': (0, 3)
}

background_block_info = {
    'platform': {'speed': 1},
    'cannon': {'entity_speed': 1, 'entity_frequency': 2},
    'laser': {'entity_frequency': 1},
    'gate_head': {'speed': .5}
}

# background_switch_pairs = ({(22, 23): (15, 25), (23, 23): (15, 26), (24, 23): (15, 27)},)
# background_switch_pairs = ({}, {}, {}, {(25, 25): (22, 22)}, {(13, 12): (22, 9)}, {})
background_switch_pairs = None  # ({}, {}, {(40, 24): (25, 26)})
for sprites in background_sprites:
    if type(background_sprites[sprites]) != list:
        raise Exception('Non-list sprite')

title_sprite = None

background = Background(background_maps, background_sprites, background_color_values, background_offsets,
                        background_block_info, [50, 50], 10, title_sprite, game.dimensions[1], (2, 2),
                        ('block', 'cannon', 'gate_head', 'gravity_switch', 'support_block', 'laser'), ('laser',),
                        background_switch_pairs)

background.level = 0
background.condition = None
background.update_level()
background.blocks[background.entrance].sprite_index = len(background.blocks[background.entrance].current_sprites()) - 1
# player.coordinates = background.convert_from_grid((34, 28))

while True:
    for event in pygame.event.get():
        if event.type == QUIT or (event.type == KEYDOWN and event.key == K_SPACE):
            pygame.quit()
            quit()
        elif event.type == KEYDOWN and event.key == K_z:
            if game.real_speed == 30:
                game.real_speed = 1
            else:
                game.real_speed = 30

    if background.level != 0:
        for platform in background.platforms:
            platform.move()

        for gate_head in background.gate_heads:
            if gate_head.retracting:
                gate_head.retract()

    if background.condition:
        if background.condition == 'reset':
            if player.update_sprites(3) == 'completed':
                player.total_reset()
                background.condition = None
                continue

        elif background.condition == 'doors_closing':
            if background.blocks[background.exit].update_sprites(5, False) == 'completed':
                background.transition_quadratic = Quadratic(1, (
                    player.fake_coordinates[1], player.fake_coordinates[1] + background.transition_height),
                                                            background.transition_quadratic_speeds[1])
                player.update_grid_coordinates()
                background.condition = 'transitioning'
                continue

        elif background.condition == 'doors_opening':
            if background.blocks[background.entrance].update_sprites(5, False) == 'completed':
                background.condition = None
                continue

        elif background.condition == 'transitioning':
            result = background.transition_quadratic.execute()

            if type(result) == tuple:
                if background.transition_phase == 1:
                    background.update_level()
                    player.fake_coordinates[1] = player.default_fake_coordinates[1] - background.transition_height
                    background.transition_quadratic = Quadratic(-1, (
                        player.fake_coordinates[1], player.default_fake_coordinates[1]),
                                                                background.transition_quadratic_speeds[0])

                    background.transition_phase = 2

                else:
                    background.condition = 'doors_opening'
                    background.transition_phase = 1
                continue

            else:
                player.fake_coordinates[1] += result

        elif background.condition == 'title':
            if not background.transition_quadratic:
                player.fake_coordinates[1] = player.default_fake_coordinates[1] - background.title_coordinates[1]
                background.transition_quadratic = Quadratic(1, (
                    player.fake_coordinates[1],
                    player.default_fake_coordinates[1] - background.transition_height),
                                                            background.transition_quadratic_speeds[1])

            else:
                pygame.time.wait(2000)
                background.condition = 'transitioning'
                continue

    else:
        background.count += 1
        if background.count % game.speed == 0:
            background.time += 1

        player.velocity = [0, 0]

        if player.block:
            dimensions = list(player.dimensions)
            dimensions[player.gravity_index] = 1

            coordinates_1 = list(player.coordinates)
            if player.gravity[player.gravity_index] == -1:
                coordinates_1[player.gravity_index] -= 1
            else:
                coordinates_1[player.gravity_index] += player.dimensions[player.gravity_index]
            coordinates_2 = list(coordinates_1)
            coordinates_2[player.gravity_index] -= player.gravity[player.gravity_index]
            coordinates = (coordinates_1, coordinates_2)

            if type(player.block) == Platform or (
                            type(player.block) == Thing and player.block.gate_head.retracting):
                velocity = [0, 0]
                if type(player.block) == Thing:
                    velocity[player.block.gate_head.direction_index] = player.block.gate_head.speed * \
                                                                       player.block.gate_head.direction[
                                                                           player.block.gate_head.direction_index] * -1
                else:
                    velocity[player.block.direction_index] = int(player.block.speed * player.block.direction[
                        player.block.direction_index])
                coordinates = [combine_lists(coordinates[i], velocity, '+') for i in range(2)]

            if (
                            collision(coordinates[0], player.dimensions, player.block.coordinates,
                                      player.block.dimensions) is True and
                            collision(coordinates[1], dimensions, player.block.coordinates,
                                      player.block.dimensions) is not True
            ):
                player.reset(('jumping', 'falling'))
                if type(player.block) == Platform or (
                                type(player.block) == Thing and player.block.gate_head.retracting):
                    # noinspection PyUnboundLocalVariable
                    player.velocity = velocity

            else:
                player.block = None

        keys = pygame.key.get_pressed()

        if keys[K_RIGHT] or keys[K_LEFT] or keys[K_d] or [K_a]:
            if not player.conditions['moving']:
                player.conditions['moving'] = True

        if (keys[K_UP] or keys[K_w]) and player.block and not (
                    player.conditions['jumping'] or player.conditions['falling']):
            player.conditions['jumping'] = True
            player.block = None
            # noinspection PyTypeChecker
            player.conditions_info['jumping']['quadratic'] = Quadratic(-1, (0,
                                                                            player.conditions_info['jumping'][
                                                                                'velocity']),
                                                                       player.conditions_info['jumping'][
                                                                           'speed'])

        if not (keys[K_RIGHT] and keys[K_d]) and player.direction == 1 or not (
                    keys[K_LEFT] and keys[K_a]) and player.direction == -1:
            player.direction = 0

        if keys[K_RIGHT] or keys[K_d]:
            player.direction = 1
        elif keys[K_LEFT] or keys[K_a]:
            player.direction = -1

        if player.gravity == [1, 0]:
            player.direction *= -1

        if player.direction == 0:
            player.reset(('moving',))
            player.direction = 1

        if not (player.block or player.conditions['falling'] or player.conditions['jumping']):
            player.conditions['falling'] = True
            # noinspection PyTypeChecker
            player.conditions_info['falling']['quadratic'] = Quadratic(1,
                                                                       (0,
                                                                        player.conditions_info['falling'][
                                                                            'velocity']),
                                                                       player.conditions_info['falling']['speed'])

        for condition in player.conditions:
            if player.conditions[condition]:
                if condition == 'moving':
                    # noinspection PyTypeChecker
                    player.velocity[opposite(player.gravity_index)] += player.conditions_info['moving'][
                                                                           'velocity'] * player.direction

                if condition == 'jumping':
                    # noinspection PyUnresolvedReferences
                    result = player.conditions_info['jumping']['quadratic'].execute()
                    if type(result) == tuple:
                        player.reset(('jumping',))
                    else:
                        player.velocity[player.gravity_index] -= result * player.gravity[player.gravity_index]

                elif condition == 'falling':
                    # noinspection PyUnresolvedReferences
                    result = player.conditions_info['falling']['quadratic'].execute()
                    player.velocity[player.gravity_index] += make_tuple(result)[0] * player.gravity[
                        player.gravity_index]

        for collision_type in ('platform', 'block', 'gate'):
            player.update_grid_coordinates()
            collided_object = None

            if collision_type == 'platform':
                for platform in background.platforms:
                    for grid_coordinates in platform.all_grid_coordinates:
                        if grid_coordinates in player.all_grid_coordinates:
                            if collision(combine_lists(player.coordinates, player.velocity, '+'), player.dimensions,
                                         platform.coordinates, platform.dimensions) is True:
                                if collision(player.coordinates, player.dimensions, platform.coordinates,
                                             platform.dimensions) is True:
                                    player.velocity[platform.direction_index] = 0
                                    player.block = platform
                                    # if platform.direction_index == player.gravity_index:
                                    #     player.reset(('jumping', 'falling'))
                                    if platform.direction[platform.direction_index] == 1:
                                        player.coordinates[platform.direction_index] = platform.coordinates[
                                                                                           platform.direction_index] + \
                                                                                       platform.dimensions[
                                                                                           platform.direction_index]
                                    else:
                                        player.coordinates[platform.direction_index] = platform.coordinates[
                                                                                           platform.direction_index] - \
                                                                                       player.dimensions[
                                                                                           platform.direction_index]

                                else:
                                    collided_object = platform
                                    player.process_collision(collided_object)

            elif collision_type == 'block':
                for grid_coordinates in player.all_grid_coordinates:
                    if background.block_type(grid_coordinates) in background.solid_block_types:
                        collided_object = background.blocks[grid_coordinates]
                        player.process_collision(collided_object)
                        if collided_object.kind == 'gravity_switch' and player.gravity_switch != collided_object:
                            player.set_gravity(collided_object)
                            player.reset(('jumping', 'falling'))

            else:
                for gate_head in background.gate_heads:
                    for entity in gate_head.entities:
                        for grid_coordinates in entity.all_grid_coordinates:
                            if grid_coordinates in player.all_grid_coordinates:
                                if collision(combine_lists(player.coordinates, player.velocity, '+'), player.dimensions,
                                             entity.coordinates,
                                             entity.dimensions) is True:
                                    collided_object = entity
                                    player.process_collision(collided_object)

            if collided_object and player.velocity != [0, 0]:
                if collision(combine_lists(player.coordinates, player.velocity, '+'), player.dimensions,
                             collided_object.coordinates, collided_object.dimensions) is True:
                    for i in range(2):
                        player.align_velocity(collided_object, i)

        player.update_grid_coordinates()

        if not background.condition:
            for grid_coordinates in player.all_grid_coordinates:
                block_type = background.block_type(grid_coordinates)

                if block_type:
                    block = background.blocks[grid_coordinates]

                    if block_type == 'exit' and player.gravity == [0, 1]:
                        if collision(
                                combine_lists(player.coordinates, player.velocity, '+'),
                                player.dimensions,
                                block.coordinates,
                                block.dimensions,
                                True) is True:
                            player.coordinates = (
                                find_center(
                                    block.dimensions,
                                    player.dimensions,
                                    c1=block.coordinates)[0],
                                block.coordinates[1] +
                                block.dimensions[1] -
                                player.dimensions[1]
                            )

                            background.condition = 'doors_closing'
                            break

                    elif block_type in ('fire', 'lava'):
                        player.die()
                        break

                    elif block_type == 'flag' and block.sprite_index == 0:
                        player.default_coordinates = background.convert_from_grid(grid_coordinates)
                        player.default_gravity = player.gravity
                        block.transforming = True

                    elif block_type == 'gate_switch' and block.gate_head.sprite_index == 0:
                        player.default_coordinates = background.convert_from_grid(grid_coordinates)
                        player.default_gravity = player.gravity
                        block.gate_head.retracting = True
                        block.gate_head.sprite_index += 1
                        block.transforming = True

        if background.condition != 'doors_closing':
            player.coordinates = combine_lists(player.velocity, player.coordinates, '+')

    if background.level != 0:
        for cannon in background.cannons:
            for entity in cannon.entities:
                entity.coordinates[cannon.direction_index] += cannon.entity_speed
                all_grid_coordinates = background.find_all_grid_coordinates(entity.coordinates, entity.dimensions)
                collided = False

                if cannon.last_coordinates in all_grid_coordinates:
                    cannon.entities.remove(entity)
                    break

                for grid_coordinates in all_grid_coordinates:
                    if not background.condition:
                        if grid_coordinates in player.all_grid_coordinates:
                            if collision(entity.coordinates, entity.dimensions, player.coordinates,
                                         player.dimensions) is True:
                                player.die()
                                collided = True

                    if not collided:
                        for gate_head in background.gate_heads:
                            for gate in gate_head.entities:
                                if grid_coordinates in gate.all_grid_coordinates:
                                    if collision(entity.coordinates, entity.dimensions,
                                                 gate.coordinates,
                                                 gate.dimensions) is True:
                                        collided = True
                                        break

                    if not collided:
                        for platform in background.platforms:
                            if grid_coordinates in platform.all_grid_coordinates:
                                if collision(entity.coordinates, entity.dimensions, platform.coordinates,
                                             platform.dimensions) is True:
                                    collided = True
                                    break

                    if collided:
                        break

                if collided:
                    cannon.entities.remove(entity)

            if game.count % cannon.entity_frequency == 0:
                cannon.entities.append(Thing(cannon.entity_sprite, list(cannon.entity_initial_coordinates)))

        for laser in background.lasers:
            if game.count % laser.entity_frequency == 0:
                laser.active = opposite(laser.active)
                if laser.active == 0:
                    laser.reset()

            if laser.active:
                laser.end = None
                for entity in laser.entities:
                    if not background.condition:
                        if entity.all_grid_coordinates in player.all_grid_coordinates:
                            if collision(entity.coordinates, entity.dimensions,
                                         player.coordinates,
                                         player.dimensions) is True:
                                player.die()

                    for gate_head in background.gate_heads:
                        for gate in gate_head.entities:
                            if entity.all_grid_coordinates in gate.all_grid_coordinates:
                                if collision(entity.coordinates, entity.dimensions,
                                             gate.coordinates,
                                             gate.dimensions) is True:
                                    laser.end = (entity, gate)
                                    break

                    for platform in background.platforms:
                        if entity.all_grid_coordinates in platform.all_grid_coordinates:
                            if collision(entity.coordinates, entity.dimensions,
                                         platform.coordinates,
                                         platform.dimensions) is True:
                                laser.end = (entity, platform)
                                break
                    if laser.end:
                        break
            else:
                laser.update_sprites(laser.sprite_speed, False)

    game.display.fill(background.block_color)

    if background.level != 0:
        for grid_coordinates in background.backgrounds:
            game.blit(background.backgrounds[grid_coordinates])

        # for grid_coordinates in background.doors:
        #     game.display.blit(background.sprites['door_background'][0],
        #                       player.generate_display_coordinates(
        #                           background.blocks[grid_coordinates].background_coordinates))

        for grid_coordinates in background.rails:
            game.blit(background.blocks[grid_coordinates])

        for gate_head in background.gate_heads:
            for entity in gate_head.entities:
                game.blit(entity)

        for cannon in background.cannons:
            for entity in cannon.entities:
                game.blit(entity)
            game.blit(cannon)

        for laser in background.lasers:
            if laser.active:
                for entity in laser.entities:
                    if laser.end and entity == laser.end[0]:
                        area_dimensions = [0, 0]
                        area_dimensions[opposite(laser.direction_index)] = laser.end[0].dimensions[
                            opposite(laser.direction_index)]
                        blit_coordinates = list(laser.end[0].coordinates)

                        if laser.direction[laser.direction_index] == 1:
                            area_dimensions[laser.direction_index] = laser.end[1].coordinates[
                                                                         laser.direction_index] - \
                                                                     laser.end[0].coordinates[laser.direction_index]
                        else:
                            blit_coordinates[laser.direction_index] = laser.end[1].coordinates[
                                                                          laser.direction_index] + \
                                                                      laser.end[1].dimensions[laser.direction_index]
                            area_dimensions[laser.direction_index] = laser.end[0].coordinates[
                                                                         laser.direction_index] - (
                                                                         laser.end[1].coordinates[
                                                                             laser.direction_index] +
                                                                         laser.end[1].dimensions[
                                                                             laser.direction_index])

                        game.display.blit(laser.entity_sprite,
                                          player.generate_display_coordinates(blit_coordinates),
                                          ((0, 0), area_dimensions))
                        break

                    else:
                        game.blit(entity)

        for grid_coordinates in background.blocks:
            if grid_coordinates not in background.doors and grid_coordinates not in background.rails and \
                    background.blocks[grid_coordinates].kind:
                block = background.blocks[grid_coordinates]
                if block.kind != 'cannon':
                    if block.transforming:
                        if block.update_sprites(5, reset=False):
                            block.transforming = False
                    game.blit(block)

        if background.condition in ('doors_closing', 'doors_opening', 'transitioning'):
            game.display.blit(player.current_sprite(), player.fake_coordinates)
            player.display_after = False
        else:
            player.display_after = True

        for grid_coordinates in background.doors:
            game.blit(background.blocks[grid_coordinates])

        for platform in background.platforms:
            game.blit(platform)

        if player.display_after:
            game.display.blit(player.current_sprite(), player.fake_coordinates)

        time = str(background.time)
        for number, i in zip(time, reversed(range(len(time)))):
            game.display.blit(background.block_sprites['number'][int(number)],
                              (game.dimensions[0] - (i + 1) * (background.number_width + background.timer_gap) -
                               background.timer_margins[0], background.timer_margins[1]))

    else:
        game.display.blit(background.title_sprite, (
            background.title_coordinates[0],
            background.title_coordinates[1] + player.fake_coordinates[1]
        ))

    pygame.display.update()
    game.clock.tick(game.real_speed)
    game.count += 1

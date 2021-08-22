import pygame
import random
pygame.init()


class XY:
    def __init__(self, x: float, y: float, parent=None):
        # Only game_objs 4 corners have parents, not used for centers
        self.x = x
        self.y = y
        self.parent = parent


class AABB:
    def __init__(self, center: XY, half_w: float, half_h: float, is_game_obj=False):
        self.__center = center
        self.half_w = half_w
        self.half_h = half_h
        self.__set_sides()
        self.points = ()
        if is_game_obj:
            self.points = self.__get_points()

    @property
    def center(self):
        return self.__center

    @center.setter
    def center(self, new_center):
        self.__center = new_center
        self.__set_sides()

    def contains_point(self, p: XY) -> bool:
        return (
            (p.x >= self.left_side) and
            (p.x <= self.right_side) and
            (p.y >= self.top_side) and
            (p.y <= self.bottom_side)
        )

    def intersects_AABB(self, other) -> bool:
        return (
            (self.left_side < other.right_side) and
            (self.right_side > other.left_side) and
            (self.top_side < other.bottom_side) and
            (self.bottom_side > other.top_side)
        )

    def to_rect(self) -> pygame.Rect:
        return pygame.Rect(
            int(self.left_side),
            int(self.top_side),
            int(self.half_w * 2),
            int(self.half_h * 2)
        )

    def __get_points(self) -> tuple:
        tl = XY(self.left_side, self.top_side, self)
        bl = XY(self.left_side, self.bottom_side, self)
        tr = XY(self.right_side, self.top_side, self)
        br = XY(self.right_side, self.bottom_side, self)
        return tl, bl, tr, br

    def __set_sides(self) -> None:
        self.left_side = self.__center.x - self.half_w
        self.right_side = self.__center.x + self.half_w
        self.top_side = self.__center.y - self.half_h
        self.bottom_side = self.__center.y + self.half_h


class QuadTree:
    QT_NODE_CAPACITY = 2

    def __init__(self, boundary: AABB):
        self.boundary = boundary
        self.points = []
        self.north_west = None
        self.north_east = None
        self.south_west = None
        self.south_east = None

    def insert(self, p: XY) -> bool:
        if not self.boundary.contains_point(p) or not self.boundary.intersects_AABB(p.parent):
            return False

        if len(self.points) < QuadTree.QT_NODE_CAPACITY and self.north_west is None:
            self.points.append(p)
            return True

        if self.north_west is None:
            self.subdivide()

        if self.north_west.insert(p):
            return True
        if self.north_east.insert(p):
            return True
        if self.south_west.insert(p):
            return True
        if self.south_east.insert(p):
            return True

        return False

    def subdivide(self) -> None:
        half_w = self.boundary.half_w / 2
        half_h = self.boundary.half_h / 2
        self.north_west = QuadTree(
            AABB(XY(self.boundary.center.x - half_w, self.boundary.center.y - half_h), half_w, half_h)
        )
        self.north_east = QuadTree(
            AABB(XY(self.boundary.center.x + half_w, self.boundary.center.y - half_h), half_w, half_h)
        )
        self.south_west = QuadTree(
            AABB(XY(self.boundary.center.x - half_w, self.boundary.center.y + half_h), half_w, half_h)
        )
        self.south_east = QuadTree(
            AABB(XY(self.boundary.center.x + half_w, self.boundary.center.y + half_h), half_w, half_h)
        )

    def query_range(self, range_: AABB) -> list:
        points_in_range = []
        if not self.boundary.intersects_AABB(range_):
            return points_in_range

        for p in self.points:
            if range_.contains_point(p) or range_.intersects_AABB(p.parent):
                points_in_range.append(p)

        if self.north_west is None:
            return points_in_range

        points_in_range.extend(self.north_west.query_range(range_))
        points_in_range.extend(self.north_east.query_range(range_))
        points_in_range.extend(self.south_west.query_range(range_))
        points_in_range.extend(self.south_east.query_range(range_))

        return points_in_range

    def clear(self) -> None:
        self.points.clear()

        if self.north_west is not None:
            self.north_west.clear()
            self.north_west = None

        if self.north_east is not None:
            self.north_east.clear()
            self.north_east = None

        if self.south_west is not None:
            self.south_west.clear()
            self.south_west = None

        if self.south_east is not None:
            self.south_east.clear()
            self.south_east = None


def draw_tree_rects(t):
    pygame.draw.rect(display, (255, 0, 0), t.boundary.to_rect(), 1)
    if t.north_west is not None:
        draw_tree_rects(t.north_west)

    if t.north_east is not None:
        draw_tree_rects(t.north_east)

    if t.south_west is not None:
        draw_tree_rects(t.south_west)

    if t.south_east is not None:
        draw_tree_rects(t.south_east)


def make_objs():
    return [
        AABB(XY(random.randint(0, WINDOW_WIDTH), random.randint(0, WINDOW_HEIGHT)), random.randint(2, 100), random.randint(2, 100), True)
        for i in range(100)
    ]


WINDOW_WIDTH = 1920
WINDOW_HEIGHT = 1080

display = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.FULLSCREEN | pygame.SRCALPHA)
clock = pygame.time.Clock()
f = pygame.font.SysFont("Courier", 12, True)

quad = QuadTree(AABB(XY(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2), WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2))

game_objs = make_objs()

player_area = AABB(XY(500, 500), 75, 75)
player_area_surface = pygame.Surface((player_area.half_w * 2, player_area.half_h * 2))
player_area_surface.set_alpha(50)
player_area_surface.fill((0, 0, 255))

draw_tree_rects(quad)

show_objs = True
draw_tree = True
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

            elif event.key == pygame.K_SPACE:
                game_objs = make_objs()

            elif event.key == pygame.K_e:
                show_objs = not show_objs

            elif event.key == pygame.K_f:
                draw_tree = not draw_tree

    player_area.center = XY(*pygame.mouse.get_pos())

    display.fill((0, 0, 0))

    quad.clear()
    for o in game_objs:
        for p in o.points:
            quad.insert(p)

    if draw_tree:
        draw_tree_rects(quad)

    if show_objs:
        for i in game_objs:
            pygame.draw.rect(display, (255, 255, 255), i.to_rect())
    else:
        for i in game_objs:
            for j in i.points:
                pygame.draw.rect(display, (255, 255, 255), (int(j.x), int(j.y), 1, 1))

    in_range = quad.query_range(player_area)
    draw_rect = set()
    for i in in_range:
        if i.parent not in draw_rect:
            draw_rect.add(i.parent)
            pygame.draw.rect(display, (255, 255, 255) if i not in in_range else (0, 255, 0), i.parent.to_rect())

    display.blit(player_area_surface, player_area.to_rect())

    pygame.display.update()
    clock.tick(60)

pygame.quit()

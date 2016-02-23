import pygame
import numpy as np
from math import radians
from pygame.color import THECOLORS
import cv2
import pymunk
from pymunk.pygame_util import from_pygame

WEBCAM = '/dev/video0'

def to_pygame(p):
    """Small hack to convert pymunk to pygame coordinates"""
    return int(p.x), int(-p.y+600)

def from_pygame(x, y):
    return int(x), int(600-y)


class Webcam:
    def __init__(self, uri=WEBCAM):
        self.uri = uri
        self.capture = cv2.VideoCapture(0)

    @property
    def frames(self):
        while True:
            print('frame')
            ret, frame = self.capture.read()
            gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            edges = cv2.Canny(gray, 60, 300)
            lines = cv2.HoughLinesP(edges, 4, radians(40), 22)
            if lines is not None:
                print(len(lines))
                for l in lines[0]:
                    x, y, x2, y2 = l
                    cv2.line(frame, (x, y), (x2, y2), (255, 0, 0), 5)
            yield frame, edges, lines[0] if lines is not None else []


class Simulation:
    def __init__(self):
        self.space = pymunk.Space()
        self.space.gravity = 0, -1000
        self.objects = list()
        b_body, b_shape = self.create_ball(200, 400)
        self.space.add(b_body, b_shape)
        self.ball = b_shape

        self.static_body = pymunk.Body()
        self.lines = []

    def step(self):
        self.space.step(0.02)

    def create_ball(self, x, y, mass=40, radius=7):
        inertia = pymunk.moment_for_circle(mass, 0, radius, (0, 0))
        body = pymunk.Body(mass, inertia)
        body.position = x, y
        shape = pymunk.Circle(body, radius, (0, 0))
        shape.elasticity = 0.95
        return body, shape

    def draw(self, screen):
        p = to_pygame(self.ball.body.position)
        radius = self.ball.radius
        pygame.draw.circle(screen, THECOLORS["blue"], p, int(radius), 2)


    def remove_walls(self):
        self.space.remove(self.lines)
        self.lines = []

    def set_walls(self, lines):
        self.lines = [pymunk.Segment(self.static_body, from_pygame(x, y), from_pygame(x2, y2), 0)
                      for x, y, x2, y2 in lines]
        self.space.add(self.lines)


pygame.init()
screen = pygame.display.set_mode((600, 600))
clock = pygame.time.Clock()
running = True


def main():
    w = Webcam()
    s = Simulation()
    cv2.startWindowThread()
    cv2.namedWindow('Video')
    while running:
        screen.fill((0, 0, 0), (0, 0, 600, 600))
        frame, edges, lines = next(w.frames)
        cv2.imshow('Video', frame)
        s.set_walls(lines)
        s.draw(screen)
        s.step()
        print(s.ball.body.position)
        clock.tick(50)
        for line in s.lines:
            body = line.body
            pv1 = body.position + line.a.rotated(body.angle)
            pv2 = body.position + line.b.rotated(body.angle)
            p1 = to_pygame(pv1)
            p2 = to_pygame(pv2)
            pygame.draw.lines(screen, THECOLORS["lightgray"], False, [p1,p2])
        pygame.display.update()


if __name__ == "__main__":
    main()


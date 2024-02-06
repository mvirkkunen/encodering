#!/usr/bin/python

import itertools
import math
import os
import subprocess
import sys

root = os.path.dirname(__file__)
sys.path.append(os.path.join(root, ".."))

import kigen.pcb as pcb, kigen.footprint as fp
from kigen.common import Vec2, Pos2, Layer

outer_diam = 24
hole_diam = 7
ring_r = 10
led_count = 30
trace_width = 0.2
#led_pad_dist = 0.787 * 2

pins = int(math.ceil((1 + math.sqrt(1 + 4 * led_count)) / 2))
print("Pins: ", pins)

ring_spacing = 0.8
ring0_r = hole_diam/2 + 1

a_step = 360 / led_count

# Load LED footprint to use

led = fp.FootprintLibrary("/usr/share/kicad/footprints/LED_SMD.pretty").load("LED_0805_2012Metric")
led_pad_dist = (led.get_pad("1").position - led.get_pad("2").position).length()

# Create ring footprint with connections

ring_fp = fp.LibraryFootprint("Led_ring", "led_ring", layer=Layer.FCu, descr="Generated LED ring connections")

def via(at):
    return fp.Pad(
        number="",
        type=fp.PadType.ThruHole,
        shape=fp.PadShape.Circle,
        at=at,
        size=0.8,
        drill=0.4,
        layers=Layer.AllCu,
    )

for i in range(led_count):
    angle = (360 / led_count) * i
    next_angle = (360 / led_count) * (i + 1)

    seg = fp.Rotate(angle)
    ring_fp.append(seg)

    #ring_fp.place(
    #    led,
    #    layer=pcb.Layer.FCu,
    #    at=ring_r,
    #    parent=seg,
    #)

    # LED assembly mark

    seg.append(
        fp.Polygon.rect(
            start=[ring_r - led_pad_dist * 0.5, -0.4],
            end=[ring_r + led_pad_dist * 0.5, 0.4],
            width=0.1,
            layer=Layer.FFab,
            fill=fp.FillMode.None_))

    x = ring_r + (i % 2 - 0.4) * led_pad_dist
    seg.append(fp.Line(start=[x, -0.4], end=[x, 0.4], width=0.1, layer=Layer.FFab))

    # Pairwise connection trace

    if i % 2 == 0:
        ring_fp.append(fp.Arc(center=[0, 0], radius=ring_r - led_pad_dist * 0.5, start_angle=angle, end_angle=next_angle, width=trace_width, layer=Layer.FCu))

# Inner connections


hookup_wires = []

if True:
    combs = list(itertools.combinations(range(pins), 2))
    print(combs)
    i = 0
    r = 0
    for key, group in itertools.groupby(combs, lambda x: x[0]):
        group = list(group)

        start_angle = (360 / led_count) * i
        angle = (360 / led_count) * (len(group) * 2 - 1)
        i += (len(group) * 2)

        print(start_angle, angle, len(group))

        # Outer segment connection rings
        ring_fp.append(fp.Arc(center=[0, 0], radius=ring_r + led_pad_dist * 0.5, start_angle=start_angle, end_angle=start_angle + angle, width=trace_width, layer="F.Cu"))

        if len(group) > 1:
            # Inner to outer segment connections
            start_angle += (360 / led_count) * 1.5
            start = Vec2(ring_r, 0).rotate(start_angle)
            end = Vec2(ring_r, 0).rotate(start_angle + angle - a_step)

            # Arc segment
            ring_fp.append(fp.Arc(center=[0, 0], radius=ring_r, start_angle=start_angle, end_angle=start_angle + angle - a_step, width=trace_width, layer="F.Cu"))

            p1 = Vec2(ring_r - led_pad_dist * 0.5, 0).rotate(start_angle - a_step / 2)
            p2 = Vec2(ring_r + led_pad_dist * 0.5, 0).rotate(start_angle + angle - a_step / 2)

            ring_fp.append(fp.Line(start=p1, end=start, width=trace_width, layer="F.Cu"))
            ring_fp.append(fp.Line(start=p2, end=end, width=trace_width, layer="F.Cu"))

        #start = Rotation(start_angle + angle + 360 / led_count).getRealPosition([hole_diam / 2 + 1 + r, 0])[0]
        #fp.append(Arc(center=[0, 0], start=start, angle=angle - 360 + 2 * 360 / led_count, width=trace_width, layer="B.Cu"))

    ranges = [[led_count // 2, 0] for _ in range(pins - 1)]

    for i, (_, b) in enumerate(combs):
        angle = (360 / led_count) * (i * 2 + 0.5)

        ranges[b - 1][0] = min(ranges[b - 1][0], i)
        ranges[b - 1][1] = max(ranges[b - 1][1], i)

        rot = fp.Rotate(angle)
        ring_fp.append(rot)
        start = [ring0_r + (b - 1) * ring_spacing, 0]
        end = [ring_r - led_pad_dist * 0.5, 0]
        rot.append(via(start))

        rot.append(fp.Line(start=start, end=end, width=trace_width, layer="F.Cu"))

    for i, (si, ei) in enumerate(ranges):
        start_angle = (360 / led_count) * (si * 2 + 0.5)
        angle = (360 / led_count) * (ei - si) * 2

        print(start_angle, angle, len(group))

        #start = fp.Rotate(start_angle).getRealPosition([ring0_r + i * ring_spacing, 0])[0]
        ring_fp.append(fp.Arc(center=[0, 0], radius=ring0_r + i * ring_spacing, start_angle=start_angle, end_angle=start_angle + angle, width=trace_width, layer=Layer.BCu))

        hookup_wires.append(start)

if False:
    via_pos = pcb.Rotation(a_step / 2).getRealPosition([ring_r, 0])[0]
    p0 = pcb.Rotation(a_step / 2).getRealPosition([ring_r + led_pad_dist * 0.5, 0])[0]

    ring_fp.append(pcb.Line(start=p0, end=via_pos, width=trace_width, layer="F.Cu"))
    ring_fp.append(via(via_pos))
    hookup_wires.insert(0, via_pos)

    for i, start in enumerate(hookup_wires):
        start = pcb.Vec2(start)
        end = pcb.Vec2(outer_diam/2 - i * 1.27 - 1.27, -outer_diam / 2)

        diag = pcb.Line(start=start, end=start+Vector2D(outer_diam, -outer_diam))

        down = pcb.Line(start=end, end=end+Vector2D(0, -outer_diam))
        corner = BaseNodeIntersection.intersectTwoLines(diag, down)[0]
        if corner.y < end.y:
            left = Line(start=end, end=end+Vector2D(-outer_diam, 0))
            corner = BaseNodeIntersection.intersectTwoLines(diag, left)[0]

        #fp.append(diag)

        ring_fp.append(pcb.Line(start=start, end=corner, width=trace_width, layer="B.Cu"))
        ring_fp.append(pcb.Line(start=corner, end=end, width=trace_width, layer="B.Cu"))
        ring_fp.append(Pad(
            type=Pad.TYPE_THT,
            shape=Pad.SHAPE_CIRCLE,
            at=end,
            size=1,
            drill=0.65,
            layers=Pad.LAYERS_THT,
        ))

# Center hole
ring_fp.append(fp.Circle(center=[0, 0], radius=hole_diam / 2, layer=Layer.EdgeCuts, width=0.1))

# Outer diam
ring_fp.append(fp.Circle(center=[0, 0], radius=outer_diam / 2, layer=Layer.EdgeCuts, width=0.1))

# Alignment hole TODO: anti rotate the thing
rot = fp.Rotate(0)
ring_fp.append(rot)

rot.append(fp.Polygon.rect(start=[6.2, -1.1], end=[7.2, 1.1], layer=Layer.EdgeCuts, width=0.1, fill=fp.FillMode.None_))
rot.append(fp.Polygon.rect(start=[-15/2, -12/2], end=[15/2, 12/2], layer=Layer.FFab, width=0.1, fill=fp.FillMode.None_))

ring_fp.save(os.path.join(root, "project", "Generated.pretty", "Led_ring.kicad_mod"))

subprocess.check_call(
    ["kicad-cli", "fp", "export", "svg", "-t", "Kicad Default", os.path.join(root, "project", "Generated.pretty")]
)

os.system("display -density 1000 Led_ring.svg")
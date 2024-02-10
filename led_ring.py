#!/usr/bin/python

from itertools import combinations, groupby, islice
import math
import pathlib
import sys
from collections import namedtuple

def pairs(iterable):
    it = iter(iterable)
    while batch := tuple(islice(it, 2)):
        yield batch

root = pathlib.Path(__file__).resolve().parent
sys.path.append(str(root / "kigen"))

import kigen.pcb as pcb, kigen.footprint as fp, kigen.symbol as sym
from kigen.common import Vec2, Pos2, Layer

outer_diam = 24
hole_diam = 7
ring_r = 10
led_count = 30
track_width = 0.2

# led_count = pins * (pins - 1) <=> pins = 1 + sqrt(1 + 4 * led_count) / 2
pins = int(math.ceil((1 + math.sqrt(1 + 4 * led_count)) / 2))

ring_spacing = 0.8
ring0_r = hole_diam * 0.5 + 1

# Load LED symbol and footprint to use

led_sym = sym.SymbolLibrary.load("/usr/share/kicad/symbols/LED.kicad_sym").get("LED")

led_fp = fp.FootprintLibrary("/usr/share/kicad/footprints/LED_SMD.pretty").load("LED_0603_1608Metric")
for t in led_fp.find_all(fp.Text):
    t.hide = True

def generate_led_pcb():
    #ring_pcb = fp.LibraryFootprint("Led_ring", "led_ring", layer=Layer.FCu, descr="Generated LED ring connections")
    angle_step = 360 / led_count
    led_pad_dist = (led_fp.get_pad("1").position - led_fp.get_pad("2").position).length()

    led_pcb = pcb.PcbFile()

    nets = [led_pcb.add_net(f"PIN{i+1}") for i in range(pins)]

    LedInfo = namedtuple("LedInfo", ["index", "outer_net", "inner_net", "angle", "center"])
    leds = [
        LedInfo(i, nets[p[0]], nets[p[1]], i * angle_step, Pos2(ring_r, 0).rotate(i * angle_step))
        for i, p
        in enumerate(p for c in list(combinations(range(pins), 2))[:led_count] for p in (c, c))
    ]

    origin = pcb.Transform((50.8, 50.8), parent=led_pcb)

    for led in leds:
        rotate = bool(led.index % 2)

        # LED footprint
        led_instance = led_pcb.place(
            footprint=led_fp,
            layer=Layer.FCu,
            at=Pos2(ring_r, 0).rotate(led.angle).add_rotation(180 if rotate else 0),
            parent=origin,
        )

        led_instance.get_pad("1").net = led.outer_net if rotate else led.inner_net
        led_instance.get_pad("2").net = led.inner_net if rotate else led.outer_net

    for (led, next_led) in pairs(leds):
        # Inner LED pair connection
        origin.append(pcb.TrackArc(
            center=[0, 0],
            radius=ring_r - led_pad_dist * 0.5,
            start_angle=led.angle,
            end_angle=next_led.angle,
            width=track_width,
            layer=Layer.FCu,
            net=led.outer_net,
        ))

    hookup_wires = []

    #i = 0
    for _, group in groupby(pairs(leds), lambda l: l[0].outer_net):
        group = list(group)
        first_led = group[0][0]
        last_led = group[-1][1]

        start_angle = first_led.angle
        end_angle = last_led.angle

        # Outer LED segment connection
        origin.append(pcb.TrackArc(
            center=[0, 0],
            radius=ring_r + led_pad_dist * 0.5,
            start_angle=start_angle,
            end_angle=end_angle,
            width=track_width,
            layer=Layer.FCu,
            net=first_led.outer_net,
        ))

        if len(group) > 1:
            # Inner to outer segment connection
            inner_pad = Vec2(ring_r - led_pad_dist * 0.5, 0).rotate(start_angle + angle_step)
            outer_pad = Vec2(ring_r + led_pad_dist * 0.5, 0).rotate(end_angle + angle_step)

            # Arc between LEDs
            arc = origin.append(pcb.TrackArc(
                center=[0, 0],
                radius=ring_r,
                start_angle=start_angle + angle_step * 1.5,
                end_angle=end_angle + angle_step * 0.5,
                width=track_width,
                layer=Layer.FCu,
                net=first_led.inner_net,
            ))

            # Inner connecting segment
            origin.append(pcb.TrackSegment(start=inner_pad, end=arc.start, width=track_width, layer=Layer.FCu, net=first_led.inner_net))

            # Outer connecting segment
            origin.append(pcb.TrackSegment(start=arc.end, end=outer_pad, width=track_width, layer=Layer.FCu, net=first_led.inner_net))

        #start = Rotation(start_angle + angle + 360 / led_count).getRealPosition([hole_diam / 2 + 1 + r, 0])[0]
        #fp.append(Arc(center=[0, 0], start=start, angle=angle - 360 + 2 * 360 / led_count, width=trace_width, layer="B.Cu"))

    for net in nets:
        net_leds = [l for l in leds if l.inner_net == net]
        if len(net_leds) > 2:
            # Inner net connection arc
            origin.append(pcb.TrackArc(
                center=[0, 0],
                radius=ring0_r + (int(net) - 3) * ring_spacing,
                start_angle=net_leds[0].angle,
                end_angle=net_leds[-1].angle - angle_step,
                width=track_width,
                layer=Layer.BCu,
                net=net,
            ))

    for (led, _) in pairs(leds):
        via_at = Vec2(ring0_r + (int(net) - 3) * ring_spacing, 0).rotate(led.angle)

        # Inner net connection arc to inner net pairwise track
        origin.append(pcb.TrackSegment(
            start=via_at,
            end=Vec2(ring_r - led_pad_dist * 0.5, 0).rotate(led.angle),
            width=track_width,
            layer=Layer.FCu,
            net=led.inner_net,
        ))

        # Via to connect inner net connection arc and above track
        origin.append(pcb.TrackVia(
            at=via_at,
            size=0.8,
            drill=0.4,
            net=led.inner_net,
        ))

    if False:

        ranges = [[led_count // 2, 0] for _ in range(pins - 1)]

        for i, (_, b) in enumerate(combs):
            angle = (360 / led_count) * (i * 2 + 0.5)

            ranges[b - 1][0] = min(ranges[b - 1][0], i)
            ranges[b - 1][1] = max(ranges[b - 1][1], i)

            rot = fp.Rotate(angle)
            origin.append(rot)
            start = [ring0_r + (b - 1) * ring_spacing, 0]
            end = [ring_r - led_pad_dist * 0.5, 0]
            rot.append(via(start))

            rot.append(fp.Line(start=start, end=end, width=track_width, layer="F.Cu"))

        for i, (si, ei) in enumerate(ranges):
            start_angle = (360 / led_count) * (si * 2 + 0.5)
            angle = (360 / led_count) * (ei - si) * 2

            #print(start_angle, angle, len(group))

            #start = fp.Rotate(start_angle).getRealPosition([ring0_r + i * ring_spacing, 0])[0]
            origin.append(fp.Arc(center=[0, 0], radius=ring0_r + i * ring_spacing, start_angle=start_angle, end_angle=start_angle + angle, width=track_width, layer=Layer.BCu))

            hookup_wires.append(start)

    # Center hole
    origin.append(pcb.Circle(center=[0, 0], radius=hole_diam / 2, layer=Layer.EdgeCuts, width=0.1))

    # PCB edge
    origin.append(pcb.Circle(center=[0, 0], radius=outer_diam / 2, layer=Layer.EdgeCuts, width=0.1))

    led_pcb.save(root / "build" / "led_pcb.kicad_pcb")

    return origin

def _generate_led_pcb(ring_fp: fp.LibraryFootprint):
    led_pcb = pcb.PcbFile()
    origin = pcb.Transform((50.8, 50.8), parent=led_pcb)

    led_pcb.place(
        footprint=ring_fp,
        layer=Layer.FCu,
        at=Vec2(0, 0),
        parent=origin,
    )

    for i in range(led_count):
        led = led_pcb.place(
            footprint=led_fp,
            layer=Layer.FCu,
            at=Pos2(ring_r, 0).rotate(angle_step * i),
            parent=origin,
        )

        led.get_pad("1").net = pcb.Net()

    # Center hole
    origin.append(pcb.Circle(center=[0, 0], radius=hole_diam / 2, layer=Layer.EdgeCuts, width=0.1))

    # Outer diam
    origin.append(pcb.Circle(center=[0, 0], radius=outer_diam / 2, layer=Layer.EdgeCuts, width=0.1))

    led_pcb.save(root / "build" / "led_pcb.kicad_pcb")

#ring_fp = generate_ring_fp()
generate_led_pcb()

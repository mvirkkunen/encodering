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
led_colors = 1 # only 1 or 2
track_width = 0.2

# led_count = pins * (pins - 1) <=> pins = 1 + sqrt(1 + 4 * led_count) / 2
pin_count = int(math.ceil((1 + math.sqrt(1 + 4 * led_count * led_colors)) / 2))

ring_spacing = 0.8
ring0_r = hole_diam * 0.5 + 1

# Load LED symbol and footprint to use

led_sym = sym.SymbolLibrary.load("/usr/share/kicad/symbols/LED.kicad_sym").get("LED")

#led_fp = fp.FootprintLibrary("/usr/share/kicad/footprints/LED_SMD.pretty").load("LED_0603_1608Metric")
#for t in led_fp.find_all(fp.Text):
#    t.hide = True
led_fp = fp.FootprintLibrary("Project.pretty").load("LED_0603_1608Metric")

pin_model = "${KICAD6_3DMODEL_DIR}/Connector_Pin.3dshapes/Pin_D1.0mm_L10.0mm.wrl"

def generate_led_pcb():
    #ring_pcb = fp.LibraryFootprint("Led_ring", "led_ring", layer=Layer.FCu, descr="Generated LED ring connections")
    angle_step = 360 / led_count
    led_pad_dist = (led_fp.get_pad("1").position - led_fp.get_pad("2").position).length()
    chamfer_angle = ((180 / math.pi) / ring_r) * led_pad_dist * 0.5
    rotation = 3 * angle_step + (90 - (pin_count * angle_step))

    mounting_pad_fp = fp.LibraryFootprint("Project.pretty", "Mounting_Pad", layer=Layer.FCu)
    mounting_pad_fp.append(fp.Pad(
        "1",
        type=fp.PadType.Smd,
        shape=fp.PadShape.RoundRect,
        at=Vec2(0, 0),
        size=Vec2(3.0, 1.6),
        drill=fp.DrillDefinition(offset=Vec2(-1, 0)),
        layers=[Layer.FCu, Layer.FMask],
        roundrect_rratio=0.25,
    ))
    mounting_pad_fp.save(root / "Project.pretty" / "Mounting_Pad.kicad_mod")

    led_pcb = pcb.PcbFile()

    nets = [led_pcb.add_net(f"PIN{i+1}") for i in range(pin_count)]

    # Generate LED net and angle information
    LedInfo = namedtuple("LedInfo", ["index", "outer_net", "inner_net", "angle", "center"])
    leds = [
        LedInfo(i, nets[p[0]], nets[p[1]], i * angle_step, Pos2(ring_r, 0).rotate(i * angle_step))
        for i, p
        in enumerate(p for c in list(combinations(range(pin_count), 2)) for p in (c,) * (3 - led_colors))
    ][:led_count]

    origin = pcb.Transform((50.8, 50.8, rotation), parent=led_pcb)

    for led in leds:
        rotate = (led_colors == 1 and bool(led.index % 2))

        # LED footprint
        led_instance = led_pcb.place(
            footprint=led_fp,
            at=led.center.add_rotation(180 if rotate else 0),
            layer=Layer.FCu,
            parent=origin,
        )

        led_instance.get_pad("1").net = led.outer_net if rotate else led.inner_net
        led_instance.get_pad("2").net = led.inner_net if rotate else led.outer_net

    inner_groups = [(g[0], g[-1], len(g)) for g in (list(g) for _, g in groupby(leds, lambda l: l.inner_net))]
    outer_groups = [(g[0], g[-1], len(g)) for g in (list(g) for _, g in groupby(leds, lambda l: l.outer_net))]

    for (first, last, count) in inner_groups:
        if count:
            # Inner LED segment connection
            origin.append(pcb.TrackArc(
                center=[0, 0],
                radius=ring_r - led_pad_dist * 0.5,
                start_angle=first.angle,
                end_angle=last.angle,
                width=track_width,
                layer=Layer.FCu,
                net=led.outer_net,
            ))

    for first, last, count in outer_groups:
        # Outer LED segment connection
        origin.append(pcb.TrackArc(
            center=[0, 0],
            radius=ring_r + led_pad_dist * 0.5,
            start_angle=first.angle,
            end_angle=last.angle,
            width=track_width,
            layer=Layer.FCu,
            net=first.outer_net,
        ))

        if count > 2:
            # Inner to outer segment connection
            inner_pad = Vec2(ring_r - led_pad_dist * 0.5, 0).rotate(first.angle + angle_step)
            outer_pad = Vec2(ring_r + led_pad_dist * 0.5, 0).rotate(last.angle + angle_step)

            # Arc between LEDs
            arc = origin.append(pcb.TrackArc(
                center=[0, 0],
                radius=ring_r,
                start_angle=first.angle + angle_step + chamfer_angle,
                end_angle=last.angle + angle_step - chamfer_angle,
                width=track_width,
                layer=Layer.FCu,
                net=first.inner_net,
            ))

            # Inner connecting segment
            origin.append(pcb.TrackSegment(start=inner_pad, end=arc.start, width=track_width, layer=Layer.FCu, net=first.inner_net))

            # Outer connecting segment
            origin.append(pcb.TrackSegment(start=arc.end, end=outer_pad, width=track_width, layer=Layer.FCu, net=first.inner_net))

    mounting_pads = []
    def add_mounting_pad(via_at, angle, net):
        pad_at = Pos2(outer_diam * 0.5 - 0.75 - 0.8, 0).rotate(angle)

        # Segment from via to mounting pad
        origin.append(pcb.TrackSegment(
            start=via_at,
            end=pad_at,
            width=track_width,
            layer=Layer.BCu,
            net=net,
        ))

        # Mounting pad itself
        pad = led_pcb.place(
            footprint=mounting_pad_fp,
            at=pad_at,
            layer=Layer.BCu,
            parent=origin,
        )
        mounting_pads.append(pad)
        pad.get_pad("1").net = net

    def add_via(at, net):
        origin.append(pcb.TrackVia(
            at=at,
            size=0.6,
            drill=0.3,
            net=net,
        ))

    for net in nets:
        net_groups = [g for g in inner_groups if g[0].inner_net == net]
        if len(net_groups) > 1:
            # Inner net connection arc
            origin.append(pcb.TrackArc(
                center=[0, 0],
                radius=ring0_r + (int(net) - 3) * ring_spacing,
                # wat
                end_angle=net_groups[0][1].angle - angle_step,
                start_angle=net_groups[-1][0].angle,
                width=track_width,
                layer=Layer.BCu,
                net=net,
            ))

        for (led, _, _) in net_groups:
            # len([g for g in net_groups if g[0].inner_net == led.inner_net]) > 1
            index = pin_count - 3 if led.inner_net == nets[1] else int(led.inner_net) - 3
            via_at = Vec2(ring0_r + index * ring_spacing, 0).rotate(led.angle)

            if led == net_groups[0][0]:
                # Pin mounting pad
                add_mounting_pad(via_at, led.angle, led.inner_net)

            # Via from inner net connection arc to segment below
            add_via(via_at, led.inner_net)

            # Segment from via to inner net group track
            origin.append(pcb.TrackSegment(
                start=via_at,
                end=Vec2(ring_r - led_pad_dist * 0.5, 0).rotate(led.angle),
                width=track_width,
                layer=Layer.FCu,
                net=led.inner_net,
            ))

    # Outer only segment connections

    last_via_at = Vec2(ring_r, 0).rotate(-angle_step * 1.5)

    # Track from outer segment to track below
    origin.append(pcb.TrackSegment(start=Vec2(ring_r + led_pad_dist * 0.5, 0), end=Vec2(ring_r, 0).rotate(-chamfer_angle), width=track_width, layer=Layer.FCu, net=nets[0]))

    # Arc to get outer track to via LEDs
    arc = origin.append(pcb.TrackArc(
        center=[0, 0],
        radius=ring_r,
        start_angle=-chamfer_angle,
        end_angle=-angle_step * 1.5,
        width=track_width,
        layer=Layer.FCu,
        net=nets[0],
    ))

    add_via(last_via_at, nets[0])
    add_mounting_pad(last_via_at, -angle_step * 2, nets[0])

    # Center hole
    origin.append(pcb.Circle(center=[0, 0], radius=hole_diam / 2, layer=Layer.EdgeCuts, width=0.1))

    # PCB edge
    origin.append(pcb.Circle(center=[0, 0], radius=outer_diam / 2, layer=Layer.EdgeCuts, width=0.1))

    led_pcb.save(root / "build" / "led_pcb" / "led_pcb.kicad_pcb")

    # Mounting hole pattern footprint

    mounting_hole_fp = fp.LibraryFootprint("Project.pretty", "Mounting_Hole_Pattern", Layer.FCu, "Mounting hole pattern for led_pcb")

    for pad in mounting_pads:
        at = pad.at.rotate(origin.at.r)

        mounting_hole_fp.append(fp.Pad(
            number=int(pad.get_pad("1").net.name[3:]),
            type=fp.PadType.ThruHole,
            shape=fp.PadShape.Circle,
            at=at,
            size=2,
            layers=[Layer.AllCu, Layer.AllMask],
            drill=1,
        ))

        mounting_hole_fp.append(fp.Model(pin_model, offset=(at.x, -at.y, -3.5)))

    mounting_hole_fp.attr = fp.FootprintAttributes(fp.FootprintType.ThroughHole, exclude_from_bom=True)
    mounting_hole_fp.append(fp.Model(root / "build" / "led_pcb.step", offset=(0, 0, -4.5 - 1.6), rotate=(180, 0, 0)))
    mounting_hole_fp.save(root / "Project.pretty" / "Mounting_Hole_Pattern.kicad_mod")

    return origin

#ring_fp = generate_ring_fp()
generate_led_pcb()

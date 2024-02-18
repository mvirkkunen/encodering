#!/usr/bin/python

from itertools import combinations, groupby, islice
import math
import pathlib
import sys
from collections import namedtuple
from dataclasses import dataclass

def pairs(iterable):
    it = iter(iterable)
    while batch := tuple(islice(it, 2)):
        yield batch

root = pathlib.Path(__file__).resolve().parent
sys.path.append(str(root / "kicadet"))

import kicadet.pcb as pcb, kicadet.footprint as fp, kicadet.symbol as sym, kicadet.schematic as sch
from kicadet.common import Vec2, Pos2, Layer

outer_diam = 24
hole_diam = 7.75
ring_r = 10
led_count = 30
led_colors = 1 # only 1 or 2
track_width = 0.2
#encoder_coord = [(-13.2/2, -6), (13.2/2, 8.5)]

# led_count = pins * (pins - 1) <=> pins = 1 + sqrt(1 + 4 * led_count) / 2
pin_count = int(math.ceil((1 + math.sqrt(1 + 4 * led_count * led_colors)) / 2))

ring_spacing = 0.8
ring0_r = hole_diam * 0.5 + 1

#led_fp = fp.FootprintLibrary("/usr/share/kicad/footprints/LED_SMD.pretty").load("LED_0603_1608Metric")
#led_fp = fp.FootprintLibrary("/usr/share/kicad/footprints/LED_SMD.pretty").load("LED_0805_2012Metric")
#for t in led_fp.find_all(fp.Text):
#    t.hide = True
project_lib = fp.FootprintLibrary("Project.pretty")
led_fp = project_lib.load("LED_0603_1608Metric")
encoder_fp = project_lib.load("Project_RotaryEncoder_Bourns_Vertical_PEC12R-3x17F-Sxxxx")
led_order_code = "C2290"

mount_hole_fp_r_offset = -0.7

alignment_hole_r = 6.5
alignment_hole_a = 30

#pin_model = "${KICAD6_3DMODEL_DIR}/Connector_Pin.3dshapes/Pin_D1.0mm_L10.0mm.wrl"
#pin_model = root / "Project.pretty" / "keystone-PN1238.STEP"
pin_model = root / "Project.pretty" / "Connfly_DS-1006-11_No_Pin.step"

###################################################################

angle_step = 360 / led_count
rotation = 3 * angle_step + (90 - (pin_count * angle_step))
#rotation = 0

@dataclass
class LedInfo:
    index: int
    outer_net: pcb.Net
    inner_net: pcb.Net
    angle: float
    center: Pos2
    rotate: float
    symbol: sch.SchematicSymbol

def generate_led_schematic(leds: list[LedInfo], nets: list[pcb.Net]):
    U = 2.54
    step = (4 * U)

    led_sch = sch.SchematicFile(page=sch.PageSettings(width=len(leds) * step + 20 * U, height=len(nets) * step + 30 * U))

    led_sym = sym.SymbolLibrary.load("/usr/share/kicad/symbols/Device.kicad_sym").get("LED")
    conn_sym = sym.SymbolLibrary.load("/usr/share/kicad/symbols/Connector_Generic.kicad_sym").get("Conn_01x01")

    origin = sch.Transform((10 * U, 10 * U), parent=led_sch)

    # Connector poins

    for i in range(len(nets)):
        led_sch.place(
            conn_sym,
            f"J{i + 1}",
            (0, i * step, 180),
            in_bom=False,
            parent=origin,
        )

    prev_x = [2 * U] * len(nets)

    for led in leds:
        x = (led.index + 1) * step
        oi = led.outer_net.ordinal - 1
        ii = led.inner_net.ordinal - 1

        top = Vec2(x, oi * step)
        bottom = Vec2(x, oi * step + 3 * U)
        inner = Vec2(x, ii * step)

        led.symbol = led_sch.place(
            led_sym,
            f"L{led.index + 1}",
            at=Pos2(top + Vec2(0, 1.5 * U), 90),
            mirror=sch.Mirror.X if led.rotate else None,
            footprint=led_fp,
            parent=origin,
        )
        led.symbol.set_property("LCSC", led_order_code)

        origin.append(sch.Wire([(prev_x[oi], top.y), top])) # top horizontal
        origin.append(sch.Wire([(prev_x[ii], inner.y), (x, inner.y)])) # bottom horizontal
        origin.append(sch.Junction(top))
        origin.append(sch.Wire([bottom, inner])) # vertical wire
        origin.append(sch.Junction(inner))

        prev_x[oi] = prev_x[ii] = x

    led_sch.save(root / "build" / "led_pcb" / "led_pcb.kicad_sch")

def generate_mounting_jig_pcb(pads: list[fp.Pad]):
    jig_pcb = pcb.PcbFile()

    position = pcb.Transform((2 * 25.4 + outer_diam * 0.5, 2 * 25.4 + outer_diam * 0.5), parent=jig_pcb)
    origin = pcb.Rotate(rotation, parent=position)

    for pad in pads:
        at = (pad.at + Vec2(mount_hole_fp_r_offset, 0))

        # Large hole
        origin.append(pcb.TrackVia(
            at=at,
            size=2.9,
            drill=1.9,
            net=0,
        ))

        origin.append(pcb.TrackVia(
            at=at.rotate(180),
            size=1.6,
            drill=0.6,
            net=0,
        ))

    # Edge silkscreen
    origin.append(pcb.Circle(center=[0, 0], radius=outer_diam / 2, layer=Layer.FSilkS, width=0.1))
    origin.append(pcb.Circle(center=[0, 0], radius=outer_diam / 2, layer=Layer.BSilkS, width=0.1))

    # PCB edge
    position.append(pcb.Circle(center=[0, 0], radius=outer_diam / 2 + 12, layer=Layer.EdgeCuts, width=0.1))

    # Center hole
    position.append(pcb.Circle(center=[0, 0], radius=hole_diam / 2, layer=Layer.EdgeCuts, width=0.1))

    # Screw slots
    hole_r = 3.75 * 0.5
    for a in range(45, 360 + 45, 90):
        #position.append(pcb.Rotate(a, pcb.Circle(center=[outer_diam / 2 + 5, 0], radius=3.75 / 2, layer=Layer.EdgeCuts, width=0.1)))
        start = Pos2(outer_diam / 2 + 6, 0).rotate(a)
        end = start.rotate(angle_step)
        #o = pcb.Rotate(a, parent=position)
        #pos = Vec2(outer_diam / 2 + 5, 0)

        endcap = pcb.Arc(start=(-hole_r, 0), mid=(0, hole_r), end=(hole_r, 0), width=0.1, layer=Layer.EdgeCuts)

        position.append(pcb.Transform(start, endcap.clone()))
        position.append(pcb.Transform(end.add_rotation(180), endcap.clone()))

        for v in [start + Vec2(hole_r, 0), start - Vec2(hole_r, 0)]:
            position.append(pcb.Arc(start=v, mid=v.rotate(angle_step * 0.5), end=v.rotate(angle_step), width=0.1, layer=Layer.EdgeCuts))

    jig_pcb.save(root / "build" / "jig_pcb" / "jig_pcb.kicad_pcb")

def generate_led_pcb():
    pad_extra_angle = angle_step * 5
    led_pad_dist = (led_fp.get_pad("1").position - led_fp.get_pad("2").position).length()
    chamfer_angle = ((180 / math.pi) / ring_r) * led_pad_dist * 0.5

    mounting_pad_fp = fp.LibraryFootprint("Project.pretty", "Mounting_Pad", layer=Layer.FCu)
    if False:
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
    if True:
        mounting_pad_fp.append(fp.Pad(
            "1",
            type=fp.PadType.Smd,
            shape=fp.PadShape.RoundRect,
            at=Vec2(0, 0),
            size=Vec2(3, 3.5),
            drill=fp.DrillDefinition(offset=Vec2(-0.6, 0)),
            solder_mask_margin=-0.2,
            layers=[Layer.FCu, Layer.FMask],
            roundrect_rratio=0.20,
        ))
    mounting_pad_fp.save(root / "Project.pretty" / "Mounting_Pad.kicad_mod")

    led_pcb = pcb.PcbFile()

    nets = [led_pcb.add_net(f"PIN{i+1}") for i in range(pin_count)]

    # Generate LED net and angle information
    leds = [
        LedInfo(i, nets[p[0]], nets[p[1]], i * angle_step, Pos2(ring_r, 0).rotate(i * angle_step), (led_colors == 1 and bool(i % 2)), None)
        for i, p
        in enumerate(p for c in list(combinations(range(pin_count), 2)) for p in (c,) * (3 - led_colors))
    ][:led_count]

    generate_led_schematic(leds, nets)

    position = pcb.Transform((25.4 + outer_diam * 0.5, 25.4 + outer_diam * 0.5, 0), parent=led_pcb)
    led_pcb.setup.aux_axis_origin = Vec2(position.at)
    origin = pcb.Transform((0, 0, rotation), parent=position)

    for led in leds:
        # LED footprint
        led_instance = led_pcb.place(
            footprint=led_fp,
            at=led.center.add_rotation(180 if led.rotate else 0),
            layer=Layer.FCu,
            symbol=led.symbol,
            parent=origin,
        )

        led_instance.get_pad("1").net = led.outer_net if led.rotate else led.inner_net
        led_instance.get_pad("2").net = led.inner_net if led.rotate else led.outer_net

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
            inner_pad = Vec2(ring_r - led_pad_dist * 0.5, 0).rotate(first.angle + (angle_step if led_colors == 1 else 0))
            outer_pad = Vec2(ring_r + led_pad_dist * 0.5, 0).rotate(last.angle + angle_step)

            # Arc between LEDs
            arc = origin.append(pcb.TrackArc(
                center=[0, 0],
                radius=ring_r,
                start_angle=first.angle + (angle_step if led_colors == 1 else 0) + chamfer_angle,
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
    def add_mounting_pad(conn_at, angle, net):
        pad_at = Pos2(outer_diam * 0.5 - 0.75 - 0.8, 0).rotate(angle)

        if conn_at is not None:
            # Segment from inner circle connection to mounting pad
            origin.append(pcb.TrackSegment(
                start=conn_at,
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
                end_angle=net_groups[0][1].angle - (angle_step if led_colors == 1 else 0),
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

                pad_angle = led.angle
                if led.inner_net == nets[-1]:
                    pad_angle += pad_extra_angle

                conn_at = Vec2(ring0_r + index * ring_spacing, 0).rotate(pad_angle)
                add_mounting_pad(conn_at, pad_angle, led.inner_net)

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

    # Outer only segment connections (pin 1)

    pin1_via = Vec2(ring_r, 0).rotate(-angle_step * 1.5)

    # Track from outer segment to arc below
    origin.append(pcb.TrackSegment(start=Vec2(ring_r + led_pad_dist * 0.5, 0), end=Vec2(ring_r, 0).rotate(-chamfer_angle), width=track_width, layer=Layer.FCu, net=nets[0]))

    # Arc to get outer track to via LEDs
    origin.append(pcb.TrackArc(
        center=[0, 0],
        radius=ring_r,
        start_angle=-chamfer_angle,
        end_angle=-angle_step * 1.5,
        width=track_width,
        layer=Layer.FCu,
        net=nets[0],
    ))

    add_via(pin1_via, nets[0])

    pin1_pad_angle = -angle_step * 2 - pad_extra_angle

    # Track from pin1 via to pad
    origin.append(pcb.TrackArc(
        center=[0, 0],
        radius=ring_r,
        start_angle=-angle_step * 1.5,
        end_angle=pin1_pad_angle,
        width=track_width,
        layer=Layer.BCu,
        net=nets[0],
    ))

    add_mounting_pad(None, pin1_pad_angle, nets[0])

    # Center hole
    origin.append(pcb.Circle(center=[0, 0], radius=hole_diam / 2, layer=Layer.EdgeCuts, width=0.1))

    # Alignment hole
    position.append(pcb.Circle(center=Vec2(alignment_hole_r, 0).rotate(alignment_hole_a), radius=1, layer=Layer.EdgeCuts, width=0.1))

    # PCB edge
    origin.append(pcb.Circle(center=[0, 0], radius=outer_diam / 2, layer=Layer.EdgeCuts, width=0.1))

    # Encoder bounds
    #position.append(pcb.Rect(start=encoder_coord[0], end=encoder_coord[1], width=0.1, layer=Layer.BSilkS))
    encoder = led_pcb.place(
        encoder_fp,
        at=(0, 0, 0),
        layer=Layer.FCu,
        parent=position,
    )

    for item in list(encoder):
        if hasattr(item, "layer") and item.layer == Layer.FSilkS:
            item.layer = Layer.BSilkS
        else:
            item.detach()

    led_pcb.save(root / "build" / "led_pcb" / "led_pcb.kicad_pcb")

    # Mounting hole pattern footprint

    mounting_hole_fp = fp.LibraryFootprint("Project.pretty", "Mounting_Hole_Pattern", Layer.FCu, "Mounting hole pattern for led_pcb")

    for pad in mounting_pads:
        at = (pad.at + Vec2(mount_hole_fp_r_offset, 0)).rotate(origin.at.r)

        mounting_hole_fp.append(fp.Pad(
            number=int(pad.get_pad("1").net.name[3:]),
            type=fp.PadType.ThruHole,
            shape=fp.PadShape.Circle,
            at=at,
            size=1.5,
            layers=[Layer.AllCu, Layer.AllMask],
            drill=0.75,
        ))

        mounting_hole_fp.append(fp.Pad(
            number=int(pad.get_pad("1").net.name[3:]),
            type=fp.PadType.Smd,
            shape=fp.PadShape.RoundRect,
            at=at,
            size=(1.5, 3),
            layers=[Layer.FCu, Layer.FMask],
        ))

        mounting_hole_fp.append(fp.Model(pin_model, offset=(at.x, -at.y, -0.1), rotate=(-90, 0, 0)))

    mounting_hole_fp.attr = fp.FootprintAttributes(fp.FootprintType.ThroughHole, exclude_from_bom=True)
    #mounting_hole_fp.append(fp.Model(root / "build" / "led_pcb.step", offset=(0, 0, 4.6)))
    mounting_hole_fp.append(fp.Model(root / "build" / "led_pcb" / "led_pcb.wrl", offset=(0, 0, 4.6)))
    mounting_hole_fp.save(root / "Project.pretty" / "Mounting_Hole_Pattern.kicad_mod")

    generate_mounting_jig_pcb(mounting_pads)

    return origin

generate_led_pcb()

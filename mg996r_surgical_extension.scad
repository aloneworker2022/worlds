// MG996R Servo — Surgical Gripper Extension
// All dimensions in mm
// Designed for 3D printing (FDM/SLA)

/* ── MG996R Datasheet Dimensions ───────────────────────────────────────────
   Body  : 40.7 × 19.7 × 42.9 mm
   Output shaft centre from bottom: 29 mm
   Mounting ear width total: 54 mm, ear thickness: 3 mm, hole Ø 4 mm
   Spline hub: Ø 5.8 mm, height 5.5 mm (25-tooth JR/Futaba spline)
   ─────────────────────────────────────────────────────────────────────── */

// ── Parameters ──────────────────────────────────────────────────────────────

// Servo body
SERVO_L   = 40.7;
SERVO_W   = 19.7;
SERVO_H   = 29.0;   // bottom to shaft centre
SERVO_TOP = 13.9;   // shaft centre to case top
EAR_SPAN  = 54.0;
EAR_T     = 3.0;
EAR_HOLE  = 4.0;
HUB_D     = 5.8;
HUB_H     = 5.5;

// Wrist housing
HOUSING_WALL  = 2.5;
HOUSING_L     = 50.0;
HOUSING_W     = SERVO_W + HOUSING_WALL * 2;
HOUSING_H     = (SERVO_H + SERVO_TOP) + HOUSING_WALL * 2;

// Surgical arm link
LINK_L   = 80.0;
LINK_W   = 12.0;
LINK_T   = 5.0;
LINK_R   = LINK_W / 2;

// Gripper jaw
JAW_L        = 45.0;
JAW_W        = 8.0;
JAW_T        = 3.5;
JAW_TIP_R    = 1.2;   // soft rounded tip radius
JAW_GAP      = 6.0;   // open gap between jaws (at servo 90°)
JAW_PIVOT_D  = 3.0;   // M3 pivot pin

// Disc horn that mounts on the servo spline
HORN_R       = 18.0;
HORN_T       = 3.5;
HORN_SPLINE  = HUB_D / 2 + 0.15; // press-fit clearance

// Rod linkage
ROD_D      = 2.0;
ROD_OFFSET = HORN_R - 4;   // attachment point on horn

// Render control
SHOW_SERVO_GHOST  = true;   // translucent servo body for reference
SHOW_HOUSING      = true;
SHOW_HORN         = true;
SHOW_LINK         = true;
SHOW_JAWS         = true;

// ── Utilities ────────────────────────────────────────────────────────────────

module fillet_box(x, y, z, r=1.5) {
    hull()
    for (dx=[r, x-r]) for (dy=[r, y-r])
        translate([dx, dy, 0]) cylinder(r=r, h=z, $fn=24);
}

module rod(from, to, d=ROD_D) {
    hull() {
        translate(from) sphere(d=d, $fn=16);
        translate(to)   sphere(d=d, $fn=16);
    }
}

// ── Servo ghost (reference, not printed) ─────────────────────────────────────

module servo_ghost() {
    color("gray", 0.25) {
        // Body
        translate([0, 0, 0])
            fillet_box(SERVO_L, SERVO_W, SERVO_H + SERVO_TOP, r=2);
        // Mounting ears
        ear_y = (EAR_SPAN - SERVO_W) / 2;
        for (s=[-1, 1])
            translate([8, s > 0 ? SERVO_W : -ear_y, SERVO_H - 4])
                cube([SERVO_L - 16, ear_y, EAR_T]);
        // Hub
        translate([SERVO_L/2, SERVO_W/2, SERVO_H + SERVO_TOP])
            cylinder(d=HUB_D, h=HUB_H, $fn=32);
    }
}

// ── Wrist housing (mounts servo, attaches to arm link) ───────────────────────

module wrist_housing() {
    difference() {
        // Outer shell
        color("white")
        translate([-HOUSING_WALL, -HOUSING_WALL, -HOUSING_WALL])
            fillet_box(SERVO_L + HOUSING_WALL*2,
                       SERVO_W + HOUSING_WALL*2,
                       SERVO_H + SERVO_TOP + HOUSING_WALL*2, r=2.5);

        // Servo cavity
        translate([0, 0, 0])
            cube([SERVO_L, SERVO_W, SERVO_H + SERVO_TOP + 1]);

        // Shaft exit hole
        translate([SERVO_L/2, SERVO_W/2, SERVO_H + SERVO_TOP - 0.5])
            cylinder(d=HUB_D + 4, h=HUB_H + HOUSING_WALL + 2, $fn=32);

        // Cable exit slot on rear face
        translate([SERVO_L - 4, SERVO_W/2 - 3, -HOUSING_WALL - 0.1])
            cube([6, 6, HOUSING_WALL + 2]);

        // M3 mounting holes through ears
        for (x=[8, SERVO_L - 8])
            translate([x, -HOUSING_WALL - 0.1, SERVO_H - 1.5])
                rotate([-90, 0, 0])
                    cylinder(d=3.2, h=HOUSING_W + 0.2, $fn=20);
    }
}

// ── Disc horn ────────────────────────────────────────────────────────────────

module disc_horn() {
    color("lightblue")
    difference() {
        union() {
            cylinder(r=HORN_R, h=HORN_T, $fn=64);
            // Rod attachment boss
            translate([ROD_OFFSET, 0, HORN_T])
                cylinder(d=5, h=3, $fn=20);
        }
        // Spline bore
        cylinder(r=HORN_SPLINE, h=HORN_T + 1, $fn=32);
        // Lightening holes
        for (a=[0:60:300])
            rotate([0, 0, a])
                translate([HORN_R * 0.55, 0, -0.1])
                    cylinder(d=5, h=HORN_T + 1, $fn=20);
        // Rod pin hole on boss
        translate([ROD_OFFSET, 0, HORN_T - 0.1])
            cylinder(d=ROD_D + 0.3, h=4, $fn=16);
    }
}

// ── Arm link ─────────────────────────────────────────────────────────────────

module arm_link() {
    color("ivory")
    difference() {
        hull() {
            cylinder(r=LINK_R, h=LINK_T, $fn=32);
            translate([LINK_L, 0, 0])
                cylinder(r=LINK_R, h=LINK_T, $fn=32);
        }
        // Proximal M4 housing bolt
        cylinder(d=4.3, h=LINK_T + 0.1, $fn=20);
        // Distal jaw pivot
        translate([LINK_L, 0, -0.1])
            cylinder(d=JAW_PIVOT_D + 0.2, h=LINK_T + 0.2, $fn=20);
        // Lightening channel
        translate([LINK_L * 0.2, -LINK_W/2 + 2.5, -0.1])
            fillet_box(LINK_L * 0.6, LINK_W - 5, LINK_T + 0.2, r=1.5);
    }
}

// ── Single jaw blade ─────────────────────────────────────────────────────────

module jaw_blade(side=1) {
    // side: +1 = upper jaw, -1 = lower jaw
    color(side > 0 ? "lightyellow" : "lightyellow")
    difference() {
        union() {
            hull() {
                // Pivot end (round)
                cylinder(d=JAW_W, h=JAW_T, $fn=32);
                // Mid-body
                translate([JAW_L * 0.6, 0, 0])
                    cylinder(d=JAW_W * 0.85, h=JAW_T, $fn=32);
            }
            hull() {
                // Mid to tip taper
                translate([JAW_L * 0.6, 0, 0])
                    cylinder(d=JAW_W * 0.85, h=JAW_T, $fn=32);
                translate([JAW_L, 0, 0])
                    cylinder(d=JAW_TIP_R * 2, h=JAW_T, $fn=24);
            }
        }
        // Pivot pin hole
        cylinder(d=JAW_PIVOT_D + 0.2, h=JAW_T + 0.1, $fn=20);
        // Rod clevis slot (at pivot end for linkage)
        translate([-JAW_W/2, -1.2, JAW_T - 1.5])
            cube([JAW_W, 2.4, 2]);
    }
}

// ── Jaw assembly (both blades + pivot pin stub) ───────────────────────────────

module jaw_assembly() {
    half_gap = JAW_GAP / 2;
    // Upper jaw — angled open
    rotate([0, 0, 15])
        translate([0, half_gap * 0.4, 0])
            jaw_blade(1);
    // Lower jaw — mirrored
    mirror([0, 1, 0])
        rotate([0, 0, 15])
            translate([0, half_gap * 0.4, 0])
                jaw_blade(-1);
    // Pivot pin
    color("silver")
        cylinder(d=JAW_PIVOT_D, h=JAW_T * 2 + 1, $fn=20);
}

// ── Push-pull rod linkage ─────────────────────────────────────────────────────

module linkage_rod() {
    from = [SERVO_L/2 + ROD_OFFSET, SERVO_W/2, SERVO_H + SERVO_TOP + HUB_H + HORN_T + 3];
    to   = [SERVO_L/2 + LINK_L,     SERVO_W/2, SERVO_H + SERVO_TOP + HUB_H + HORN_T + 3];
    color("silver") rod(from, to);
}

// ── Full assembly ─────────────────────────────────────────────────────────────

module full_assembly() {
    if (SHOW_SERVO_GHOST)  servo_ghost();

    if (SHOW_HOUSING)
        translate([-HOUSING_WALL, -HOUSING_WALL, -HOUSING_WALL])
            wrist_housing();

    horn_z = SERVO_H + SERVO_TOP + HOUSING_WALL;
    if (SHOW_HORN)
        translate([SERVO_L/2, SERVO_W/2, horn_z])
            disc_horn();

    link_z = horn_z + HORN_T + 2;
    if (SHOW_LINK)
        translate([SERVO_L/2 - 6, SERVO_W/2, link_z])
            arm_link();

    jaw_z = link_z;
    if (SHOW_JAWS)
        translate([SERVO_L/2 - 6 + LINK_L, SERVO_W/2, jaw_z])
            jaw_assembly();

    if (SHOW_LINK)
        linkage_rod();
}

// ── Individual print plates (uncomment to export STL) ────────────────────────

//translate([0,   0, 0]) wrist_housing();
//translate([70,  0, 0]) disc_horn();
//translate([0,  50, 0]) arm_link();
//translate([70, 50, 0]) jaw_blade(1);
//translate([70, 65, 0]) jaw_blade(-1);

// ── Default: show full assembly ───────────────────────────────────────────────

full_assembly();

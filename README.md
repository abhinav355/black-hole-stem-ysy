# Black Hole Simulation

An interactive black hole simulation made with **Python, PyWebView, JavaScript, HTML Canvas and CSS**.

This is my 6th attempt at making this thing, which probably explains why some parts look surprisingly decent and other parts look like I fought general relativity at 3 AM.

The Python side handles the simulation and physics calculations. JavaScript receives the simulation state and draws everything on a fullscreen HTML canvas.

It includes:

* a growing black hole
* accretion disk particles
* background stars
* gravitational lensing
* approximate light-ray bending
* photon sphere
* ISCO
* Hawking temperature
* Hawking luminosity
* tidal-force estimate
* Eddington luminosity estimate
* quasinormal-mode estimate
* particle trails
* jets
* clickable matter blobs
* black-hole spin control
* ripples and visual effects
* a small live HUD

This is **not a fully accurate general-relativity simulator**. Some formulas are real physics formulas, some are simplified versions, and some parts are mainly there to make the simulation visually understandable without requiring a supercomputer to render one orange pixel.

---

# Files

```text
.
├── main.py
├── index.html
├── load.js
└── style.css
```

### `main.py`

This is the main simulation.

It handles:

* particles
* gravity
* black-hole mass
* accretion
* stars
* gravitational lensing
* ray tracing
* disk rings
* jets
* entropy estimate
* physics calculations
* simulation timing
* communication with PyWebView

### `load.js`

This is the renderer.

It gets frame data from Python and draws:

* stars
* ray paths
* accretion disk
* disk glow
* fake Doppler-style brightness
* warped back side of the disk
* jets
* particles
* trails
* matter blobs
* black hole
* photon sphere
* HUD
* scanlines
* vignette
* crosshair

### `index.html`

Contains the canvas, HUD, Pause button and Stop button.

### `style.css`

Handles the fullscreen black interface, controls, HUD and crosshair-style cursor.

---

# How it works

Python runs the physics loop in a separate thread.

The frontend repeatedly asks Python for the newest frame:

```text
Python simulation
       ↓
 build_frame()
       ↓
 JSON frame data
       ↓
 PyWebView API
       ↓
 load.js
       ↓
 HTML Canvas
```

The physics loop tries to sleep at roughly 120 iterations per second, while the actual simulation timestep is limited to a maximum of:

```text
dt = 1 / 30 seconds
```

The JavaScript side polls for frames about every:

```text
16 ms
```

and also renders using `requestAnimationFrame()`.

---

# Controls

### Left click

Adds a matter blob at the cursor.

A normal click adds:

```text
mass = 1.0
```

It also creates some ambient particles and a ripple around the click.

### Hold left mouse button

Continuously adds smaller amounts of matter:

```text
mass = 0.4
```

approximately every:

```text
70 ms
```

Nearby blobs merge/grow instead of always creating another blob.

### Mouse wheel

Changes black-hole spin.

Each wheel step changes spin by:

```text
0.02
```

Spin is clamped between:

```text
0 ≤ spin ≤ 0.998
```

### Pause

Stops updates to the main simulation.

### Stop

Stops the simulation thread completely.

This is not the same as Pause. Once `dead = True`, the physics loop exits.

---

# Main simulation constants

The simulation uses its own scaled units:

```python
GRAVITY = 800
C_SIM = 400
MAX_PARTICLES = 2000
TRAIL_LEN = 40
```

`GRAVITY` and `C_SIM` are simulation constants, not the real SI values of \(G\) and \(c\).

Some HUD calculations separately use actual physical constants.

So this project currently mixes **simulation units** and **SI-based informational calculations**.

---

# Physics and formulas

These are the formulas currently present in the code.

## Distance / vector magnitude

For a vector:

```text
(x, y)
```

the magnitude is:

```text
|v| = √(x² + y²)
```

A normalized vector is:

```text
nx = x / |v|
ny = y / |v|
```

This is used constantly for gravity directions, trajectories and lensing.

---

## Schwarzschild / event-horizon radius

The code calculates:

```text
rₛ = 2GM / c²
```

where:

```text
G = GRAVITY
M = black-hole mass
c = C_SIM
```

In code:

```python
2 * GRAVITY * mass / C_SIM²
```

This radius is also used to decide when particles or blobs are swallowed.

---

## Orbital velocity

Particles placed into the disk start using:

```text
v = √(GM / r)
```

This is basically the Newtonian circular-orbit velocity.

Particles get a little randomness added so the disk doesn't look like someone drew 400 perfectly synchronized dots in PowerPoint.

---

# ISCO

For the normal simulation:

```text
rISCO = 3rₛ
```

Since:

```text
rₛ = 2GM/c²
```

this corresponds to:

```text
rISCO = 6GM/c²
```

for a Schwarzschild black hole.

There is also a separate Kerr ISCO function later in the code, but it is currently not connected to the main disk simulation.

---

# Photon sphere

The photon sphere is:

```text
rph = 1.5rₛ
```

or:

```text
rph = 3GM/c²
```

The renderer draws this as a faint ring around the black hole.

---

# Tidal-force estimate at ISCO

The code uses:

```text
tidal = 2GM / rISCO³
```

This value is shown in the HUD.

---

# Hawking temperature

For the HUD, the simulation converts its mass using:

```text
Mkg = M × 10³⁰
```

and calculates:

```text
Tₕ = ħc³ / (8πGMkB)
```

using approximately:

```text
ħ  = 1.055 × 10⁻³⁴
c  = 2.998 × 10⁸
G  = 6.674 × 10⁻¹¹
kB = 1.381 × 10⁻²³
```

The result is displayed as:

```text
T_h
```

in the HUD.

---

# Hawking luminosity

The code calculates:

```text
Lₕ = ħc⁶ / (15360πG²M²)
```

and displays it as:

```text
L_h
```

---

# Accretion-disk temperature

The code first gets:

```text
x = r / rₛ
```

Then:

```text
fac = 3GMṁ / (8πc³)
```

and:

```text
inner = 1 - rₛ/x
```

Finally:

```text
T = [fac × inner / r³]^(1/4)
```

This is the exact form currently implemented.

It is used mainly to assign temperatures/colors to the disk rings.

---

# Disk luminosity

There is also this function:

```text
L = 0.1 ṁ c²
```

This assumes roughly 10% efficiency.

The function exists, but it is currently not used by the main simulation or HUD.

---

# Kerr horizon

The code defines:

```text
M' = rₛ / 2
a = spin × M'
```

and calculates:

```text
r = M' + √(M'² - a²)
```

A fallback returns the normal horizon radius if the square-root value would become invalid.

This function currently exists but is not used for the visible event horizon.

---

# Kerr ergosphere

There is a `kerr_ergo()` function.

Right now it calculates the exact same expression as `kerr_horizon()`:

```text
r = M' + √(M'² - a²)
```

So the project does **not currently simulate a separate ergosphere**.

This is one of the things that still needs fixing.

---

# Frame-dragging angular velocity

A helper function calculates:

```text
ω = 2Mar / (r⁴ + a²r² + 2Ma²r)
```

with:

```text
M = rₛ/2
a = spin × M
```

However, this exact helper function is currently unused.

The live particle simulation instead uses its own simpler frame-dragging force.

---

# Simplified GR velocity correction

Particle gravity is multiplied by:

```text
GR correction = 1 + 3v²/c²
```

so:

```text
a = GM/r² × (1 + 3v²/c²)
```

This is an approximation used to make the motion less purely Newtonian.

It is not a full solution of Einstein's field equations.

---

# Simplified frame dragging

When:

```text
spin > 0.01
```

particles receive an additional tangential acceleration:

```text
fd = spin × GM/(r²c) × 50
```

That force is applied perpendicular to the radial direction.

The `× 50` is a simulation scaling factor.

---

# Speed limit

Particle speed is calculated using:

```text
v = √(vx² + vy²)
```

If:

```text
v > 0.99c
```

the velocity is scaled back to:

```text
0.99c
```

because apparently even my particles need someone enforcing the speed limit.

---

# Blob gravity

Matter blobs use:

```text
a = GM/r²
```

They also receive a tangential spiral component:

```text
spiral = 0.15 + 0.1 sin(0.5t + bornTime)
```

Their position is changed using radial and tangential acceleration values.

There is also a tiny damping factor:

```text
x = x × 0.9998
y = y × 0.9998
```

---

# Black-hole growth

When a blob reaches roughly the horizon:

```text
r < 1.05rₛ
```

the black-hole mass increases by:

```text
ΔM = 0.7 × blobMass
```

and:

```text
accretionRate += 2 × blobMass
```

Particles can also increase black-hole mass by:

```text
ΔM = particleSize × 0.001
```

when they cross approximately:

```text
1.01rₛ
```

---

# Accretion-rate decay

Every simulation update:

```text
accretionRate = accretionRate × 0.995
```

so recent accretion gradually fades away.

---

# Jet creation

Jets start being generated when:

```text
blackHoleMass > 3
```

Jet particles begin with speeds between:

```text
0.3c and 0.8c
```

The time between jet creation is:

```text
max(0.02, 0.15 - 0.003M)
```

So larger black holes produce jets more frequently in this simulation.

---

# Gravitational lensing

The code calculates an approximate Einstein radius:

```text
RE = √(4GM/c²) × 80
```

The `× 80` is a visual scaling factor.

Stars farther than:

```text
3RE
```

are left unchanged.

---

# Light deflection

Approximate deflection is:

```text
α = 4GM/(c²r) × 50
```

Again, `× 50` is being used as a visual scaling factor.

The apparent position is then shifted using:

```text
rapparent = r + αr/2
```

---

# Lensing magnification

The normalized separation is:

```text
u = r / RE
```

with a minimum value of `0.1`.

Magnification is:

```text
A = (u² + 2) / [u√(u² + 4)]
```

The code uses this value to change apparent star brightness and size.

---

# Secondary lensed image

When a star is sufficiently close:

```text
r < 1.5RE
```

the code can create a secondary image on the opposite side.

Its radius is estimated with:

```text
rsecondary = max(
    1.6rₛ,
    RE²/(2r)
)
```

---

# Approximate light-ray tracing

The simulation creates 24 light rays.

Each ray begins about:

```text
300
```

simulation units from the black hole.

For every ray step:

```text
a = 2GM/r²
```

The acceleration bends its velocity toward the black hole.

After that, velocity is normalized again so that:

```text
|v| = c
```

The ray uses:

```text
dt = 0.008
```

and runs for at most:

```text
120 steps
```

A ray is considered captured at:

```text
r < 1.05rₛ
```

and stops being traced if:

```text
r > 500
```

---

# Entropy / disk organization

This isn't black-hole thermodynamic entropy.

It is a rough measurement of how evenly the disk particles are distributed.

The disk is divided into:

```text
16 angular bins
```

For each bin:

```text
pi = countᵢ / total
```

Then Shannon entropy is calculated:

```text
H = -Σ pi log₂(pi)
```

So this value describes the distribution of disk particles around the black hole.

---

# Quasinormal-mode estimate

The code sets:

```text
M = rₛ / 2
```

and calculates:

```text
real = 0.3737c / (2πM)
imag = 0.0890c / (2πM)
```

The HUD displays this approximately as:

```text
qnm real, imag i
```

---

# Eddington luminosity

The implemented expression is:

```text
Ledd =
4πG M mp (2.998 × 10⁻⁸)
──────────────────────────
          σT
```

using:

```text
mp = 1.673 × 10⁻²⁷
σT = 6.652 × 10⁻²⁹
```

There is an important problem here:

```python
2.998e-8
```

is currently in the source.

If this was intended to represent the speed of light, it would normally be around:

```text
2.998 × 10⁸
```

So the current HUD Eddington value is very likely wrong by a huge factor.

I left this documented instead of silently pretending the code says something else.

---

# Relativistic orbit helper

There is an experimental orbit function using:

```text
L = r × vtangential
```

and:

```text
dV =
-GM/r²
+ L²/r³
- 3GML²/(c²r⁴)
```

The last term is a relativistic correction.

The radial velocity is updated with:

```text
vr = vr + dV × dt
```

and tangential velocity becomes:

```text
vt = L/r
```

This function exists but is not connected to the normal particles.

---

# Effective potential

Another experimental helper uses:

```text
Veff = (1 - rₛ/r)(1 + L²/(r²c²))
```

There is also code that numerically estimates:

```text
dV/dr
```

and:

```text
d²V/dr²
```

using finite differences, then performs a Newton-style update:

```text
rnew = r - (dV/dr)/(d²V/dr²)
```

to search for an orbit radius.

This is also not connected to the visible simulation yet.

---

# Tortoise coordinate

The code includes:

```text
r* = r + rₛ ln|r/rₛ - 1|
```

There is also an inverse function that numerically solves for `r` using Newton iteration.

These functions currently aren't part of the visual simulation.

---

# Kerr ISCO helper

There is a more complete spin-dependent ISCO function.

First:

```text
a = clamp(spin, 0, 0.998)
```

Then:

```text
Z1 =
1 + (1-a²)^(1/3)
[(1+a)^(1/3) + (1-a)^(1/3)]
```

```text
Z2 = √(3a² + Z1²)
```

Finally:

```text
rISCO =
3 + Z2 - √[(3-Z1)(3+Z1+2Z2)]
```

This is currently unused by the main disk, which still uses:

```text
rISCO = 3rₛ
```

So changing spin does not currently move the main ISCO according to this Kerr formula.

---

# Gravitational-wave strain helper

There is also:

```text
h = 4G²m₁m₂ / (c⁴d)
```

This function exists in the code but isn't connected to anything visible.

---

# Orbital precession helper

The code calculates:

```text
Δφ = 6πGM/(c²r)
```

Again, this currently exists as a helper and isn't used by the visible particle simulation.

---

# Visual formulas

Not everything is pretending to be Einstein. Some math exists purely to make the thing look less dead.

### Blob pulse

```text
pulse = 1 + 0.05 sin(0.003t + 10hue)
```

### Disk brightness variation

The renderer uses:

```text
doppler = 0.6 + 0.4 cos(angle)
```

This changes brightness around the disk.

It is a visual Doppler-like effect, not a full relativistic Doppler calculation.

### Disk warp

The back part of the disk gets:

```text
warp = 0.8rₛ(1 - radialFraction)
```

to make it appear bent around the black hole.

### Jet visual length

```text
jetLength = 18rₛ
```

### Jet visual intensity

```text
intensity =
clamp[(M - 3) × 0.025, 0, 0.12]
```

---

# HUD

The HUD currently displays:

```text
particles
blobs
T_h
L_h
tidal
edd
qnm
t
```

It also shows the last few simulation events, for example when a blob is created, grows or gets eaten.

---

# Current problems and unfinished parts

This project works, but some parts are still experimental.

## 1. Kerr calculations aren't connected properly

Spin changes particle motion slightly, but the main event horizon and disk ISCO still use the Schwarzschild-style calculations.

There are proper helper functions for Kerr ISCO and other spin calculations, but they aren't connected yet.

---

## 2. Kerr ergosphere is not actually separate

`kerr_ergo()` currently uses the same calculation as `kerr_horizon()`.

So right now there is no real ergosphere implementation.

---

## 3. Eddington luminosity probably has a typo

The code contains:

```python
2.998e-8
```

instead of something like:

```python
2.998e8
```

if that constant was meant to be the speed of light.

So `edd` on the HUD should not currently be trusted.

---

## 4. The accretion-disk temperature is heavily simplified

The temperature system is mainly being used for visual disk coloring.

It should not be treated as an accurate physical accretion-disk model.

---

## 5. Blob movement isn't a normal velocity integration

Particles have proper:

```text
position
velocity
acceleration
```

style updating.

Blobs instead directly add acceleration-like values to their position:

```text
position += acceleration × dt
```

So blob motion is intentionally/simple-ish rather than a proper orbital integrator.

Physics looked at this and filed a complaint.

---

## 6. Jet particles move twice per update

Every particle first gets the normal:

```text
x += vx × dt
y += vy × dt
```

update.

Jet particles then enter another block where velocity is damped and position gets updated again.

So jets effectively receive another movement step during the same frame.

This might be intentional for the effect, but mathematically it means jets do not use the same integration as other particles.

---

## 7. Several physics functions are currently unused

The code already contains experiments for:

* Kerr horizon
* Kerr ergosphere
* frame-dragging omega
* disk luminosity
* relativistic orbit integration
* effective potential
* stable-orbit searching
* Penrose-style shape generation
* tortoise coordinates
* Kerr ISCO
* gravitational-wave strain
* orbital precession

But they aren't connected to the main renderer/simulation yet.

Basically there is a tiny physics graveyard at the bottom of `main.py`.

---

## 8. Maximum simulation particles vs rendered particles

The simulation permits up to:

```text
2000 particles
```

but `build_frame()` sends only the latest:

```text
800 particles
```

to the frontend.

This helps performance, but it means not every simulated particle is necessarily rendered.

---

## 9. Stop cannot be undone from the UI

Pause can be toggled.

Stop does:

```python
dead = True
```

which exits the simulation loop.

There is a Python `reset_sim()` function, but there is currently no Reset button in `index.html`.

So Stop is basically the button labeled:

> I have made my decision.

---

# Things I couldn't fully do yet

The code already experiments with more advanced GR ideas, but they have not been fully integrated.

The main missing step is making spin affect the whole simulation consistently.

Right now different parts use different levels of physics:

```text
Newtonian gravity
        +
small relativistic corrections
        +
approximate frame dragging
        +
visual lensing
        +
some real physical HUD formulas
```

instead of one complete spacetime/geodesic model.

A full Kerr geodesic simulation would require replacing a lot of the current approximations rather than just adding another `if spin > 0.01` and praying to Einstein.

---

# What can be improved next

The most useful next steps based on the code that already exists would be:

1. connect `kerr_isco()` to the accretion disk
2. use the Kerr horizon when spin changes
3. implement the ergosphere separately
4. fix the Eddington luminosity constant
5. connect the existing effective-potential/orbit functions
6. improve blob integration using velocity
7. clean up the jet double-movement behavior
8. decide which advanced helper functions are actually going to be used
9. add a Reset control for `reset_sim()`
10. make the simulation units and real SI calculations more clearly separated

That should happen before adding another 900 equations because this file has already begun developing its own gravitational field.

---

# Running the project

The Python file imports:

```python
webview
```

so PyWebView needs to be installed.

Install it with:

```bash
pip install pywebview
```

Then keep these files together:

```text
main.py
index.html
load.js
style.css
```

Run:

```bash
python main.py
```

`main.py` creates a PyWebView window pointing to:

```text
index.html
```

and starts the simulation automatically.

The window currently starts at:

```text
1100 × 780
```

and is resizable.

---

# How Python and JavaScript communicate

Python exposes these functions to the frontend:

```text
get_frame
add_mass_at
set_paused
stop_sim
reset_sim
adjust_spin
get_ray_paths
```

JavaScript calls them through:

```text
pywebview.api
```

`get_frame()` returns JSON containing the simulation state.

The main frame contains:

```text
c = black-hole core
b = blobs
m = particles
s = lensed stars
r = ripples
d = disk rings
y = ray paths
i = HUD information
```

The short keys reduce the amount of data being passed every frame.

---

# Rendering

The renderer uses HTML Canvas.

The final drawing order is roughly:

```text
background
stars
light rays
disk glow
warped disk back
disk rings
Doppler-style disk details
jets
ripples
particle trails
particles
matter blobs
black hole
vignette
scanlines
crosshair
HUD
```

Drawing the black hole after the disk/particles lets the dark center cover objects that visually pass behind the event horizon.

---

# Performance

There are a few protections against the simulation turning a laptop into an accretion disk itself.

The code:

* caps particles at 2000
* sends only 800 particles to JavaScript
* limits trails to 40 positions
* caches the static background
* retraces rays around every 0.1 seconds instead of every frame
* limits the simulation timestep
* uses a separate simulation thread
* limits ray tracing to 24 rays and 120 steps each

The background canvas is rebuilt only when necessary, such as after resizing.

---

# Final note

This project is a mix of physics, approximations and visual tricks.

Some values are based on real equations. Some are deliberately scaled so that the effects are actually visible. Some advanced functions exist but aren't wired into the simulation yet.

So this should be treated as an **interactive black-hole simulation/visualization**, not an astrophysics research tool.

Which is probably for the best because clicking inside an actual event horizon would make debugging significantly more annoying.

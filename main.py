import json, math, time, random, threading
from collections import deque

#its my 8th attempt to make and 19th update. i should be better i mean way better then this in 2027
def clamp(value,low,high):
    if value<low:
        return low
    if value > high:
        return high
    return value
def normalize_2d(x, y):
    magnitude = math.sqrt(x * x + y * y)
    if magnitude < 1e-12:
        return (0.0, 0.0)
    return (x / magnitude, y / magnitude)

GRAVITY = 80
C_SIM = 140
CSCR = 420.0
MAX_PARTICLES = 1200
TRAIL_LEN = 18
PI2 = math.pi * 2
M_MAX = 14.0
WIN_H = 780

def horizon_radius(mass):
    return 2.0 * GRAVITY * mass / (C_SIM * C_SIM)
def orbital_speed(r, mass):
    return math.sqrt(GRAVITY * mass / r)
def isco_r(rs):
    return 3.0 * rs
def photon_sphere(rs):
    return 1.5 * rs
def tidal_at_isco(mass):
    rs=horizon_radius(mass)
    return 2.0*GRAVITY*mass/(isco_r(rs)**3)
def hawking_temp(mass_kg):
    return 1.055e-34*(2.998e8)**3/(8.0*math.pi*6.674e-11*mass_kg*1.381e-23)

def hawking_lum(mass_kg):
    return 1.055e-34*(2.998e8)**6/(15360.0*math.pi*6.674e-11**2*mass_kg**2)
def disk_temp(r, mass, mdot):
    rs=horizon_radius(mass)
    x=r/rs
    fac=3.0*GRAVITY*mass*mdot/(8.0*math.pi*C_SIM**3)
    inner=1.0-rs/x
    return (fac*inner/(r**3))**0.25
def kerr_horizon(mass, spin):
    M=horizon_radius(mass)/2.0
    a=spin*M
    d=M*M-a*a
    if d<0: return horizon_radius(mass)
    return M+math.sqrt(d)
def frame_drag_omega(r, mass, spin):
    M=horizon_radius(mass)/2.0
    a=spin*M
    return 2.0*M*a*r/(r**4+a*a*r*r+2.0*M*a*a*r)
def gr_correction(v_squared):
    return 1.0 + 3.0 * v_squared / (C_SIM * C_SIM)
def eddington_lum(mass_kg):
    return 4*math.pi*6.674e-11*mass_kg*1.673e-27*2.998e8/6.652e-29
def qnm_freq(mass):
    M=horizon_radius(mass)/2.0
    real_part=0.3737*C_SIM/(PI2*max(M,0.01))
    imag_part=0.0890*C_SIM/(PI2*max(M,0.01))
    return real_part, imag_part

def shadow_px(mass, spin=0.0):
    #the shadow the canvas actually draws, in px. blob world lives here
    b = 35.1*math.pow(max(mass, 0.1)/5.0, 0.45)*(1.0-0.13*spin)
    if b < 22.0: b = 22.0
    hi = WIN_H*0.16
    if b > hi: b = hi
    return b

def blobG(mass):
    return shadow_px(mass)*CSCR*CSCR/(2.0*max(mass, 0.1))

bh_x=0.0
bh_y=0.0
bh_mass=   5.0
bh_spin=  0.0
paused =False
dead =False
sim_time= 0.0
dt=1.0/60.0
accretion_rate=0.0
total_eaten=0.0
jet_timer =0.0
entropy_val = 0.0
blobs=[]
particles= []
ripples =[]
bg_stars =[]
lensed_stars =[]
disk_rings=[]
ray_paths = []
ray_timer = 0.0
lens_timer = 0.0
ring_timer = 0.0
frame_timer = 0.0
event_log = deque(maxlen=20)
#dicttt to semd
frame_data = {}
frame_dirty = False


def init_everything():
    global bh_x, bh_y, bh_mass, bh_spin, paused, dead
    global sim_time, dt, accretion_rate, total_eaten, jet_timer
    global entropy_val, blobs, particles, ripples
    global bg_stars, lensed_stars, disk_rings
    global ray_paths, ray_timer
    global lens_timer, ring_timer, frame_timer
    global frame_data, frame_dirty, event_log

    bh_x=0.0; bh_y=0.0; bh_mass=5.0; bh_spin=0.0
    paused=False; dead=False; sim_time=0.0; dt=1.0/60.0
    accretion_rate=0.0; total_eaten=0.0; jet_timer=0.0
    entropy_val=0.0
    blobs=[]; particles=[]; ripples=[]
    bg_stars = []
    lensed_stars = []
    disk_rings = []
    ray_paths = []
    ray_timer = 0.0
    lens_timer = 0.0
    ring_timer = 0.0
    frame_timer = 0.0
    frame_data = {}
    frame_dirty = False
    event_log = deque(maxlen=20)
    make_bg_stars(420)
    make_disk_rings(80)


def make_bg_stars(n):
    global bg_stars
    bg_stars=[]
    for _ in range(n):
        angle=random.uniform(0, PI2)
        dist=random.uniform(30, 500)
        bg_stars.append((
            dist*math.cos(angle),
            dist*math.sin(angle),
            random.uniform(0.3, 1.0),
            random.uniform(0.5, 2.0),
            random.uniform(0.5, 3.0),
            random.uniform(0, 1)
        ))

def make_disk_rings(n):
    global disk_rings
    disk_rings=[]
    rs=horizon_radius(bh_mass)
    ir=isco_r(rs)
    rin=max(ir, rs*1.5)
    rout=rin+12.0*rs
    for i in range(n):
        frac=i/max(n-1, 1)
        r=rin+frac*(rout-rin)
        t=disk_temp(r, bh_mass, max(accretion_rate, 0.01))
        disk_rings.append((r, t, frac))

def try_grow_existing_blob(wx, wy, amount):
    active = [
        b for b in blobs
        if b["alive"]
    ]
    if not active:
        return False
    b = min(
        active,
        key=lambda item: (
            (wx - item["x"]) ** 2 +
            (wy - item["y"]) ** 2
        ),)
    if (wx-b["x"])**2+(wy-b["y"])**2 > 70.0*70.0:
        return False
    b["mass"] += amount
    b["draw_radius"] = min(
        8.0 +
        math.sqrt(max(b["mass"], 0.1)) * 4.0,
        34.0,)
    event_log.append(
        "grew single clump to " +
        str(round(b["mass"], 1))
)
    return True

def make_blob(wx, wy, amount):
    dx = wx - bh_x
    dy = wy - bh_y
    radius = max(
        math.sqrt(dx * dx + dy * dy),
        shadow_px(bh_mass) * 1.6,
    )
    G = blobG(bh_mass)
    vc = math.sqrt(G*bh_mass/radius)
    tx, ty = normalize_2d(-dy, dx)
    inward_x, inward_y = normalize_2d(-dx, -dy)
    orbit_speed = min(
        orbital_speed(radius, bh_mass) * 0.0 + vc * 0.55,
        CSCR * 0.30,
    )
    infall_speed = min(
        orbit_speed * 0.12,
        CSCR * 0.04, )
    return {
        "x": wx,
       "y": wy,
        "vx": (
            tx * orbit_speed +
            inward_x * infall_speed
     ),
        "vy": (
            ty * orbit_speed +
            inward_y * infall_speed
     ),
        "mass": amount,
        "draw_radius": min(
            8.0 +
            math.sqrt(max(amount, 0.1)) * 4.0,
            34.0,),
        "alive": True,
        "born": sim_time,
        "hue": 0.08,}
#want to die T_T
def add_mass_at(wx, wy, amount=1.0):
    global accretion_rate
    if not try_grow_existing_blob(wx, wy, amount):
        if len(blobs) < 36:
            blobs.append(
                make_blob(
                    wx,
                  wy,
                    amount,
         )
            )
            event_log.append(
                "new single mass at %.0f, %.0f" %
                (wx, wy)
        )
        else:
            event_log.append("clump cap")
    ripples.append(
        make_ripple(
            wx,
            wy,
            150,
            120,
            min(
                0.15 + amount * 0.05,
                0.6,
),))

def make_ambient_particle(cx, cy):
    ang=random.uniform(0, PI2)
    off=random.uniform(10, 60)
    px=cx+off*math.cos(ang)
    py=cy+off*math.sin(ang)
    rs=horizon_radius(bh_mass)
    r=math.sqrt((px-bh_x)**2+(py-bh_y)**2)
    if r<rs*1.2:
        r=rs*1.5
        px=bh_x+r*math.cos(ang)
        py=bh_y+r*math.sin(ang)
    vo=orbital_speed(r, bh_mass)
    tx,ty=normalize_2d(bh_y-py, px-bh_x)
    sc=random.uniform(0.7, 1.3)
    return {"x":px,"y":py,"vx":tx*vo*sc+random.gauss(0,vo*0.1),"vy":ty*vo*sc+random.gauss(0,vo*0.1),"br":random.uniform(0.5,1),"ht":random.uniform(0.2,0.9),"age":0.0,"die":random.uniform(15,45),"tr":deque(maxlen=TRAIL_LEN),"tp":2,"sz":random.uniform(1,3)}

def make_disk_particle():
    rs=horizon_radius(bh_mass)
    ir=isco_r(rs)
    r=random.uniform(ir*1.1, ir+12.0*rs)
    a=random.uniform(0, PI2)
    px=bh_x+r*math.cos(a)
    py=bh_y+r*math.sin(a)
    vo=orbital_speed(r, bh_mass)
    tx,ty=normalize_2d(bh_y-py, px-bh_x)
    return {"x":px,"y":py,"vx":tx*vo*random.uniform(0.92,1.08),"vy":ty*vo*random.uniform(0.92,1.08),"br":random.uniform(0.4,1),"ht":clamp((r-ir)/(ir*8),0,1),"age":0.0,"die":random.uniform(20,60),"tr":deque(maxlen=TRAIL_LEN),"tp":0,"sz":random.uniform(1,2.5)}

def make_jet_particle(direction):
    sp=C_SIM*random.uniform(0.3, 0.8)
    return {"x":bh_x+random.gauss(0,2),"y":bh_y,"vx":random.gauss(0,0.08)*sp*0.3,"vy":direction*sp,"br":random.uniform(0.6,1),"ht":0.1+random.uniform(0,0.2),"age":0.0,"die":random.uniform(3,10),"tr":deque(maxlen=TRAIL_LEN),"tp":1,"sz":random.uniform(1,2)}
def make_ripple(ox, oy, max_r, speed, strength):
    return {"ox":ox,"oy":oy,"r":0,"mr":max_r,"sp":speed,"st":strength,"t0":sim_time}
def update_blobs():
    global bh_mass, total_eaten, accretion_rate
    if not blobs:
        return
    sh = shadow_px(bh_mass, bh_spin)
    G = blobG(bh_mass)
    mu = G*bh_mass
    n = len(blobs)
    ax = [0.0]*n
    ay = [0.0]*n

    for i in range(n):
        bi = blobs[i]
        if not bi["alive"]:
            continue
        for j in range(i+1, n):
            bj = blobs[j]
            if not bj["alive"]:
                continue
            dx = bj["x"]-bi["x"]
            dy = bj["y"]-bi["y"]
            d2 = dx*dx + dy*dy + 250.0
            d = math.sqrt(d2)
            if d < (bi["draw_radius"]+bj["draw_radius"])*0.85 + 6.0:
                m = bi["mass"]+bj["mass"]
                big, small = (bi, bj) if bi["mass"] >= bj["mass"] else (bj, bi)
                wvx = (bi["vx"]*bi["mass"]+bj["vx"]*bj["mass"])/m
                wvy = (bi["vy"]*bi["mass"]+bj["vy"]*bj["mass"])/m
                big["vx"] = (wvx+big["vx"])*0.5
                big["vy"] = (wvy+big["vy"])*0.5
                big["mass"] = m
                big["draw_radius"] = min(8.0+math.sqrt(max(m, 0.1))*4.0, 34.0)
                small["alive"] = False
                ripples.append(make_ripple(big["x"], big["y"], 130, 150, 0.3))
                event_log.append("clumps merged, m=%.1f" % m)
                continue
            f = G/d2
            if f > 300.0:
                f = 300.0
            ux = dx/d
            uy = dy/d
            ax[i] += f*bj["mass"]*ux
            ay[i] += f*bj["mass"]*uy
            ax[j] -= f*bi["mass"]*ux
            ay[j] -= f*bi["mass"]*uy
            lim = (bi["draw_radius"]+bj["draw_radius"])*2.4
            if d < lim:
                k = (1.0-d/lim)*1.2
                dvx = bj["vx"]-bi["vx"]
                dvy = bj["vy"]-bi["vy"]
                ax[i] += k*dvx; ay[i] += k*dvy
                ax[j] -= k*dvx; ay[j] -= k*dvy

    surviving = []
    for i in range(n):
        b = blobs[i]
        if not b["alive"]:
            continue
        dx = bh_x - b["x"]
        dy = bh_y - b["y"]
        r = math.sqrt(dx*dx + dy*dy)
        if r < sh * 1.06:
            swallowed_mass = b["mass"] * 0.7
            room = M_MAX - bh_mass
            if room > 0.0:
                bh_mass += min(swallowed_mass, room)
            total_eaten += b["mass"]
            accretion_rate += b["mass"] * 2.0
            ripples.append(
                make_ripple(
                    b["x"],
                    b["y"],
                    200,
                    180,
                    min(
                        0.2 + b["mass"] * 0.03,
                        0.5,
                    ),
                )
            )
            event_log.append(
                "ate %.1f, bh=%.1f" %
                (b["mass"], bh_mass)
            )
            continue
        safe_r = max(r, sh * 1.1)
        L = b["x"]*b["vy"] - b["y"]*b["vx"]
        bend = 1.0 + 3.0*L*L/(CSCR*CSCR*safe_r*safe_r)
        accel = (
            mu /
            (safe_r * safe_r)
            * bend
        )
        if accel > 4000.0:
            accel = 4000.0
        nx, ny = normalize_2d(dx, dy)
        b["vx"] += nx * accel * dt
        b["vy"] += ny * accel * dt
        tdf = 1.0
        if r < sh * 8.0:
            tdf = math.sqrt(max(1.0 - sh*0.85/max(r, 1.0), 0.18))
        hd = dt * tdf

        b["vx"] *= 0.9992
        b["vy"] *= 0.9992
        speed = math.sqrt(
            b["vx"] ** 2 +
            b["vy"] ** 2
        )
        escape_speed = math.sqrt(
            2.0 * mu / safe_r
        )
        bound_speed = min(
            CSCR * 0.85,
            escape_speed * 0.96,
        )
        if speed > bound_speed:
            cap = bound_speed / speed
            b["vx"] *= cap
            b["vy"] *= cap
        b["x"] += b["vx"] * hd
        b["y"] += b["vy"] * hd
        if not (math.isfinite(b["x"]) and math.isfinite(b["y"])):
            continue
        if math.hypot(b["x"], b["y"]) > 1900.0:
            event_log.append("clump drifted off")
            continue
        surviving.append(b)
    blobs.clear()
    blobs.extend(surviving)
def step_particle(p):
    global bh_mass
    rs = horizon_radius(bh_mass)
    p["age"] += dt
    if p["age"] > p["die"]:
        return False
    dx = bh_x - p["x"]
    dy = bh_y - p["y"]
    r = math.sqrt(dx*dx + dy*dy)
    if r < rs * 1.01:
        bh_mass += p["sz"] * 0.001
        return False
    v_sq = p["vx"] ** 2 + p["vy"] ** 2
    gr = gr_correction(v_sq)
    safe_r = max(r, rs * 1.08)
    compactness = clamp(
        rs / safe_r,
        0.0,
        0.92,
    )
    accel = (
        GRAVITY * bh_mass / (safe_r * safe_r)
        * (1.0 + 0.8 * compactness * compactness)
        * gr
    )
    nx, ny = normalize_2d(dx, dy)
    p["vx"] += nx * accel * dt
    p["vy"] += ny * accel * dt
    if bh_spin > 0.01 and r < rs * 18:
        tx, ty = -ny, nx
        fd = (
            bh_spin *
            GRAVITY *
            bh_mass /
            (safe_r * safe_r * C_SIM)
            * 9)
        p["vx"] += tx * fd * dt
        p["vy"] += ty * fd * dt
    # nothing goes faster than light and i know u know
    speed = math.sqrt(p["vx"]**2 + p["vy"]**2)
    if speed > C_SIM * 0.99:
        cap = C_SIM * 0.99 / speed
        p["vx"] *= cap
        p["vy"] *= cap

    p["x"] += p["vx"] * dt
    p["y"] += p["vy"] * dt
    p["tr"].append((p["x"], p["y"], p["br"]))
    p["br"] = max(0, 1.0 - p["age"] / p["die"])
    if r <rs* 6:
        p["ht"] = clamp(1.0 - (r - rs) / (rs * 5), 0.1, 1.0)
    if p["tp"] == 0:
        viscosity = 1.0 - min(
        0.012,
        dt * (0.004 + compactness * 0.02),
        )
        p["vx"] *= viscosity
        p["vy"] *= viscosity

    #ignore gravity and just fly out
    if p["tp"] ==1:
        p["vx"] *= 0.99
        p["vy"] *= 0.99
        p["x"] += p["vx"] * dt
        p["y"] += p["vy"] * dt
    return True
def update_all_particles():
    alive = []

    for particle in particles:
        if step_particle(particle):
            alive.append(particle)
    particles[:] = alive[-MAX_PARTICLES:]


def update_ripples():
    i = 0
    while i < len(ripples):
        rp = ripples[i]
        rp["r"] += rp["sp"] * dt
        rp["st"] *= 0.97
        if rp["r"] > rp["mr"] or rp["st"] < 0.005:
            ripples.pop(i)
        else:
            i += 1
def maintain_population():
    global jet_timer, accretion_rate
    disk_count = sum(1 for s in particles if s["tp"] == 0)
    if disk_count < 280 and random.random() < 0.32:
        particles.append(make_disk_particle())
    jet_timer += dt
    jet_interval = max(0.02, 0.15 - bh_mass * 0.003)
    if jet_timer > jet_interval and bh_mass > 3:
        particles.append(make_jet_particle(1))
        particles.append(make_jet_particle(-1))
        jet_timer = 0
    ambient_count = sum(1 for s in particles if s["tp"] == 2)
    if ambient_count < 60 and random.random() < 0.11:
        a = random.uniform(0, PI2)
        d = random.uniform(100, 400)
        particles.append(make_ambient_particle(bh_x + d*math.cos(a), bh_y + d*math.sin(a)))
    accretion_rate *= 0.995
def lens_one_star(sx, sy, brightness, size, twinkle, hue):
    rs = horizon_radius(bh_mass)
    einstein_r = math.sqrt(4 * GRAVITY * bh_mass / (C_SIM * C_SIM)) * 80
    dx=sx -bh_x
    dy=sy-bh_y
    r=math.sqrt(dx*dx+dy*dy)

    if r <rs*1.5:
        return []
    if r>= einstein_r * 3:
        return [(sx, sy, brightness, size, twinkle, hue, False)]
    deflection = 4 * GRAVITY * bh_mass / (C_SIM * C_SIM * r) * 50
    nx, ny = normalize_2d(dx, dy)
    apparent_r = r + deflection * r * 0.5
    app_x = bh_x + nx * apparent_r
    app_y = bh_y + ny * apparent_r
    u = max(r / einstein_r, 0.1)
    mag = (u*u + 2) / (u * math.sqrt(u*u + 4))
    result = []
    if r<einstein_r *1.5:
        sec_r = max(rs * 1.6, einstein_r * einstein_r / r * 0.5)
        sec_bri = brightness * min(mag * 0.3, 2.0)
        result.append((bh_x - nx*sec_r, bh_y - ny*sec_r, sec_bri, size*0.6, twinkle, hue, True))
    app_bri = min(brightness * mag, 2.0)
    result.append((app_x, app_y, app_bri, size * min(mag*0.5, 3), twinkle, hue, False))
    return result
def compute_lensing():
    global lensed_stars
    lensed_stars = []
    for star in bg_stars:
        lensed_stars.extend(lens_one_star(*star))
# this is a rough measure of how "organized" the disk is
def calc_entropy():
    global entropy_val
    disk_parts = [s for s in particles if s["tp"] == 0]
    if len(disk_parts) < 2:
        entropy_val = 0
        return
    num_bins = 16
    bins = [0] * num_bins
    for p in disk_parts:
        angle = math.atan2(p["y"] - bh_y, p["x"] - bh_x)
        idx = int((angle + math.pi) / (PI2) * num_bins) % num_bins
        bins[idx] += 1
    total = sum(bins)
    ent = 0
    for count in bins:
        if count > 0:
            prob = count / total
            ent -= prob * math.log2(prob)
    entropy_val = ent
def build_frame():
    global frame_data, frame_dirty
    rs = horizon_radius(bh_mass)
    ir = isco_r(rs)
    ps = photon_sphere(rs)
    mkg = bh_mass * 1e30
    core={"x":bh_x,"y":bh_y,"m":bh_mass,"rs":rs,"isco":ir,"ps":ps,"spin":bh_spin,"eaten":total_eaten,"ent":round(entropy_val,3)}
    bl=[{"x":round(b["x"],2),"y":round(b["y"],2),"m":round(b["mass"],2),"r":round(b["draw_radius"],2),"h":round(b["hue"],3)} for b in blobs if b["alive"]]
    ml=[]
    for p in particles[-600:]:
        tr = [
        (
            round(t[0], 1),
            round(t[1], 1),
            round(t[2], 2),
        )
        for t in list(p["tr"])[-12:]
    ]
        ml.append({"x":round(p["x"],2),"y":round(p["y"],2),"b":round(p["br"],3),"w":round(p["ht"],3),"k":p["tp"],"s":round(p["sz"],2),"t":tr})
    sl=[]
    for lx,ly,lb,ls,tw,hu,sec in lensed_stars:
        fl=lb*(0.85+0.15*math.sin(sim_time*tw+hu*100))
        sl.append({"x":round(lx,1),"y":round(ly,1),"b":round(fl,3),"s":round(ls,2),"h":round(hu,3),"c":sec})
    rl=[{"x":round(r["ox"],1),"y":round(r["oy"],1),"r":round(r["r"],1),"a":round(r["st"],4)} for r in ripples]
    dl=[]
    for ring_r,ring_t,ring_f in disk_rings:
        dl.append({"r":round(ring_r,2),"t":round(min(ring_t*100,1),4),"f":round(ring_f,3)})
    rays_out=[{"p":[(round(q[0],1),round(q[1],1)) for q in ry["p"]],"x":ry["x"]} for ry in ray_paths]
    info={
        "ht":"%.2e"%hawking_temp(mkg),
        "hl":"%.2e"%hawking_lum(mkg),
        "td":round(tidal_at_isco(bh_mass),4),
        "tm":round(sim_time,2),
        "np":len(particles),
        "nb":len([b for b in blobs if b["alive"]]),
        "edd":"%.2e"%eddington_lum(mkg),
        "qnm":"%.3f, %.4fi"%qnm_freq(bh_mass),
        "lg":list(event_log)[-5:]
    }
    frame_data={"c":core,"b":bl,"m":ml,"s":sl,"r":rl,"d":dl,"y":rays_out,"i":info}
    frame_dirty=True
def get_frame():
    global frame_dirty
    if frame_dirty:
        frame_dirty=False
        return json.dumps(frame_data)
    return None
def trace_one_ray(sx, sy, dx, dy, rs):
    vx=dx*C_SIM; vy=dy*C_SIM
    path=[(sx,sy,False)]
    rdt=0.008
    for _ in range(120):
        rx=bh_x-sx; ry=bh_y-sy
        r=math.sqrt(rx*rx+ry*ry)
        if r<rs*1.05:
            path.append((sx,sy,True)); break
        if r>500:
            path.append((sx,sy,False)); break
        a=GRAVITY*bh_mass/(r*r)*2.0
        nx,ny=normalize_2d(rx,ry)
        vx+=nx*a*rdt; vy+=ny*a*rdt
        s=math.sqrt(vx*vx+vy*vy)
        vx=vx/s*C_SIM; vy=vy/s*C_SIM
        sx+=vx*rdt; sy+=vy*rdt
        path.append((sx,sy,False))
    return path
def trace_all_rays():
    rs=horizon_radius(bh_mass)
    ps=photon_sphere(rs)
    rays=[]
    for i in range(24):
        ang=(i/24)*PI2
        sx=bh_x+300*math.cos(ang)
        sy=bh_y+300*math.sin(ang)
        imp=ps*random.uniform(0.5, 2.5)
        aim=ang+math.pi+random.uniform(-0.3, 0.3)
        tx=bh_x+imp*math.cos(aim+math.pi/2)
        ty=bh_y+imp*math.sin(aim+math.pi/2)
        ddx,ddy=normalize_2d(tx-sx, ty-sy)
        p=trace_one_ray(sx,sy,ddx,ddy,rs)
        if len(p)>3:
            rays.append({"p":[(round(q[0],1),round(q[1],1)) for q in p],"x":p[-1][2]})
    return rays
def update_rays(wall_dt):
    global ray_paths, ray_timer
    ray_timer+=wall_dt
    if ray_timer > 0.35:
        ray_timer=0
        ray_paths=trace_all_rays()
def get_ray_paths():
    return json.dumps(ray_paths)
def set_paused(v):
    global paused
    paused=bool(v)
def stop_sim():
    global dead
    dead=True
def reset_sim():
    global blobs, particles, ripples
    init_everything()
def adjust_spin(d):
    global bh_spin
    bh_spin=clamp(bh_spin+d, 0, 0.998)
def physics_loop():
    global sim_time, dt
    global lens_timer, ring_timer, frame_timer
    last = time.perf_counter()
    while not dead:
        now = time.perf_counter()
        wall_dt = min(
            now - last,
            0.05,)
        last = now
        if not paused:
            dt = min(
                wall_dt,
                1.0 / 60.0, )
            sim_time += dt
            update_blobs()
            update_all_particles()
            update_ripples()
            maintain_population()
            lens_timer += dt
            ring_timer += dt
            frame_timer += dt
            if lens_timer >= 0.25:
                lens_timer = 0.0
                compute_lensing()
            if ring_timer >= 0.25:
                ring_timer = 0.0
                make_disk_rings(80)
            if frame_timer >= 1.0 / 30.0:
                frame_timer = 0.0
                calc_entropy()
                build_frame()
        update_rays(wall_dt)
        time.sleep(1.0 / 180.0)
def start():
    import webview
    init_everything()
    threading.Thread(target=physics_loop, daemon=True).start()
    w=webview.create_window(title="muhahaha",url="index.html",width=1100,height=780,resizable=True,frameless=False,easy_drag=True,text_select=False)
    w.expose(get_frame,add_mass_at,set_paused,stop_sim,reset_sim,adjust_spin,get_ray_paths)
    webview.start(debug=False)
start()

#this all looks right if any problem pls tell me

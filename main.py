import json, math ,time,  random  ,threading
from collections import deque

#its my 6th attempt to make bruh 2026 i should be better i mean way better then this in 2027
#TODO: fix this horrible mess later
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
def hash_int(n):
    n=((n>>13)^n)*1274126177
    return ((n>>16)^n&0x7fffffff)/0x7fffffff
def noise_1d(x):
    ix=int(math.floor(x))
    fx=x-ix
    fx=fx*fx*(3-2*fx)
    return hash_int(ix)+(hash_int(ix+1)-hash_int(ix))*fx
def fbm(x, octaves=4):
    val=0.0; a=0.5; f=1.0
    for _ in range(octaves):
        val+=a*noise_1d(x*f)
        a*=0.5
        f*=2.17
    return val
GRAVITY = 800
C_SIM = 400
MAX_PARTICLES=2000
TRAIL_LEN = 40
PI2 = math.pi * 2
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
def disk_luminosity(_mass, mdot):
    _ = _mass
    return 0.1*mdot*C_SIM**2
def kerr_horizon(mass, spin):
    M=horizon_radius(mass)/2.0
    a=spin*M
    d=M*M-a*a
    if d<0: return horizon_radius(mass)
    return M+math.sqrt(d)
def kerr_ergo(mass, spin):
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
    return 4*math.pi*6.674e-11*mass_kg*1.673e-27*2.998e-8/6.652e-29
def qnm_freq(mass):
    M=horizon_radius(mass)/2.0
    real_part=0.3737*C_SIM/(PI2*max(M,0.01))
    imag_part=0.0890*C_SIM/(PI2*max(M,0.01))
    return real_part, imag_part
def temp_to_rgb(t):
    t=clamp(t,0,1)
    if t<0.2:
        f=t/0.2
        r,g,b=clamp(int(20+160*f),0,255),clamp(int(5+25*f),0,255),clamp(int(40+20*f),0,255)
    elif t<0.5:
        f=(t-0.2)/0.3
        r,g,b=clamp(int(180+75*f),0,255),clamp(int(30+90*f),0,255),clamp(int(60-40*f),0,255)
    elif t<0.8:
        f=(t-0.5)/0.3
        r,g,b=255,clamp(int(120+120*f),0,255),clamp(int(20+60*f),0,255)
    else:
        f=(t-0.8)/0.2
        r,g,b=clamp(int(255-35*f),0,255),clamp(int(240),0,255),clamp(int(80+175*f),0,255)
    return "rgb(%d,%d,%d)"%(r,g,b)
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
ray_paths=[]
ray_timer= 0.0
event_log=deque( maxlen=20)
#dicttt to semd
frame_data = {}
frame_dirty = False


def init_everything():
    global bh_x, bh_y, bh_mass, bh_spin, paused, dead
    global sim_time, dt, accretion_rate, total_eaten, jet_timer
    global entropy_val, blobs, particles, ripples
    global bg_stars, lensed_stars, disk_rings
    global ray_paths, ray_timer, frame_data, frame_dirty, event_log

    bh_x=0.0; bh_y=0.0; bh_mass=5.0; bh_spin=0.0
    paused=False; dead=False; sim_time=0.0; dt=1.0/60.0
    accretion_rate=0.0; total_eaten=0.0; jet_timer=0.0
    entropy_val=0.0
    blobs=[]; particles=[]; ripples=[]
    bg_stars=[]; lensed_stars=[]; disk_rings=[]
    ray_paths=[]; ray_timer=0.0
    frame_data={}; frame_dirty=False
    event_log=deque(maxlen=20)
    make_bg_stars(600)
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
    for b in blobs:
        if not b["alive"]:
            continue
        dx = wx - b["x"]
        dy = wy - b["y"]
        distance = math.sqrt(dx*dx + dy*dy)
        if distance < b["draw_radius"] + 15:
            b["mass"] += amount
            b["draw_radius"] = min(b["draw_radius"] + 2.5, 60)
            event_log.append("grew blob to " + str(round(b["mass"], 1)))
            return True
    return False


def make_blob(wx, wy, amount):
    return {
        "x": wx,
        "y": wy,
        "mass": amount,
        "draw_radius": 4.0 + amount * 1.5,
        "alive": True,
        "born": sim_time,
        "hue": random.uniform(0, 1),
    }

#want to die T_T
def add_mass_at(wx, wy, amount=1.0):
    global accretion_rate
    if not try_grow_existing_blob(wx, wy, amount):
        blobs.append(make_blob(wx, wy, amount))
        event_log.append("new blob at %.0f, %.0f" % (wx, wy))
    for _ in range(5):
        particles.append(make_ambient_particle(wx, wy))
    ripples.append(make_ripple(wx, wy, 150, 120, min(0.15 + amount*0.05, 0.6)))
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
    rs = horizon_radius(bh_mass)
    surviving = []
    for b in blobs:
        if not b["alive"]:
            continue
        dx = bh_x - b["x"]
        dy = bh_y - b["y"]
        r = math.sqrt(dx*dx + dy*dy)
        if r < rs * 1.05:
            bh_mass += b["mass"] * 0.7
            total_eaten += b["mass"] * 0.7
            accretion_rate += b["mass"] * 2.0
            ripples.append(make_ripple(b["x"], b["y"], 200, 180, min(0.2+b["mass"]*0.03, 0.5)))
            event_log.append("ate %.1f, bh=%.1f" % (b["mass"], bh_mass))
            continue

        #neoh sys to pull itin!
        accel = GRAVITY * bh_mass / (r * r)
        nx, ny = normalize_2d(dx, dy)
        tx, ty = -ny, nx
        spiral = 0.15 + 0.1 * math.sin(sim_time * 0.5 + b["born"])

        b["x"] += (nx * accel + tx * accel * spiral) * dt
        b["y"] += (ny * accel + ty * accel * spiral) * dt
        # tini tiny drag
        b["x"] *= 0.9998
        b["y"] *= 0.9998
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
    v_sq = p["vx"]**2 + p["vy"]**2
    gr = gr_correction(v_sq)
    accel = GRAVITY * bh_mass / (r * r) * gr

    nx, ny = normalize_2d(dx, dy)
    p["vx"] += nx * accel * dt
    p["vy"] += ny * accel * dt
    if bh_spin > 0.01:
        tx, ty = -ny, nx
        fd = bh_spin * GRAVITY * bh_mass / (r * r * C_SIM) * 50
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

    #ignore gravity and just fly out
    if p["tp"] ==1:
        p["vx"] *= 0.99
        p["vy"] *= 0.99
        p["x"] += p["vx"] * dt
        p["y"] += p["vy"] * dt
    return True
def update_all_particles():
    i = 0
    while i < len(particles):
        if not step_particle(particles[i]):
            particles.pop(i)
        else:
            i += 1
    # hard cap so it doesnt lag
    while len(particles) > MAX_PARTICLES:
        particles.pop(0)


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
    if disk_count < 400 and random.random() < 0.4:
        particles.append(make_disk_particle())
    jet_timer += dt
    jet_interval = max(0.02, 0.15 - bh_mass * 0.003)
    if jet_timer > jet_interval and bh_mass > 3:
        particles.append(make_jet_particle(1))
        particles.append(make_jet_particle(-1))
        jet_timer = 0
    ambient_count = sum(1 for s in particles if s["tp"] == 2)
    if ambient_count < 100 and random.random() < 0.15:
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
    for p in particles[-800:]:
        tr=[(round(t[0],1),round(t[1],1),round(t[2],2)) for t in p["tr"]]
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
        # aim slightly off center with random impact parameter
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
    if ray_timer>0.1:
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
def geodesic_step(x, y, vx, vy, mass, step_dt):
    r=math.sqrt(x*x+y*y)
    nx,ny=x/r,y/r
    v_radial=vx*nx+vy*ny
    v_tangential=-vx*ny+vy*nx
    L=r*v_tangential
    dV=-GRAVITY*mass/(r*r)+L*L/(r**3)-3*GRAVITY*mass*L*L/(C_SIM**2*r**4)
    v_radial+=dV*step_dt
    v_tangential=L/r
    vx=v_radial*nx-v_tangential*ny
    vy=v_radial*ny+v_tangential*nx
    x+=vx*step_dt; y+=vy*step_dt
    return x,y,vx,vy
def integrate_full_orbit(mass, r_start, L, steps=500):
    rs=horizon_radius(mass)
    step_dt=0.01; r=r_start; phi=0; vr=0
    path=[]
    for _ in range(steps):
        path.append((r,phi))
        dV=-GRAVITY*mass/(r*r)+L*L/(r**3)-3*GRAVITY*mass*L*L/(C_SIM**2*r**4)
        vr+=dV*step_dt
        r+=vr*step_dt
        if r>rs*1.01:
            phi+=L/(r*r)*step_dt
        else:
            break
        if r<rs*0.5 or r>500:
            break
    return path
def effective_potential(r, L, rs):
    f=1.0-rs/r
    return f*(1+L*L/(r*r*C_SIM*C_SIM))
def find_stable_orbit_r(L, rs):
    lo=rs*1.5; hi=rs*50; r=(lo+hi)/2
    for _ in range(40):
        eps=r*1e-6
        v1=effective_potential(r+eps, L, rs)
        v2=effective_potential(r-eps, L, rs)
        dV=(v1-v2)/(2*eps)
        v5=effective_potential(r+eps, L, rs)
        v6=effective_potential(r, L, rs)
        v7=effective_potential(r-eps, L, rs)
        d2V=(v5-2*v6+v7)/(eps*eps)
        if abs(d2V)<1e-15: break
        r=clamp(r-dV/d2V, lo, hi)
    return r
def penrose_shape(n=64):
    pts=[]
    for i in range(n):
        th=(i/n)*PI2
        r=1.0/(abs(math.cos(th))+abs(math.sin(th)))
        pts.append((r*math.cos(th), r*math.sin(th)))
    return pts
def tortoise(r, rs):
    return r+rs*math.log(abs(r/rs-1))
def inv_tortoise(r_star, rs):
    r=r_star
    for _ in range(30):
        if r<=rs*1.001: r=rs*1.01
        f=r+rs*math.log(abs(r/rs-1))-r_star
        df=1+rs/(r-rs)
        if abs(df)<1e-15: break
        r=r-f/df
        r=max(r, rs*1.001)
    return r
def kerr_isco(spin):
    a=clamp(spin,0,0.998)
    z1=1+(1-a*a)**(1/3)*((1+a)**(1/3)+(1-a)**(1/3))
    z2=math.sqrt(3*a*a+z1*z1)
    return 3+z2-math.sqrt((3-z1)*(3+z1+2*z2))
def gw_strain(m1, m2, distance):
    return 4*6.674e-11**2*m1*m2/(2.998e8**4*distance)
def orbital_precession(r, mass):
    return 6*math.pi*GRAVITY*mass/(C_SIM**2*r)
def physics_loop():
    global sim_time, dt
    last = time.perf_counter()
    while not dead:
        now = time.perf_counter()
        wall_dt = now - last
        last = now
        if not paused:
            dt = min(wall_dt, 1.0/30.0)
            sim_time += dt
            update_blobs()
            update_all_particles()
            update_ripples()
            maintain_population()
            compute_lensing()
            if int(sim_time * 2) % 4 == 0:
                make_disk_rings(80)
            calc_entropy()
            build_frame()
        update_rays(wall_dt)
        time.sleep(1.0 / 120)
def start():
    import webview
    init_everything()
    threading.Thread(target=physics_loop, daemon=True).start()
    w=webview.create_window(title="muhahaha",url="index.html",width=1100,height=780,resizable=True,frameless=False,easy_drag=True,text_select=False)
    w.expose(get_frame,add_mass_at,set_paused,stop_sim,reset_sim,adjust_spin,get_ray_paths)
    webview.start(debug=False)
start()






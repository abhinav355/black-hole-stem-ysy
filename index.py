import math
import threading
import time
import webview


G = 6.67430e-11
LIGHT_SPEED = 299792458.0

SOLAR_MASS = 1.98847e30
EARTH_MASS = 5.9722e24

MAX_TRAIL = 500


class Vector:
    """A small two-dimensional vector used by the physics engine."""

    def __init__(self, x=0.0, y=0.0):
        self.x = float(x)
        self.y = float(y)

    def add(self, other):
        return Vector(
            self.x + other.x,
            self.y + other.y
        )

    def subtract(self, other):
        return Vector(
            self.x - other.x,
            self.y - other.y
        )

    def multiply(self, value):
        return Vector(
            self.x * value,
            self.y * value
        )

    def divide(self, value):

        if value == 0:
            return Vector()

        return Vector(
            self.x / value,
            self.y / value
        )

    def length(self):
        return math.sqrt(
            self.x * self.x +
            self.y * self.y
        )

    def distance_to(self, other):
        return self.subtract(other).length()

    def normalized(self):

        size = self.length()

        if size == 0:
            return Vector()

        return self.divide(size)

    def copy(self):
        return Vector(
            self.x,
            self.y
        )

    def to_dict(self):
        return {
            "x": self.x,
            "y": self.y
        }


class SpaceObject:
    """A physical object tracked by the simulation."""

    def __init__(
        self,
        object_id,
        name,
        mass,
        x,
        y,
        vx,
        vy,
        radius
    ):

        self.id = object_id
        self.name = name

        self.mass = float(mass)

        self.position = Vector(x, y)
        self.velocity = Vector(vx, vy)

        self.radius = float(radius)

        self.alive = True

        self.trail = []

        self.age = 0.0

        self.trail.append(
            self.position.copy()
        )

    def speed(self):
        return self.velocity.length()

    def add_trail(self):

        self.trail.append(
            self.position.copy()
        )

        if len(self.trail) > MAX_TRAIL:
            self.trail.pop(0)

    def data(self):

        return {
            "id": self.id,
            "name": self.name,
            "mass": self.mass,

            "x": self.position.x,
            "y": self.position.y,

            "vx": self.velocity.x,
            "vy": self.velocity.y,

            "speed": self.speed(),

            "radius": self.radius,

            "alive": self.alive,

            "age": self.age,

            "trail": [
                point.to_dict()
                for point in self.trail
            ]
        }


class BlackHole:
    """The central black hole and its basic gravitational calculations."""

    def __init__(self, mass):

        self.mass = mass

        self.position = Vector(
            0,
            0
        )

        self.spin = 0.0

    def schwarzschild_radius(self):

        return (
            2 *
            G *
            self.mass /
            (LIGHT_SPEED ** 2)
        )

    def gravity_at(self, position):

        direction = (
            self.position.subtract(position)
        )

        distance = direction.length()

        if distance <= 0.0:
            return Vector()

        strength = (
            G *
            self.mass /
            (distance ** 2)
        )

        return (
            direction.normalized()
            .multiply(strength)
        )

    def orbital_speed(self, distance):

        if distance <= 0:
            return 0.0

        return math.sqrt(
            G *
            self.mass /
            distance
        )

    def escape_speed(self, distance):

        if distance <= 0:
            return 0.0

        return math.sqrt(
            2 *
            G *
            self.mass /
            distance
        )


class Simulation:
    """Owns the simulation state and advances it in fixed-size steps."""

    def __init__(self):

        self.black_hole = BlackHole(
            10 * SOLAR_MASS
        )

        self.objects = []

        self.next_id = 1

        self.simulation_time = 0.0

        self.time_step = 1.0

        self.speed = 1.0

        self.paused = True

        self.substeps = 4

        self.lock = threading.Lock()

        self.last_update = time.time()

    def add_object(
        self,
        name,
        mass,
        x,
        y,
        vx,
        vy,
        radius=1.0
    ):

        try:

            mass = float(mass)
            x = float(x)
            y = float(y)
            vx = float(vx)
            vy = float(vy)
            radius = float(radius)

        except (TypeError, ValueError):

            raise ValueError(
                "Object values must be numbers."
            )

        if mass <= 0:

            raise ValueError(
                "Mass must be greater than zero."
            )

        object_id = self.next_id

        self.next_id += 1

        thing = SpaceObject(
            object_id,
            str(name),
            mass,
            x,
            y,
            vx,
            vy,
            radius
        )

        with self.lock:

            self.objects.append(
                thing
            )

        return thing.id

    def remove_object(self, object_id):

        with self.lock:

            for thing in self.objects:

                if thing.id == int(object_id):

                    thing.alive = False

                    return True

        return False

    def clear_objects(self):

        with self.lock:

            self.objects.clear()

            self.next_id = 1

            self.simulation_time = 0.0

    def get_object(self, object_id):

        for thing in self.objects:

            if thing.id == object_id:
                return thing

        return None

    def gravity_from_object(
        self,
        source,
        target
    ):

        direction = (
            source.position.subtract(
                target.position
            )
        )

        distance = direction.length()

        if distance < 1.0:
            return Vector()

        strength = (
            G *
            source.mass /
            (distance ** 2)
        )

        return (
            direction.normalized()
            .multiply(strength)
        )

    def acceleration(self, thing):

        total = (
            self.black_hole.gravity_at(
                thing.position
            )
        )

        for other in self.objects:

            if other is thing:
                continue

            if not other.alive:
                continue

            total = total.add(
                self.gravity_from_object(
                    other,
                    thing
                )
            )

        return total

    def calculate_all_acceleration(self):

        result = {}

        for thing in self.objects:

            if not thing.alive:
                continue

            result[thing.id] = (
                self.acceleration(thing)
            )

        return result

    def move_objects(self, dt):

        accelerations = (
            self.calculate_all_acceleration()
        )

        old_positions = {}

        for thing in self.objects:

            if not thing.alive:
                continue

            old_positions[thing.id] = (
                thing.position.copy()
            )

            acceleration = (
                accelerations[thing.id]
            )

            thing.velocity = (
                thing.velocity.add(
                    acceleration.multiply(
                        dt * 0.5
                    )
                )
            )

            thing.position = (
                thing.position.add(
                    thing.velocity.multiply(dt)
                )
            )

        new_accelerations = (
            self.calculate_all_acceleration()
        )

        for thing in self.objects:

            if not thing.alive:
                continue

            acceleration = (
                new_accelerations[thing.id]
            )

            thing.velocity = (
                thing.velocity.add(
                    acceleration.multiply(
                        dt * 0.5
                    )
                )
            )

            thing.age += dt

            old_position = (
                old_positions[thing.id]
            )

            distance_moved = (
                thing.position.distance_to(
                    old_position
                )
            )

            if distance_moved > 0:

                thing.add_trail()

        self.simulation_time += dt

    def absorb_objects(self):

        horizon = (
            self.black_hole
            .schwarzschild_radius()
        )

        for thing in self.objects:

            if not thing.alive:
                continue

            distance = (
                thing.position.distance_to(
                    self.black_hole.position
                )
            )

            if distance <= horizon:

                thing.alive = False

                self.black_hole.mass += (
                    thing.mass
                )

    def collide_objects(self):

        alive = [
            thing
            for thing in self.objects
            if thing.alive
        ]

        for first_index in range(
            len(alive)
        ):

            first = alive[first_index]

            for second_index in range(
                first_index + 1,
                len(alive)
            ):

                second = alive[
                    second_index
                ]

                if not first.alive:
                    break

                if not second.alive:
                    continue

                distance = (
                    first.position.distance_to(
                        second.position
                    )
                )

                if distance <= (
                    first.radius +
                    second.radius
                ):

                    self.merge_objects(
                        first,
                        second
                    )

    def merge_objects(
        self,
        first,
        second
    ):

        total_mass = (
            first.mass +
            second.mass
        )

        new_x = (
            first.position.x *
            first.mass +
            second.position.x *
            second.mass
        ) / total_mass

        new_y = (
            first.position.y *
            first.mass +
            second.position.y *
            second.mass
        ) / total_mass

        new_vx = (
            first.velocity.x *
            first.mass +
            second.velocity.x *
            second.mass
        ) / total_mass

        new_vy = (
            first.velocity.y *
            first.mass +
            second.velocity.y *
            second.mass
        ) / total_mass

        first.mass = total_mass

        first.position = Vector(
            new_x,
            new_y
        )

        first.velocity = Vector(
            new_vx,
            new_vy
        )

        first.radius = max(
            first.radius,
            second.radius
        )

        second.alive = False

    def update(self):
        """Advance the simulation once, unless it is currently paused."""

        if self.paused:
            return

        total_time = (
            self.time_step *
            self.speed
        )

        steps = max(
            1,
            int(self.substeps)
        )

        small_step = (
            total_time /
            steps
        )

        with self.lock:

            for _ in range(steps):

                self.move_objects(
                    small_step
                )

                self.absorb_objects()

                self.collide_objects()

    def set_mass(self, solar_masses):

        solar_masses = float(
            solar_masses
        )

        if solar_masses <= 0:

            raise ValueError(
                "Black hole mass must be positive."
            )

        with self.lock:

            self.black_hole.mass = (
                solar_masses *
                SOLAR_MASS
            )

    def set_time_step(self, value):

        value = float(value)

        if value <= 0:

            raise ValueError(
                "Time step must be positive."
            )

        self.time_step = value

    def set_speed(self, value):

        value = float(value)

        if value < 0:
            value = 0

        self.speed = value

    def pause(self):

        self.paused = True

        return True

    def resume(self):

        self.paused = False

        return True

    def toggle_pause(self):

        self.paused = not self.paused

        return self.paused

    def reset(self):

        with self.lock:

            self.simulation_time = 0.0

            for thing in self.objects:

                thing.alive = True

                thing.age = 0.0

                thing.trail.clear()

                thing.trail.append(
                    thing.position.copy()
                )

    def make_orbit(
        self,
        name,
        mass,
        distance,
        clockwise=False
    ):

        x = distance
        y = 0.0

        speed = (
            self.black_hole
            .orbital_speed(distance)
        )

        if clockwise:

            velocity = Vector(
                0,
                -speed
            )

        else:

            velocity = Vector(
                0,
                speed
            )

        return self.add_object(
            name,
            mass,
            x,
            y,
            velocity.x,
            velocity.y,
            1.0
        )

    def get_state(self):

        with self.lock:

            horizon = (
                self.black_hole
                .schwarzschild_radius()
            )

            objects = []

            for thing in self.objects:

                data = thing.data()

                distance = (
                    thing.position
                    .distance_to(
                        self.black_hole.position
                    )
                )

                data["distance"] = distance

                data["inside_horizon"] = (
                    distance <= horizon
                )

                if distance > 0:

                    data["orbital_speed"] = (
                        self.black_hole
                        .orbital_speed(
                            distance
                        )
                    )

                    data["escape_speed"] = (
                        self.black_hole
                        .escape_speed(
                            distance
                        )
                    )

                else:

                    data["orbital_speed"] = 0

                    data["escape_speed"] = 0

                objects.append(data)

            return {

                "time": self.simulation_time,

                "paused": self.paused,

                "speed": self.speed,

                "time_step": self.time_step,

                "substeps": self.substeps,

                "black_hole": {

                    "mass": (
                        self.black_hole.mass
                    ),

                    "solar_mass": (
                        self.black_hole.mass /
                        SOLAR_MASS
                    ),

                    "x": (
                        self.black_hole
                        .position.x
                    ),

                    "y": (
                        self.black_hole
                        .position.y
                    ),

                    "radius": horizon,

                    "spin": (
                        self.black_hole.spin
                    )
                },

                "objects": objects
            }


class App:
    """Methods exposed to the webview's JavaScript API."""

    def __init__(self):

        self.simulation = Simulation()

        self.window = None

        self.running = True

    def start(self):

        self.simulation.resume()

        return {
            "ok": True
        }

    def pause(self):

        self.simulation.pause()

        return {
            "ok": True
        }

    def toggle(self):

        paused = (
            self.simulation
            .toggle_pause()
        )

        return {
            "paused": paused
        }

    def reset(self):

        self.simulation.reset()

        return {
            "ok": True
        }

    def clear(self):

        self.simulation.clear_objects()

        return {
            "ok": True
        }

    def get_state(self):

        return self.simulation.get_state()

    def set_black_hole_mass(
        self,
        solar_masses
    ):

        self.simulation.set_mass(
            solar_masses
        )

        return self.get_state()

    def set_time_step(self, value):

        self.simulation.set_time_step(
            value
        )

        return {
            "ok": True
        }

    def set_simulation_speed(
        self,
        value
    ):

        self.simulation.set_speed(
            value
        )

        return {
            "ok": True
        }

    def add_object(
        self,
        name,
        mass,
        x,
        y,
        vx,
        vy,
        radius=1.0
    ):

        object_id = (
            self.simulation.add_object(
                name,
                mass,
                x,
                y,
                vx,
                vy,
                radius
            )
        )

        return {
            "ok": True,
            "id": object_id
        }

    def add_orbiting_object(
        self,
        name,
        mass,
        distance,
        clockwise=False
    ):

        object_id = (
            self.simulation.make_orbit(
                name,
                mass,
                distance,
                clockwise
            )
        )

        return {
            "ok": True,
            "id": object_id
        }

    def remove_object(self, object_id):

        removed = (
            self.simulation
            .remove_object(object_id)
        )

        return {
            "ok": removed
        }

    def set_substeps(self, value):

        value = int(value)

        if value < 1:
            value = 1

        if value > 32:
            value = 32

        self.simulation.substeps = value

        return {
            "substeps": value
        }


def run_physics(app):
    """Run the physics worker at roughly 60 updates per second."""

    previous = time.perf_counter()
    frame_interval = 1.0 / 60.0

    while app.running:

        now = time.perf_counter()

        if now - previous >= frame_interval:

            app.simulation.update()

            # Keep the loop from drifting when an update takes a little longer
            # than one frame, while avoiding a burst of catch-up updates.
            previous = now

        else:

            time.sleep(0.001)


def when_loaded():

    pass


if __name__ == "__main__":

    app = App()

    window = webview.create_window(
        "Black Hole Laboratory",
        "index.html",
        js_api=app,
        width=1400,
        height=850,
        min_size=(1000, 650),
        resizable=True,
        background_color="#05070c"
    )

    app.window = window

    physics_thread = threading.Thread(
        target=run_physics,
        args=(app,),
        daemon=True
    )

    physics_thread.start()

    webview.start(
        when_loaded,
        debug=False
    )

    app.running = False
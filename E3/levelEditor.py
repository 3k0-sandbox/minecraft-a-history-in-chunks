import gzip, math, random
from perlin_noise import PerlinNoise
from PIL import Image

WIDTH  = 256
HEIGHT = 64
DEPTH  = 256
SIZE   = WIDTH * HEIGHT * DEPTH   # 4,194,304

AIR         = 0
ROCK        = 1
GRASS       = 2
DIRT        = 3
STONEBRICKS = 4
WOOD        = 5


# ───────────────────────────────────────────────────────────────────
# 1. LOAD / SAVE
# ───────────────────────────────────────────────────────────────────

def load_level(path="level.dat"):
    """
    Load a gzip-compressed level file into a mutable bytearray.
    """
    with gzip.open(path, 'rb') as f:
        data = f.read()
    if len(data) != SIZE:
        raise ValueError(f'Unexpected size! Expected {SIZE} bytes, got {len(data)}.')
    return bytearray(data)


def save_level(arr, path="level.dat"):
    """
    Write a flat bytearray of exactly SIZE bytes as a gzip-compressed level file.
    """
    if len(arr) != SIZE:
        raise ValueError(f'Unexpected size! Block array must be {SIZE} bytes')
    with gzip.open(path, 'wb', compresslevel=9) as f:
        f.write(arr)


# ───────────────────────────────────────────────────────────────────
# 2. INDEX / GET / SET
# ───────────────────────────────────────────────────────────────────

def index(x, y, z):
    """
    Y-major linear index for coordinate (x, y, z).
    """
    return (y * WIDTH + z) * DEPTH + x

def get_block(arr, x, y, z):
    return arr[(y * WIDTH + z) * DEPTH + x]

def set_block(x, y, z, value, arr):
    arr[index(x, y, z)] = value


# ───────────────────────────────────────────────────────────────────
# 3. CREATE / CONVERT WORLDS
# ───────────────────────────────────────────────────────────────────

def fill_world(value=ROCK, path="level.dat"):
    """
    Fill every block in the world with a single block type.
    """
    arr = bytes([value] * SIZE)
    save_level(arr, path)


def flat_world(height=43, block=ROCK, path="level.dat"):
    """
    Generate a completely flat world up to `height` layers.
    Defaults to the rd-132211 / rd-132328 world height of 43.
    """
    arr = bytearray(SIZE)
    for y in range(height):
        layer_start = index(0, y, 0)
        arr[layer_start:layer_start + WIDTH * DEPTH] = bytes([block]) * (WIDTH * DEPTH)
    save_level(arr, path)


def convert_world(path="level.dat"):
    """
    Convert an rd-132211/rd-132328 world so its block IDs are compatible with
    later pre-classic: the top layer (y=42) becomes GRASS, everything else STONEBRICKS.
    """
    arr = load_level(path)
    for y in range(HEIGHT):
        start = index(0, y, 0)
        end   = start + WIDTH * DEPTH
        layer = arr[start:end]
        for i in range(len(layer)):
            if layer[i] != AIR:
                layer[i] = GRASS if y == 42 else STONEBRICKS
        arr[start:end] = layer
    save_level(arr, path)


# ───────────────────────────────────────────────────────────────────
# 4. TRANSFORM / COPY
# ───────────────────────────────────────────────────────────────────

def translate(dx, dy, dz, path="level.dat"):
    """Shift every block in the world by (dx, dy, dz). Blocks shifted out-of-bounds are lost."""
    old = load_level(path)
    new = bytearray(SIZE)
    for y in range(HEIGHT):
        ny = y - dy
        if not (0 <= ny < HEIGHT): continue
        for z in range(DEPTH):
            nz = z - dz
            if not (0 <= nz < DEPTH): continue
            for x in range(WIDTH):
                nx = x - dx
                if not (0 <= nx < WIDTH): continue
                new[index(x, y, z)] = old[index(nx, ny, nz)]
    save_level(new, path)


def reflect(flipx=False, flipy=False, flipz=False, path="level.dat"):
    old = load_level(path)
    new = bytearray(SIZE)
    for y in range(HEIGHT):
        for z in range(DEPTH):
            for x in range(WIDTH):
                dst = index(
                    WIDTH  - 1 - x if flipx else x,
                    HEIGHT - 1 - y if flipy else y,
                    DEPTH  - 1 - z if flipz else z,
                )
                new[dst] = old[index(x, y, z)]
    save_level(new, path)


def rotate_y(turns=1, path="level.dat"):
    """
    Rotate the world around the Y-axis.
    turns=1 -> 90 clockwise, turns=2 -> 180, turns=3 -> 90 counter-clockwise.
    """
    old   = load_level(path)
    new   = bytearray(SIZE)
    turns = turns % 4
    for y in range(HEIGHT):
        for z in range(DEPTH):
            for x in range(WIDTH):
                if   turns == 0: nx, nz = x,               z
                elif turns == 1: nx, nz = WIDTH - 1 - z,   x
                elif turns == 2: nx, nz = WIDTH - 1 - x,   DEPTH - 1 - z
                elif turns == 3: nx, nz = z,               DEPTH - 1 - x
                new[index(nx, y, nz)] = old[index(x, y, z)]
    save_level(new, path)


def clone(x0, y0, z0, x1, y1, z1, src_path="monpe.dat", dst_path="level.dat"):
    """
    Copy the region [x0,x1] x [y0,y1] x [z0,z1] from src_path into dst_path,
    at the same coordinates. 
    """
    source = load_level(src_path)
    dest   = load_level(dst_path)
    for y in range(y0, y1 + 1):
        for z in range(z0, z1 + 1):
            for x in range(x0, x1 + 1):
                set_block(x, y, z, get_block(source, x, y, z), dest)
    save_level(dest, dst_path)


def clone_w_translate(x0, y0, z0, x1, y1, z1, dx, dy, dz,
                      src_path="monpe.dat", dst_path="level.dat"):
    """
    Copy the region [x0,x1] x [y0,y1] x [z0,z1] from src_path into dst_path,
    offsetting each block by (dx, dy, dz).
    """
    source = load_level(src_path)
    dest   = load_level(dst_path)
    for y in range(y0, y1 + 1):
        for z in range(z0, z1 + 1):
            for x in range(x0, x1 + 1):
                nx, ny, nz = x + dx, y + dy, z + dz
                if 0 <= nx < WIDTH and 0 <= ny < HEIGHT and 0 <= nz < DEPTH:
                    set_block(nx, ny, nz, get_block(source, x, y, z), dest)
    save_level(dest, dst_path)

def half_and_half(isX, isNear, world1_path="level.dat", world2_path="level.dat", dst_path="level.dat"):
    """
    Combine half of world1 with half of world2 into dst_path.

    isX:     if True, the dividing line runs along X (i.e. the split is at Z=128).
             if False, the dividing line runs along Z (i.e. the split is at X=128).
    isNear:  if True,  world1 contributes the half closer to 0 (low X or low Z).
             if False, world1 contributes the far half (high X or high Z).
    """
    w1    = load_level(world1_path)
    w2    = load_level(world2_path)
    final = bytearray(SIZE)

    if isX:
        # dividing line along X axis -> split at X=128
        w1_x0, w1_x1 = (0, 128)     if isNear else (128, WIDTH)
        w2_x0, w2_x1 = (128, WIDTH) if isNear else (0, 128)
        w1_z0, w1_z1 = 0, DEPTH
        w2_z0, w2_z1 = 0, DEPTH
    else:
        # dividing line along Z axis -> split at Z=128
        w1_z0, w1_z1 = (0, 128)     if isNear else (128, DEPTH)
        w2_z0, w2_z1 = (128, DEPTH) if isNear else (0, 128)
        w1_x0, w1_x1 = 0, WIDTH
        w2_x0, w2_x1 = 0, WIDTH

    for y in range(HEIGHT):
        for z in range(w1_z0, w1_z1):
            for x in range(w1_x0, w1_x1):
                set_block(x, y, z, get_block(w1, x, y, z), final)
        for z in range(w2_z0, w2_z1):
            for x in range(w2_x0, w2_x1):
                set_block(x, y, z, get_block(w2, x, y, z), final)

    save_level(final, dst_path)

# ───────────────────────────────────────────────────────────────────
# 5. SOLID SHAPES
# ───────────────────────────────────────────────────────────────────

def make_rect(x0, y0, z0, x1, y1, z1, block=ROCK, path="level.dat"):
    arr = load_level(path)
    for y in range(y0, y1):
        for z in range(z0, z1):
            for x in range(x0, x1):
                set_block(x, y, z, block, arr)
    save_level(arr, path)


def make_hollow_rect(x0, y0, z0, x1, y1, z1, block=ROCK, path="level.dat"):
    arr = load_level(path)
    for y in range(y0, y1):
        for z in range(z0, z1):
            for x in range(x0, x1):
                on_face = (x in (x0, x1 - 1) or y in (y0, y1 - 1) or z in (z0, z1 - 1))
                if on_face:
                    set_block(x, y, z, block, arr)
    save_level(arr, path)


def make_sphere(cx, cy, cz, r, block=ROCK, path="level.dat"):
    arr = load_level(path)
    for y in range(max(0, cy - r), min(HEIGHT, cy + r + 1)):
        for z in range(max(0, cz - r), min(DEPTH,  cz + r + 1)):
            for x in range(max(0, cx - r), min(WIDTH,  cx + r + 1)):
                if (x - cx) ** 2 + (y - cy) ** 2 + (z - cz) ** 2 <= r ** 2:
                    set_block(x, y, z, block, arr)
    save_level(arr, path)


def make_hollow_sphere(cx, cy, cz, r, thickness=1, block=ROCK, path="level.dat"):
    arr    = load_level(path)
    r_out2 = r ** 2
    r_in2  = (r - thickness) ** 2
    for y in range(max(0, cy - r), min(HEIGHT, cy + r + 1)):
        for z in range(max(0, cz - r), min(DEPTH,  cz+r + 1)):
            for x in range(max(0, cx - r), min(WIDTH,  cx + r + 1)):
                d2 = (x - cx) ** 2 + (y - cy) ** 2 + (z - cz) ** 2
                if r_in2 < d2 <= r_out2:
                    set_block(x, y, z, block, arr)
    save_level(arr, path)


def make_torus(cx, cy, cz, R, r, block=ROCK, path="level.dat"):
    """
    Place a torus centred at (cx, cy, cz).
    R = distance from the torus centre to the tube centre.
    r = radius of the tube.
    """
    arr = load_level(path)
    for y in range(max(0, cy - r),   min(HEIGHT, cy + r + 1)):
        for z in range(max(0, cz - R - r), min(DEPTH,  cz + R + r + 1)):
            for x in range(max(0, cx - R - r), min(WIDTH,  cx + R + r + 1)):
                dist_xz = ((x - cx) ** 2 + (z - cz) ** 2) ** 0.5
                if (R - dist_xz) ** 2 + (y - cy) ** 2 <= r ** 2:
                    set_block(x, y, z, block, arr)
    save_level(arr, path)


def make_cylinder(cx, cz, y0, y1, r, block=ROCK, path="level.dat"):
    arr = load_level(path)
    for y in range(y0, y1):
        for z in range(max(0, cz - r), min(DEPTH, cz + r + 1)):
            for x in range(max(0, cx - r), min(WIDTH, cx + r + 1)):
                if (x - cx) ** 2 + (z - cz) ** 2 <= r ** 2:
                    set_block(x, y, z, block, arr)
    save_level(arr, path)


def make_cone(cx, cz, y_base, y_tip, base_r, block=ROCK, path="level.dat"):
    arr = load_level(path)
    height = y_tip - y_base
    if height == 0:
        return
    for y in range(min(y_base, y_tip), max(y_base, y_tip) + 1):
        t = (y - y_base) / height
        r = int(base_r * (1 - abs(t)))
        r = max(0, r)
        for z in range(max(0, cz - r), min(DEPTH, cz + r + 1)):
            for x in range(max(0, cx - r), min(WIDTH, cx + r + 1)):
                if (x - cx) ** 2 + (z - cz) ** 2 <= r ** 2:
                    set_block(x, y, z, block, arr)
    save_level(arr, path)


def make_pyramid(cx, cz, y_base, height, block=ROCK, path="level.dat"):
    arr = load_level(path)
    for dy in range(height):
        half = height - dy
        y    = y_base + dy
        if not (0 <= y < HEIGHT): continue
        for z in range(cz - half, cz + half + 1):
            for x in range(cx - half, cx + half + 1):
                if 0 <= x < WIDTH and 0 <= z < DEPTH:
                    set_block(x, y, z, block, arr)
    save_level(arr, path)

def make_shift_pyramid(cx, cz, y_base, height, path="level.dat"):
    arr = load_level(path)
    i = 1
    for dy in range(height):
        half = height - dy
        y    = y_base + dy
        if not (0 <= y < HEIGHT): continue
        for z in range(cz - half, cz + half + 1):
            for x in range(cx - half, cx + half + 1):
                if 0 <= x < WIDTH and 0 <= z < DEPTH:
                    set_block(x, y, z, i, arr)
                    i += 1
                    if (i >= 6):
                        i = 1
    save_level(arr, path)


def make_arch(cx, cy, cz, span, thickness, depth, block=ROCK, path="level.dat"):
    """
    Place a semicircular arch facing along the Z axis.
    span      = outer radius of the arch.
    thickness = wall thickness of the arch ring.
    depth     = how many blocks thick the arch is along Z.
    """
    arr   = load_level(path)
    r_out = span
    r_in  = span - thickness
    for z in range(cz, cz + depth):
        if not (0 <= z < DEPTH): continue
        for y in range(cy, cy + span + 1):
            if not (0 <= y < HEIGHT): continue
            for x in range(cx - span, cx + span + 1):
                if not (0 <= x < WIDTH): continue
                if y < cy: continue # only the upper semicircle
                d2 = (x - cx) ** 2 + (y - cy) ** 2
                if r_in ** 2 < d2 <= r_out ** 2:
                    set_block(x, y, z, block, arr)
    save_level(arr, path)


def make_helix(cx, cz, y0, y1, r, pitch, thickness=2, block=ROCK, path="level.dat"):
    """
    Place a heli1x coil from y0 to y1.
    r         = distance from axis to centre of tube.
    pitch     = vertical rise per full revolution (in blocks).
    thickness = cross-section r of the tube.
    """
    arr    = load_level(path)
    height = y1 - y0
    steps  = height * 8
    for step in range(steps):
        t     = step / steps
        angle = t * (height / pitch) * 2 * math.pi
        hx    = cx + int(r * math.cos(angle))
        hz    = cz + int(r * math.sin(angle))
        hy    = y0 + int(t * height)
        # fill a small sphere at each point along the path
        for dy in range(-thickness, thickness + 1):
            for dz in range(-thickness, thickness + 1):
                for dx in range(-thickness, thickness + 1):
                    if dx * dx + dy * dy + dz * dz <= thickness ** 2:
                        nx, ny, nz = hx + dx, hy + dy, hz + dz
                        if 0 <= nx < WIDTH and 0 <= ny < HEIGHT and 0 <= nz < DEPTH:
                            set_block(nx, ny, nz, block, arr)
    save_level(arr, path)


# ───────────────────────────────────────────────────────────────────
# 6. TERRAIN / PROCEDURAL SHAPES (Starts from an empty world!)
# ───────────────────────────────────────────────────────────────────

def checkerboard_world(block=ROCK, path="level.dat"):
    """
    Fill the world with a 1-block-tall XOR checkerboard at y=0.
    Every other column (by x^z parity) is filled with `block`.
    Starts from an empty world.
    """
    arr = bytearray(SIZE)
    for z in range(DEPTH):
        for x in range(WIDTH):
            if (x ^ z) & 1:
                set_block(x, 0, z, block, arr)
    save_level(arr, path)


def generate_sine_wave(amplitude=20, frequency=2, block=ROCK, path="level.dat"):
    """
    Generate a world whose height profile follows a sine wave along X.
    amplitude = maximum height of the wave (blocks).
    frequency = number of complete cycles across the full WIDTH.
    Starts from an empty world.
    """
    arr = bytearray(SIZE)
    for z in range(DEPTH):
        for x in range(WIDTH):
            sine_value = (math.sin((x / WIDTH) * frequency * 2 * math.pi) + 1) / 2
            y_max      = int(sine_value * amplitude)
            for y in range(y_max + 1):
                set_block(x, y, z, block, arr)
    save_level(arr, path)


def generate_ripple(center_x=128, center_z=128, max_height=20, wavelength=8,
                    decay=0.02, block=ROCK, path="level.dat"):
    """
    Generate a radial sine-wave ripple emanating from (center_x, center_z).
    The amplitude decays exponentially with distance.
    Starts from an empty world.
    """
    arr = bytearray(SIZE)
    for z in range(DEPTH):
        for x in range(WIDTH):
            dx       = x - center_x
            dz       = z - center_z
            distance = math.sqrt(dx*dx + dz*dz)
            y_max    = int(
                math.sin(distance / wavelength * 2 * math.pi)
                * max_height * math.exp(-decay * distance)
                + max_height / 2
            )
            y_max = max(0, min(HEIGHT - 1, y_max))
            for y in range(y_max + 1):
                set_block(x, y, z, block, arr)
    save_level(arr, path)


def generate_terrain(octaves=4, seed=1234, path="level.dat"):
    """
    Generate Perlin Noise terrain. Noise value in [-1, 1] is mapped to [0, HEIGHT-1].
    Starts from an empty world.
    """
    arr   = bytearray(SIZE)
    noise = PerlinNoise(octaves, seed)
    for z in range(DEPTH):
        for x in range(WIDTH):
            n     = noise([x / WIDTH, z / DEPTH])
            y_max = int((n + 1) / 2 * (HEIGHT - 1))
            for y in range(y_max + 1):
                set_block(x, y, z, GRASS, arr)
    save_level(arr, path)


def carve_torus_pedestal(cx, cy, cz, R, r, path="level.dat"):
    """
    Starting from the existing level, carve away everything that lies
    outside the footprint of a torus (cx,cy,cz) with major radius R and tube radius r.
    Starts from a populated world!
    """
    arr = load_level(path)
    for z in range(DEPTH):
        for x in range(WIDTH):
            dist_xz = ((x - cx) ** 2 + (z - cz) ** 2) ** 0.5
            if dist_xz > R + r or dist_xz < R - r:
                for y in range(HEIGHT):
                    set_block(x, y, z, AIR, arr)
            else:
                for y in range(HEIGHT):
                    if y <= cy:
                        if (R - dist_xz) ** 2 + (y - cy) ** 2 > r ** 2:
                            set_block(x, y, z, AIR, arr)
    save_level(arr, path)


# ───────────────────────────────────────────────────────────────────
# 7. IMAGE LAYER
# ───────────────────────────────────────────────────────────────────

# I coded this a quarter way through doing the pixel art to see
# if it was even worth my time pursuing, as it was going to take
# over ten hours total
def apply_image_layer(image_path, src_path="monpe.dat", dst_path="level.dat"):
    arr = load_level(src_path)
    img = Image.open(image_path)
    img_width, img_depth = img.size
    for z in range(img_width):
        for x in range(img_depth):
            r, g, b, a = img.getpixel((z, x))
            block = AIR if r == 0 else ROCK
            set_block(img_depth - 1 - x + 128, 0, img_width - 1 - z, block, arr)
    save_level(arr, dst_path)


if __name__ == '__main__':
    # put desired changes below
    convert_world()
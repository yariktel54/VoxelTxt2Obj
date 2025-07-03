import numpy as np

def read_cube_from_file(filename):
    with open(filename, 'r') as f:
        lines = [line.strip() for line in f if line.strip()]

    layer_size = len(lines[0].split())
    num_layers = len(lines) // layer_size

    cube = np.zeros((layer_size, layer_size, num_layers), dtype=int)

    for z in range(num_layers):
        print("Слой зчитаний: ", z)
        for y in range(layer_size):
            line = lines[z * layer_size + y]
            parts = line.split()
            for x, char in enumerate(parts):
                cube[x, y, z] = int(char)
    return cube

# === Генерація кубиків як mesh ===
def cube_to_obj_optimized(cube, filename="optimized.obj"):
    vertex_list = []
    face_list = []
    vertex_cache = {}
    vertex_index = 1

    def add_face(v0, v1, v2, v3):
        nonlocal vertex_index
        indices = []
        for vx, vy, vz in [v0, v1, v2, v3]:
            key = (vx, vy, vz)
            if key not in vertex_cache:
                vertex_cache[key] = vertex_index
                vertex_list.append(f"v {vx} {vy} {vz}")
                indices.append(vertex_index)
                vertex_index += 1
            else:
                indices.append(vertex_cache[key])
        face_list.append("f {} {} {} {}".format(*indices))

    sx, sy, sz = cube.shape

    for x in range(sx):
        for y in range(sy):
            for z in range(sz):
                if cube[x, y, z] == 0:
                    continue

                # LEFT (-X)
                if x == 0 or cube[x-1, y, z] == 0:
                    add_face((x, y, z), (x, y+1, z), (x, y+1, z+1), (x, y, z+1))

                # RIGHT (+X)
                if x == sx-1 or cube[x+1, y, z] == 0:
                    add_face((x+1, y, z), (x+1, y, z+1), (x+1, y+1, z+1), (x+1, y+1, z))

                # BOTTOM (-Y)
                if y == 0 or cube[x, y-1, z] == 0:
                    add_face((x, y, z), (x+1, y, z), (x+1, y, z+1), (x, y, z+1))

                # TOP (+Y)
                if y == sy-1 or cube[x, y+1, z] == 0:
                    add_face((x, y+1, z), (x, y+1, z+1), (x+1, y+1, z+1), (x+1, y+1, z))

                # BACK (-Z)
                if z == 0 or cube[x, y, z-1] == 0:
                    add_face((x, y, z), (x, y+1, z), (x+1, y+1, z), (x+1, y, z))

                # FRONT (+Z)
                if z == sz-1 or cube[x, y, z+1] == 0:
                    add_face((x, y, z+1), (x+1, y, z+1), (x+1, y+1, z+1), (x, y+1, z+1))

    with open(filename, "w") as f:
        f.write("\n".join(vertex_list))
        f.write("\n")
        f.write("\n".join(face_list))

    print(f"✅ Оптимізований OBJ збережено як: {filename}")
    print(f"🔢 Вершин: {len(vertex_list)} | Граней: {len(face_list)}")


# === Використання ===
cube = read_cube_from_file("3D 100.txt")
cube_to_obj_optimized(cube, "cube_model_optimized.obj")

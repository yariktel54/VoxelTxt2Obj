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
def cube_to_obj_streaming(cube, filename="optimized_streamed.obj", chunk_size=10):
    sx, sy, sz = cube.shape

    # Відкриваємо файл для запису
    with open(filename, "w") as f:
        vertex_cache = {}
        vertex_index = 1

        def add_vertex(v):
            nonlocal vertex_index
            if v not in vertex_cache:
                vertex_cache[v] = vertex_index
                f.write(f"v {v[0]} {v[1]} {v[2]}\n")
                vertex_index += 1
            return vertex_cache[v]

        def add_face(v0, v1, v2, v3):
            indices = [add_vertex(v) for v in [v0, v1, v2, v3]]
            f.write("f {} {} {} {}\n".format(*indices))

        # Проходимо по чанках по осі z (шари)
        for z_start in range(0, sz, chunk_size):
            z_end = min(z_start + chunk_size, sz)
            print(f"Обробка шарів з {z_start} по {z_end - 1}")

            for x in range(sx):
                for y in range(sy):
                    for z in range(z_start, z_end):
                        if cube[x, y, z] == 0:
                            continue

                        if x == 0 or cube[x-1, y, z] == 0:
                            add_face((x, y, z), (x, y, z+1), (x, y+1, z+1), (x, y+1, z))

                        if x == sx-1 or cube[x+1, y, z] == 0:
                            add_face((x+1, y, z), (x+1, y+1, z), (x+1, y+1, z+1), (x+1, y, z+1))

                        if x == 0 or cube[x-1, y, z] == 0:
                            add_face((x, y, z), (x, y+1, z), (x, y+1, z+1), (x, y, z+1))

                        if y == 0 or cube[x, y-1, z] == 0:
                            add_face((x, y, z), (x+1, y, z), (x+1, y, z+1), (x, y, z+1))

                        if y == sy-1 or cube[x, y+1, z] == 0:
                            add_face((x, y+1, z), (x, y+1, z+1), (x+1, y+1, z+1), (x+1, y+1, z))

                        if z == 0 or cube[x, y, z-1] == 0:
                            add_face((x, y, z), (x, y+1, z), (x+1, y+1, z), (x+1, y, z))

                        if z == sz-1 or cube[x, y, z+1] == 0:
                            add_face((x, y, z+1), (x+1, y, z+1), (x+1, y+1, z+1), (x, y+1, z+1))
                            
    print(f"✅ Оптимізований OBJ (streaming) збережено як: {filename}")


# === Використання ===
cube = read_cube_from_file("3D 600.txt")
cube_to_obj_streaming(cube, "cube_model_optimized_ram.obj")

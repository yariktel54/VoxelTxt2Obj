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
def cube_to_obj(cube, filename="output.obj"):
    vertex_list = []
    face_list = []
    vert_count = 0

    def add_cube(x, y, z):
        nonlocal vert_count

        # координати 8 вершин куба
        v = [
            (x, y, z),
            (x+1, y, z),
            (x+1, y+1, z),
            (x, y+1, z),
            (x, y, z+1),
            (x+1, y, z+1),
            (x+1, y+1, z+1),
            (x, y+1, z+1),
        ]

        # додаємо вершини
        for vx, vy, vz in v:
            vertex_list.append(f"v {vx} {vy} {vz}")

        # індекси вершин для кожної грані (нумерація з 1 в .obj)
        faces = [
            (0, 1, 2, 3),  # нижня
            (4, 5, 6, 7),  # верхня
            (0, 1, 5, 4),  # перед
            (2, 3, 7, 6),  # зад
            (1, 2, 6, 5),  # права
            (0, 3, 7, 4),  # ліва
        ]

        for f in faces:
            idx = [str(vert_count + i + 1) for i in f]
            face_list.append("f " + " ".join(idx))

        vert_count += 8

    prev_x = 0

    # === Генеруємо всі кубики ===
    for x, y, z in np.argwhere(cube == 1):
        add_cube(x, y, z)
        if prev_x != x:
            prev_x = x
            print("Доданий слой у 3Д модель: ", x)

    # === Запис у файл ===
    with open(filename, "w") as f:
        f.write("\n".join(vertex_list) + "\n" + "\n".join(face_list))

    print(f"✅ OBJ файл збережено як: {filename}")

# === Використання ===
cube = read_cube_from_file("3D 100.txt")
cube_to_obj(cube, "cube_model.obj")

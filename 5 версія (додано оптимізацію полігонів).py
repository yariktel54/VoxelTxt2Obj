import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import numpy as np

def read_cube_from_file(filename):
    with open(filename, 'r') as f:
        lines = [line.strip() for line in f if line.strip()]

    layer_size = len(lines[0].split())
    num_layers = len(lines) // layer_size

    cube = np.zeros((layer_size, layer_size, num_layers), dtype=int)

    for z in range(num_layers):
        for y in range(layer_size):
            line = lines[z * layer_size + y]
            parts = line.split()
            for x, char in enumerate(parts):
                cube[x, y, z] = int(char)
    return cube

def cube_to_obj_optimized_merge(cube, filename, progress_callback=None):
    sx, sy, sz = cube.shape

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

        # Функція пошуку максимальних прямокутників в бінарній матриці
        # Джерело ідеї: алгоритм "Largest Rectangle in a Binary Matrix"
        def find_rectangles(grid):
            rectangles = []
            rows, cols = len(grid), len(grid[0])
            height = [0] * cols

            for r in range(rows):
                stack = []
                for c in range(cols+1):
                    curr_height = height[c] if c < cols else 0
                    if c < cols and grid[r][c]:
                        height[c] += 1
                    else:
                        height[c] = 0

                    while stack and (c == cols or height[stack[-1]] > height[c]):
                        h = height[stack.pop()]
                        w = c if not stack else c - stack[-1] - 1
                        top_row = r - h + 1
                        left_col = stack[-1] + 1 if stack else 0
                        rectangles.append((top_row, left_col, r, c-1))
                    stack.append(c)
            return rectangles

        # Але цей алгоритм вимагає ускладнення, тому зробимо простіший підхід:
        # Пройдемось по кожному рядку, знайшовши всі послідовні ділянки True (1),
        # і зібравши їх у прямокутники зверху вниз.

        # Функція пошуку прямокутників у 2D бінарній матриці (спрощена)
        def merge_rectangles(grid):
            rows, cols = len(grid), len(grid[0])
            visited = [[False]*cols for _ in range(rows)]
            rects = []

            for r in range(rows):
                c = 0
                while c < cols:
                    if grid[r][c] and not visited[r][c]:
                        # знайти ширину прямокутника
                        width = 1
                        while c + width < cols and grid[r][c + width] and not visited[r][c + width]:
                            width += 1
                        # знайти висоту прямокутника
                        height = 1
                        done = False
                        while r + height < rows and not done:
                            for cc in range(c, c + width):
                                if not grid[r + height][cc] or visited[r + height][cc]:
                                    done = True
                                    break
                            if not done:
                                height += 1
                        # позначити прямокутник як відвіданий
                        for rr in range(r, r + height):
                            for cc in range(c, c + width):
                                visited[rr][cc] = True
                        rects.append((r, c, height, width))
                        c += width
                    else:
                        c += 1
            return rects

        # Генерація граней для кожної сторони
        # LEFT (-X)
        for x in range(sx):
            # 2D маска y,z
            grid = [[False]*sz for _ in range(sy)]
            for y in range(sy):
                for z in range(sz):
                    if cube[x, y, z] == 1 and (x == 0 or cube[x-1, y, z] == 0):
                        grid[y][z] = True
            rects = merge_rectangles(grid)
            for r, c, h, w in rects:
                # (x, y, z) - ліва грань, треба побудувати квадрат по прямокутнику (r,c,h,w)
                v0 = (x,     r,     c)
                v1 = (x,     r,     c + w)
                v2 = (x,     r + h, c + w)
                v3 = (x,     r + h, c)
                # Порядок вершин з врахуванням орієнтації (обернений як у тебе)
                add_face(v0, v1, v2, v3)

        # RIGHT (+X)
        for x in range(sx):
            grid = [[False]*sz for _ in range(sy)]
            for y in range(sy):
                for z in range(sz):
                    if cube[x, y, z] == 1 and (x == sx-1 or cube[x+1, y, z] == 0):
                        grid[y][z] = True
            rects = merge_rectangles(grid)
            for r, c, h, w in rects:
                v0 = (x+1, r,     c)
                v1 = (x+1, r + h, c)
                v2 = (x+1, r + h, c + w)
                v3 = (x+1, r,     c + w)
                add_face(v0, v1, v2, v3)

        # BOTTOM (-Y)
        for y in range(sy):
            grid = [[False]*sx for _ in range(sz)]
            for x in range(sx):
                for z in range(sz):
                    if cube[x, y, z] == 1 and (y == 0 or cube[x, y-1, z] == 0):
                        grid[z][x] = True
            rects = merge_rectangles(grid)
            for r, c, h, w in rects:
                v0 = (c,     y, r)
                v1 = (c + w, y, r)
                v2 = (c + w, y, r + h)
                v3 = (c,     y, r + h)
                add_face(v0, v1, v2, v3)

        # TOP (+Y)
        for y in range(sy):
            grid = [[False]*sx for _ in range(sz)]
            for x in range(sx):
                for z in range(sz):
                    if cube[x, y, z] == 1 and (y == sy-1 or cube[x, y+1, z] == 0):
                        grid[z][x] = True
            rects = merge_rectangles(grid)
            for r, c, h, w in rects:
                v0 = (c,     y+1, r)
                v1 = (c,     y+1, r + h)
                v2 = (c + w, y+1, r + h)
                v3 = (c + w, y+1, r)
                add_face(v0, v1, v2, v3)

        # BACK (-Z)
        for z in range(sz):
            grid = [[False]*sx for _ in range(sy)]
            for x in range(sx):
                for y in range(sy):
                    if cube[x, y, z] == 1 and (z == 0 or cube[x, y, z-1] == 0):
                        grid[y][x] = True
            rects = merge_rectangles(grid)
            for r, c, h, w in rects:
                v0 = (c,     r,     z)
                v1 = (c + w, r,     z)
                v2 = (c + w, r + h, z)
                v3 = (c,     r + h, z)
                add_face(v0, v3, v2, v1)

        # FRONT (+Z)
        for z in range(sz):
            grid = [[False]*sx for _ in range(sy)]
            for x in range(sx):
                for y in range(sy):
                    if cube[x, y, z] == 1 and (z == sz-1 or cube[x, y, z+1] == 0):
                        grid[y][x] = True
            rects = merge_rectangles(grid)
            for r, c, h, w in rects:
                v0 = (c,     r,     z+1)
                v1 = (c,     r + h, z+1)
                v2 = (c + w, r + h, z+1)
                v3 = (c + w, r,     z+1)
                add_face(v0, v3, v2, v1)

        if progress_callback:
            progress_callback("Готово!")


def start_conversion(filepath, chunk_size, progress_label, button):
    def task():
        try:
            progress_label.config(text="Зчитування файлу...")
            cube = read_cube_from_file(filepath)
            progress_label.config(text=f"Файл зчитано. Розмір куба: {cube.shape}")
            obj_filename = filepath.rsplit('.', 1)[0] + ".obj"
            progress_label.config(text="Початок генерації OBJ...")
            cube_to_obj_optimized_merge(cube, obj_filename, lambda msg: progress_label.config(text=msg))
            messagebox.showinfo("Готово", f"Файл збережено як:\n{obj_filename}")
        except Exception as e:
            messagebox.showerror("Помилка", str(e))
        finally:
            button.config(state=tk.NORMAL)

    button.config(state=tk.DISABLED)
    threading.Thread(target=task).start()

def browse_file(entry):
    filepath = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
    if filepath:
        entry.delete(0, tk.END)
        entry.insert(0, filepath)

def main():
    root = tk.Tk()
    root.title("Конвертер куба в OBJ (оптимізований)")

    tk.Label(root, text="Файл з кубом (.txt):").grid(row=0, column=0, sticky="w", padx=5, pady=5)
    entry_path = tk.Entry(root, width=50)
    entry_path.grid(row=0, column=1, padx=5, pady=5)
    btn_browse = tk.Button(root, text="Вибрати файл", command=lambda: browse_file(entry_path))
    btn_browse.grid(row=0, column=2, padx=5, pady=5)

    tk.Label(root, text="Розмір чанку:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
    entry_chunk = tk.Entry(root, width=10)
    entry_chunk.grid(row=1, column=1, sticky="w", padx=5, pady=5)
    entry_chunk.insert(0, "1")  # мінімальний за замовчуванням

    progress_label = tk.Label(root, text="Очікування...")
    progress_label.grid(row=2, column=0, columnspan=3, padx=5, pady=10)

    btn_start = tk.Button(root, text="Запустити конвертацію",
                          command=lambda: start_conversion(entry_path.get(), int(entry_chunk.get()), progress_label, btn_start))
    btn_start.grid(row=3, column=0, columnspan=3, pady=10)

    root.mainloop()

if __name__ == "__main__":
    main()

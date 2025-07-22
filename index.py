import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import numpy as np

def read_cube_from_file(filename, y_start=0, y_stop=None):
    with open(filename, 'r') as f:
        lines = [line.strip() for line in f if line.strip()]

    line_len = len(lines[0].split())
    total_lines = len(lines)
    total_layers = total_lines // line_len

    if y_start < 0 or y_start is None:
        y_start = 0
    if y_stop is None or y_stop > line_len:
        y_stop = line_len
    if y_stop <= y_start:
        raise ValueError("y_stop має бути більше за y_start")

    height = y_stop - y_start
    cube = np.zeros((line_len, height, total_layers), dtype=int)

    for z in range(total_layers):
        for y in range(y_start, y_stop):
            line = lines[z * line_len + y]
            parts = line.split()
            for x, char in enumerate(parts):
                cube[x, y - y_start, z] = int(char)
    return cube


def cube_to_obj_optimized_merge(cube, filename, progress_callback=None, invert=False):
    if invert:
        cube = 1 - cube

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

        def merge_rectangles(grid):
            rows, cols = len(grid), len(grid[0])
            visited = [[False]*cols for _ in range(rows)]
            rects = []

            for r in range(rows):
                c = 0
                while c < cols:
                    if grid[r][c] and not visited[r][c]:
                        width = 1
                        while c + width < cols and grid[r][c + width] and not visited[r][c + width]:
                            width += 1
                        height = 1
                        done = False
                        while r + height < rows and not done:
                            for cc in range(c, c + width):
                                if not grid[r + height][cc] or visited[r + height][cc]:
                                    done = True
                                    break
                            if not done:
                                height += 1
                        for rr in range(r, r + height):
                            for cc in range(c, c + width):
                                visited[rr][cc] = True
                        rects.append((r, c, height, width))
                        c += width
                    else:
                        c += 1
            return rects

        # Цикл по чанках по осі X (ліва/права)
        for x0 in range(0, sx, 1):
            x1 = min(x0 + 1, sx)
            for x in range(x0, x1):
                if progress_callback:
                    progress_callback(f"Генерація: X = {x+1}/{sx} (ліва грань)")
                # LEFT (-X)
                grid = [[False]*sz for _ in range(sy)]
                for y in range(sy):
                    for z in range(sz):
                        if cube[x, y, z] == 1 and (x == 0 or cube[x-1, y, z] == 0):
                            grid[y][z] = True
                rects = merge_rectangles(grid)
                for r, c, h, w in rects:
                    v0 = (x,     r,     c)
                    v1 = (x,     r,     c + w)
                    v2 = (x,     r + h, c + w)
                    v3 = (x,     r + h, c)
                    add_face(v0, v1, v2, v3)

                if progress_callback:
                    progress_callback(f"Генерація: X = {x+1}/{sx} (права грань)")
                # RIGHT (+X)
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

        # Чанки по осі Y (верх/низ)
        for y0 in range(0, sy, 1):
            y1 = min(y0 + 1, sy)
            for y in range(y0, y1):
                if progress_callback:
                    progress_callback(f"Генерація: Y = {y+1}/{sy} (нижня грань)")
                # BOTTOM (-Y)
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

                if progress_callback:
                    progress_callback(f"Генерація: Y = {y+1}/{sy} (верхня грань)")
                # TOP (+Y)
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

        # Чанки по осі Z (перед/зад)
        for z0 in range(0, sz, 1):
            z1 = min(z0 + 1, sz)
            for z in range(z0, z1):
                if progress_callback:
                    progress_callback(f"Генерація: Z = {z+1}/{sz} (задня грань)")
                # BACK (-Z)
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

                if progress_callback:
                    progress_callback(f"Генерація: Z = {z+1}/{sz} (передня грань)")
                # FRONT (+Z)
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

def start_conversion(filepath, y_start_raw, y_stop_raw, invert, progress_label, button):
    def task():
        try:
            try:
                y_start = int(y_start_raw) if y_start_raw.strip() else 0
            except ValueError:
                y_start = 0
            try:
                y_stop = int(y_stop_raw) if y_stop_raw.strip() else None
            except ValueError:
                y_stop = None

            progress_label.config(text="Зчитування файлу...")
            cube = read_cube_from_file(filepath, y_start=y_start, y_stop=y_stop)
            progress_label.config(text=f"Файл зчитано. Розмір куба: {cube.shape}")
            obj_filename = filepath.rsplit('.', 1)[0] + ".obj"
            progress_label.config(text="Початок генерації OBJ...")
            cube_to_obj_optimized_merge(cube, obj_filename, lambda msg: progress_label.config(text=msg), invert=invert)
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

    tk.Label(root, text="Початковий шар Y (опц.):").grid(row=1, column=0, sticky="w", padx=5, pady=5)
    entry_y_start = tk.Entry(root, width=10)
    entry_y_start.grid(row=1, column=1, sticky="w", padx=5, pady=5)

    tk.Label(root, text="Останній шар Y (опц.):").grid(row=2, column=0, sticky="w", padx=5, pady=5)
    entry_y_stop = tk.Entry(root, width=10)
    entry_y_stop.grid(row=2, column=1, sticky="w", padx=5, pady=5)

    invert_var = tk.BooleanVar()
    chk_invert = tk.Checkbutton(root, text="Інвертувати модель (показати пустоти)", variable=invert_var)
    chk_invert.grid(row=2, column=2, padx=5, pady=5)


    progress_label = tk.Label(root, text="Очікування...")
    progress_label.grid(row=2, column=0, columnspan=3, padx=5, pady=10)

    btn_start = tk.Button(root, text="Запустити конвертацію",
        command=lambda: start_conversion(
            entry_path.get(),
            entry_y_start.get(),
            entry_y_stop.get(),
            invert_var.get(),
            progress_label,
            btn_start
        )
    )
    btn_start.grid(row=3, column=0, columnspan=3, pady=10)

    root.mainloop()

if __name__ == "__main__":
    main()
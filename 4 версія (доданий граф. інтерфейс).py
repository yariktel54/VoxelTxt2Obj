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

def cube_to_obj_streaming(cube, filename, chunk_size, progress_callback=None):
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

        for z_start in range(0, sz, chunk_size):
            z_end = min(z_start + chunk_size, sz)

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

            if progress_callback:
                progress_callback(f"Оброблено шарів: {z_end} / {sz}")

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
            cube_to_obj_streaming(cube, obj_filename, chunk_size, lambda msg: progress_label.config(text=msg))
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

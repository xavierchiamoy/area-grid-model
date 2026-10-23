import time

from PIL import ImageGrab

from area_grid_app import AreaGridApp
import tkinter as tk


root = tk.Tk()
app = AreaGridApp(root)
root.geometry("1600x860+0+0")
root.attributes("-topmost", True)
root.update()
time.sleep(0.4)
root.update()

outer = root.winfo_children()[0]
for widget in outer.winfo_children()[:4]:
    widget.pack_forget()
root.update()
time.sleep(0.15)
root.update()
app.redraw()
root.update()

x = app.canvas.winfo_rootx()
y = app.canvas.winfo_rooty()
width = app.canvas.winfo_width()
height = app.canvas.winfo_height()
ImageGrab.grab(bbox=(x, y, x + width, y + height)).save("preview.png")
ImageGrab.grab(bbox=(x + int(width * 0.55), y, x + width, y + height)).save(
    "preview_right.png"
)

app.toggle_row(1)
root.update()
time.sleep(0.08)
root.update()
app.redraw()
root.update()
ImageGrab.grab(bbox=(x, y, x + width, y + height)).save("preview_selected.png")
ImageGrab.grab(bbox=(x + int(width * 0.55), y, x + width, y + height)).save(
    "preview_selected_right.png"
)
root.destroy()

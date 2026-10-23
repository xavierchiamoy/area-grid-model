from __future__ import annotations

import re
import tkinter as tk
from dataclasses import dataclass
from tkinter import filedialog, messagebox, ttk
from typing import Optional


APP_TITLE = "格子面积模型"
BG = "#F5F7FB"
CARD = "#FFFFFF"
TEXT = "#172033"
MUTED = "#667085"
ACCENT = "#4F46E5"
GRID = "#586174"
ROW_COLORS = (
    "#F8C56B",
    "#72B7F2",
    "#8ED6B0",
    "#D7A9F3",
    "#F39A9A",
    "#86D8D8",
)
ROW_ARROW_COLORS = ("#C96A10", "#2563EB", "#23845A", "#8B5BB5")


@dataclass(frozen=True)
class AreaModel:
    total_width: int
    total_height: int
    width_parts: tuple[int, ...]
    height_parts: tuple[int, ...]
    display_expression: str


class FormulaError(ValueError):
    pass


def normalize_expression(expression: str) -> str:
    table = str.maketrans(
        {
            "X": "×",
            "x": "×",
            "*": "×",
            "＋": "+",
            "＝": "=",
            "（": "(",
            "）": ")",
        }
    )
    return re.sub(r"\s+", "", expression.translate(table))


def parse_factor(text: str) -> tuple[int, ...]:
    text = text.strip()
    if text.startswith("(") and text.endswith(")"):
        text = text[1:-1]
    if not text:
        raise FormulaError("括号里需要填写数字。")
    values = text.split("+")
    if any(not re.fullmatch(r"\d+", value) for value in values):
        raise FormulaError("每个长度都要是正整数，例如 10+6。")
    numbers = tuple(int(value) for value in values)
    if any(number <= 0 for number in numbers):
        raise FormulaError("长度必须大于 0。")
    return numbers


def auto_split_number(number: int) -> tuple[int, ...]:
    """Split 16 into 10+6 while keeping single digits and exact tens intact."""
    ones = number % 10
    tens_part = number - ones
    if tens_part > 0 and ones > 0:
        return tens_part, ones
    return (number,)


def split_product(text: str) -> tuple[str, str]:
    depth = 0
    positions: list[int] = []
    for index, char in enumerate(text):
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth < 0:
                raise FormulaError("括号没有正确配对。")
        elif char == "×" and depth == 0:
            positions.append(index)
    if depth != 0:
        raise FormulaError("括号没有正确配对。")
    if len(positions) != 1:
        raise FormulaError("请用一个乘号连接长和宽，例如 (10+6)×(10+2)。")
    position = positions[0]
    return text[:position], text[position + 1 :]


def parse_expression(expression: str) -> AreaModel:
    normalized = normalize_expression(expression)
    if not normalized:
        raise FormulaError("请先输入一个算式。")

    if normalized.count("=") > 1:
        raise FormulaError("算式中只能有一个等号。")

    left = ""
    right = normalized
    if "=" in normalized:
        left, right = normalized.split("=", 1)

    right_width, right_height = split_product(right)
    width_parts = parse_factor(right_width)
    height_parts = parse_factor(right_height)
    if len(width_parts) == 1:
        width_parts = auto_split_number(width_parts[0])
    if len(height_parts) == 1:
        height_parts = auto_split_number(height_parts[0])
    total_width = sum(width_parts)
    total_height = sum(height_parts)

    if left:
        left_width_text, left_height_text = split_product(left)
        left_width_parts = parse_factor(left_width_text)
        left_height_parts = parse_factor(left_height_text)
        if len(left_width_parts) != 1 or len(left_height_parts) != 1:
            raise FormulaError("等号左边请写总长×总宽，例如 16×12。")
        expected_width = left_width_parts[0]
        expected_height = left_height_parts[0]
        if (expected_width, expected_height) != (total_width, total_height):
            raise FormulaError(
                f"等号两边不相等：右边得到 {total_width}×{total_height}，"
                f"不是 {expected_width}×{expected_height}。"
            )

    if total_width > 200 or total_height > 200:
        raise FormulaError("为了让格子保持清楚，长和宽暂时不能超过 200。")

    return AreaModel(
        total_width,
        total_height,
        width_parts,
        height_parts,
        f"{total_width}×{total_height}",
    )


def piece_terms(model: AreaModel) -> list[tuple[int, int, int]]:
    return [
        (width, height, width * height)
        for height in model.height_parts
        for width in model.width_parts
    ]


def vertical_steps(model: AreaModel) -> list[tuple[int, int, int]]:
    """Return (row index, multiplier part, partial product) in calculation order."""
    return [
        (row, model.height_parts[row], model.total_width * model.height_parts[row])
        for row in reversed(range(len(model.height_parts)))
    ]


def group_expression(model: AreaModel, row: int) -> str:
    height = model.height_parts[row]
    return "＋".join(f"（{width}×{height}）" for width in model.width_parts)


class AreaGridApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("1180x860")
        self.root.minsize(1000, 760)
        self.root.configure(bg=BG)

        self.model: Optional[AreaModel] = None
        self.active_row: Optional[int] = None
        self.row_buttons: list[ttk.Button] = []
        self.button_rows: list[int] = []
        self.redraw_job: Optional[str] = None

        self._configure_styles()
        self._build_ui()
        self.expression_var.set("16×12")
        self.generate()

    def _configure_styles(self) -> None:
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TFrame", background=BG)
        style.configure("Card.TFrame", background=CARD)
        style.configure(
            "Title.TLabel",
            background=BG,
            foreground=TEXT,
            font=("Microsoft YaHei UI", 22, "bold"),
        )
        style.configure(
            "Subtitle.TLabel",
            background=BG,
            foreground=MUTED,
            font=("Microsoft YaHei UI", 10),
        )
        style.configure(
            "CardTitle.TLabel",
            background=CARD,
            foreground=TEXT,
            font=("Microsoft YaHei UI", 12, "bold"),
        )
        style.configure(
            "Body.TLabel",
            background=CARD,
            foreground=TEXT,
            font=("Microsoft YaHei UI", 10),
        )
        style.configure(
            "Muted.TLabel",
            background=CARD,
            foreground=MUTED,
            font=("Microsoft YaHei UI", 9),
        )
        style.configure(
            "Accent.TButton",
            font=("Microsoft YaHei UI", 10, "bold"),
            foreground="white",
            background=ACCENT,
            padding=(16, 9),
        )
        style.map("Accent.TButton", background=[("active", "#4338CA")])
        style.configure(
            "Toggle.TButton",
            font=("Microsoft YaHei UI", 9),
            padding=(10, 8),
        )

    def _build_ui(self) -> None:
        outer = ttk.Frame(self.root, padding=(24, 18, 24, 22))
        outer.pack(fill="both", expand=True)

        ttk.Label(outer, text=APP_TITLE, style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            outer,
            text="输入乘法分配律算式，立即生成可切分、可突出显示的格子面积图",
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(2, 14))

        input_card = ttk.Frame(outer, style="Card.TFrame", padding=14)
        input_card.pack(fill="x", pady=(0, 14))
        input_card.columnconfigure(0, weight=1)

        self.expression_var = tk.StringVar()
        entry = ttk.Entry(
            input_card,
            textvariable=self.expression_var,
            font=("Microsoft YaHei UI", 14),
        )
        entry.grid(row=0, column=0, sticky="ew", padx=(0, 10), ipady=7)
        entry.bind("<Return>", lambda _event: self.generate())
        ttk.Button(
            input_card,
            text="生成格子图",
            style="Accent.TButton",
            command=self.generate,
        ).grid(row=0, column=1)
        ttk.Label(
            input_card,
            text="示例：输入 16×12，直接得到面积结果和格子图　也支持 *、x、X",
            style="Muted.TLabel",
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(8, 0))

        result_card = ttk.Frame(outer, style="Card.TFrame", padding=(16, 12))
        result_card.pack(fill="x", pady=(0, 14))
        self.result_var = tk.StringVar()
        tk.Label(
            result_card,
            textvariable=self.result_var,
            bg=CARD,
            fg=ACCENT,
            font=("Microsoft YaHei UI", 18, "bold"),
            anchor="center",
        ).pack(fill="x")

        content = ttk.Frame(outer)
        content.pack(fill="both", expand=True)
        content.columnconfigure(0, weight=1)
        content.rowconfigure(0, weight=1)

        canvas_card = ttk.Frame(content, style="Card.TFrame", padding=12)
        canvas_card.grid(row=0, column=0, sticky="nsew")
        canvas_card.rowconfigure(1, weight=1)
        canvas_card.columnconfigure(0, weight=1)

        toolbar = ttk.Frame(canvas_card, style="Card.TFrame")
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        ttk.Label(
            toolbar,
            text="面积格子图与竖式计算",
            style="CardTitle.TLabel",
        ).pack(side="left")
        ttk.Button(toolbar, text="保存为图片", command=self.save_image).pack(side="right")

        self.canvas = tk.Canvas(
            canvas_card,
            bg="#FBFCFE",
            height=430,
            highlightthickness=1,
            highlightbackground="#E1E5ED",
        )
        self.canvas.grid(row=1, column=0, sticky="nsew")
        self.canvas.bind("<Configure>", self._schedule_redraw)

        controls = ttk.Frame(canvas_card, style="Card.TFrame")
        controls.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        controls.columnconfigure(0, weight=1)
        controls.columnconfigure(1, weight=1)

        ttk.Label(controls, text="分组查看", style="CardTitle.TLabel").grid(
            row=0, column=0, sticky="w", padx=(0, 16)
        )
        ttk.Label(
            controls,
            text="点击某一行，只显示这一行的面积块；再次点击即可恢复全部。",
            style="Muted.TLabel",
            wraplength=520,
            justify="left",
        ).grid(row=1, column=0, sticky="ew", padx=(0, 16), pady=(5, 9))

        self.toggle_frame = ttk.Frame(controls, style="Card.TFrame")
        self.toggle_frame.grid(row=2, column=0, sticky="ew", padx=(0, 16))
        self.toggle_frame.columnconfigure(0, weight=1)

        ttk.Label(controls, text="图例", style="CardTitle.TLabel").grid(
            row=0, column=1, sticky="w"
        )
        self.legend_frame = ttk.Frame(controls, style="Card.TFrame")
        self.legend_frame.grid(row=1, column=1, rowspan=2, sticky="nw", pady=(8, 0))

    def generate(self) -> None:
        try:
            model = parse_expression(self.expression_var.get())
        except FormulaError as exc:
            messagebox.showerror("算式有问题", str(exc), parent=self.root)
            return

        self.model = model
        self.active_row = None
        self.expression_var.set(model.display_expression)
        self._update_explanation()
        self._build_toggle_buttons()
        self._build_legend()
        self.redraw()

    def _update_explanation(self) -> None:
        if self.model is None:
            return
        model = self.model
        total = model.total_width * model.total_height
        self.result_var.set(
            f"{model.total_width}×{model.total_height} = {total}"
        )

    def _build_toggle_buttons(self) -> None:
        for child in self.toggle_frame.winfo_children():
            child.destroy()
        self.row_buttons.clear()
        self.button_rows.clear()
        if self.model is None:
            return

        for button_index, row in enumerate(reversed(range(len(self.model.height_parts)))):
            expression = group_expression(self.model, row)
            button = ttk.Button(
                self.toggle_frame,
                text=f"只显示 {expression}",
                style="Toggle.TButton",
                command=lambda value=row: self.toggle_row(value),
            )
            button.grid(row=button_index, column=0, sticky="ew", pady=3)
            self.row_buttons.append(button)
            self.button_rows.append(row)

    def _refresh_toggle_labels(self) -> None:
        if self.model is None:
            return
        for button, row in zip(self.row_buttons, self.button_rows):
            expression = group_expression(self.model, row)
            if self.active_row == row:
                button.configure(text="恢复显示全部")
            else:
                button.configure(text=f"只显示 {expression}")

    def _build_legend(self) -> None:
        for child in self.legend_frame.winfo_children():
            child.destroy()
        if self.model is None:
            return
        for row, height in enumerate(self.model.height_parts):
            color = ROW_COLORS[row % len(ROW_COLORS)]
            swatch = tk.Canvas(
                self.legend_frame,
                width=18,
                height=18,
                bg=CARD,
                highlightthickness=0,
            )
            swatch.grid(row=row, column=0, padx=(0, 7), pady=3)
            swatch.create_rectangle(2, 2, 16, 16, fill=color, outline="")
            text = "、".join(f"{width}×{height}" for width in self.model.width_parts)
            ttk.Label(self.legend_frame, text=text, style="Body.TLabel").grid(
                row=row, column=1, sticky="w", pady=3
            )

    def toggle_row(self, row: int) -> None:
        self.active_row = None if self.active_row == row else row
        self._refresh_toggle_labels()
        self.redraw()

    def _schedule_redraw(self, _event: tk.Event) -> None:
        if self.redraw_job:
            self.root.after_cancel(self.redraw_job)
        self.redraw_job = self.root.after(50, self.redraw)

    def redraw(self) -> None:
        self.redraw_job = None
        self.canvas.delete("all")
        if self.model is None:
            return

        model = self.model
        canvas_width = max(self.canvas.winfo_width(), 200)
        canvas_height = max(self.canvas.winfo_height(), 200)
        margin_left = 58
        margin_top = 48
        margin_bottom = 66
        graph_area_right = max(canvas_width * 0.56, margin_left + 240)
        usable_width = max(graph_area_right - margin_left - 28, 100)
        usable_height = max(canvas_height - margin_top - margin_bottom, 100)
        cell = min(usable_width / model.total_width, usable_height / model.total_height)
        cell = max(cell, 2.0)
        graph_width = cell * model.total_width
        graph_height = cell * model.total_height
        x0 = margin_left + max((usable_width - graph_width) / 2, 0)
        y0 = margin_top + (usable_height - graph_height) / 2
        x1 = x0 + graph_width
        y1 = y0 + graph_height

        self.canvas.create_text(
            (x0 + x1) / 2,
            20,
            text=f"总长度 {model.total_width}",
            fill=MUTED,
            font=("Microsoft YaHei UI", 10, "bold"),
        )
        self.canvas.create_text(
            22,
            (y0 + y1) / 2,
            text=f"总\n宽\n度\n{model.total_height}",
            fill=MUTED,
            font=("Microsoft YaHei UI", 9, "bold"),
            justify="center",
        )

        row_centers: dict[int, float] = {}
        # Heights are displayed bottom-to-top so the ones strip is at the top.
        y_cursor = y1
        for row, height in enumerate(model.height_parts):
            rect_y1 = y_cursor
            rect_y0 = rect_y1 - height * cell
            row_centers[row] = (rect_y0 + rect_y1) / 2
            visible = self.active_row is None or self.active_row == row
            x_cursor = x0
            for width in model.width_parts:
                rect_x0 = x_cursor
                rect_x1 = rect_x0 + width * cell
                if visible:
                    self._draw_piece(
                        rect_x0,
                        rect_y0,
                        rect_x1,
                        rect_y1,
                        width,
                        height,
                        cell,
                        ROW_COLORS[row % len(ROW_COLORS)],
                    )
                x_cursor = rect_x1
            y_cursor = rect_y0

        self.canvas.create_rectangle(x0, y0, x1, y1, outline=TEXT, width=3)

        x_cursor = x0
        for width in model.width_parts:
            segment_x1 = x_cursor + width * cell
            self.canvas.create_text(
                (x_cursor + segment_x1) / 2,
                y1 + 23,
                text=str(width),
                fill=TEXT,
                font=("Microsoft YaHei UI", 10, "bold"),
            )
            x_cursor = segment_x1

        y_cursor = y1
        for height in model.height_parts:
            segment_y0 = y_cursor - height * cell
            self.canvas.create_text(
                x0 - 25,
                (segment_y0 + y_cursor) / 2,
                text=str(height),
                fill=TEXT,
                font=("Microsoft YaHei UI", 10, "bold"),
            )
            y_cursor = segment_y0

        if self.active_row is not None:
            active_height = model.height_parts[self.active_row]
            self.canvas.create_text(
                (x0 + x1) / 2,
                y1 + 48,
                text=f"当前只显示宽度为 {active_height} 的一行",
                fill=ACCENT,
                font=("Microsoft YaHei UI", 9, "bold"),
            )

        calculation_left = max(graph_area_right + 20, x1 + 45)
        calculation_right = canvas_width - 22
        if calculation_right - calculation_left >= 190:
            self._draw_vertical_calculation(
                calculation_left,
                calculation_right,
                row_centers,
                x1,
            )

    def _draw_vertical_calculation(
        self,
        calculation_left: float,
        calculation_right: float,
        row_centers: dict[int, float],
        graph_right: float,
    ) -> None:
        if self.model is None:
            return

        model = self.model
        calculation_center = (calculation_left + calculation_right) / 2
        number_right = calculation_right - 30
        line_left = number_right - 105
        line_right = number_right + 4
        top = 44
        number_font = ("Consolas", 22, "bold")
        result_font = ("Consolas", 20, "bold")

        self.canvas.create_text(
            calculation_center,
            20,
            text="竖式计算",
            fill=TEXT,
            font=("Microsoft YaHei UI", 12, "bold"),
        )
        self.canvas.create_text(
            number_right,
            top + 20,
            text=str(model.total_width),
            anchor="e",
            fill=TEXT,
            font=number_font,
        )
        self.canvas.create_text(
            number_right,
            top + 59,
            text=f"× {model.total_height}",
            anchor="e",
            fill=TEXT,
            font=number_font,
        )
        self.canvas.create_line(
            line_left,
            top + 82,
            line_right,
            top + 82,
            fill=TEXT,
            width=2,
        )

        steps = vertical_steps(model)
        product_items: dict[int, tuple[int, float]] = {}
        first_product_y = top + 116
        step_gap = 52
        for step_index, (row, height, product) in enumerate(steps):
            product_y = first_product_y + step_index * step_gap
            item = self.canvas.create_text(
                number_right,
                product_y,
                text=str(product),
                anchor="e",
                fill=ROW_ARROW_COLORS[row % len(ROW_ARROW_COLORS)],
                font=result_font,
            )
            product_items[row] = (item, product_y)

        final_line_y = first_product_y + len(steps) * step_gap - 22
        self.canvas.create_line(
            line_left,
            final_line_y,
            line_right,
            final_line_y,
            fill=TEXT,
            width=2,
        )
        self.canvas.create_text(
            number_right,
            final_line_y + 27,
            text=str(model.total_width * model.total_height),
            anchor="e",
            fill=ACCENT,
            font=("Consolas", 22, "bold"),
        )

        for row, (item, product_y) in product_items.items():
            if row not in row_centers:
                continue
            color = ROW_ARROW_COLORS[row % len(ROW_ARROW_COLORS)]
            selected = self.active_row is None or self.active_row == row
            line_color = color if selected else "#C9CED8"
            line_width = 3 if self.active_row == row else 2
            dash = None if selected else (5, 4)
            product_bbox = self.canvas.bbox(item)
            arrow_start_x = (
                product_bbox[0] - 14 if product_bbox else calculation_left + 23
            )
            elbow_x = graph_right + 28
            self.canvas.create_line(
                arrow_start_x,
                product_y,
                elbow_x,
                product_y,
                graph_right + 5,
                row_centers[row],
                fill=line_color,
                width=line_width,
                dash=dash,
                arrow=tk.LAST,
                arrowshape=(10, 12, 5),
            )

        if self.active_row in product_items:
            item, _product_y = product_items[self.active_row]
            bbox = self.canvas.bbox(item)
            if bbox:
                self.canvas.create_oval(
                    bbox[0] - 12,
                    bbox[1] - 7,
                    bbox[2] + 12,
                    bbox[3] + 7,
                    outline=ROW_ARROW_COLORS[self.active_row % len(ROW_ARROW_COLORS)],
                    width=4,
                )

    def _draw_piece(
        self,
        x0: float,
        y0: float,
        x1: float,
        y1: float,
        width: int,
        height: int,
        cell: float,
        color: str,
    ) -> None:
        self.canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline=TEXT, width=2)

        grid_width = 1 if cell >= 8 else 0
        if grid_width:
            for unit in range(1, width):
                x = x0 + unit * cell
                self.canvas.create_line(x, y0, x, y1, fill=GRID, width=grid_width)
            for unit in range(1, height):
                y = y0 + unit * cell
                self.canvas.create_line(x0, y, x1, y, fill=GRID, width=grid_width)

        area = width * height
        pixel_width = x1 - x0
        pixel_height = y1 - y0
        if pixel_width >= 72 and pixel_height >= 42:
            font_size = max(8, min(14, int(min(pixel_width / 9, pixel_height / 4))))
            self.canvas.create_text(
                (x0 + x1) / 2,
                (y0 + y1) / 2,
                text=f"{width}×{height}\n= {area}",
                fill=TEXT,
                font=("Microsoft YaHei UI", font_size, "bold"),
                justify="center",
            )
        elif pixel_width >= 36 and pixel_height >= 22:
            self.canvas.create_text(
                (x0 + x1) / 2,
                (y0 + y1) / 2,
                text=f"{width}×{height}",
                fill=TEXT,
                font=("Microsoft YaHei UI", 8, "bold"),
            )

    def save_image(self) -> None:
        if self.model is None:
            return
        filename = filedialog.asksaveasfilename(
            parent=self.root,
            title="保存格子图",
            defaultextension=".png",
            filetypes=[("PNG 图片", "*.png")],
            initialfile="面积格子图.png",
        )
        if not filename:
            return

        try:
            from PIL import Image, ImageGrab

            self.root.update_idletasks()
            x = self.canvas.winfo_rootx()
            y = self.canvas.winfo_rooty()
            width = self.canvas.winfo_width()
            height = self.canvas.winfo_height()
            image = ImageGrab.grab(bbox=(x, y, x + width, y + height))
            if image.mode != "RGB":
                image = image.convert("RGB")
            image.save(filename, format="PNG")
        except Exception as exc:
            messagebox.showerror("保存失败", f"图片没有保存成功：\n{exc}", parent=self.root)
            return
        messagebox.showinfo("保存成功", "格子图已经保存。", parent=self.root)


def main() -> None:
    root = tk.Tk()
    AreaGridApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

from PIL import Image, ImageDraw


size = 256
image = Image.new("RGBA", (size, size), "#F5F7FB")
draw = ImageDraw.Draw(image)

left, top, right, bottom = 27, 27, 229, 229
split_x = 154
split_y = 77
draw.rounded_rectangle((14, 14, 242, 242), radius=42, fill="#4F46E5")
draw.rectangle((left, top, split_x, split_y), fill="#72B7F2")
draw.rectangle((split_x, top, right, split_y), fill="#72B7F2")
draw.rectangle((left, split_y, split_x, bottom), fill="#F8C56B")
draw.rectangle((split_x, split_y, right, bottom), fill="#F8C56B")

for x in range(left, right + 1, 25):
    draw.line((x, top, x, bottom), fill="#172033", width=3)
for y in range(top, bottom + 1, 25):
    draw.line((left, y, right, y), fill="#172033", width=3)
draw.line((split_x, top, split_x, bottom), fill="#172033", width=6)
draw.line((left, split_y, right, split_y), fill="#172033", width=6)
draw.rectangle((left, top, right, bottom), outline="#172033", width=7)

image.save("area_grid.ico", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])

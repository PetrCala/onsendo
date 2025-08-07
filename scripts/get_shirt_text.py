import os
from PIL import Image, ImageDraw, ImageFont

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
font_mapping = {
    "YujiMai-Regular": "YujiMai-Regular.ttf",
    "YujiBoku-Regular": "YujiBoku-Regular.ttf",
    "NotoSerifJP-Regular": "NotoSerifJP-Regular.ttf",
}

# === SETTINGS ===
text = "一\n山\n百\n楽"  # vertical stacking with line breaks
font_size = 400  # Increased resolution for higher quality
output_file = os.path.join(project_root, "output", "shirt", "shirt_text.png")

# === SELECT FONT ===
print("Available fonts:")
for i, (name, filename) in enumerate(font_mapping.items(), 1):
    print(f"{i}. {name} ({filename})")
choice = input("Enter the number or name of the font to use: ").strip()

if choice.isdigit():
    idx = int(choice) - 1
    if 0 <= idx < len(font_mapping):
        font_path = list(font_mapping.values())[idx]
    else:
        print("Invalid selection. Using default font.")
        font_path = "YujiMai-Regular.ttf"
else:
    # Try to match by name
    if choice in font_mapping:
        font_path = font_mapping[choice]
    else:
        print("Invalid selection. Using default font.")
        font_path = "YujiMai-Regular.ttf"

font_path = os.path.join(project_root, "data", "fonts", font_path)

# === CREATE IMAGE ===
# Load font
font = ImageFont.truetype(font_path, font_size)

# Measure text size with reduced spacing
dummy_img = Image.new("RGBA", (1, 1), (255, 255, 255, 0))
draw = ImageDraw.Draw(dummy_img)
spacing = 20  # Increased spacing proportionally with font size
bbox = draw.textbbox((0, 0), text, font=font, spacing=spacing, align="center")
text_width = int(bbox[2] - bbox[0])
text_height = int(bbox[3] - bbox[1])

# Add top padding to move the first character down
top_padding = 0  # Adjust this value to move the text down more or less
final_width = text_width
final_height = text_height + top_padding

# Create final image with transparent background
image = Image.new("RGBA", (final_width, final_height), (255, 255, 255, 0))
draw = ImageDraw.Draw(image)

# Draw text in black, adjusting position to remove extra space and add top padding
# Start at the top of the actual text content, not the font's baseline, plus padding
draw.multiline_text(
    (-bbox[0], -bbox[1] + top_padding),
    text,
    font=font,
    fill=(0, 0, 0, 255),
    spacing=spacing,
    align="center",
)

# === SAVE IMAGE ===
if not os.path.exists(os.path.dirname(output_file)):
    os.makedirs(os.path.dirname(output_file))
image.save(output_file, "PNG")

print(f"Saved {output_file} successfully!")

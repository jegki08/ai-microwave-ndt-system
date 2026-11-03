import os
import shutil

src_dir = r"C:\Users\LENOVO\.gemini\antigravity\brain\4fde4e1e-ec54-4644-92ae-b8ffb7021c00\.user_uploaded"
dest_dir = r"c:\Users\LENOVO\Downloads\microwave_ndt_2day_prototype\microwave_ndt_prototype\presentation_images"

# List png files
files = [f for f in os.listdir(src_dir) if f.endswith('.png')]
for f in files:
    src_path = os.path.join(src_dir, f)
    size = os.path.getsize(src_path)
    print(f"{f}: {size} bytes")

# Copy the latest dashboard screenshots
if files:
    # sort by mtime
    files.sort(key=lambda x: os.path.getmtime(os.path.join(src_dir, x)))
    shutil.copy(os.path.join(src_dir, files[-1]), os.path.join(dest_dir, "ui_screenshot_latest.png"))
    shutil.copy(os.path.join(src_dir, files[-2]), os.path.join(dest_dir, "ui_screenshot_2.png"))
    if len(files) >= 3:
        shutil.copy(os.path.join(src_dir, files[-3]), os.path.join(dest_dir, "ui_screenshot_3.png"))
    print("Copied UI screenshots successfully.")

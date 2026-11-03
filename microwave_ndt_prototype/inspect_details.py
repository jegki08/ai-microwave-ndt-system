import pptx

sample_path = r"C:\Users\LENOVO\.gemini\antigravity\brain\4fde4e1e-ec54-4644-92ae-b8ffb7021c00\.user_uploaded\media_1793456791123_d52cff05.pptx"
prs = pptx.Presentation(sample_path)

print("=== SLIDE 1 TEXT ===")
for shape in prs.slides[0].shapes:
    if shape.has_text_frame:
        print(shape.text)

print("\n=== SLIDE 9 & 10 (LITERATURE SURVEY) ===")
for s_num in [8, 9]:
    slide = prs.slides[s_num]
    print(f"Slide {s_num+1} shapes count:", len(slide.shapes))
    for shape in slide.shapes:
        if shape.has_table:
            print(f"  Table found: {len(shape.table.rows)} rows, {len(shape.table.columns)} cols")
            for r in shape.table.rows:
                row_txt = [c.text.strip().replace('\n', ' ') for c in r.cells]
                print("   ", " | ".join(row_txt))
        elif shape.has_text_frame:
            print("   Text:", shape.text[:100])

print("\n=== SLIDE 18 (DATAFLOW) & 19 (ARCHITECTURE) ===")
for s_num in [17, 18]:
    slide = prs.slides[s_num]
    print(f"Slide {s_num+1} shapes:")
    for shape in slide.shapes:
        print(f"   Shape: {shape.name}, type: {shape.shape_type}")

print("\n=== SLIDE 22-27 (SCREENSHOTS) ===")
for s_num in range(21, 27):
    slide = prs.slides[s_num]
    print(f"Slide {s_num+1} shapes:")
    for shape in slide.shapes:
        print(f"   Shape: {shape.name}, type: {shape.shape_type}")
        if shape.has_text_frame and shape.text.strip():
            print(f"      Text: {shape.text.strip()}")

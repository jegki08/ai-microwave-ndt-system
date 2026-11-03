import pptx

sample_path = r"C:\Users\LENOVO\.gemini\antigravity\brain\4fde4e1e-ec54-4644-92ae-b8ffb7021c00\.user_uploaded\media_1793456791123_d52cff05.pptx"
prs = pptx.Presentation(sample_path)
print(f"Total slides: {len(prs.slides)}")

for i, slide in enumerate(prs.slides):
    print(f"\n--- SLIDE {i+1} ---")
    for s_idx, shape in enumerate(slide.shapes):
        if shape.has_text_frame:
            text = shape.text.strip().replace("\n", " | ")
            if text:
                print(f"  Shape {s_idx} ({shape.name}): {text[:150]}")

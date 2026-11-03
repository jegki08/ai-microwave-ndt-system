import pptx

sample_path = r"C:\Users\LENOVO\.gemini\antigravity\brain\4fde4e1e-ec54-4644-92ae-b8ffb7021c00\.user_uploaded\media_1793456791123_d52cff05.pptx"
prs = pptx.Presentation(sample_path)

for i, slide in enumerate(prs.slides):
    title = "NO TITLE"
    for shape in slide.shapes:
        if shape.has_text_frame and shape.name.startswith("Title"):
            title = shape.text.strip().replace("\n", " ")
    print(f"Slide {i+1}: Title = '{title}'")
    for s_idx, shape in enumerate(slide.shapes):
        if shape.has_text_frame and not shape.name.startswith("Slide Number") and not shape.name.startswith("Date") and not shape.name.startswith("Footer"):
            t = shape.text.strip().replace("\n", " ")
            if t and t != title:
                print(f"    Body: {t[:120]}")

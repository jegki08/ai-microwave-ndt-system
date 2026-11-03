import pptx

pptx_path = r"c:\Users\LENOVO\Downloads\microwave_ndt_2day_prototype\Microwave_NDT_Jagadeesh_Presentation.pptx"
prs = pptx.Presentation(pptx_path)

print(f"Total Slides: {len(prs.slides)}")

for i, slide in enumerate(prs.slides):
    shapes_info = []
    title = "NO TITLE"
    for shape in slide.shapes:
        if shape.has_text_frame:
            txt = shape.text_frame.text.strip().replace("\n", " ")
            if any(k in txt for k in ["AI-BASED", "PRESENTATION", "ABSTRACT", "INTRODUCTION", "EXISTING", "PROBLEM", "PROPOSED", "ADVANTAGE", "LITERATURE", "MODULE", "DATAFLOW", "ARCHITECTURE", "ALGORITHM", "CONCLUSION", "SCREENSHOT", "REFERENCE", "THANK"]):
                title = txt[:65]
        if shape.has_table:
            shapes_info.append(f"Table({len(shape.table.rows)}x{len(shape.table.columns)})")
        elif shape.shape_type == 13: # Picture
            shapes_info.append("Picture")
    print(f"Slide {i+1:2d}: {title} | Shapes: {len(slide.shapes)} | Extras: {', '.join(shapes_info) if shapes_info else 'Text/Cards'}")

print("\n--- Verifying Slide 1 specific requirements ---")
slide1 = prs.slides[0]
for s in slide1.shapes:
    if s.has_text_frame:
        print(s.text_frame.text)

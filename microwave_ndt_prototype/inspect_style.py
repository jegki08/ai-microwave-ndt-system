import pptx

sample_path = r"C:\Users\LENOVO\.gemini\antigravity\brain\4fde4e1e-ec54-4644-92ae-b8ffb7021c00\.user_uploaded\media_1793456791123_d52cff05.pptx"
prs = pptx.Presentation(sample_path)
print("Slide width (inches):", prs.slide_width.inches)
print("Slide height (inches):", prs.slide_height.inches)

for i in [0, 1, 2, 8, 17, 21, 29]:
    s = prs.slides[i]
    print(f"\n--- Slide {i+1} background & shape details ---")
    for shp in s.shapes:
        if shp.has_text_frame:
            for p in shp.text_frame.paragraphs:
                for r in p.runs:
                    print(f"   Font: {r.font.name}, size: {r.font.size.pt if r.font.size else 'None'}, color: {r.font.color.rgb if r.font.color and r.font.color.type == 1 else 'theme'}")
                    break
                break

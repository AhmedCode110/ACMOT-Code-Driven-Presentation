from theme.layouts import LAYOUTS


def slide_background(slide):
    return LAYOUTS.get(slide.get("type", "image_backed"), LAYOUTS["image_backed"])["background"]


def image_alt(slide):
    number = int(slide["id"])
    title = slide.get("title") or f"Slide {number}"
    return f"Original visual reference for slide {number}: {title}"

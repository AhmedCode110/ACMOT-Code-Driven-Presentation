from content.slides import SLIDES


def ordered_slides():
    return [SLIDES[key] for key in sorted(SLIDES)]


def slide_count():
    return len(SLIDES)

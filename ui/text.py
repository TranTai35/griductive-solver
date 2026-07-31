from ui.theme import font


def draw_text(surface, text, position, size=20, color=(255, 255, 255), bold=False, anchor="topleft"):
    image = font(size, bold).render(str(text), True, color)
    rect = image.get_rect()
    setattr(rect, anchor, position)
    surface.blit(image, rect)
    return rect


def wrap_lines(text, max_width, size=18, bold=False):
    face = font(size, bold)
    words = str(text).split()
    lines, current = [], ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if face.size(candidate)[0] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [""]


def draw_wrapped(surface, text, rect, size=18, color=(255, 255, 255), bold=False, line_gap=5):
    y = rect.top
    for line in wrap_lines(text, rect.width, size, bold):
        image = font(size, bold).render(line, True, color)
        surface.blit(image, (rect.left, y))
        y += image.get_height() + line_gap
        if y > rect.bottom:
            break
    return y


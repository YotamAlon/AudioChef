from kivy.uix.widget import Widget


def toggle_widget(wid: Widget, hide: bool) -> None:
    if hasattr(wid, "saved_attrs"):
        if not hide:
            wid.height, wid.size_hint_y, wid.opacity, wid.disabled = wid.saved_attrs
            del wid.saved_attrs
    elif hide:
        wid.saved_attrs = wid.height, wid.size_hint_y, wid.opacity, wid.disabled
        wid.height, wid.size_hint_y, wid.opacity, wid.disabled = 0, None, 0, True

"""
JanSamadhan SVG Icon Registry.
Provides self-contained inline SVG strings with zero external network or font dependencies.
All icons are designed on a 24x24 viewBox with 1.75px stroke width, rounded caps and joins.
"""

from typing import Optional

ICONS = {
    "chat_bubble_dots": (
        '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>'
        '<circle cx="8" cy="10" r="1" fill="currentColor"></circle>'
        '<circle cx="12" cy="10" r="1" fill="currentColor"></circle>'
        '<circle cx="16" cy="10" r="1" fill="currentColor"></circle>'
    ),
    "document_list": (
        '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>'
        '<polyline points="14 2 14 8 20 8"></polyline>'
        '<line x1="16" y1="13" x2="8" y2="13"></line>'
        '<line x1="16" y1="17" x2="8" y2="17"></line>'
        '<line x1="10" y1="9" x2="8" y2="9"></line>'
    ),
    "track_status": (
        '<path d="M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2"></path>'
        '<rect x="9" y="3" width="6" height="4" rx="2"></rect>'
        '<path d="m9 14 2 2 4-4"></path>'
    ),
    "bell": (
        '<path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"></path>'
        '<path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"></path>'
    ),
    "user_outline": (
        '<path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"></path>'
        '<circle cx="12" cy="7" r="4"></circle>'
    ),
    "user": (
        '<path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"></path>'
        '<circle cx="12" cy="7" r="4"></circle>'
    ),
    "settings": (
        '<path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"></path>'
        '<circle cx="12" cy="12" r="3"></circle>'
    ),
    "help_circle": (
        '<circle cx="12" cy="12" r="10"></circle>'
        '<path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path>'
        '<line x1="12" y1="17" x2="12.01" y2="17"></line>'
    ),
    "bot": (
        '<rect width="18" height="12" x="3" y="6" rx="2"></rect>'
        '<path d="M9 10h.01M15 10h.01M12 2v4M2 12h1M21 12h1"></path>'
    ),
    "search_status": (
        '<circle cx="11" cy="11" r="8"></circle>'
        '<line x1="21" y1="21" x2="16.65" y2="16.65"></line>'
        '<line x1="8" y1="9.5" x2="14" y2="9.5"></line>'
        '<line x1="8" y1="12.5" x2="14" y2="12.5"></line>'
    ),
    "search": (
        '<circle cx="11" cy="11" r="8"></circle>'
        '<line x1="21" y1="21" x2="16.65" y2="16.65"></line>'
    ),
    "file_text": (
        '<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"></path>'
        '<path d="M14 2v4a2 2 0 0 0 2 2h4"></path>'
        '<path d="M10 9H8M16 13H8M16 17H8"></path>'
    ),
    "bolt": (
        '<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>'
    ),
    "handshake": (
        '<path d="m11 17 2 2a1 1 0 0 0 1.4 0l4.3-4.3a1 1 0 0 0 0-1.4l-2.3-2.3a1 1 0 0 0-1.4 0L13 13"></path>'
        '<path d="m7 7 4.3 4.3a1 1 0 0 0 1.4 0l2.3-2.3a1 1 0 0 0 0-1.4L13 5.6a1 1 0 0 0-1.4 0L9.3 7.9"></path>'
        '<path d="M2 13a6 6 0 0 0 6 6l2-2"></path>'
        '<path d="M22 11a6 6 0 0 0-6-6l-2 2"></path>'
    ),
    "headphones": (
        '<path d="M3 14h3a2 2 0 0 1 2 2v3a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-7a9 9 0 0 1 18 0v7a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3"></path>'
    ),
    "paperclip": (
        '<path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l8.57-8.57A4 4 0 1 1 18 8.84l-8.59 8.57a2 2 0 0 1-2.83-2.83l8.49-8.48"></path>'
    ),
    "send": (
        '<line x1="22" y1="2" x2="11" y2="13"></line>'
        '<polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>'
    ),
    "mic": (
        '<path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"></path>'
        '<path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>'
        '<line x1="12" y1="19" x2="12" y2="22"></line>'
    ),
    "volume": (
        '<polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>'
        '<path d="M15.54 8.46a5 5 0 0 1 0 7.07"></path>'
    ),
    "globe": (
        '<circle cx="12" cy="12" r="10"></circle>'
        '<line x1="2" y1="12" x2="22" y2="12"></line>'
        '<path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path>'
    ),
    "chevron_down": (
        '<polyline points="6 9 12 15 18 9"></polyline>'
    ),
    "check": (
        '<polyline points="20 6 9 17 4 12"></polyline>'
    ),
    "double_check": (
        '<polyline points="18 6 7 17 2 12"></polyline>'
        '<polyline points="22 10 15.5 16.5"></polyline>'
    ),
    "file_plus": (
        '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>'
        '<polyline points="14 2 14 8 20 8"></polyline>'
        '<line x1="12" y1="18" x2="12" y2="12"></line>'
        '<line x1="9" y1="15" x2="15" y2="15"></line>'
    ),
    "droplet": (
        '<path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"></path>'
    ),
    "map_pin": (
        '<path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"></path>'
        '<circle cx="12" cy="10" r="3"></circle>'
    ),
}

def icon(name: str, size: int = 24, color: Optional[str] = None, stroke_width: float = 1.75) -> str:
    """
    Renders an inline SVG icon string.
    - name: Icon identifier from ICONS registry.
    - size: Width and height in pixels (default: 24).
    - color: Stroke color (defaults to 'currentColor' for CSS inheritance).
    - stroke_width: Stroke thickness (default: 1.75).
    """
    content = ICONS.get(name, "")
    color_val = color or "currentColor"
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
        f'stroke="{color_val}" stroke-width="{stroke_width}" stroke-linecap="round" stroke-linejoin="round" '
        f'aria-hidden="true" class="icon-{name}" style="display:inline-block;vertical-align:middle;flex-shrink:0;">'
        f'{content}'
        f'</svg>'
    )

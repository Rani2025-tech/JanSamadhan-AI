"""
JanSamadhan SVG Icon Registry.
Provides self-contained inline SVG strings with zero external network or font dependencies.
All icons are designed on a 24x24 viewBox with 2px stroke width, rounded caps and joins.
"""

from typing import Optional

ICONS = {
    "user_shield_check": (
        '<g fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<circle cx="10" cy="7" r="4"></circle>'
        '<path d="M3 20v-2a4 4 0 0 1 4-4h4a4 4 0 0 1 2.5 0.88"></path>'
        '</g>'
        '<path d="M14.5 13.5v3c0 2.2 1.8 3.8 3 4.5 1.2-.7 3-2.3 3-4.5v-3l-3-1.2-3 1.2z" fill="currentColor" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"></path>'
        '<path d="M16 16.5l1 1 2-2" fill="none" stroke="#FFFFFF" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"></path>'
    ),
    "lock_keyhole": (
        '<circle cx="12" cy="16" r="1"></circle>'
        '<rect x="3" y="10" width="18" height="12" rx="2"></rect>'
        '<path d="M7 10V7a5 5 0 0 1 10 0v3"></path>'
    ),
    "users": (
        '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"></path>'
        '<circle cx="9" cy="7" r="4"></circle>'
        '<path d="M22 21v-2a4 4 0 0 0-3-3.87"></path>'
        '<path d="M16 3.13a4 4 0 0 1 0 7.75"></path>'
    ),
    "landmark": (
        '<line x1="3" y1="22" x2="21" y2="22"></line>'
        '<line x1="6" y1="18" x2="6" y2="11"></line>'
        '<line x1="10" y1="18" x2="10" y2="11"></line>'
        '<line x1="14" y1="18" x2="14" y2="11"></line>'
        '<line x1="18" y1="18" x2="18" y2="11"></line>'
        '<polygon points="12 2 20 7 4 7"></polygon>'
    ),
    "user": (
        '<path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"></path>'
        '<circle cx="12" cy="7" r="4"></circle>'
    ),
    "lock": (
        '<rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>'
        '<path d="M7 11V7a5 5 0 0 1 10 0v4"></path>'
    ),
    "lock_filled": (
        '<path d="M18 8h-1V6c0-2.76-2.24-5-5-5S7 3.24 7 6v2H6c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V10c0-1.1-.9-2-2-2zm-6 9c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zm3.1-9H8.9V6c0-1.71 1.39-3.1 3.1-3.1 1.71 0 3.1 1.39 3.1 3.1v2z" fill="currentColor" stroke="none"></path>'
    ),
    "eye": (
        '<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>'
        '<circle cx="12" cy="12" r="3"></circle>'
    ),
    "eye_off": (
        '<path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path>'
        '<line x1="1" y1="1" x2="23" y2="23"></line>'
    ),
    "smartphone": (
        '<rect x="5" y="2" width="14" height="20" rx="2" ry="2"></rect>'
        '<line x1="12" y1="18" x2="12.01" y2="18"></line>'
    ),
    "arrow_right": (
        '<line x1="5" y1="12" x2="19" y2="12"></line>'
        '<polyline points="12 5 19 12 12 19"></polyline>'
    ),
    "arrow_left": (
        '<line x1="19" y1="12" x2="5" y2="12"></line>'
        '<polyline points="12 19 5 12 12 5"></polyline>'
    ),
    "search": (
        '<circle cx="11" cy="11" r="8"></circle>'
        '<line x1="21" y1="21" x2="16.65" y2="16.65"></line>'
    ),
    "mail": (
        '<rect width="20" height="16" x="2" y="4" rx="2"></rect>'
        '<path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"></path>'
    ),
    "shield_check": (
        '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10"></path>'
        '<path d="m9 12 2 2 4-4"></path>'
    ),
    "globe": (
        '<circle cx="12" cy="12" r="10"></circle>'
        '<line x1="2" y1="12" x2="22" y2="12"></line>'
        '<path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path>'
    ),
    "speech_check": (
        '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>'
        '<polyline points="9 10 12 13 16 8"></polyline>'
    ),
    "bot": (
        '<rect width="18" height="12" x="3" y="6" rx="2"></rect>'
        '<path d="M9 10h.01M15 10h.01M12 2v4M2 12h1M21 12h1"></path>'
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
        '<path d="M19.07 4.93a10 10 0 0 1 0 14.14"></path>'
    ),
    "handshake": (
        '<path d="m11 17 2 2a1 1 0 0 0 1.4 0l4.3-4.3a1 1 0 0 0 0-1.4l-2.3-2.3a1 1 0 0 0-1.4 0L13 13"></path>'
        '<path d="m7 7 4.3 4.3a1 1 0 0 0 1.4 0l2.3-2.3a1 1 0 0 0 0-1.4L13 5.6a1 1 0 0 0-1.4 0L9.3 7.9"></path>'
        '<path d="M2 13a6 6 0 0 0 6 6l2-2"></path>'
        '<path d="M22 11a6 6 0 0 0-6-6l-2 2"></path>'
    ),
    "bell": (
        '<path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"></path>'
        '<path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"></path>'
    ),
    "file_text": (
        '<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"></path>'
        '<path d="M14 2v4a2 2 0 0 0 2 2h4"></path>'
        '<path d="M10 9H8M16 13H8M16 17H8"></path>'
    ),
    "clipboard_check": (
        '<rect width="8" height="4" x="8" y="2" rx="1" ry="1"></rect>'
        '<path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"></path>'
        '<path d="m9 14 2 2 4-4"></path>'
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
    "headphones": (
        '<path d="M3 14h3a2 2 0 0 1 2 2v3a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-7a9 9 0 0 1 18 0v7a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3"></path>'
    ),
    "check": (
        '<polyline points="20 6 9 17 4 12"></polyline>'
    ),
}

def icon(name: str, size: int = 24, color: Optional[str] = None, stroke_width: float = 2.0) -> str:
    """
    Renders an inline SVG icon string.
    - name: Icon identifier from ICONS registry.
    - size: Width and height in pixels (default: 24).
    - color: Stroke color (defaults to 'currentColor' for CSS inheritance).
    - stroke_width: Stroke thickness (default: 2.0).
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

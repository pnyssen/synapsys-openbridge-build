"""Read-only HTML view of the scaffold projection (Architecture > Lenses > Context scaffold).

RC06a: this module no longer builds any HTML itself. It is a thin adapter over the one screen renderer (screen_render), kept so
the existing controller call sv.render(out, mode) and the existing imports keep working. Presentation only: it changes no data,
kind, PPV, approval or right.
"""
try:  # inside Odoo
    from . import screen_render as _r
except ImportError:  # offline tests load modules by path
    import screen_render as _r

STYLE = _r.STYLE
BACK = _r.BACK


def render(out, mode='enable'):
    if not isinstance(out, dict) or out.get('result') != 'OK':
        return _r.render_unavailable(out, 'Context scaffold')
    return _r.render_screen(out)

def migrate(cr, version):
    """Upgrade safety on databases where the website module is installed.

    website adds ir.ui.view.visibility (required, default 'public'). When this module upgrades, it loads
    before website, so the ORM does not yet know the field and new views insert without it: the NOT NULL
    column then fails the whole upgrade (Odoo.sh build 42381149, 20 Nov 2026). Give the column the same
    default website's ORM uses, at database level. No effect where website is not installed."""
    cr.execute("""SELECT 1 FROM information_schema.columns
                  WHERE table_name = 'ir_ui_view' AND column_name = 'visibility'""")
    if cr.fetchone():
        cr.execute("ALTER TABLE ir_ui_view ALTER COLUMN visibility SET DEFAULT 'public'")

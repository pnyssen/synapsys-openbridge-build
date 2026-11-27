from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    """Upgrade path for databases installed before the seat instructions were held in the Architecture.
    1. Rows that existed before this version get no V20 state: the new column's default ('candidate') would
       misstate canon loaded from V19, so it is cleared (unknown stays unknown).
    2. post_init_hook runs only on install, so load the instruction set here (idempotent, fails closed)."""
    cr.execute("UPDATE synapsys_canon SET state = NULL WHERE kind = 'reference'")
    from odoo.addons.synapsys.hooks import load_domain_instructions
    load_domain_instructions(api.Environment(cr, SUPERUSER_ID, {}))

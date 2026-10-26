from odoo.exceptions import UserError


def pre_init_hook(env):
    """Refuse installation on duplicates instead of silently missing the index."""
    env.cr.execute("""
        SELECT 1 FROM res_partner
        WHERE nullif(btrim(email), '') IS NOT NULL
        GROUP BY lower(btrim(email)) HAVING count(*) > 1 LIMIT 1
    """)
    if env.cr.fetchone():
        raise UserError(
            env._(
                "Duplicate contact emails exist. Merge or correct duplicates "
                "(including archived contacts) before installing Unique Partner Email."
            )
        )

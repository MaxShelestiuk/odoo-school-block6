from odoo import models


class ResPartner(models.Model):
    """Enforce one nonblank email across active and archived contacts."""

    _inherit = "res.partner"

    _email_unique = models.UniqueIndex(
        "(lower(nullif(btrim(email), '')))",
        "This email address is already used by another contact.",
    )

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class HrHospitalDisease(models.Model):
    """Manage disease records and their business rules."""

    _name = "hr.hospital.disease"
    _description = "Disease"
    _parent_name = "parent_id"

    name = fields.Char(required=True, translate=True)
    complete_name = fields.Char(
        string="Complete Name",
        compute="_compute_complete_name",
        store=False,
        recursive=True,
    )
    parent_id = fields.Many2one(
        comodel_name="hr.hospital.disease",
        string="Parent Disease",
        ondelete="restrict",
        index=True,
    )
    child_ids = fields.One2many(
        comodel_name="hr.hospital.disease",
        inverse_name="parent_id",
        string="Child Diseases",
    )

    @api.depends_context("lang")
    @api.depends("name", "parent_id.complete_name")
    def _compute_complete_name(self):
        """Build a language-aware path through the disease hierarchy."""
        for disease in self:
            name = disease.name or ""
            if disease.parent_id:
                disease.complete_name = f"{disease.parent_id.complete_name} / {name}"
            else:
                disease.complete_name = name

    @api.depends_context("lang")
    @api.depends("complete_name")
    def _compute_display_name(self):
        """Build the record label from its identifying fields."""
        for disease in self:
            disease.display_name = disease.complete_name or ""

    @api.constrains("parent_id")
    def _check_parent_id(self):
        """Reject cyclic disease hierarchies."""
        if self._has_cycle():
            raise ValidationError(
                self.env._("A disease hierarchy cannot contain cycles.")
            )

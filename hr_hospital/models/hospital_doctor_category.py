from odoo import fields, models


class HospitalDoctorCategory(models.Model):
    """Manage doctor qualification records and their business rules."""

    _name = "hospital.doctor.category"
    _description = "Doctor Qualification"
    _order = "sequence, name, id"

    name = fields.Char(string="Name", required=True, translate=True)
    sequence = fields.Integer(string="Sequence", default=10)
    is_intern = fields.Boolean(string="Intern Category")
    doctor_ids = fields.One2many(
        comodel_name="hr.hospital.doctor",
        inverse_name="category_id",
        string="Doctors",
    )

    _name_unique = models.Constraint(
        "UNIQUE(name)",
        "This qualification name already exists!",
    )

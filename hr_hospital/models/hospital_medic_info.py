from odoo import api, fields, models


class HospitalMedicInfo(models.AbstractModel):
    """Manage medical information records and their business rules."""

    _name = "hospital.medic.info"
    _description = "Medical Information"

    blood_group = fields.Selection(
        selection=[
            ("o_positive", "O(I) Rh+"),
            ("o_negative", "O(I) Rh-"),
            ("a_positive", "A(II) Rh+"),
            ("a_negative", "A(II) Rh-"),
            ("b_positive", "B(III) Rh+"),
            ("b_negative", "B(III) Rh-"),
            ("ab_positive", "AB(IV) Rh+"),
            ("ab_negative", "AB(IV) Rh-"),
        ],
        string="Blood Group",
    )
    gender = fields.Selection(
        selection=[
            ("male", "Male"),
            ("female", "Female"),
        ],
        string="Gender",
    )
    birth_date = fields.Date(string="Birth Date")
    age = fields.Integer(
        string="Age",
        compute="_compute_age",
    )

    @api.depends("birth_date")
    def _compute_age(self):
        """Compute completed years, returning zero for an unknown birthday."""
        today = fields.Date.today()
        for record in self:
            if not record.birth_date:
                record.age = 0
                continue

            birthday = record.birth_date
            record.age = (
                today.year
                - birthday.year
                - ((today.month, today.day) < (birthday.month, birthday.day))
            )

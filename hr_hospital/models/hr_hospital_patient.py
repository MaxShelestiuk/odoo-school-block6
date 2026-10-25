from odoo import api, fields, models


class HrHospitalPatient(models.Model):
    """Manage hospital patient records and their business rules."""

    _name = "hr.hospital.patient"
    _inherit = "hospital.medic.info"
    _description = "Hospital Patient"

    name = fields.Char(required=True)
    user_id = fields.Many2one(
        "res.users",
        string="System User",
        ondelete="set null",
        index=True,
    )
    personal_doctor_id = fields.Many2one(
        comodel_name="hr.hospital.doctor",
        string="Personal Doctor",
        ondelete="restrict",
    )
    doctor_history_ids = fields.One2many(
        comodel_name="hospital.doctor.history",
        inverse_name="patient_id",
        string="Personal Doctor History",
    )
    insurance_policy_number = fields.Char(
        string="Insurance Policy Number",
        size=20,
    )

    phone = fields.Char(string="Phone")
    visit_ids = fields.One2many(
        "hr.hospital.patient.visit",
        "patient_id",
        string="Visits",
    )
    visit_count = fields.Integer(
        compute="_compute_visit_count",
        string="Visit Count",
    )

    @api.depends("visit_ids")
    def _compute_visit_count(self):
        """Count the patient visits, including archived visits."""
        for patient in self:
            patient.visit_count = len(patient.with_context(active_test=False).visit_ids)

    def action_open_visits(self):
        """Open this patient history, including archived visits."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Visit History"),
            "res_model": "hr.hospital.patient.visit",
            "view_mode": "list,form",
            "domain": [("patient_id", "=", self.id)],
            "context": {"default_patient_id": self.id, "active_test": False},
        }

    def action_quick_visit(self):
        """Open a visit form with defaults from this record."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Book a Visit"),
            "res_model": "hr.hospital.patient.visit",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_patient_id": self.id,
                "default_doctor_id": self.personal_doctor_id.id,
                "default_name": self.env._("Visit: %s", self.name),
            },
        }

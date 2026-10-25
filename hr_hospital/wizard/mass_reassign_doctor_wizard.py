from odoo import fields, models
from odoo.exceptions import UserError


class MassReassignDoctorWizard(models.TransientModel):
    """Manage mass reassignment of personal doctor records and their business rules."""

    _name = "mass.reassign.doctor.wizard"
    _description = "Mass Reassignment of Personal Doctor"

    new_doctor_id = fields.Many2one(
        comodel_name="hr.hospital.doctor",
        string="New Doctor",
        required=True,
    )
    change_date = fields.Date(
        string="Change Date",
        default=fields.Date.today,
    )

    def action_reassign(self):
        """Change personal doctors and preserve dated assignment history."""
        self.ensure_one()

        if self.env.context.get("active_model") != "hr.hospital.patient":
            raise UserError(self.env._("Open the wizard from the patient list."))

        patients = (
            self.env["hr.hospital.patient"]
            .browse(self.env.context.get("active_ids") or [])
            .exists()
        )

        if not patients:
            raise UserError(self.env._("Select at least one patient."))

        effective_date = self.change_date or fields.Date.today()
        history_model = self.env["hospital.doctor.history"].with_context(
            active_test=False,
        )

        for patient in patients:
            if patient.personal_doctor_id == self.new_doctor_id:
                continue

            previous_history = history_model.browse([])
            if patient.personal_doctor_id:
                previous_history = history_model.search(
                    [
                        ("patient_id", "=", patient.id),
                        ("doctor_id", "=", patient.personal_doctor_id.id),
                        ("change_date", "=", False),
                    ],
                    order="assignment_date desc, id desc",
                    limit=1,
                )

            if previous_history:
                if effective_date < previous_history.assignment_date:
                    raise UserError(
                        self.env._(
                            "For patient %(patient)s, the doctor change date "
                            "cannot precede the previous assignment.",
                            patient=patient.name,
                        )
                    )
                previous_history.write(
                    {
                        "change_date": effective_date,
                    }
                )

            patient.write(
                {
                    "personal_doctor_id": self.new_doctor_id.id,
                }
            )
            history_model.create(
                [
                    {
                        "patient_id": patient.id,
                        "doctor_id": self.new_doctor_id.id,
                        "assignment_date": effective_date,
                    }
                ]
            )

        return {"type": "ir.actions.act_window_close"}

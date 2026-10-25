from odoo import api, fields, models
from odoo.exceptions import UserError


class HrHospitalPatientVisit(models.Model):
    """Manage patient visit records and their business rules."""

    _name = "hr.hospital.patient.visit"
    _description = "Patient Visit"
    _inherit = ["mail.thread"]

    name = fields.Char(required=True, default=lambda self: self.env._("New Visit"))
    active = fields.Boolean(default=True)
    state = fields.Selection(
        selection=[
            ("planned", "Planned"),
            ("done", "Done"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        required=True,
        default="planned",
        tracking=True,
    )
    patient_id = fields.Many2one(
        comodel_name="hr.hospital.patient",
        string="Patient",
    )
    doctor_id = fields.Many2one(
        comodel_name="hr.hospital.doctor",
        string="Doctor",
        tracking=True,
    )
    visit_datetime = fields.Datetime(
        string="Planned Date and Time",
    )
    actual_visit_datetime = fields.Datetime(
        string="Actual Date and Time",
    )
    summary = fields.Html(string="Clinical Summary")
    disease_id = fields.Many2one(
        comodel_name="hr.hospital.disease",
        string="Disease",
        ondelete="restrict",
    )

    same_disease_visit_count = fields.Integer(
        string="Visits with This Disease",
        compute="_compute_same_disease_visit_count",
    )

    @api.depends("disease_id")
    def _compute_same_disease_visit_count(self):
        """Count accessible visits sharing each diagnosis."""
        counts = dict(
            self.with_context(active_test=False)._read_group(
                [("disease_id", "in", self.disease_id.ids)],
                ["disease_id"],
                ["__count"],
            )
        )
        for visit in self:
            visit.same_disease_visit_count = counts.get(visit.disease_id, 0)

    @api.depends("patient_id.name", "name")
    def _compute_display_name(self):
        """Build the record label from its identifying fields."""
        for visit in self:
            visit.display_name = visit.patient_id.name or visit.name or ""

    def action_same_disease_visits(self):
        """Open accessible visits with this diagnosis."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Visits with This Disease"),
            "res_model": self._name,
            "view_mode": "list,form",
            "domain": [("disease_id", "=", self.disease_id.id)]
            if self.disease_id
            else [("id", "=", False)],
            "context": {"active_test": False},
        }

    def write(self, vals):
        """Protect completed visits while retaining normal ORM access checks."""
        completed_visits = self.filtered(lambda visit: visit.state == "done")

        if completed_visits:
            if "state" in vals and vals["state"] != "done":
                raise UserError(
                    self.env._("The status of a completed visit cannot be changed.")
                )

            if "active" in vals and not vals["active"]:
                raise UserError(self.env._("A completed visit cannot be archived."))

            for visit in completed_visits:
                if "doctor_id" in vals and vals["doctor_id"] != visit.doctor_id.id:
                    raise UserError(
                        self.env._("The doctor of a completed visit cannot be changed.")
                    )

                for field_name in (
                    "visit_datetime",
                    "actual_visit_datetime",
                ):
                    if field_name not in vals:
                        continue

                    new_value = fields.Datetime.to_datetime(vals[field_name]) or False
                    if new_value != visit[field_name]:
                        raise UserError(
                            self.env._(
                                "The date or time of a completed visit "
                                "cannot be changed."
                            )
                        )

        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _unlink_if_completed(self):
        """Keep completed visits unless a module administrator deletes them."""
        if self.env.user.has_group("hr_hospital.group_hospital_admin"):
            return
        if any(visit.state == "done" for visit in self):
            raise UserError(self.env._("A completed visit cannot be deleted."))

    @api.model
    def _cancel_overdue_visits(self, selected_ids=None):
        """Cancel accessible planned visits whose scheduled time has passed."""
        domain = [
            ("state", "=", "planned"),
            ("visit_datetime", "<", fields.Datetime.now()),
        ]
        if selected_ids is not None:
            domain.append(("id", "in", selected_ids))
        visits = self.search(domain)
        visits.write({"state": "cancelled"})
        return len(visits)

    @api.model
    def action_cancel_selected_overdue(self):
        # Empty selection must never become a global cancellation.
        """Cancel overdue visits from the explicit active selection only."""
        if self.env.context.get("active_model") != self._name:
            return False
        self._cancel_overdue_visits(self.env.context.get("active_ids") or [])
        return {"type": "ir.actions.client", "tag": "reload"}

    @api.model
    def _cron_cancel_overdue_visits(self):
        """Cancel overdue planned visits from the daily scheduled action."""
        return self._cancel_overdue_visits()

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class HrHospitalDoctor(models.Model):
    """Manage hospital doctor records and their business rules."""

    _name = "hr.hospital.doctor"
    _inherit = "hospital.medic.info"
    _description = "Hospital Doctor"

    name = fields.Char(required=True)
    category_id = fields.Many2one(
        comodel_name="hospital.doctor.category",
        string="Qualification",
        ondelete="restrict",
        group_expand="_read_group_category_id",
    )
    user_id = fields.Many2one(
        comodel_name="res.users",
        string="System User",
        ondelete="set null",
    )
    is_intern = fields.Boolean(
        string="Is an Intern",
        compute="_compute_is_intern",
        store=True,
    )
    supervisor_doctor_id = fields.Many2one(
        comodel_name="hr.hospital.doctor",
        string="Supervisor",
        ondelete="restrict",
    )

    @api.depends("category_id.is_intern")
    def _compute_is_intern(self):
        """Ознаку інтерна беремо з булевого поля кваліфікації.
        Альтернатива — порівнювати категорію з записом через XML ID.
        Булеве поле дозволяє налаштовувати категорії без прив'язки
        логіки до одного майстер-запису.
        """
        for doctor in self:
            doctor.is_intern = doctor.category_id.is_intern

    @api.constrains("supervisor_doctor_id")
    def _check_supervisor_doctor(self):
        """Reject assigning an intern as a supervisor."""
        for doctor in self:
            if doctor.supervisor_doctor_id.is_intern:
                raise ValidationError(self.env._("An intern cannot be a supervisor."))

    active = fields.Boolean(default=True)
    intern_ids = fields.One2many(
        "hr.hospital.doctor",
        "supervisor_doctor_id",
        string="Interns",
        domain=[("is_intern", "=", True)],
    )
    intern_names = fields.Char(
        string="Intern Names",
        compute="_compute_intern_names",
    )

    @api.depends("intern_ids.name", "intern_ids.is_intern")
    def _compute_intern_names(self):
        """Join the names of supervised interns for kanban display."""
        for doctor in self:
            interns = doctor.intern_ids.filtered("is_intern")
            doctor.intern_names = ", ".join(interns.mapped("name"))

    @api.model
    def _read_group_category_id(self, categories, domain):
        """Include empty qualifications in grouped doctor views."""
        return categories.search([])

    def action_quick_visit(self):
        """Open a visit form with defaults from this record."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Book a Visit"),
            "res_model": "hr.hospital.patient.visit",
            "view_mode": "form",
            "target": "new",
            "context": {"default_doctor_id": self.id},
        }

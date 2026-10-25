from odoo import api, fields, models


class HrHospitalPatient(models.Model):
    _name = 'hr.hospital.patient'
    _inherit = 'hospital.medic.info'
    _description = 'Hospital Patient'

    name = fields.Char(required=True)
    user_id = fields.Many2one(
        "res.users", string="System User", ondelete="set null", index=True,
    )
    personal_doctor_id = fields.Many2one(
        comodel_name='hr.hospital.doctor',
        string='Персональний лікар',
        ondelete='restrict',
    )
    doctor_history_ids = fields.One2many(
        comodel_name='hospital.doctor.history',
        inverse_name='patient_id',
        string='Історія персональних лікарів',
    )
    insurance_policy_number = fields.Char(
        string='Номер страхового поліса',
        size=20,
    )

    phone = fields.Char(string='Телефон')
    visit_ids = fields.One2many(
        'hr.hospital.patient.visit', 'patient_id', string='Візити',
    )
    visit_count = fields.Integer(
        compute='_compute_visit_count',
        string='Кількість візитів',
    )

    @api.depends('visit_ids')
    def _compute_visit_count(self):
        for patient in self:
            patient.visit_count = len(patient.with_context(active_test=False).visit_ids)

    def action_open_visits(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window', 'name': self.env._('Історія візитів'),
            'res_model': 'hr.hospital.patient.visit', 'view_mode': 'list,form',
            'domain': [('patient_id', '=', self.id)],
            'context': {'default_patient_id': self.id, 'active_test': False},
        }

    def action_quick_visit(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window', 'name': self.env._('Запис до лікаря'),
            'res_model': 'hr.hospital.patient.visit', 'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_patient_id': self.id,
                'default_doctor_id': self.personal_doctor_id.id,
                'default_name': self.env._('Візит: %s', self.name),
            },
        }

from odoo import api, fields, models
from odoo.exceptions import UserError


class HrHospitalPatientVisit(models.Model):
    _name = 'hr.hospital.patient.visit'
    _description = 'Patient Visit'
    _inherit = ['mail.thread']

    name = fields.Char(required=True, default='Новий візит')
    active = fields.Boolean(default=True)
    state = fields.Selection(
        selection=[
            ('planned', 'Заплановано'),
            ('done', 'Завершено'),
            ('cancelled', 'Скасовано'),
        ],
        string='Статус',
        required=True,
        default='planned',
        tracking=True,
    )
    patient_id = fields.Many2one(
        comodel_name='hr.hospital.patient',
        string='Пацієнт',
    )
    doctor_id = fields.Many2one(
        comodel_name='hr.hospital.doctor',
        string='Лікар',
        tracking=True,
    )
    visit_datetime = fields.Datetime(
        string='Запланована дата та час',
    )
    actual_visit_datetime = fields.Datetime(
        string='Фактична дата та час',
    )
    summary = fields.Html(string='Епікриз')
    disease_id = fields.Many2one(
        comodel_name='hr.hospital.disease',
        string='Хвороба',
        ondelete='restrict',
    )

    same_disease_visit_count = fields.Integer(
        string='Візити з цією хворобою', compute='_compute_same_disease_visit_count',
    )

    @api.depends('disease_id')
    def _compute_same_disease_visit_count(self):
        counts = dict(self.with_context(active_test=False)._read_group(
            [('disease_id', 'in', self.disease_id.ids)],
            ['disease_id'], ['__count'],
        ))
        for visit in self:
            visit.same_disease_visit_count = counts.get(visit.disease_id, 0)

    @api.depends('patient_id.name', 'name')
    def _compute_display_name(self):
        for visit in self:
            visit.display_name = visit.patient_id.name or visit.name or ''

    def action_same_disease_visits(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Візити з цією хворобою'),
            'res_model': self._name, 'view_mode': 'list,form',
            'domain': [('disease_id', '=', self.disease_id.id)]
            if self.disease_id else [('id', '=', False)],
            'context': {'active_test': False},
        }

    def write(self, vals):
        completed_visits = self.filtered(lambda visit: visit.state == 'done')

        if completed_visits:
            if 'state' in vals and vals['state'] != 'done':
                raise UserError('Не можна змінювати статус завершеного візиту.')

            if 'active' in vals and not vals['active']:
                raise UserError('Не можна архівувати завершений візит.')

            for visit in completed_visits:
                if ('doctor_id' in vals and vals['doctor_id'] != visit.doctor_id.id):
                    raise UserError('Не можна змінювати лікаря завершеного візиту.')

                for field_name in ('visit_datetime', 'actual_visit_datetime',):
                    if field_name not in vals:
                        continue

                    new_value = (fields.Datetime.to_datetime(vals[field_name]) or False)
                    if new_value != visit[field_name]:
                        raise UserError(
                            'Не можна змінювати дату або час '
                            'завершеного візиту.'
                        )

        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _unlink_if_completed(self):
        if self.env.user.has_group('hr_hospital.group_hospital_admin'):
            return
        if any(visit.state == 'done' for visit in self):
            raise UserError(
                'Не можна видаляти завершений візит.'
            )

    @api.model
    def _cancel_overdue_visits(self, selected_ids=None):
        domain = [
            ('state', '=', 'planned'),
            ('visit_datetime', '<', fields.Datetime.now()),
        ]
        if selected_ids is not None:
            domain.append(('id', 'in', selected_ids))
        visits = self.search(domain)
        visits.write({'state': 'cancelled'})
        return len(visits)

    @api.model
    def action_cancel_selected_overdue(self):
        # Empty selection must never become a global cancellation.
        if self.env.context.get('active_model') != self._name:
            return False
        self._cancel_overdue_visits(self.env.context.get('active_ids') or [])
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    @api.model
    def _cron_cancel_overdue_visits(self):
        return self._cancel_overdue_visits()

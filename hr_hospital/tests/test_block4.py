from datetime import datetime, timedelta

from lxml import etree

from odoo import Command, fields
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestBlock4(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Visit = cls.env['hr.hospital.patient.visit']
        cls.Wizard = cls.env['hospital.disease.month.report.wizard']
        cls.doctors = cls.env['hr.hospital.doctor'].create([
            {'name': 'Mentor A'}, {'name': 'Doctor B'},
        ])
        cls.patients = cls.env['hr.hospital.patient'].create([
            {'name': 'Patient Alpha', 'phone': '001234567'},
            {'name': 'Patient Beta', 'phone': '009876543'},
        ])
        cls.parent = cls.env['hr.hospital.disease'].create({'name': 'Parent'})
        cls.child = cls.env['hr.hospital.disease'].create({
            'name': 'Child', 'parent_id': cls.parent.id,
        })
        cls.visits = cls.Visit.create([
            {'name': 'A', 'patient_id': cls.patients[0].id,
             'doctor_id': cls.doctors[0].id, 'disease_id': cls.child.id,
             'visit_datetime': '2026-10-31 12:00:00'},
            {'name': 'B', 'patient_id': cls.patients[1].id,
             'doctor_id': cls.doctors[1].id, 'disease_id': cls.parent.id,
             'visit_datetime': '2026-11-01 00:00:00'},
        ])

    def test_patient_actions_and_search(self):
        for patient, visit in zip(self.patients, self.visits):
            action = patient.action_open_visits()
            self.assertEqual(self.Visit.search(action['domain']), visit)
            self.assertEqual(patient.visit_count, 1)
            quick = patient.action_quick_visit()
            defaults = self.Visit.with_context(**quick['context']).default_get(
                ['patient_id', 'doctor_id', 'name'],
            )
            self.assertEqual(defaults['patient_id'], patient.id)
            self.assertEqual(quick['target'], 'new')
        self.assertEqual(self.env['hr.hospital.patient'].search([
            '|', ('name', 'ilike', 'Alpha'), ('phone', 'ilike', 'Alpha'),
        ]), self.patients[0])
        self.assertEqual(self.env['hr.hospital.patient'].search([
            '|', ('name', 'ilike', '123456'), ('phone', 'ilike', '123456'),
        ]), self.patients[0])

    def test_doctor_interns_and_quick_visit(self):
        intern = self.env['hr.hospital.doctor'].create({
            'name': 'Intern',
            'category_id': self.env.ref('hr_hospital.doctor_category_intern').id,
            'supervisor_doctor_id': self.doctors[0].id,
        })
        self.assertIn(intern, self.doctors[0].intern_ids)
        self.assertNotIn(intern, self.doctors[1].intern_ids)
        self.assertIn(self.doctors[0], self.env['hr.hospital.doctor'].search([
            ('intern_ids.is_intern', '=', True),
        ]))
        action = self.doctors[0].action_quick_visit()
        self.assertEqual(action['context']['default_doctor_id'], self.doctors[0].id)
        self.assertEqual(action['target'], 'new')

    def test_visit_stat_display_name_and_aggregation(self):
        visit = self.visits[0]
        self.assertEqual(visit.display_name, self.patients[0].name)
        self.assertEqual(visit.same_disease_visit_count, 1)
        self.assertEqual(self.Visit.search(
            visit.action_same_disease_visits()['domain'],
        ), visit)
        for groupby in (['doctor_id', 'state', 'visit_datetime:month'],
                        ['visit_datetime:month', 'disease_id']):
            rows = self.Visit._read_group(
                [('id', 'in', self.visits.ids)], groupby, ['__count'],
            )
            self.assertEqual(sum(row[-1] for row in rows), 2)

    def test_disease_hierarchical_searchpanel(self):
        panel = self.Visit.search_panel_select_range(
            'disease_id', hierarchize=True, enable_counters=True,
        )
        self.assertEqual(panel['parent_field'], 'parent_id')
        self.assertTrue(any(row['id'] == self.child.id for row in panel['values']))
        self.assertEqual(self.Visit.search([
            ('disease_id', 'child_of', self.parent.id),
        ]), self.visits)

    def test_empty_report_and_print_binding(self):
        wizard = self.Wizard.with_context(
            active_model='hr.hospital.doctor', active_ids=self.doctors.ids,
        ).create({})
        action = wizard.action_show_visits()
        self.assertEqual(action['domain'], [])
        self.assertEqual(action['context']['group_by'], 'disease_id')
        self.assertFalse(action['context']['active_test'])
        binding = self.env.ref('hr_hospital.disease_month_report_wizard_action')
        self.assertEqual(binding.binding_type, 'report')
        self.assertEqual(binding.binding_view_types, 'list,form')
        bindings = self.env['ir.actions.actions'].get_bindings('hr.hospital.doctor')
        self.assertIn(binding.id, [item['id'] for item in bindings['report']])

    def test_report_dates_and_multiple_filters(self):
        wizard = self.Wizard.with_context(tz='Europe/Kyiv').create({
            'doctor_ids': [Command.set(self.doctors.ids)],
            'disease_ids': [Command.set(self.parent.ids)],
            'date_from': '2026-10-01', 'date_to': '2026-10-31',
        })
        self.assertEqual(self.Visit.search(wizard.action_show_visits()['domain']),
                         self.visits[0])
        # Last day 14:00 local, last second, and next-day midnight.
        late = self.visits[0].copy({'visit_datetime': '2026-10-31 21:59:59'})
        excluded = self.visits[0].copy({'visit_datetime': '2026-10-31 22:00:00'})
        result = self.Visit.search(wizard.action_show_visits()['domain'])
        self.assertIn(late, result)
        self.assertNotIn(excluded, result)
        wizard.date_from = '2026-11-01'
        with self.assertRaises(UserError):
            wizard.action_show_visits()

    def test_server_action_selection_and_cron(self):
        yesterday = fields.Datetime.now() - timedelta(days=1)
        tomorrow = fields.Datetime.now() + timedelta(days=1)
        overdue = self.visits[0].copy({'visit_datetime': yesterday})
        untouched = self.visits[0].copy({'visit_datetime': yesterday})
        future = self.visits[0].copy({'visit_datetime': tomorrow})
        done = self.visits[0].copy({'visit_datetime': yesterday, 'state': 'done'})
        server = self.env.ref('hr_hospital.hospital_visit_cancel_overdue_action')
        server.with_context(active_model=self.Visit._name,
                            active_ids=(overdue | future | done).ids).run()
        self.assertEqual(overdue.state, 'cancelled')
        self.assertEqual(untouched.state, 'planned')
        self.assertEqual(future.state, 'planned')
        self.assertEqual(done.state, 'done')
        server.with_context(active_model=self.Visit._name, active_ids=[]).run()
        self.assertEqual(untouched.state, 'planned')
        cron = self.env.ref('hr_hospital.hospital_visit_cancel_overdue_cron')
        self.assertEqual((cron.interval_number, cron.interval_type), (1, 'days'))
        # Test records live in a savepoint; run the exact cron server action
        # in this transaction. A separate integration script exercises the
        # real manual trigger with committed fixtures and its own cursor.
        cron.ir_actions_server_id.with_context({}).run()
        untouched.invalidate_recordset()
        self.assertEqual(untouched.state, 'cancelled')
        self.assertEqual(future.state, 'planned')

    def test_chatter_targeted_tracking_and_completed_guard(self):
        visit = self.visits[0].with_context(tracking_disable=False, mail_notrack=False)
        self.env.flush_all()
        self.env.cr.precommit.run()
        visit.doctor_id = self.doctors[1]
        self.env.flush_all()
        self.env.cr.precommit.run()
        tracking = visit.message_ids.tracking_value_ids
        self.assertIn('doctor_id', tracking.field_id.mapped('name'))
        visit.state = 'cancelled'
        self.env.flush_all()
        self.env.cr.precommit.run()
        self.assertIn(
            'state', visit.message_ids.tracking_value_ids.field_id.mapped('name'),
        )
        before = visit.message_ids
        visit.summary = '<p>Untracked note</p>'
        self.env.flush_all()
        self.env.cr.precommit.run()
        self.assertEqual(visit.message_ids, before)
        visit.state = 'done'
        with self.assertRaises(UserError):
            visit.state = 'planned'

    def test_all_view_architectures(self):
        for model, kinds in {
            'hr.hospital.patient.visit': ['list', 'form', 'search', 'calendar',
                                          'pivot', 'graph'],
            'hr.hospital.doctor': ['list', 'form', 'search', 'kanban'],
            'hr.hospital.patient': ['list', 'form', 'search'],
            'hr.hospital.disease': ['list', 'form', 'search'],
        }.items():
            for kind in kinds:
                result = self.env[model].get_view(view_type=kind)
                arch = etree.fromstring(result['arch'])
                self.assertEqual(arch.tag, kind)
                self.assertFalse(arch.xpath('//*[@attrs or @states]'))
                if kind in ('pivot', 'graph'):
                    for node in arch.findall('field'):
                        self.assertTrue(self.env[model]._fields[node.get('name')].store)

    def test_demo_distribution(self):
        if not self.env.ref("hr_hospital.patient_visit_demo_7",
                            raise_if_not_found=False):
            self.skipTest("Demo data is not installed")
        visits = self.Visit.browse([
            self.env.ref(f'hr_hospital.patient_visit_demo_{i}').id
            for i in range(7, 13)
        ])
        self.assertEqual(len(visits), 6)
        self.assertGreater(len({v.visit_datetime.month for v in visits}), 1)
        self.assertTrue(all(
            v.visit_datetime.year == datetime.now().year for v in visits
        ))
        for i in (1, 2):
            intern = self.env.ref(f'hr_hospital.doctor_demo_intern_{i}')
            self.assertTrue(intern.is_intern)
            self.assertTrue(intern.supervisor_doctor_id)

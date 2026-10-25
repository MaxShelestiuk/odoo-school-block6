"""Exercise the role ladder with real, non-superuser environments."""
from odoo import Command, fields
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestBlock6(TransactionCase):
    """Check visibility, mutations and block-three business invariants."""

    @classmethod
    def setUpClass(cls):
        """Build independent fixtures without relying on demo records."""
        super().setUpClass()
        cls.users = {}
        for role in ('patient', 'intern', 'doctor', 'manager', 'admin', 'outsider'):
            groups = cls.env.ref('base.group_user')
            if role != 'outsider':
                groups |= cls.env.ref('hr_hospital.group_hospital_' + role)
            cls.users[role] = cls.env['res.users'].create({
                'name': role, 'login': 'test.block6.' + role,
                'group_ids': [Command.set(groups.ids)],
            })
        cls.doctor = cls.env['hr.hospital.doctor'].create({
            'name': 'Mentor', 'user_id': cls.users['doctor'].id,
        })
        cls.intern = cls.env['hr.hospital.doctor'].create({
            'name': 'Intern', 'user_id': cls.users['intern'].id,
            'supervisor_doctor_id': cls.doctor.id,
            'category_id': cls.env.ref('hr_hospital.doctor_category_intern').id,
        })
        cls.other = cls.env['hr.hospital.doctor'].create({'name': 'Other'})
        cls.patient = cls.env['hr.hospital.patient'].create({
            'name': 'Patient', 'user_id': cls.users['patient'].id,
        })
        cls.other_patient = cls.env['hr.hospital.patient'].create({'name': 'Other'})
        cls.visits = cls.env['hr.hospital.patient.visit'].create([
            {'name': 'Own patient', 'patient_id': cls.patient.id,
             'doctor_id': cls.other.id},
            {'name': 'Mentor visit', 'patient_id': cls.other_patient.id,
             'doctor_id': cls.doctor.id},
            {'name': 'Intern visit', 'patient_id': cls.other_patient.id,
             'doctor_id': cls.intern.id},
            {'name': 'Other visit', 'patient_id': cls.other_patient.id,
             'doctor_id': cls.other.id},
        ])

    def test_exact_visibility_and_read(self):
        """Each role sees precisely its patient, doctor or supervisor domain."""
        for role, indexes in {
            'patient': [0], 'intern': [2], 'doctor': [1, 2],
            'manager': [0, 1, 2, 3], 'admin': [0, 1, 2, 3],
        }.items():
            visits = self.visits.with_user(self.users[role])
            found = visits.search([('id', 'in', self.visits.ids)])
            self.assertEqual(set(found.ids), {self.visits[i].id for i in indexes})
            found.read(['name', 'patient_id', 'doctor_id', 'state'])
            for i in set(range(4)) - set(indexes):
                with self.assertRaises(AccessError):
                    visits[i].read(['name'])

    def test_write_permissions(self):
        """Read-only rules never broaden the inherited write domain."""
        for role, allowed in {'patient': [], 'intern': [2], 'doctor': [1, 2],
                              'manager': [], 'admin': [0, 1, 2, 3]}.items():
            for i, visit in enumerate(self.visits):
                if i in allowed:
                    visit.with_user(self.users[role]).write({'summary': '<p>OK</p>'})
                else:
                    with self.assertRaises(AccessError):
                        visit.with_user(self.users[role]).write({'summary': 'Denied'})

    def test_admin_delete_and_create(self):
        """Only the module administrator can create or delete visits."""
        for role in ('patient', 'intern', 'doctor', 'manager'):
            with self.assertRaises(AccessError):
                self.visits[2].with_user(self.users[role]).unlink()
            with self.assertRaises(AccessError):
                self.visits.with_user(self.users[role]).create({'name': 'Denied'})
        visit = self.visits.with_user(self.users['admin']).create({
            'name': 'Completed', 'state': 'done',
        })
        visit.unlink()
        self.assertFalse(visit.exists())

    def test_outsider_all_models(self):
        """An internal user outside the ladder gets no hospital access."""
        for model in ('hr.hospital.patient.visit', 'hr.hospital.patient',
                      'hr.hospital.doctor', 'hr.hospital.disease',
                      'hospital.doctor.category', 'hospital.doctor.history'):
            with self.assertRaises(AccessError):
                self.env[model].with_user(self.users['outsider']).search([])

    def test_patient_identity_is_protected(self):
        """A patient cannot take over another identity or inspect its history."""
        with self.assertRaises(AccessError):
            self.patient.with_user(self.users['patient']).write({
                'user_id': self.users['doctor'].id,
            })
        with self.assertRaises(AccessError):
            self.other_patient.with_user(self.users['patient']).read(['name'])

    def test_compute_age(self):
        """Compute age for a birthday today and for an unknown birthday."""
        today = fields.Date.today()
        self.patient.birth_date = today.replace(year=today.year - 20)
        self.assertEqual(self.patient.age, 20)
        self.patient.birth_date = False
        self.assertEqual(self.patient.age, 0)

    def test_compute_intern_and_supervisor_constraint(self):
        """Qualification controls intern status and excludes intern mentors."""
        self.assertTrue(self.intern.is_intern)
        self.assertFalse(self.doctor.is_intern)
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.doctor.supervisor_doctor_id = self.intern

    def test_disease_hierarchy_cycle(self):
        """Hierarchy computes names and rejects cycles transactionally."""
        root = self.env['hr.hospital.disease'].create({'name': 'Root'})
        child = root.copy({'name': 'Child', 'parent_id': root.id})
        self.assertEqual(child.complete_name, 'Root / Child')
        with self.assertRaises(ValidationError), self.cr.savepoint():
            root.parent_id = child

    def test_completed_visit_write_guard_with_user(self):
        """A real doctor cannot reschedule or reopen a completed visit."""
        visit = self.visits[1].with_user(self.users['doctor'])
        visit.write({'state': 'done'})
        for vals in ({'state': 'planned'}, {'active': False},
                     {'doctor_id': self.other.id},
                     {'visit_datetime': '2030-01-01 12:00:00'}):
            with self.assertRaises(UserError):
                visit.write(vals)
        visit.write({'summary': '<p>Follow-up note</p>'})
        self.assertIn('Follow-up', visit.summary)

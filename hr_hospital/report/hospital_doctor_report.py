from odoo import api, fields, models


class ReportHospitalDoctor(models.AbstractModel):
    _name = 'report.hr_hospital.report_hospital_doctor'
    _description = 'Hospital Doctor PDF Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        doctors = self.env['hr.hospital.doctor'].browse(docids).exists()
        visit_model = self.env['hr.hospital.patient.visit'].with_context(
            active_test=False,
        )

        visits_by_doctor = {}
        patients_by_doctor = {}
        for doctor in doctors:
            visits = visit_model.search(
                [('doctor_id', '=', doctor.id)],
                order="visit_datetime desc nulls last, id desc",
            )
            assigned_patients = self.env['hr.hospital.patient'].search(
                [('personal_doctor_id', '=', doctor.id)],
            )
            visits_by_doctor[doctor.id] = visits
            patients_by_doctor[doctor.id] = (
                assigned_patients | visits.mapped('patient_id')
            )

        return {
            'doc_ids': docids,
            'doc_model': 'hr.hospital.doctor',
            'docs': doctors,
            'visits_by_doctor': visits_by_doctor,
            'patients_by_doctor': patients_by_doctor,
            'print_datetime': fields.Datetime.now(),
        }

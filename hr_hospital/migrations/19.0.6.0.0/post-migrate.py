"""Normalize shipped disease sources without overwriting custom labels."""
from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    """Move known Ukrainian demo labels into their translation slot."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    terms = {
        'doctor_category_intern': ('Лікар-інтерн', 'Intern Doctor'),
        'doctor_category_specialist': ('Лікар-спеціаліст', 'Specialist Doctor'),
        'doctor_category_highest': ('Лікар вищої категорії', 'Highest Category Doctor'),
        'hospital_visit_cancel_overdue_cron': (
            'Hospital: скасування протермінованих візитів',
            'Hospital: Cancel Overdue Visits',
        ),
        'disease_demo_infectious': ('Інфекційні', 'Infectious Diseases'),
        'disease_demo_viral': ('Вірусні', 'Viral Diseases'),
        'disease_demo_flu': ('Грип', 'Influenza'),
        'disease_demo_bacterial': ('Бактеріальні', 'Bacterial Diseases'),
        'disease_demo_scarlet_fever': ('Скарлатина', 'Scarlet Fever'),
    }
    for xmlid, (ukrainian, english) in terms.items():
        record = env.ref('hr_hospital.' + xmlid, raise_if_not_found=False)
        if record and record.with_context(lang='en_US').name == ukrainian:
            record.with_context(lang='en_US').name = english
            if env['res.lang'].search_count([('code', '=', 'uk_UA')]):
                record.with_context(lang='uk_UA').name = ukrainian

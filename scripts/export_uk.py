"""Run with odoo-bin shell -d DATABASE < scripts/export_uk.py.

Odoo creates the PO structure; existing translations are retained by msgid.
Review and translate new empty entries before committing the exported file.
"""
import io
from pathlib import Path

import polib

from odoo.modules.module import get_module_path
from odoo.tools.translate import trans_export

# Odoo shell supplies env; this script is intentionally not standalone.
module = env['ir.module.module'].search([('name', '=', 'hr_hospital')])  # noqa: F821
if module.state != 'installed':
    raise RuntimeError('Install hr_hospital before exporting translations.')
env['res.lang']._activate_lang('uk_UA')  # noqa: F821

path = Path(get_module_path('hr_hospital')) / 'i18n' / 'uk_UA.po'
previous = polib.pofile(str(path)) if path.exists() else []
translations = {entry.msgid: entry.msgstr for entry in previous if entry.msgstr}
with io.BytesIO() as stream:
    trans_export('uk_UA', ['hr_hospital'], stream, 'po', env)  # noqa: F821
    catalog = polib.pofile(stream.getvalue().decode('utf-8'))
for entry in catalog:
    if entry.msgid in translations:
        entry.msgstr = translations[entry.msgid]
catalog.metadata['Language'] = 'uk_UA'
catalog.metadata['Last-Translator'] = 'Maksym Shelestiuk'
catalog.metadata['Language-Team'] = 'Ukrainian'
path.parent.mkdir(exist_ok=True)
catalog.save(str(path))
print(f'Exported {len(catalog)} entries; '
      f'{len(catalog.untranslated_entries())} require translation.')

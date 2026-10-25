"""Validate manifests, XML, PO references, RST and module description assets."""
import ast
from pathlib import Path

import polib
from docutils.core import publish_doctree
from lxml import etree, html
from PIL import Image

root = Path(__file__).resolve().parents[1]
for addon in ('hr_hospital', 'partner_email_unique'):
    folder = root / addon
    manifest = ast.literal_eval((folder / '__manifest__.py').read_text())
    assert manifest['version'].startswith('19.0.')
    for key in ('data', 'demo', 'images'):
        for path in manifest.get(key, []):
            assert (folder / path).is_file(), path
    for path in folder.rglob('*.xml'):
        etree.parse(str(path))
    for path in folder.rglob('*.rst'):
        publish_doctree(path.read_text(), settings_overrides={'halt_level': 2})
    page = folder / 'static/description/index.html'
    images = html.parse(str(page)).xpath('//img/@src')
    assert images
    for src in images + ['icon.png']:
        with Image.open(page.parent / src) as image:
            image.verify()
    print(addon, 'manifest/XML/RST/artwork OK')
catalog = polib.pofile(str(root / 'hr_hospital/i18n/uk_UA.po'))
assert not catalog.untranslated_entries()
assert not catalog.fuzzy_entries()
for entry in catalog:
    assert 'module: hr_hospital' in entry.comment
    assert entry.occurrences
print('Odoo PO:', len(catalog), 'translated entries with source references')
for folder in ('models', 'wizard', 'report'):
    for path in (root / 'hr_hospital' / folder).glob('*.py'):
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
                assert ast.get_docstring(node), (path, node.name)
print('Application classes and methods have docstrings')

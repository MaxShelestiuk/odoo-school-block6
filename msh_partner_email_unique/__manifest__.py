{
    "name": "Unique Partner Email",
    "summary": "Prevent duplicate contact emails, including imports"
    " and archived contacts",
    "description": "Database-enforced, case-insensitive email uniqueness "
    "across contacts. "
    "Blank emails remain unrestricted. Existing duplicates block installation.",
    "version": "19.0.1.0.0",
    "category": "Contacts",
    "author": "Maksym Shelestiuk",
    "website": "https://github.com/MaxShelestiuk",
    "license": "LGPL-3",
    "depends": ["base"],
    "pre_init_hook": "pre_init_hook",
    "images": ["static/description/banner.png"],
    "installable": True,
    "application": False,
    "auto_install": False,
}

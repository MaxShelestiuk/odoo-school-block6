Unique Partner Email
====================

Odoo 19 addon by Maksym Shelestiuk, licensed under LGPL-3.

Behavior
--------

A PostgreSQL unique expression index rejects duplicate contact emails on
create, update, CSV import and concurrent inserts. Comparison ignores case
and leading/trailing ASCII spaces. Missing, empty and space-only emails are
allowed. Archived contacts, child contacts and contacts across companies
share the same uniqueness namespace. Email aliases, display names and internal
spaces are not canonicalized; this module does not validate email syntax.

Installation
------------

Copy ``partner_email_unique`` into an Odoo 19 addons directory, update the
Apps list and install Unique Partner Email. Only ``base`` is required.
Existing duplicates cause a clear installation error before index creation.
Review and merge/correct duplicate contacts first; the addon never merges or
deletes contacts automatically. Shared company/person addresses must also be
resolved if they are duplicated. Uninstalling removes the index and preserves
contacts. Reinstallation checks current data again.

Testing
-------

Use an isolated database::

    odoo-bin -d email_test -i partner_email_unique --test-enable \
      --test-tags=/partner_email_unique --stop-after-init --no-http

Tests cover empty addresses, case/space normalization, archived contacts,
batch creation, update and CSV import through the ORM loader. To check the
UI, create a contact with an email and attempt another with the same email;
Odoo must display the unique-index validation message. Two contacts without
email must succeed.

Odoo Apps release
-----------------

The addon is independent of ``hr_hospital`` and can be copied unchanged to
a dedicated private GitHub repository on branch ``19.0``. It includes a
manifest, icon, banner, description page, changelog and tests. Before public
release, verify the maintainer profile, marketplace account and repository
access settings. Create or connect the Odoo Apps account, register the private
repository using the marketplace's access mechanism, and review its rendered
listing. Repository creation, push, account setup, marketplace submission and
mentor messages are not performed by this local implementation.

Provide the mentor with the repository URL, listing URL and an actual listing
screenshot after publication. The local description page is not a marketplace
publication or proof of marketplace approval.

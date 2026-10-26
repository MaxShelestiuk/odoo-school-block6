from psycopg2 import IntegrityError

from odoo.tests import TransactionCase, tagged
from odoo.tools import mute_logger


@tagged("post_install", "-at_install")
class TestPartnerEmail(TransactionCase):
    """Check the database guarantee on create, update, batch and CSV import."""

    def test_blank_emails(self):
        """Missing and whitespace-only addresses remain unrestricted."""
        contacts = self.env["res.partner"].create(
            [
                {"name": "Blank A"},
                {"name": "Blank B", "email": False},
                {"name": "Blank C", "email": ""},
                {"name": "Blank D", "email": "  "},
            ]
        )
        self.assertEqual(len(contacts), 4)

    @mute_logger("odoo.sql_db")
    def test_case_whitespace_and_archived(self):
        """Archived contacts still reserve their case-insensitive email."""
        self.env["res.partner"].create(
            {
                "name": "First",
                "email": "unique-test@example.org",
                "active": False,
            }
        )
        with self.assertRaises(IntegrityError), self.cr.savepoint():
            self.env["res.partner"].create(
                {
                    "name": "Second",
                    "email": " UNIQUE-test@EXAMPLE.org ",
                }
            )
            self.env.flush_all()

    @mute_logger("odoo.sql_db")
    def test_write_and_batch(self):
        """Updates and batch inserts cannot bypass the unique index."""
        first, second = self.env["res.partner"].create(
            [
                {"name": "A", "email": "write-a@example.org"},
                {"name": "B", "email": "write-b@example.org"},
            ]
        )
        with self.assertRaises(IntegrityError), self.cr.savepoint():
            second.email = first.email
            self.env.flush_all()
        with self.assertRaises(IntegrityError), self.cr.savepoint():
            self.env["res.partner"].create(
                [
                    {"name": "C", "email": "batch@example.org"},
                    {"name": "D", "email": "batch@example.org"},
                ]
            )
            self.env.flush_all()

    @mute_logger("odoo.sql_db")
    def test_csv_import(self):
        """The same ORM loader used by CSV import reports duplicates."""
        result = self.env["res.partner"].load(
            ["name", "email"],
            [
                ["CSV A", "csv-block6@example.org"],
                ["CSV B", "CSV-block6@example.org"],
            ],
        )
        self.assertTrue(any(m["type"] == "error" for m in result["messages"]))
        self.assertFalse(result["ids"])

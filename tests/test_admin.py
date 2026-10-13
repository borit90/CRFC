import tempfile
import unittest
from datetime import date
from pathlib import Path
import sqlite3
from unittest.mock import patch

import app as app_module


class AdminPanelTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_database_path = app_module.app.config["DATABASE_PATH"]
        app_module.app.config["DATABASE_PATH"] = Path(self.temp_dir.name) / "club.sqlite3"
        app_module.initialize_database()
        self.credentials = patch.multiple(
            app_module,
            ADMIN_USERNAME="test-admin",
            ADMIN_PASSWORD="test-password",
        )
        self.credentials.start()
        self.client = app_module.app.test_client()

    def tearDown(self):
        self.credentials.stop()
        app_module.app.config["DATABASE_PATH"] = self.original_database_path
        self.temp_dir.cleanup()

    def csrf_token(self):
        with self.client.session_transaction() as browser_session:
            token = browser_session.get("_csrf_token")
        if token:
            return token
        response = self.client.get("/admin/login")
        self.assertEqual(response.status_code, 200)
        with self.client.session_transaction() as browser_session:
            return browser_session["_csrf_token"]

    def sign_in(self):
        token = self.csrf_token()
        response = self.client.post(
            "/admin/login",
            data={
                "csrf_token": token,
                "username": "test-admin",
                "password": "test-password",
            },
        )
        self.assertEqual(response.status_code, 302)
        dashboard = self.client.get("/admin")
        self.assertEqual(dashboard.status_code, 200)
        self.assertIn(b"Admin Control Panel", dashboard.data)

    def test_admin_panel_redirects_to_login_when_unauthenticated(self):
        response = self.client.get("/admin")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, "/admin/login")

    def test_invalid_credentials_are_rejected(self):
        token = self.csrf_token()

        response = self.client.post(
            "/admin/login",
            data={
                "csrf_token": token,
                "username": "test-admin",
                "password": "wrong-password",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"username or password was incorrect", response.data)

    def test_results_can_be_added_updated_and_removed(self):
        self.sign_in()
        token = self.csrf_token()
        response = self.client.post(
            "/admin/results/save",
            data={
                "csrf_token": token,
                "date": "October 10, 2026",
                "opponent": "Test United",
                "score": "3-1",
                "venue": "Home",
                "competition": "League",
                "goalscorers": "Jamie LePage, Finlay Parry (2)",
            },
        )
        self.assertEqual(response.status_code, 302)
        result = app_module.get_collection("results")[-1]

        public_results = self.client.get("/results")
        self.assertIn(b"Jamie LePage, Finlay Parry (2)", public_results.data)

        response = self.client.post(
            "/admin/results/save",
            data={
                "csrf_token": token,
                "id": result["id"],
                "date": result["date"],
                "opponent": result["opponent"],
                "score": "4-1",
                "venue": result["venue"],
                "competition": result["competition"],
                "goalscorers": "Updated scorer",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(b"Updated scorer", self.client.get("/results").data)

        response = self.client.post(
            f"/admin/results/{result['id']}/delete",
            data={"csrf_token": token},
        )
        self.assertEqual(response.status_code, 302)
        self.assertNotIn(
            "Test United",
            [record["opponent"] for record in app_module.get_collection("results")],
        )

    def test_players_and_staff_can_be_managed(self):
        self.sign_in()
        token = self.csrf_token()
        player_response = self.client.post(
            "/admin/players/save",
            data={
                "csrf_token": token,
                "name": "New Player",
                "position": "Forward",
                "number": "99",
                "bio": "Test profile",
            },
        )
        self.assertEqual(player_response.status_code, 302)
        self.assertIn(b"New Player", self.client.get("/players").data)

        staff_response = self.client.post(
            "/admin/staff/save",
            data={
                "csrf_token": token,
                "name": "New Staff Member",
                "role": "Assistant Manager",
                "bio": "Manager profile",
            },
        )
        self.assertEqual(staff_response.status_code, 302)
        staff_member = app_module.get_collection("staff")[-1]
        self.assertIn(b"New Staff Member", self.client.get("/staff").data)

        update_response = self.client.post(
            "/admin/staff/save",
            data={
                "csrf_token": token,
                "id": staff_member["id"],
                "name": "New Staff Member",
                "role": "First Team Coach",
                "bio": "Updated profile",
            },
        )
        self.assertEqual(update_response.status_code, 302)
        self.assertEqual(app_module.get_collection("staff")[-1]["role"], "First Team Coach")

        delete_response = self.client.post(
            f"/admin/staff/{staff_member['id']}/delete",
            data={"csrf_token": token},
        )
        self.assertEqual(delete_response.status_code, 302)
        self.assertNotIn(
            "New Staff Member",
            [member["name"] for member in app_module.get_collection("staff")],
        )

    def test_admin_mutations_require_csrf_token(self):
        self.sign_in()

        response = self.client.post(
            "/admin/results/save",
            data={"opponent": "Invalid", "score": "0-0"},
        )

        self.assertEqual(response.status_code, 400)

    def test_admin_tabs_include_fixture_management(self):
        self.sign_in()

        response = self.client.get("/admin")

        self.assertIn(b'role="tablist"', response.data)
        for section in (b"Players", b"Staff", b"Results", b"Fixtures"):
            self.assertIn(section, response.data)
        self.assertIn(b'id="panel-fixtures"', response.data)

    def test_fixtures_can_be_added_updated_and_removed_in_admin(self):
        self.sign_in()
        token = self.csrf_token()
        response = self.client.post(
            "/admin/fixtures/save",
            data={
                "csrf_token": token,
                "date": "2099-10-13",
                "opponent": "Tab Test FC",
                "venue": "Test Ground",
                "competition": "Cup",
            },
        )
        self.assertEqual(response.status_code, 302)
        fixture = app_module.get_collection("fixtures")[-1]
        self.assertIn(b"Tab Test FC", self.client.get("/fixtures").data)

        response = self.client.post(
            "/admin/fixtures/save",
            data={
                "csrf_token": token,
                "id": fixture["id"],
                "date": fixture["date"],
                "opponent": "Updated Test FC",
                "venue": fixture["venue"],
                "competition": fixture["competition"],
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(b"Updated Test FC", self.client.get("/fixtures").data)

        response = self.client.post(
            f"/admin/fixtures/{fixture['id']}/delete",
            data={"csrf_token": token},
        )
        self.assertEqual(response.status_code, 302)
        self.assertNotIn(
            fixture["id"],
            [item["id"] for item in app_module.get_collection("fixtures")],
        )


class FixtureDateTests(unittest.TestCase):
    def test_only_fixtures_before_today_are_hidden(self):
        fixtures = [
            {"opponent": "Past", "date": "October 12, 2026"},
            {"opponent": "Today", "date": "October 13, 2026"},
            {"opponent": "Future", "date": "2026-10-14"},
        ]
        original_get_collection = app_module.get_collection
        with patch.object(
            app_module,
            "get_collection",
            side_effect=lambda collection: fixtures if collection == "fixtures" else original_get_collection(collection),
        ):
            upcoming = app_module.get_upcoming_matches(today=date(2026, 10, 13))

        self.assertEqual([match["opponent"] for match in upcoming], ["Today", "Future"])

    def test_fixture_screen_and_homepage_omit_past_fixtures(self):
        fixtures = [
            {"opponent": "Past Fixture", "date": "January 1, 2020", "venue": "Old", "competition": "League"},
            {"opponent": "Future Fixture", "date": "December 31, 2099", "venue": "New", "competition": "Cup"},
        ]
        original_get_collection = app_module.get_collection
        with patch.object(
            app_module,
            "get_collection",
            side_effect=lambda collection: fixtures if collection == "fixtures" else original_get_collection(collection),
        ):
            fixtures_response = app_module.app.test_client().get("/fixtures")
            home_response = app_module.app.test_client().get("/home")

        self.assertEqual(fixtures_response.status_code, 200)
        self.assertNotIn(b"Past Fixture", fixtures_response.data)
        self.assertIn(b"Future Fixture", fixtures_response.data)
        self.assertNotIn(b"Past Fixture", home_response.data)
        self.assertIn(b"Future Fixture", home_response.data)


class StaffMigrationTests(unittest.TestCase):
    def test_existing_database_gets_manager_once(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "legacy.sqlite3"
            connection = sqlite3.connect(database_path)
            try:
                for collection, schema in app_module.COLLECTION_SCHEMAS.items():
                    connection.execute(schema)
                    fields = app_module.COLLECTION_FIELDS[collection]
                    records = (
                        app_module.matches
                        if collection == "fixtures"
                        else getattr(app_module, collection)
                    )
                    if collection == "staff":
                        records = [
                            member for member in records
                            if member["name"] != "Jamie LePage"
                        ]
                    placeholders = ", ".join("?" for _ in fields)
                    field_names = ", ".join(fields)
                    connection.executemany(
                        f"INSERT INTO {collection} ({field_names}) VALUES ({placeholders})",
                        [tuple(record.get(field, "") for field in fields) for record in records],
                    )
                connection.commit()
            finally:
                connection.close()

            original_database_path = app_module.app.config["DATABASE_PATH"]
            app_module.app.config["DATABASE_PATH"] = database_path
            try:
                app_module.initialize_database()
                jamie_records = [
                    member for member in app_module.get_collection("staff")
                    if member["name"] == "Jamie LePage"
                ]
                self.assertEqual(len(jamie_records), 1)
                self.assertEqual(jamie_records[0]["role"], "First Team Manager")

                with app_module.get_db_connection() as connection:
                    connection.execute(
                        "DELETE FROM staff WHERE name = ?", ("Jamie LePage",)
                    )
                app_module.initialize_database()
                self.assertFalse(
                    any(
                        member["name"] == "Jamie LePage"
                        for member in app_module.get_collection("staff")
                    )
                )
            finally:
                app_module.app.config["DATABASE_PATH"] = original_database_path


if __name__ == "__main__":
    unittest.main()

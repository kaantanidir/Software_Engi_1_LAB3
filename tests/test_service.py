"""Regression tests for the selected features and their failure/authorization paths."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import json
from pathlib import Path
import tempfile
import unittest

from smartbrew.service import RuleError, Store


class SmartBrewTests(unittest.TestCase):
    """Each test owns a clean database, so it never consumes a demonstrator's stock."""

    def setUp(self):
        """Purpose: create isolated fixtures. Inputs: test instance. Returns: None."""
        test_root = Path(__file__).resolve().parents[1] / "tmp" / "tests"
        test_root.mkdir(parents=True, exist_ok=True)
        self.folder = tempfile.TemporaryDirectory(dir=test_root)
        self.store = Store(Path(self.folder.name) / "test.db")
        _, self.customer = self.store.auth("login", {"email": "alex@smartbrew.test", "password": "DemoPass123!"})
        _, self.tech = self.store.auth("login", {"email": "tech@smartbrew.test", "password": "246810"})
        self.body = {"config": {"drink": "latte", "milk": "oat"}, "method": "contactless", "points": 0, "key": "test-purchase-001"}

    def tearDown(self):
        """Purpose: delete isolated test fixtures. Inputs: test instance. Returns: None."""
        self.folder.cleanup()

    def test_account_credentials_nfc_and_defaults(self):
        """Purpose: verify F01 identity/preferences persistence. Inputs: seeded/new accounts. Returns: None."""
        response, token = self.store.auth("register", {"email": "new@example.test", "name": "New", "password": "UniquePass123!"})
        self.assertEqual(response["user"]["points"], 0)
        with self.assertRaises(RuleError):
            self.store.auth("register", {"email": "new@example.test", "name": "New", "password": "UniquePass123!"})
        with self.assertRaises(RuleError):
            self.store.auth("login", {"email": "alex@smartbrew.test", "password": "wrong"})
        response, nfc = self.store.auth("login", {"method": "nfc", "nfc": "DEMO-NFC-001"})
        self.assertEqual(response["user"]["name"], "Alex")
        self.store.auth("profile", {"milk": "oat", "strength": "strong", "temperature": 75}, nfc)
        self.assertEqual(Store(self.store.path).state(nfc)["user"]["preferences"]["milk"], "oat")
        self.store.auth("logout", {}, token)
        self.assertIsNone(self.store.state(token)["user"])

    def test_login_rejects_mixed_authentication_methods(self):
        """Purpose: prevent the hidden-NFC password bypass. Inputs: mixed or incomplete credentials. Returns: None."""
        for body in ({"email": "nobody@example.test", "password": "wrong", "nfc": "DEMO-NFC-001"},
                     {"method": "nfc", "nfc": "DEMO-NFC-001", "email": "alex@smartbrew.test"},
                     {"nfc": "DEMO-NFC-001"}, {"method": "unknown", "email": "alex@smartbrew.test"}):
            with self.assertRaises(RuleError):
                self.store.auth("login", body)

    def test_separate_accounts_keep_private_records_after_relogin(self):
        """Purpose: preserve owner isolation across sign-in/restart. Inputs: two independent customer sessions. Returns: None."""
        _, first = self.store.auth("register", {"name": "First", "email": "first@example.test", "password": "FirstPass123!"})
        _, second = self.store.auth("register", {"name": "Second", "email": "second@example.test", "password": "SecondPass123!"})
        saved = self.store.recipes(first, "save", {"name": "First private recipe", "config": self.body["config"]})
        order = self.store.checkout(first, self.body)["order"]
        self.assertEqual(self.store.state(second)["recipes"], [])
        self.assertEqual(self.store.state(second)["orders"], [])
        for action in ("update", "delete"):
            with self.assertRaises(RuleError):
                self.store.recipes(second, action, {"id": saved["id"], "name": "Stolen", "config": {}})
        with self.assertRaises(RuleError):
            self.store.email_receipt(second, {"id": order["id"]})
        self.store.auth("logout", {}, first)
        _, again = self.store.auth("login", {"method": "password", "email": "first@example.test", "password": "FirstPass123!"})
        restored = Store(self.store.path).state(again)
        self.assertEqual(restored["user"]["name"], "First")
        self.assertEqual(restored["recipes"][0]["id"], saved["id"])
        self.assertEqual(restored["orders"][0]["id"], order["id"])

    def test_menu_categories_nutrition(self):
        """Purpose: verify F02 menu details. Inputs: seeded catalog. Returns: None."""
        menu = self.store.state()["menu"]
        self.assertEqual({drink["category"] for drink in menu}, {"Coffee", "Chocolate"})
        self.assertTrue(all(isinstance(d["kcal"], int) and isinstance(d["allergens"], list) for d in menu))
        self.assertEqual(len(menu), 6)

    def test_quote_customization_and_validation(self):
        """Purpose: verify F03 settings, pricing and validation. Inputs: custom recipe. Returns: None."""
        with self.store.connection() as db:
            base = self.store.quote(db, {"drink": "latte"})
            custom = self.store.quote(db, {"drink": "latte", "milk": "oat", "extra": 1, "syrup": 2, "temperature": 75})
        self.assertEqual(custom["price"] - base["price"], 1500)
        self.assertEqual(custom["ingredients"]["syrup"], 20)
        self.assertEqual(custom["allergens"], ["oats"])
        for field, value in (("temperature", 500), ("extra", -1), ("syrup", True), ("milk", "unknown")):
            with self.assertRaises(RuleError):
                self.store.config({field: value})

    def test_saved_recipe_management_and_ownership(self):
        """Purpose: verify F04 CRUD and ownership. Inputs: two customers. Returns: None."""
        recipe = self.store.recipes(self.customer, "save", {"name": "Morning oat", "config": self.body["config"]})
        recipe_id = recipe["id"]
        self.store.recipes(self.customer, "update", {"id": recipe_id, "name": "Afternoon oat", "config": {"drink": "mocha"}})
        self.assertEqual(self.store.state(self.customer)["recipes"][0]["name"], "Afternoon oat")
        _, other = self.store.auth("register", {"email": "other@example.test", "name": "Other", "password": "AnotherPass123!"})
        with self.assertRaises(RuleError):
            self.store.recipes(other, "delete", {"id": recipe_id})
        self.store.recipes(self.customer, "delete", {"id": recipe_id})
        self.assertEqual(self.store.state(self.customer)["recipes"], [])

    def test_availability_threshold_and_quantity(self):
        """Purpose: verify F05 threshold and checkout revalidation. Inputs: changing stock. Returns: None."""
        self.store.admin(self.tech, "stock", {"ingredient": "oat", "level": 99})
        with self.assertRaises(RuleError):
            self.store.checkout(self.customer, self.body)
        self.store.admin(self.tech, "stock", {"ingredient": "oat", "level": 150})
        with self.store.connection() as db:
            self.assertFalse(self.store.quote(db, self.body["config"])["available"])
            self.assertTrue(self.store.quote(db, {"drink": "espresso"})["available"])
        self.store.admin(self.tech, "refill", {"ingredient": "oat"})
        self.assertEqual(self.store.checkout(self.customer, self.body)["status"], "completed")

    def test_recommendation_context_history_and_availability(self):
        """Purpose: verify F06 ranking signals/fallback. Inputs: weather/time/history/stock. Returns: None."""
        before = self.store.recommendations(self.customer)["recommendations"]
        self.store.admin(self.tech, "context", {"network": True, "weather": "warm", "period": "afternoon", "email_ok": True})
        after = self.store.recommendations(self.customer)["recommendations"]
        self.assertNotEqual([d["score"] for d in before], [d["score"] for d in after])
        self.store.checkout(self.customer, self.body)
        ranked = self.store.recommendations(self.customer)["recommendations"]
        latte = next(d for d in ranked if d["config"]["drink"] == "latte")
        self.assertIn("A frequent choice", latte["reasons"])
        self.store.admin(self.tech, "stock", {"ingredient": "beans", "level": 0})
        self.assertTrue(all(d["config"]["drink"] == "cocoa" for d in self.store.recommendations()["recommendations"]))

    def test_recommendation_periods_temperatures_conditions_and_tie_breaks(self):
        """Purpose: verify every period, temperature, weather condition, offline rule and tie-breaker. Inputs: guest context matrix. Returns: None."""
        expected_periods = (
            ("morning", "espresso", 18, "Morning pick-me-up"),
            ("afternoon", "latte", 16, "Smooth afternoon balance"),
            ("evening", "cocoa", 18, "Gentle evening unwind"),
            ("night", "cocoa", 20, "Late-hour comfort pick"),
        )
        for period, top_drink, top_score, reason in expected_periods:
            self.store.admin(self.tech, "context", {"network": False, "weather": "cold", "condition": "snowy", "period": period, "email_ok": True})
            payload = self.store.recommendations()
            ranked = payload["recommendations"]
            self.assertEqual(ranked[0]["config"]["drink"], top_drink)
            self.assertEqual(ranked[0]["score"], top_score)
            self.assertIn(reason, ranked[0]["reasons"])
            self.assertIn("Local context; weather offline", ranked[0]["reasons"])
            self.assertIn("weather unavailable", payload["context"])

        expected_temps = (
            ("cold", "cocoa", 18, "Rich warmth for cold weather"),
            ("mild", "cappuccino", 15, "Balanced for mild weather"),
            ("warm", "americano", 16, "Lighter profile for warm weather"),
            ("hot", "americano", 17, "Clean, lighter profile for hot weather"),
        )
        for weather, target_drink, expected_score, reason in expected_temps:
            self.store.admin(self.tech, "context", {"network": True, "weather": weather, "period": "night", "email_ok": True})
            ranked = self.store.recommendations()["recommendations"]
            entry = next(d for d in ranked if d["config"]["drink"] == target_drink)
            if weather != "cold":
                self.assertEqual(entry["score"], expected_score)
            self.assertIn(reason, entry["reasons"])
            for item in ranked:
                for cond_reason in ("Crisp pick for sunny skies", "Smooth comfort for cloudy skies", "Cozy choice for a rainy day", "Extra-cozy for snowy weather"):
                    self.assertNotIn(cond_reason, item["reasons"])

        expected_conditions = (
            ("unknown", "americano", 19, None),
            ("sunny", "americano", 22, "Crisp pick for sunny skies"),
            ("cloudy", "latte", 24, "Smooth comfort for cloudy skies"),
            ("rainy", "latte", 23, "Cozy choice for a rainy day"),
            ("snowy", "latte", 24, "Extra-cozy for snowy weather"),
        )
        for condition, target_drink, expected_score, reason in expected_conditions:
            self.store.admin(self.tech, "context", {"network": True, "weather": "warm", "condition": condition, "period": "afternoon", "email_ok": True})
            ranked = self.store.recommendations()["recommendations"]
            entry = next(d for d in ranked if d["config"]["drink"] == target_drink)
            self.assertEqual(entry["score"], expected_score)
            if reason:
                self.assertIn(reason, entry["reasons"])

        self.store.admin(self.tech, "context", {"network": True, "weather": "cold", "condition": "rainy", "period": "morning", "email_ok": True})
        rainy_morning = self.store.recommendations()["recommendations"]
        self.assertEqual([ (d["config"]["drink"], d["score"]) for d in rainy_morning ], [
            ("cappuccino", 23),
            ("cocoa", 22),
            ("latte", 21),
            ("mocha", 21),
            ("americano", 19),
            ("espresso", 18),
        ])

    def test_recommendation_period_mode_manual_vs_controlled_clock(self):
        """Purpose: verify deterministic clock periods versus manual technician override. Inputs: injected clock hours. Returns: None."""
        clock_cases = (
            (5, "morning"),
            (11, "morning"),
            (12, "afternoon"),
            (16, "afternoon"),
            (17, "evening"),
            (21, "evening"),
            (22, "night"),
            (3, "night"),
        )
        for hour, expected_period in clock_cases:
            self.store.clock = lambda h=hour: datetime(2026, 10, 21, h, 15)
            self.store.admin(self.tech, "context", {"network": True, "weather": "mild", "condition": "unknown", "period_mode": "auto", "period": "morning", "email_ok": True})
            auto_result = self.store.recommendations()
            self.assertEqual(auto_result["effective_period"], expected_period)
            self.assertEqual(auto_result["period_source"], "local_clock")
            self.assertIn("(local clock)", auto_result["context"])

        self.store.clock = lambda: datetime(2026, 10, 21, 23, 45)
        self.store.admin(self.tech, "context", {"network": True, "weather": "mild", "condition": "unknown", "period_mode": "manual", "period": "morning", "email_ok": True})
        manual_result = self.store.recommendations()
        self.assertEqual(manual_result["effective_period"], "morning")
        self.assertEqual(manual_result["period_source"], "technician_override")
        self.assertIn("(technician override)", manual_result["context"])

    def test_recommendation_personalization_ownership_caps_and_pending_exclusion(self):
        """Purpose: verify two-customer isolation, saved recipes, 3-order cap and pending/declined exclusion. Inputs: two customer sessions. Returns: None."""
        _, first = self.store.auth("register", {"name": "First", "email": "first-rec@example.test", "password": "FirstPass123!"})
        _, second = self.store.auth("register", {"name": "Second", "email": "second-rec@example.test", "password": "SecondPass123!"})
        self.store.auth("profile", {"milk": "none", "strength": "strong", "temperature": 85}, first)
        self.store.admin(self.tech, "context", {"network": True, "weather": "cold", "condition": "snowy", "period": "night", "email_ok": True})

        guest_ranked = self.store.recommendations()["recommendations"]
        self.assertEqual(guest_ranked[0]["config"]["drink"], "cocoa")
        self.assertEqual(guest_ranked[0]["score"], 33)
        self.assertEqual(guest_ranked[0]["config"]["milk"], "dairy")

        self.store.recipes(first, "save", {"name": "Pure Espresso", "config": {"drink": "espresso", "milk": "none", "strength": "strong", "temperature": 85}})
        after_save = {d["config"]["drink"]: d for d in self.store.recommendations(first)["recommendations"]}
        self.assertEqual(after_save["espresso"]["score"], 35)
        self.assertIn("In your saved recipes", after_save["espresso"]["reasons"])
        self.assertIn("Matches your no-milk preference", after_save["espresso"]["reasons"])
        self.assertIn("Matches your strong strength preference", after_save["espresso"]["reasons"])

        for idx, expected_score in enumerate((47, 59, 71, 71), start=1):
            self.store.checkout(first, {"config": {"drink": "espresso", "milk": "none", "strength": "strong", "temperature": 85}, "method": "contactless", "points": 0, "key": f"esp-cap-00{idx}"})
            ranked_first = self.store.recommendations(first)["recommendations"]
            self.assertEqual(ranked_first[0]["config"]["drink"], "espresso")
            self.assertEqual(ranked_first[0]["score"], expected_score)
            self.assertIn("A frequent choice", ranked_first[0]["reasons"])

        second_ranked = {d["config"]["drink"]: d for d in self.store.recommendations(second)["recommendations"]}
        self.assertNotIn("In your saved recipes", second_ranked["espresso"]["reasons"])
        self.assertNotIn("A frequent choice", second_ranked["espresso"]["reasons"])
        self.assertEqual(second_ranked["espresso"]["score"], 10)

        self.store.admin(self.tech, "simulation", {"payment_mode": "decline"})
        with self.assertRaises(RuleError):
            self.store.checkout(second, {"config": {"drink": "mocha"}, "method": "contactless", "points": 0, "key": "declined-mocha-001"})
        self.store.admin(self.tech, "simulation", {"payment_mode": "normal"})
        self.store.admin(self.tech, "context", {"network": False, "weather": "cold", "condition": "snowy", "period": "night", "email_ok": False})
        pending = self.store.checkout(second, {"config": {"drink": "mocha"}, "method": "apple_pay", "points": 0, "key": "pending-mocha-001"})
        self.assertEqual(pending["status"], "pending")
        second_after = {d["config"]["drink"]: d for d in self.store.recommendations(second)["recommendations"]}
        self.assertNotIn("A frequent choice", second_after["mocha"]["reasons"])

    def test_recommendations_use_the_customers_actual_preferences(self):
        """Purpose: rank purchasable personalized variants. Inputs: oat preference and depleted dairy. Returns: None."""
        self.store.auth("profile", {"milk": "oat", "strength": "strong", "temperature": 75}, self.customer)
        self.store.admin(self.tech, "stock", {"ingredient": "dairy", "level": 0})
        latte = next(row for row in self.store.recommendations(self.customer)["recommendations"] if row["config"]["drink"] == "latte")
        self.assertEqual(latte["config"]["milk"], "oat")
        self.assertEqual(latte["config"]["temperature"], 75)
        self.assertTrue(latte["available"])

    def test_payment_snapshot_and_persistence(self):
        """Purpose: verify F07 immutable records. Inputs: completed custom order. Returns: None."""
        result = self.store.checkout(self.customer, self.body)
        self.body["config"]["milk"] = "dairy"
        records = Store(self.store.path).state(self.customer)["orders"]
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["recipe"]["config"]["milk"], "oat")
        self.assertEqual(result["order"]["paid"], 3900)

    def test_all_payment_methods(self):
        """Purpose: verify all five simulated payment adapters. Inputs: method fixtures. Returns: None."""
        for method in ("contactless", "emv_chip", "apple_pay", "google_pay", "prepaid"):
            result = self.store.checkout(self.customer, {**self.body, "key": "method-test-" + method, "method": method})
            self.assertEqual(result["status"], "completed")

    def test_decline_has_no_partial_effects(self):
        """Purpose: verify atomic failure across stock/points/waste/balance. Inputs: forced decline. Returns: None."""
        self.store.admin(self.tech, "simulation", {"payment_mode": "decline"})
        before_user = self.store.state(self.customer)["user"]
        before_admin = self.store.state(self.tech)
        with self.assertRaises(RuleError):
            self.store.checkout(self.customer, {**self.body, "points": 100})
        self.assertEqual(before_user, self.store.state(self.customer)["user"])
        self.assertEqual(before_admin["ingredients"], self.store.state(self.tech)["ingredients"])
        self.assertEqual(before_admin["bins"], self.store.state(self.tech)["bins"])
        self.assertEqual(self.store.state(self.customer)["orders"], [])

    def test_only_technicians_control_payment_simulation(self):
        """Purpose: keep payment simulation server-controlled. Inputs: protected settings and forged checkout fields. Returns: None."""
        for token in (self.customer, ""):
            with self.assertRaises(RuleError):
                self.store.admin(token, "simulation", {"payment_mode": "decline"})
        for outcome in ("approve", "decline"):
            with self.assertRaises(RuleError):
                self.store.checkout(self.customer, {**self.body, "outcome": outcome})
        self.store.admin(self.tech, "simulation", {"payment_mode": "decline"})
        with self.assertRaises(RuleError) as failure:
            self.store.checkout(self.customer, self.body)
        self.assertEqual(failure.exception.status, 402)
        self.store.admin(self.tech, "simulation", {"payment_mode": "normal"})
        self.assertEqual(self.store.checkout(self.customer, self.body)["status"], "completed")

    def test_prepaid_insufficient_balance(self):
        """Purpose: reject insufficient prepaid funds. Inputs: zero-balance new user. Returns: None."""
        _, token = self.store.auth("register", {"email": "empty@example.test", "name": "Empty", "password": "AnotherPass123!"})
        with self.assertRaises(RuleError):
            self.store.checkout(token, {**self.body, "method": "prepaid"})
        self.assertEqual(self.store.state(token)["orders"], [])

    def test_idempotent_concurrent_checkout(self):
        """Purpose: verify concurrent retries cannot duplicate a purchase. Inputs: same key in two threads. Returns: None."""
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(self.store.checkout, self.customer, self.body) for _ in range(2)]
            results = [future.result() for future in futures]
        self.assertEqual(results[0]["order"]["id"], results[1]["order"]["id"])
        self.assertEqual(len(self.store.state(self.customer)["orders"]), 1)
        with self.assertRaises(RuleError):
            self.store.checkout(self.customer, {**self.body, "points": 1})

    def test_loyalty_success_limits_and_free_purchase(self):
        """Purpose: verify F08 bounded redemption/earning. Inputs: earned points and order totals. Returns: None."""
        result = self.store.checkout(self.customer, {**self.body, "points": 100})
        self.assertEqual(result["order"]["discount"], 1000)
        self.assertEqual(self.store.state(self.customer)["user"]["points"], 179)
        with self.assertRaises(RuleError):
            self.store.checkout(self.customer, {**self.body, "key": "too-many-points", "points": 500})
        with self.assertRaises(RuleError):
            self.store.checkout("", {**self.body, "key": "guest-points-001", "points": 1})
        with self.store.connection(True) as db:
            db.execute("UPDATE users SET points=300 WHERE email='alex@smartbrew.test'")
        free = self.store.checkout(self.customer, {**self.body, "key": "free-drink-001", "config": {"drink": "espresso"}, "points": 240})
        self.assertEqual(free["order"]["paid"], 0)
        self.assertEqual(self.store.state(self.customer)["user"]["points"], 60)

    def test_qr_receipt_and_email_fallback(self):
        """Purpose: verify F09 receipt ownership/outbox/fallback. Inputs: completed order/email outage. Returns: None."""
        order = self.store.checkout(self.customer, self.body)["order"]
        self.assertEqual(self.store.receipt(order["receipt"])["paid"], order["paid"])
        result = self.store.email_receipt(self.customer, {"id": order["id"]})
        self.assertTrue(result["delivered"])
        self.assertEqual(len(self.store.state(self.tech)["outbox"]), 1)
        self.store.admin(self.tech, "context", {"network": False, "weather": "cold", "period": "morning", "email_ok": False})
        self.assertFalse(self.store.email_receipt(self.customer, {"id": order["id"]})["delivered"])

    def test_refills_waste_halts_faults_and_diagnostics(self):
        """Purpose: verify F10 maintenance and safety. Inputs: full bins/fault/refill. Returns: None."""
        self.store.admin(self.tech, "waste", {"bin": "grounds", "level": 100})
        with self.assertRaises(RuleError):
            self.store.checkout(self.customer, self.body)
        self.store.admin(self.tech, "empty", {"bin": "grounds"})
        self.store.admin(self.tech, "fault", {"fault": "GRINDER_JAM"})
        with self.assertRaises(RuleError):
            self.store.checkout(self.customer, self.body)
        self.store.admin(self.tech, "fault", {"fault": ""})
        self.store.checkout(self.customer, self.body)
        self.store.admin(self.tech, "refill", {"ingredient": "oat"})
        state = self.store.state(self.tech)
        oat = next(i for i in state["ingredients"] if i["id"] == "oat")
        self.assertEqual(oat["level"], oat["capacity"])
        self.assertTrue(any(e["code"] == "GRINDER_JAM" for e in self.store.diagnostics(self.tech)["events"]))

    def test_access_control_and_hashed_credentials(self):
        """Purpose: verify security refinements. Inputs: customer/guest/DB rows. Returns: None."""
        for token in (self.customer, ""):
            with self.assertRaises(RuleError):
                self.store.admin(token, "refill", {"ingredient": "oat"})
            with self.assertRaises(RuleError):
                self.store.diagnostics(token)
        with self.store.connection() as db:
            row = db.execute("SELECT * FROM users WHERE email='alex@smartbrew.test'").fetchone()
            self.assertNotEqual(row["hash"], "DemoPass123!")
            self.assertEqual(len(row["salt"]), 32)
        self.assertNotIn("ingredients", self.store.state(self.customer))

    def test_offline_pending_reconciles_once_and_prepaid_works(self):
        """Purpose: verify offline fallback without false approval. Inputs: wallet pending/reconnect/prepaid. Returns: None."""
        self.store.admin(self.tech, "context", {"network": False, "weather": "cold", "period": "morning", "email_ok": False})
        self.assertTrue(self.store.recommendations()["recommendations"])
        request = {**self.body, "method": "apple_pay", "points": 100}
        self.assertEqual(self.store.checkout(self.customer, request)["status"], "pending")
        self.assertEqual(self.store.checkout(self.customer, request)["status"], "pending")
        self.assertEqual(self.store.state(self.customer)["orders"], [])
        self.assertEqual(len(self.store.state(self.customer)["pending"]), 1)
        self.assertEqual(self.store.state(self.customer)["pending"][0]["points"], 100)
        prepaid = self.store.checkout(self.customer, {**self.body, "key": "offline-prepaid-001", "method": "prepaid"})
        self.assertTrue(prepaid["order"]["offline"])
        self.store.admin(self.tech, "context", {"network": True, "weather": "cold", "period": "morning", "email_ok": True})
        first = self.store.checkout(self.customer, request)
        second = self.store.checkout(self.customer, request)
        self.assertEqual(first["order"]["id"], second["order"]["id"])
        self.assertEqual(self.store.state(self.customer)["pending"][0]["status"], "completed")


if __name__ == "__main__":
    unittest.main()

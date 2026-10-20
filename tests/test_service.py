"""Regression tests for the selected features and their failure/authorization paths."""

from concurrent.futures import ThreadPoolExecutor
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
        response, nfc = self.store.auth("login", {"nfc": "DEMO-NFC-001"})
        self.assertEqual(response["user"]["name"], "Alex")
        self.store.auth("profile", {"milk": "oat", "strength": "strong", "temperature": 75}, nfc)
        self.assertEqual(Store(self.store.path).state(nfc)["user"]["preferences"]["milk"], "oat")
        self.store.auth("logout", {}, token)
        self.assertIsNone(self.store.state(token)["user"])

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
        self.assertIn("A recent favorite", latte["reasons"])
        self.store.admin(self.tech, "stock", {"ingredient": "beans", "level": 0})
        self.assertTrue(all(d["config"]["drink"] == "cocoa" for d in self.store.recommendations()["recommendations"]))

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
        before_user = self.store.state(self.customer)["user"]
        before_admin = self.store.state(self.tech)
        with self.assertRaises(RuleError):
            self.store.checkout(self.customer, {**self.body, "points": 100, "outcome": "decline"})
        self.assertEqual(before_user, self.store.state(self.customer)["user"])
        self.assertEqual(before_admin["ingredients"], self.store.state(self.tech)["ingredients"])
        self.assertEqual(before_admin["bins"], self.store.state(self.tech)["bins"])
        self.assertEqual(self.store.state(self.customer)["orders"], [])

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

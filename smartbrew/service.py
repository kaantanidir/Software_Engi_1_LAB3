"""Business rules for the ten-feature SmartBrew prototype, backed by SQLite."""

from contextlib import contextmanager
from datetime import datetime, timezone
from hashlib import pbkdf2_hmac, sha256
from hmac import compare_digest
import json
from pathlib import Path
import secrets
import sqlite3
import time

MENU = [
    {"id": "espresso", "name": "Espresso", "category": "Coffee", "price": 2400, "kcal": 4, "milk_ml": 0, "beans_g": 9, "water_ml": 40, "image": "espresso.svg"},
    {"id": "americano", "name": "Americano", "category": "Coffee", "price": 2900, "kcal": 6, "milk_ml": 0, "beans_g": 12, "water_ml": 180, "image": "americano.svg"},
    {"id": "latte", "name": "Caffe Latte", "category": "Coffee", "price": 3600, "kcal": 110, "milk_ml": 180, "beans_g": 10, "water_ml": 40, "image": "latte.svg"},
    {"id": "cappuccino", "name": "Cappuccino", "category": "Coffee", "price": 3400, "kcal": 85, "milk_ml": 120, "beans_g": 10, "water_ml": 40, "image": "cappuccino.svg"},
    {"id": "mocha", "name": "Mocha", "category": "Chocolate", "price": 3900, "kcal": 190, "milk_ml": 140, "beans_g": 10, "water_ml": 40, "cocoa_g": 15, "image": "mocha.svg"},
    {"id": "cocoa", "name": "Hot Chocolate", "category": "Chocolate", "price": 3200, "kcal": 180, "milk_ml": 200, "beans_g": 0, "water_ml": 20, "cocoa_g": 20, "image": "cocoa.svg"},
]
INGREDIENTS = [("beans", "Coffee beans", "g", 1000, 20), ("water", "Water", "ml", 5000, 100),
               ("dairy", "Dairy milk", "ml", 2000, 100), ("oat", "Oat milk", "ml", 2000, 100),
               ("cocoa", "Cocoa", "g", 500, 25), ("syrup", "Vanilla syrup", "ml", 500, 20), ("cups", "Cups", "pcs", 50, 2)]
METHODS = ("emv_chip", "contactless", "apple_pay", "google_pay", "prepaid")


class RuleError(Exception):
    """An expected business-rule failure with an HTTP-friendly status."""

    def __init__(self, message, status=400):
        """Purpose: describe a rejected action. Inputs: message/status. Returns: None."""
        super().__init__(message)
        self.status = status


def stamp():
    """Purpose: timestamp audit records. Inputs: none. Returns: UTC ISO string."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def password_hash(password, salt):
    """Purpose: derive a salted credential hash. Inputs: password/salt strings. Returns: hex hash."""
    return pbkdf2_hmac("sha256", password.encode(), salt.encode(), 210000).hex()


def integer(value, name, minimum, maximum):
    """Purpose: reject invalid bounded integers. Inputs: value/name/bounds. Returns: int or raises RuleError."""
    if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
        raise RuleError(f"{name} must be an integer from {minimum} to {maximum}.")
    return value


class Store:
    """Persistence, access control, recipes and atomic checkout operations."""

    def __init__(self, path):
        """Purpose: initialize a database. Inputs: database path. Returns: None."""
        self.path = str(path)
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    @contextmanager
    def connection(self, write=False):
        """Purpose: scope a DB transaction. Inputs: write lock flag. Yields: connection; commits or rolls back."""
        conn = sqlite3.connect(self.path, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        try:
            if write:
                conn.execute("BEGIN IMMEDIATE")
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def initialize(self):
        """Purpose: create tables/demo fixtures only once. Inputs: self. Returns: None."""
        with self.connection() as db:
            db.executescript("""
            CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,email TEXT UNIQUE NOT NULL,name TEXT NOT NULL,
              salt TEXT NOT NULL,hash TEXT NOT NULL,role TEXT NOT NULL,nfc TEXT UNIQUE,prefs TEXT NOT NULL,points INTEGER NOT NULL DEFAULT 0,balance INTEGER NOT NULL DEFAULT 0);
            CREATE TABLE IF NOT EXISTS sessions(token_hash TEXT PRIMARY KEY,user_id INTEGER REFERENCES users(id),expires REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS ingredients(id TEXT PRIMARY KEY,name TEXT,unit TEXT,level INTEGER,capacity INTEGER,threshold INTEGER);
            CREATE TABLE IF NOT EXISTS bins(id TEXT PRIMARY KEY,level INTEGER,capacity INTEGER);
            CREATE TABLE IF NOT EXISTS recipes(id INTEGER PRIMARY KEY,user_id INTEGER REFERENCES users(id),name TEXT NOT NULL,config TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS orders(id INTEGER PRIMARY KEY,user_id INTEGER REFERENCES users(id),created TEXT,recipe TEXT NOT NULL,
              amount INTEGER,discount INTEGER,paid INTEGER,method TEXT,offline INTEGER,receipt TEXT UNIQUE,idem TEXT UNIQUE,request_hash TEXT);
            CREATE TABLE IF NOT EXISTS pending(id TEXT PRIMARY KEY,user_id INTEGER REFERENCES users(id),created TEXT,config TEXT,method TEXT,status TEXT NOT NULL,request_hash TEXT,points INTEGER NOT NULL DEFAULT 0);
            CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY,created TEXT,severity TEXT,code TEXT,message TEXT);
            CREATE TABLE IF NOT EXISTS outbox(id INTEGER PRIMARY KEY,created TEXT,recipient TEXT,body TEXT,order_id INTEGER REFERENCES orders(id));
            CREATE TABLE IF NOT EXISTS settings(id INTEGER PRIMARY KEY CHECK(id=1),network INTEGER,weather TEXT,period TEXT,email_ok INTEGER,fault TEXT);
            INSERT OR IGNORE INTO settings VALUES(1,1,'cold','morning',1,'');
            """)
            pending_columns = {row["name"] for row in db.execute("PRAGMA table_info(pending)")}
            if "points" not in pending_columns:
                db.execute("ALTER TABLE pending ADD COLUMN points INTEGER NOT NULL DEFAULT 0")
            for key, name, unit, capacity, threshold in INGREDIENTS:
                db.execute("INSERT OR IGNORE INTO ingredients VALUES(?,?,?,?,?,?)", (key, name, unit, capacity, capacity, threshold))
            for key in ("liquid", "grounds"):
                db.execute("INSERT OR IGNORE INTO bins VALUES(?,0,100)", (key,))
            if not db.execute("SELECT 1 FROM users LIMIT 1").fetchone():
                self.add_user(db, "alex@smartbrew.test", "DemoPass123!", "Alex", "customer", "DEMO-NFC-001", 250, 20000)
                self.add_user(db, "tech@smartbrew.test", "246810", "Technician", "technician", "MASTER-NFC-001", 0, 0)
                self.event(db, "info", "READY", "Local simulator initialized. No real payment processor is connected.")

    def add_user(self, db, email, password, name, role="customer", nfc=None, points=0, balance=0):
        """Purpose: persist a credential/profile. Inputs: DB and account values. Returns: new user id."""
        salt = secrets.token_hex(16)
        cursor = db.execute("INSERT INTO users(email,name,salt,hash,role,nfc,prefs,points,balance) VALUES(?,?,?,?,?,?,?,?,?)",
                            (email, name, salt, password_hash(password, salt), role, nfc,
                             json.dumps({"milk": "dairy", "strength": "regular", "temperature": 70}), points, balance))
        return cursor.lastrowid

    def user(self, db, token, role=None):
        """Purpose: authorize a session/role. Inputs: DB, raw session, optional role. Returns: user row or raises."""
        hashed = sha256((token or "").encode()).hexdigest()
        row = db.execute("SELECT u.* FROM users u JOIN sessions s ON u.id=s.user_id WHERE s.token_hash=? AND s.expires>?", (hashed, time.time())).fetchone()
        if row is None or (role and row["role"] != role):
            raise RuleError("Please sign in with the required role.", 403)
        return row

    def public_user(self, row):
        """Purpose: hide credentials. Inputs: user row. Returns: safe profile dictionary."""
        return {"id": row["id"], "name": row["name"], "email": row["email"], "role": row["role"], "preferences": json.loads(row["prefs"]), "points": row["points"], "balance": row["balance"]}

    def auth(self, action, data, token=""):
        """Purpose: register/login/logout/update defaults. Inputs: action, JSON body, session. Returns: response and optional cookie token."""
        with self.connection(True) as db:
            if action == "logout":
                db.execute("DELETE FROM sessions WHERE token_hash=?", (sha256(token.encode()).hexdigest(),))
                return {"ok": True}, ""
            if action == "profile":
                account = self.user(db, token, "customer")
                config = self.config({**data, "drink": "latte", "syrup": 0, "extra": 0})
                preferences = {key: config[key] for key in ("milk", "strength", "temperature")}
                db.execute("UPDATE users SET prefs=? WHERE id=?", (json.dumps(preferences), account["id"]))
                account = db.execute("SELECT * FROM users WHERE id=?", (account["id"],)).fetchone()
                return {"user": self.public_user(account)}, None
            if action == "register":
                email = str(data.get("email", "")).strip().lower()
                name = str(data.get("name", "")).strip()
                password = data.get("password", "")
                if "@" not in email or "." not in email.rsplit("@", 1)[-1] or len(email) > 120 or not 1 <= len(name) <= 60 or not isinstance(password, str) or not 10 <= len(password) <= 128:
                    raise RuleError("Enter a name, valid email and password of 10-128 characters.")
                try:
                    user_id = self.add_user(db, email, password, name, balance=0)
                except sqlite3.IntegrityError:
                    raise RuleError("This email is already registered.", 409) from None
                row = db.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
            elif action == "login":
                if data.get("nfc"):
                    row = db.execute("SELECT * FROM users WHERE nfc=?", (str(data["nfc"]),)).fetchone()
                else:
                    row = db.execute("SELECT * FROM users WHERE email=?", (str(data.get("email", "")).lower().strip(),)).fetchone()
                    password = str(data.get("password", ""))[:129]
                    if row is None or not compare_digest(password_hash(password, row["salt"]), row["hash"]):
                        row = None
                if row is None:
                    raise RuleError("Credentials were not recognized.", 403)
            else:
                raise RuleError("Unknown account action.", 404)
            new_token = secrets.token_urlsafe(32)
            db.execute("INSERT INTO sessions VALUES(?,?,?)", (sha256(new_token.encode()).hexdigest(), row["id"], time.time() + 8 * 3600))
            return {"user": self.public_user(row)}, new_token

    def config(self, values):
        """Purpose: normalize supported settings. Inputs: recipe dictionary. Returns: validated config."""
        config = {"drink": values.get("drink", "latte"), "milk": values.get("milk", "dairy"), "strength": values.get("strength", "regular"),
                  "temperature": values.get("temperature", 70), "syrup": values.get("syrup", 0), "extra": values.get("extra", 0)}
        if config["drink"] not in [d["id"] for d in MENU] or config["milk"] not in ("dairy", "oat", "none") or config["strength"] not in ("mild", "regular", "strong"):
            raise RuleError("Choose a supported drink, milk and strength.")
        integer(config["temperature"], "Temperature", 50, 90)
        integer(config["syrup"], "Syrup shots", 0, 4)
        integer(config["extra"], "Extra espresso shots", 0, 3)
        return config

    def quote(self, db, values):
        """Purpose: price/validate recipe against stock/safety. Inputs: DB/config. Returns: full quote dictionary."""
        config = self.config(values)
        drink = next(d for d in MENU if d["id"] == config["drink"])
        beans = drink["beans_g"]
        if beans:
            beans += {"mild": -2, "regular": 0, "strong": 3}[config["strength"]]
        needs = {"beans": beans + config["extra"] * 9, "water": drink["water_ml"] + config["extra"] * 30, "cups": 1}
        if drink["milk_ml"] and config["milk"] != "none":
            needs[config["milk"]] = drink["milk_ml"]
        if drink.get("cocoa_g"):
            needs["cocoa"] = drink["cocoa_g"]
        if config["syrup"]:
            needs["syrup"] = config["syrup"] * 10
        reasons = []
        stock = {r["id"]: dict(r) for r in db.execute("SELECT * FROM ingredients")}
        for ingredient, quantity in needs.items():
            if quantity and (stock[ingredient]["level"] <= 0 or stock[ingredient]["level"] < stock[ingredient]["threshold"] or stock[ingredient]["level"] < quantity):
                reasons.append(stock[ingredient]["name"] + " unavailable")
        bins = [dict(r) for r in db.execute("SELECT * FROM bins")]
        for waste in bins:
            addition = 5 if waste["id"] == "liquid" else (4 if needs["beans"] else 0)
            if waste["level"] >= waste["capacity"] or waste["level"] + addition > waste["capacity"]:
                reasons.append(waste["id"].capitalize() + " bin full")
        settings = dict(db.execute("SELECT * FROM settings WHERE id=1").fetchone())
        if settings["fault"]:
            reasons.append("Machine fault: " + settings["fault"])
        price = drink["price"] + config["extra"] * 600 + config["syrup"] * 300 + (300 if config["milk"] == "oat" and drink["milk_ml"] else 0)
        kcal = max(0, drink["kcal"] + config["syrup"] * 25 + config["extra"] * 4 - (40 if config["milk"] == "none" and drink["milk_ml"] else 0))
        allergens = ["milk"] if config["milk"] == "dairy" and drink["milk_ml"] else (["oats"] if config["milk"] == "oat" and drink["milk_ml"] else [])
        return {"config": config, "name": drink["name"], "price": price, "kcal": kcal, "allergens": allergens, "ingredients": needs,
                "available": not reasons, "reasons": reasons, "category": drink["category"], "image": drink["image"], "nutrition_note": "Illustrative recipe estimates"}

    def state(self, token=""):
        """Purpose: supply UI state without protected data leaks. Inputs: session. Returns: menu/profile or admin state."""
        with self.connection() as db:
            try:
                account = self.user(db, token)
            except RuleError:
                account = None
            settings = dict(db.execute("SELECT * FROM settings WHERE id=1").fetchone())
            result = {"user": self.public_user(account) if account else None, "settings": settings, "menu": [self.quote(db, {"drink": d["id"]}) for d in MENU]}
            if account and account["role"] == "customer":
                result["recipes"] = [dict(r, config=json.loads(r["config"])) for r in db.execute("SELECT * FROM recipes WHERE user_id=? ORDER BY id DESC", (account["id"],))]
                result["orders"] = [self.order_dict(r) for r in db.execute("SELECT * FROM orders WHERE user_id=? ORDER BY id DESC LIMIT 50", (account["id"],))]
                result["pending"] = [dict(r) for r in db.execute("SELECT id,created,method,status,config,points FROM pending WHERE user_id=? ORDER BY created DESC", (account["id"],))]
            if account and account["role"] == "technician":
                result["ingredients"] = [dict(r) for r in db.execute("SELECT * FROM ingredients")]
                result["bins"] = [dict(r) for r in db.execute("SELECT * FROM bins")]
                result["events"] = [dict(r) for r in db.execute("SELECT * FROM events ORDER BY id DESC LIMIT 100")]
                result["outbox"] = [dict(r) for r in db.execute("SELECT * FROM outbox ORDER BY id DESC LIMIT 10")]
            return result

    def recipes(self, token, action, data):
        """Purpose: save/update/delete owned recipes. Inputs: token/action/recipe data. Returns: recipe id/result."""
        with self.connection(True) as db:
            account = self.user(db, token, "customer")
            recipe_id = data.get("id")
            if action in ("update", "delete"):
                integer(recipe_id, "Recipe id", 1, 1000000000)
                owned = db.execute("SELECT 1 FROM recipes WHERE id=? AND user_id=?", (recipe_id, account["id"])).fetchone()
                if not owned:
                    raise RuleError("Recipe not found for this account.", 404)
            if action == "delete":
                db.execute("DELETE FROM recipes WHERE id=?", (recipe_id,))
                return {"ok": True}
            if action not in ("save", "update"):
                raise RuleError("Unknown recipe action.")
            name = str(data.get("name", "")).strip()
            if not 1 <= len(name) <= 60:
                raise RuleError("Give the recipe a name of 1-60 characters.")
            config = json.dumps(self.config(data.get("config", {})))
            if action == "save":
                recipe_id = db.execute("INSERT INTO recipes(user_id,name,config) VALUES(?,?,?)", (account["id"], name, config)).lastrowid
            else:
                db.execute("UPDATE recipes SET name=?,config=? WHERE id=?", (name, config, recipe_id))
            return {"id": recipe_id, "ok": True}

    def recommendations(self, token=""):
        """Purpose: score available menu using local context/history. Inputs: session. Returns: ranked drinks with reasons."""
        state = self.state(token)
        user = state["user"]
        prefs = user["preferences"] if user else {}
        history = [o["recipe"]["config"]["drink"] for o in state.get("orders", [])]
        settings = state["settings"]
        results = []
        for entry in state["menu"]:
            if not entry["available"]:
                continue
            drink = entry["config"]["drink"]
            score = 10
            reasons = []
            if drink in history:
                score += min(30, history.count(drink) * 10)
                reasons.append("A recent favorite")
            if settings["period"] == "morning" and drink in ("espresso", "americano", "cappuccino"):
                score += 15
                reasons.append("A morning coffee")
            if settings["network"] and settings["weather"] == "cold" and drink in ("cocoa", "mocha", "latte"):
                score += 12
                reasons.append("For a cool day")
            if prefs.get("milk") == "oat" and drink in ("latte", "cappuccino"):
                score += 9
                reasons.append("Pairs with your oat preference")
            if not settings["network"]:
                reasons.append("Local context; weather offline")
            results.append({**entry, "score": score, "reasons": reasons or ["Available today"]})
        results.sort(key=self.recommendation_key)
        return {"recommendations": results}

    @staticmethod
    def recommendation_key(entry):
        """Purpose: order recommendation scores. Inputs: scored drink. Returns: stable sort tuple."""
        return (-entry["score"], entry["name"])

    def checkout(self, token, data):
        """Purpose: commit one simulated purchase atomically. Inputs: optional session/checkout data. Returns: order or pending result."""
        key = str(data.get("key", ""))
        if not 8 <= len(key) <= 100:
            raise RuleError("Checkout requires a request key of 8-100 characters.")
        config = self.config(data.get("config", {}))
        method = data.get("method", "contactless")
        if method not in METHODS:
            raise RuleError("Unsupported payment method.")
        points = integer(data.get("points", 0), "Points", 0, 1000000)
        signature = sha256(json.dumps([config, method, points], sort_keys=True).encode()).hexdigest()
        with self.connection(True) as db:
            account = self.user(db, token, "customer") if token else None
            owner = account["id"] if account else None
            previous = db.execute("SELECT * FROM orders WHERE idem=?", (key,)).fetchone()
            pending = db.execute("SELECT * FROM pending WHERE id=?", (key,)).fetchone()
            if pending and (pending["user_id"] != owner or pending["request_hash"] != signature):
                raise RuleError("Request key already used for another pending payment.", 409)
            if previous:
                if previous["user_id"] != owner or previous["request_hash"] != signature:
                    raise RuleError("Request key already used for a different purchase.", 409)
                return {"status": "completed", "order": self.order_dict(previous), "replayed": True}
            quote = self.quote(db, config)
            if not quote["available"]:
                raise RuleError("Cannot order: " + "; ".join(quote["reasons"]), 409)
            if points and (not account or points > account["points"] or points * 10 > quote["price"]):
                raise RuleError("Redeem within your points balance and the drink price.")
            paid = quote["price"] - points * 10
            settings = db.execute("SELECT * FROM settings WHERE id=1").fetchone()
            if not settings["network"] and method != "prepaid" and paid:
                if not account:
                    raise RuleError("Sign in for a pending offline request, or choose an offline-capable employee card.")
                db.execute("INSERT OR IGNORE INTO pending(id,user_id,created,config,method,status,request_hash,points) VALUES(?,?,?,?,?,?,?,?)", (key, owner, stamp(), json.dumps(config, sort_keys=True), method, "pending", signature, points))
                return {"status": "pending", "message": "External authorization is unavailable. No charge or dispensing; reconnect and retry."}
            if data.get("outcome", "approve") == "decline" and paid:
                raise RuleError("Payment simulator declined. No stock, balance or points changed.", 402)
            if data.get("outcome", "approve") not in ("approve", "decline"):
                raise RuleError("Unsupported simulator outcome.")
            if method == "prepaid" and paid:
                if not account or account["balance"] < paid:
                    raise RuleError("Employee card has insufficient balance.", 402)
                db.execute("UPDATE users SET balance=balance-? WHERE id=?", (paid, owner))
            for ingredient, amount in quote["ingredients"].items():
                db.execute("UPDATE ingredients SET level=level-? WHERE id=?", (amount, ingredient))
            # These counter increments model hardware signals, not physical dispensing.
            db.execute("UPDATE bins SET level=level+5 WHERE id='liquid'")
            db.execute("UPDATE bins SET level=level+? WHERE id='grounds'", (4 if quote["ingredients"]["beans"] else 0,))
            if account:
                earned = paid // 100
                db.execute("UPDATE users SET points=points-?+? WHERE id=?", (points, earned, owner))
            receipt = secrets.token_urlsafe(18)
            cursor = db.execute("INSERT INTO orders(user_id,created,recipe,amount,discount,paid,method,offline,receipt,idem,request_hash) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                                (owner, stamp(), json.dumps(quote), quote["price"], points * 10, paid, method, int(not settings["network"]), receipt, key, signature))
            db.execute("UPDATE pending SET status='completed' WHERE id=? AND user_id=?", (key, owner))
            self.event(db, "info", "PURCHASE", f"Order {cursor.lastrowid} completed via payment simulator ({method}).")
            for row in db.execute("SELECT * FROM ingredients WHERE level<threshold"):
                self.event(db, "warning", "LOW_INGREDIENT", row["name"] + " below minimum threshold.")
            for row in db.execute("SELECT * FROM bins WHERE level>=80"):
                self.event(db, "error" if row["level"] >= 100 else "warning", "WASTE_FULL" if row["level"] >= 100 else "WASTE_HIGH", row["id"] + " waste needs emptying.")
            row = db.execute("SELECT * FROM orders WHERE id=?", (cursor.lastrowid,)).fetchone()
            return {"status": "completed", "order": self.order_dict(row), "replayed": False}

    def order_dict(self, row):
        """Purpose: decode an order without private request identifiers. Inputs: order row. Returns: public order data."""
        keys = ("id", "created", "amount", "discount", "paid", "method", "offline", "receipt")
        result = {key: row[key] for key in keys}
        result["recipe"] = json.loads(row["recipe"])
        return result

    def receipt(self, receipt_token):
        """Purpose: resolve a capability receipt. Inputs: unguessable receipt token. Returns: immutable purchase or raises."""
        with self.connection() as db:
            row = db.execute("SELECT * FROM orders WHERE receipt=?", (receipt_token,)).fetchone()
            if row is None:
                raise RuleError("Receipt not found.", 404)
            return self.order_dict(row)

    def email_receipt(self, token, data):
        """Purpose: simulate receipt email in a persistent outbox. Inputs: owner session/order/email. Returns: delivery/fallback result."""
        with self.connection(True) as db:
            account = self.user(db, token, "customer")
            order = db.execute("SELECT * FROM orders WHERE id=? AND user_id=?", (data.get("id"), account["id"])).fetchone()
            if not order:
                raise RuleError("Order not found for this account.", 404)
            email = str(data.get("email", account["email"])).strip()
            if "@" not in email or len(email) > 120:
                raise RuleError("Enter a valid email address.")
            settings = db.execute("SELECT * FROM settings WHERE id=1").fetchone()
            if not settings["network"] or not settings["email_ok"]:
                return {"delivered": False, "receipt": order["receipt"], "message": "Email simulator unavailable. Your QR receipt is still available."}
            db.execute("INSERT INTO outbox(created,recipient,body,order_id) VALUES(?,?,?,?)", (stamp(), email, json.dumps(self.order_dict(order)), order["id"]))
            return {"delivered": True, "message": "Receipt saved in the local email simulator outbox; no external email was sent."}

    def admin(self, token, action, data):
        """Purpose: maintain simulated hardware/context. Inputs: admin session/action/body. Returns: operation confirmation."""
        with self.connection(True) as db:
            self.user(db, token, "technician")
            if action == "refill":
                cursor = db.execute("UPDATE ingredients SET level=capacity WHERE id=?", (str(data.get("ingredient", "")),))
                if not cursor.rowcount:
                    raise RuleError("Unknown ingredient.")
                self.event(db, "info", "REFILL", "Technician confirmed refill: " + data["ingredient"])
            elif action == "stock":
                row = db.execute("SELECT * FROM ingredients WHERE id=?", (str(data.get("ingredient", "")),)).fetchone()
                if not row:
                    raise RuleError("Unknown ingredient.")
                level = integer(data.get("level"), "Level", 0, row["capacity"])
                db.execute("UPDATE ingredients SET level=? WHERE id=?", (level, row["id"]))
                self.event(db, "warning" if level < row["threshold"] else "info", "STOCK_SENSOR", row["name"] + f" simulated level: {level}")
            elif action in ("waste", "empty"):
                bin_id = data.get("bin")
                if bin_id not in ("liquid", "grounds"):
                    raise RuleError("Unknown waste bin.")
                level = 0 if action == "empty" else integer(data.get("level"), "Waste level", 0, 150)
                db.execute("UPDATE bins SET level=? WHERE id=?", (level, bin_id))
                self.event(db, "error" if level >= 100 else "info", "WASTE_FULL" if level >= 100 else "WASTE_UPDATE", f"{bin_id} bin at {level}%")
            elif action == "context":
                network = data.get("network", True)
                email_ok = data.get("email_ok", True)
                weather = data.get("weather", "cold")
                period = data.get("period", "morning")
                if not isinstance(network, bool) or not isinstance(email_ok, bool) or weather not in ("cold", "warm") or period not in ("morning", "afternoon"):
                    raise RuleError("Unsupported simulator context.")
                db.execute("UPDATE settings SET network=?,weather=?,period=?,email_ok=? WHERE id=1", (int(network), weather, period, int(email_ok)))
                self.event(db, "info", "CONTEXT", "Technician changed network/weather/time simulator.")
            elif action == "fault":
                fault = data.get("fault", "")
                if fault not in ("", "GRINDER_JAM", "HEATER_FAULT"):
                    raise RuleError("Unsupported fault code.")
                db.execute("UPDATE settings SET fault=? WHERE id=1", (fault,))
                self.event(db, "error" if fault else "info", fault or "FAULT_CLEARED", "Simulated fault: " + (fault or "cleared"))
            else:
                raise RuleError("Unknown maintenance action.", 404)
            return {"ok": True}

    def diagnostics(self, token):
        """Purpose: authorize a diagnostic export. Inputs: admin session. Returns: exportable local event records."""
        with self.connection() as db:
            self.user(db, token, "technician")
            return {"exported": stamp(), "events": [dict(r) for r in db.execute("SELECT * FROM events ORDER BY id DESC")]}

    @staticmethod
    def event(db, severity, code, message):
        """Purpose: append a diagnostic event. Inputs: DB/severity/code/message. Returns: None."""
        db.execute("INSERT INTO events(created,severity,code,message) VALUES(?,?,?,?)", (stamp(), severity, code, message))

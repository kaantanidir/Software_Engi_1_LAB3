## Page 1

SmartBrew AI - Task 2b Deliverable
Requirements and Planning
This document defines user stories, system requirements, and an initial product backlog for SmartBrew AI. The system is an intelligent coffee machine that supports personalized ordering, user
profiles, AI recommendations, mood-based suggestions, inventory control, payments, receipts, and technician maintenance.
Custom Feature
The custom feature added by our group is Loyalty Point Redemption. It allows customers to redeem earned loyalty points during payment to reduce or cover the cost of a beverage.
User Stories
US-01 - Browse Menu and Nutrition
As a Customer, I want to browse beverage categories and inspect nutrition information so that I can choose a drink that fits my preferences and dietary needs.
US-02 - Log In
As a Customer, I want to log in using credentials or an NFC/card tap so that I can quickly access my personal preference profile.
US-03 - Create or Manage Profile
As a Customer, I want to create and manage my preference profile so that the machine can remember my favorite drink settings.
US-04 - Customize Beverage
As a Customer, I want to customize beverage parameters such as milk type, coffee strength, temperature, and syrup shots so that I receive the exact drink I want.
US-05 - Check Ingredient Availability
As a Customer, I want the machine to prevent unavailable drink selections so that I do not order a beverage that cannot be prepared.
US-06 - Generate Recommendations
As a Customer, I want to receive personalized beverage recommendations so that I can quickly choose a drink based on my preferences, history, time of day, and context.
US-07 - Analyze Mood
As a Customer, I want the machine to analyze my mood when recommendation mode is used so that it can suggest drinks that match my current state.
US-08 - Process Natural Language Order
As a Customer, I want to request a drink using free-form natural language so that I can order complex custom drinks without manually navigating every menu option.
US-09 - Process Payment
As a Customer, I want to pay using supported methods such as contactless card, digital wallet, or prepaid employee card so that I can complete checkout quickly.


## Page 2

US-10 - Redeem Loyalty Points
As a Customer, I want to redeem loyalty points earned from previous purchases so that I can receive discounts or free drinks.
US-11 - Receive Receipt
As a Customer, I want to receive a receipt by QR code or email so that I can keep proof of my purchase.
US-12 - Manage Inventory
As a Technician, I want to register ingredient refills and monitor waste levels so that the machine remains operational and does not offer drinks with depleted ingredients.
US-13 - View Error Logs
As a Technician, I want to view real-time machine error logs so that I can diagnose problems such as grinder jams, heater faults, and low ingredient thresholds.


## Page 3

System Requirements
ID
Name
Requirement
REQ-01
Browse Menu and Nutrition
The system shall display beverage categories, available menu items, and nutrition information through the touchscreen interface.
REQ-02
User Authentication
The system shall authenticate customers using credentials or NFC/card tap and load the associated preference profile after successful login.
REQ-03
Profile Management
The system shall allow customers to create and update preference profiles containing default drink settings such as milk type, strength, and temperature.
REQ-04
Beverage Customization
The system shall allow customers to customize beverage parameters, including milk type, coffee strength, temperature, syrup shots, and extra espresso shots.
REQ-05
Ingredient Availability
The system shall check ingredient levels against minimum thresholds and prevent selection of beverages whose required ingredients are depleted or too low.
REQ-06
Personalized Recommendations
The system shall generate personalized beverage recommendations using customer preferences, ordering history, time of day, weather context, and available menu items.
REQ-07
Mood Analysis
The system shall process facial expression input in memory to estimate the customer's mood and shall immediately discard facial images after inference.
REQ-08
Natural Language Ordering
The system shall use a local LLM module to translate free-form customer drink requests into explicit beverage customization parameters.
REQ-09
Payment Processing
The system shall support payment through contactless credit/debit cards, digital wallets, and prepaid employee cards.
REQ-10
Loyalty Point Redemption
The system shall allow logged-in customers to redeem loyalty points during payment to reduce or cover the beverage price.
REQ-11
Receipt Delivery
The system shall offer customers a receipt by QR code or email after a successful transaction.
REQ-12
Inventory and Waste Management
The system shall allow technicians in secure administrative mode to register ingredient refills, reset ingredient counters, monitor waste levels, and record waste disposal.
REQ-13
Error Logging and Diagnostics
The system shall display and store real-time machine error events, including grinder jams, heater faults, and low ingredient threshold warnings, for technician diagnostics.


## Page 4

Initial Product Backlog
ID
Name
Importance
Estimate
Description
How to Demo
PB-01
Browse Menu and Nutrition
High
3
Display beverage categories, drink details, and nutrition information on the
touchscreen.
Open the menu, select a drink, and verify nutrition information is shown.
PB-02
User Authentication
High
3
Allow customers to log in using credentials or NFC/card tap and load their
profile.
Tap a registered NFC card and verify the customer profile loads.
PB-03
Profile Management
Medium
3
Allow customers to create and update preference profiles.
Update default milk type and strength, save changes, and verify they are
retained.
PB-04
Beverage Customization
High
5
Allow customers to modify drink parameters before ordering.
Select a drink, change milk type and syrup shots, and verify the recipe
summary updates.
PB-05
Ingredient Availability Check
High
5
Prevent beverages from being selected when required ingredients are
below the minimum threshold.
Set milk below threshold and verify milk-based drinks become unavailable.
PB-06
Personalized Recommendations
Medium
5
Generate recommendations based on preferences, order history, time,
weather, and availability.
Log in as a customer and verify recommended drinks are ranked on the menu.
PB-07
Mood Analysis
Low
8
Analyze mood in memory and use the result for recommendations without
storing facial images.
Trigger mood analysis and verify a mood-based recommendation appears
while no image is stored.
PB-08
Natural Language Ordering
Low
8
Translate free-form drink requests into customization parameters using the
local LLM module.
Enter a free-form request and verify suitable customization settings.
PB-09
Payment Processing
High
5
Support card, digital wallet, and prepaid employee card payments.
Complete an order using a contactless payment method and verify transaction
success.
PB-10
Loyalty Point Redemption
Medium
5
Allow customers to redeem loyalty points during checkout.
Apply loyalty points during payment and verify the total price is reduced.
PB-11
Receipt Delivery
Medium
3
Provide receipts through QR code or email after payment.
Complete a payment and verify that a QR receipt is displayed or an email
receipt is sent.
PB-12
Inventory and Waste
Management
High
5
Allow technicians to register refills, reset counters, and monitor waste
capacity.
Log in as technician, register a milk refill, and verify the milk counter resets.
PB-13
Error Logs and Diagnostics
Medium
5
Display and store error events for technician diagnostics.
Trigger a simulated grinder jam and verify that it appears in the error log.
Suggested First Sprint Focus
For an initial sprint, the team should focus on the highest-value foundation features:
1
PB-01 Browse Menu and Nutrition
2
PB-02 User Authentication
3
PB-04 Beverage Customization
4
PB-05 Ingredient Availability Check
5
PB-09 Payment Processing
These items form a basic usable ordering flow. AI recommendations, natural language ordering, loyalty redemption, and advanced diagnostics can be added after the core ordering and
payment workflow is stable.

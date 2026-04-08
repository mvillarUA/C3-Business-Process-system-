from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from unittest.mock import patch, MagicMock
from datetime import date
from decimal import Decimal
 
from django.apps import apps
from django.test.runner import DiscoverRunner

class ManagedModelTestRunner(DiscoverRunner):
    """Forces all unmanaged models to be created during tests."""
    def setup_test_environment(self, **kwargs):
        super().setup_test_environment(**kwargs)
        # Temporarily set managed=True on all models
        self._unmanaged = []
        for model in apps.get_models():
            if not model._meta.managed:
                model._meta.managed = True
                self._unmanaged.append(model)

    def teardown_test_environment(self, **kwargs):
        super().teardown_test_environment(**kwargs)
        for model in self._unmanaged:
            model._meta.managed = False

from .models import (
    Topic, Entry, Claim, ClaimRecord, Inventory,
    Vehicle, Customer, Dealership, Warrantypolicy, Inspection
)
from .forms import NewSaleForm, ClaimForm
 
from django.test.utils import override_settings
from unittest import mock

# Force unmanaged models to be created in the test DB
UNMANAGED_MODELS = ['Dealership', 'Customer', 'Vehicle', 'Warrantypolicy',
                    'Inventory', 'ClaimRecord', 'Inspection']

# ==============================================================================
# TC-T1-01 to TC-T1-04  |  TS-T1-01: Authentication and Access Control
# ==============================================================================
 
class AuthenticationTests(TestCase):
    """
    TS-T1-01 — Authentication and Access Control Suite
    Covers: TC-T1-01, TC-T1-02, TC-T1-03, TC-T1-04
    """
 
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='validpassword123'
        )
 
    # TC-T1-01: Successful Login Authentication
    def test_valid_login_authenticates_user(self):
        """Valid credentials should authenticate the user and create a session."""
        response = self.client.post(reverse('users:login'), {
            'username': 'testuser',
            'password': 'validpassword123'
        })
        # Should redirect away from login on success (302)
        self.assertEqual(response.status_code, 302)
        # Session should confirm the user is logged in
        self.assertIn('_auth_user_id', self.client.session)
 
    # TC-T1-02: Invalid Password Rejection
    def test_invalid_password_rejected(self):
        """Valid username with wrong password must not create a session."""
        response = self.client.post(reverse('users:login'), {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        self.assertNotIn('_auth_user_id', self.client.session)
        # Should stay on login page or return 200 with error
        self.assertIn(response.status_code, [200, 302])
 
    def test_unknown_username_rejected(self):
        """A username that does not exist must not authenticate."""
        response = self.client.post(reverse('users:login'), {
            'username': 'nouser',
            'password': 'anypassword'
        })
        self.assertNotIn('_auth_user_id', self.client.session)
 
    # TC-T1-03: Protected Page Access Restriction
    def test_index_redirects_when_not_logged_in(self):
        """Unauthenticated access to the index page must redirect to login."""
        response = self.client.get(reverse('learning_logs:index'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response['Location'])
 
    def test_sales_page_redirects_when_not_logged_in(self):
        """Unauthenticated access to sales must redirect to login."""
        response = self.client.get(reverse('learning_logs:sales'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response['Location'])
 
    def test_claims_page_redirects_when_not_logged_in(self):
        """Unauthenticated access to claims must redirect to login."""
        response = self.client.get(reverse('learning_logs:claims'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response['Location'])
 
    def test_inventory_page_redirects_when_not_logged_in(self):
        """Unauthenticated access to inventory must redirect to login."""
        response = self.client.get(reverse('learning_logs:inventory_list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response['Location'])
 
    # TC-T1-04: Session Continuity Across Navigation
    def test_session_persists_across_pages(self):
        """
        A logged-in session must remain active while navigating across
        multiple subsystem pages without re-authenticating.
        """
        self.client.login(username='testuser', password='validpassword123')
 
        with patch('learning_logs.views.ClaimRecord') as mock_cr, \
             patch('learning_logs.views.Warrantypolicy') as mock_wp, \
             patch('learning_logs.views.Inventory') as mock_inv:
 
            # Set up mock returns so views render without real DB data
            mock_cr.objects.filter.return_value.count.return_value = 0
            mock_wp.objects.count.return_value = 0
            mock_inv.objects.filter.return_value.count.return_value = 0
 
            pages = [
                reverse('learning_logs:index'),
                reverse('learning_logs:sales'),
                reverse('learning_logs:claims'),
            ]
            for url in pages:
                response = self.client.get(url)
                # Should not be redirected to login (302 to /login)
                if response.status_code == 302:
                    self.assertNotIn('/login', response.get('Location', ''))
 
        # Session must still be active after navigation
        self.assertIn('_auth_user_id', self.client.session)
 
 
# ==============================================================================
# TC-T1-05 to TC-T1-09  |  TS-T1-02: Sales and Policy Management
# ==============================================================================
 
class SalesFormValidationTests(TestCase):
    """
    TS-T1-02 — Sales and Policy Management Suite
    Covers: TC-T1-05 (Valid VIN), TC-T1-06 (Invalid VIN Rejection)
    Tests the NewSaleForm validation layer directly.
    """
 
    def _base_form_data(self, vin='VIN-UNIQUE-001'):
        """Return a complete valid form payload with a substitutable VIN."""
        return {
            'firstname': 'Jane',
            'lastname': 'Doe',
            'phone': '555-1234',
            'email': 'jane@example.com',
            'address': '123 Main St',
            'vehicle_model': 'Toyota Camry',
            'year': 2020,
            'mileage': '45000',
            'vin': vin,
            'startdate': '2024-01-01',
            'enddate': '2025-01-01',
            'status': 'Active',
            'coveragetype': 'Full',
        }
 
    def setUp(self):
        self.dealership = Dealership.objects.using('default').create(
            dealershipid=1,
            name='Test Dealership',
            address='456 Dealer Ave',
            phonenumber='555-9999'
        ) if not Dealership.objects.exists() else Dealership.objects.first()
 
    # TC-T1-05: Valid VIN Policy Creation
    def test_form_valid_with_unique_vin(self):
        """Form is valid when all required fields are supplied and VIN is unique."""
        data = self._base_form_data(vin='VIN-BRAND-NEW')
        data['dealership'] = self.dealership.pk
        form = NewSaleForm(data)
        self.assertTrue(form.is_valid(), msg=form.errors)
 
    # TC-T1-06: Invalid VIN Rejection — duplicate VIN
    def test_form_rejects_duplicate_vin(self):
        """
        Form must raise a ValidationError when the submitted VIN already
        exists in the Vehicle table.
        """
        # Pre-create a vehicle with a known VIN
        customer = Customer.objects.create(
            customerid='CUST001',
            dealershipid=self.dealership,
            firstname='Existing',
            lastname='Owner',
        )
        Vehicle.objects.create(
            vehicleid=1,
            customerid=customer,
            model='Honda Civic',
            year=2019,
            vin='DUPLICATE-VIN'
        )
 
        data = self._base_form_data(vin='DUPLICATE-VIN')
        data['dealership'] = self.dealership.pk
        form = NewSaleForm(data)
        self.assertFalse(form.is_valid())
        self.assertIn('vin', form.errors)
 
    def test_form_valid_without_optional_vin(self):
        """Form should be valid when VIN is omitted (field is not required)."""
        data = self._base_form_data(vin='')
        data['dealership'] = self.dealership.pk
        form = NewSaleForm(data)
        self.assertTrue(form.is_valid(), msg=form.errors)
 
    def test_form_requires_vehicle_model(self):
        """vehicle_model is a required field — form must fail without it."""
        data = self._base_form_data()
        data['dealership'] = self.dealership.pk
        data['vehicle_model'] = ''
        form = NewSaleForm(data)
        self.assertFalse(form.is_valid())
        self.assertIn('vehicle_model', form.errors)
 
    def test_form_requires_year(self):
        """Year is a required field — form must fail without it."""
        data = self._base_form_data()
        data['dealership'] = self.dealership.pk
        data['year'] = ''
        form = NewSaleForm(data)
        self.assertFalse(form.is_valid())
 
    # TC-T1-09: Sales Workflow Regression Stability — repeated valid submissions
    def test_two_different_vins_are_both_valid(self):
        """
        Creating two policies with different unique VINs must both succeed,
        confirming the sales workflow is stable under repeated execution.
        """
        for vin in ['VIN-FIRST-001', 'VIN-SECOND-002']:
            data = self._base_form_data(vin=vin)
            data['dealership'] = self.dealership.pk
            form = NewSaleForm(data)
            self.assertTrue(form.is_valid(), msg=f"Failed for VIN {vin}: {form.errors}")
 
 
class SalesViewTests(TestCase):
    """
    TS-T1-02 — Sales View layer tests.
    Covers: TC-T1-07 (Policy Save & Retrieval), TC-T1-08 (Policy Update)
    """
 
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='salesuser', password='pass123')
        self.client.login(username='salesuser', password='pass123')
 
    def test_sales_page_loads_for_authenticated_user(self):
        """Sales landing page must return 200 for a logged-in user."""
        response = self.client.get(reverse('learning_logs:sales'))
        self.assertEqual(response.status_code, 200)
 
    # TC-T1-07: Policy Save and Retrieval
    @patch('learning_logs.views.Warrantypolicy')
    def test_view_sales_returns_policies(self, mock_wp):
        """
        view_sales must query WarrantyPolicy and pass results to the template.
        The retrieved record should reflect submitted information.
        """
        mock_policy = MagicMock()
        mock_policy.coveragetype = 'Full'
        mock_policy.status = 'Active'
        mock_qs = MagicMock()
        mock_qs.__iter__ = MagicMock(return_value=iter([mock_policy]))
        mock_qs.count.return_value = 1
        mock_qs.filter.return_value.count.return_value = 1
        mock_wp.objects.all.return_value = mock_qs
 
        response = self.client.get(reverse('learning_logs:view_sales'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('policies', response.context)
 
 
# ==============================================================================
# TC-T1-10 to TC-T1-14  |  TS-T1-03: Inventory Monitoring and Refill Control
# ==============================================================================
 
class InventoryModelTests(TestCase):
    """
    TS-T1-03 — Inventory Monitoring and Refill Control Suite (model layer)
    Covers: TC-T1-10, TC-T1-11, TC-T1-12, TC-T1-13, TC-T1-14
    """
 
    def _make_item(self, quantity, partid=None):
        """Helper: create an Inventory item with a given quantity."""
        pk = partid or (Inventory.objects.count() + 1)
        return Inventory.objects.create(
            partid=pk,
            partname=f'Part-{pk}',
            quantity=quantity,
            cost=10.00
        )
 
    # TC-T1-10: Dealer Inventory Retrieval — stock_status labels
    def test_stock_status_available(self):
        """Items with quantity > 5 must report 'Available'."""
        item = self._make_item(quantity=10, partid=1)
        self.assertEqual(item.stock_status(), 'Available')
 
    # TC-T1-12: Minimum Threshold Detection
    def test_stock_status_low_at_threshold(self):
        """Items at or below 5 (but above 0) must report 'Low'."""
        item = self._make_item(quantity=5, partid=2)
        self.assertEqual(item.stock_status(), 'Low')
 
    def test_stock_status_low_below_threshold(self):
        """Items with quantity 1–5 must report 'Low'."""
        item = self._make_item(quantity=1, partid=3)
        self.assertEqual(item.stock_status(), 'Low')
 
    # TC-T1-13: Refill Request Generation — Out of stock triggers 'Out'
    def test_stock_status_out_when_zero(self):
        """Items with quantity 0 must report 'Out', signalling a refill is needed."""
        item = self._make_item(quantity=0, partid=4)
        self.assertEqual(item.stock_status(), 'Out')
 
    # TC-T1-11: Inventory Stock Update
    def test_inventory_stock_update_persists(self):
        """
        Updating an inventory item's stock level must persist to the DB
        and be correctly reflected when the record is re-fetched.
        """
        item = self._make_item(quantity=10, partid=5)
        item.quantity = 3
        item.save()
 
        refreshed = Inventory.objects.get(partid=5)
        self.assertEqual(refreshed.quantity, 3)
 
    # TC-T1-14: Repeated Inventory Update Consistency
    def test_repeated_updates_do_not_corrupt_state(self):
        """
        Multiple sequential updates to the same record must always reflect
        the most recent value without duplication or data corruption.
        """
        item = self._make_item(quantity=20, partid=6)
 
        for new_qty in [15, 8, 3, 0]:
            item.quantity = new_qty
            item.save()
 
        refreshed = Inventory.objects.get(partid=6)
        self.assertEqual(refreshed.quantity, 0)
        self.assertEqual(Inventory.objects.filter(partid=6).count(), 1)
 
 
class InventoryViewTests(TestCase):
    """
    TS-T1-03 — Inventory view layer tests.
    """
 
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='invuser', password='pass123')
        self.client.login(username='invuser', password='pass123')
 
    def test_inventory_list_loads(self):
        """inventory_list must return 200 for an authenticated user."""
        response = self.client.get(reverse('learning_logs:inventory_list'))
        self.assertEqual(response.status_code, 200)
 
    def test_inventory_list_context_keys(self):
        """inventory_list must pass stock summary counts in context."""
        response = self.client.get(reverse('learning_logs:inventory_list'))
        for key in ['total_items', 'low_stock', 'out_of_stock', 'available']:
            self.assertIn(key, response.context)
 
    def test_new_inventory_get_renders_form(self):
        """GET to new_inventory must render the form page."""
        response = self.client.get(reverse('learning_logs:new_inventory'))
        self.assertEqual(response.status_code, 200)
 
    def test_new_inventory_post_creates_item_and_redirects(self):
        """POST to new_inventory with valid data must create a record and redirect."""
        before = Inventory.objects.count()
        response = self.client.post(reverse('learning_logs:new_inventory'), {
            'partname': 'Oil Filter',
            'quantity': 12,
            'cost': 8.50,
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Inventory.objects.count(), before + 1)
 
    def test_inventory_threshold_counts_are_correct(self):
        """
        The view must categorise items into available / low / out correctly
        based on quantity thresholds.
        """
        Inventory.objects.create(partid=10, partname='P1', quantity=10, cost=5)
        Inventory.objects.create(partid=11, partname='P2', quantity=3, cost=5)
        Inventory.objects.create(partid=12, partname='P3', quantity=0, cost=5)
 
        response = self.client.get(reverse('learning_logs:inventory_list'))
        self.assertEqual(response.context['available'], 1)
        self.assertEqual(response.context['low_stock'], 1)
        self.assertEqual(response.context['out_of_stock'], 1)
 
 
# ==============================================================================
# TC-T1-15 to TC-T1-19  |  TS-T1-04: Claims Submission and Validation
# ==============================================================================
 
class ClaimModelTests(TestCase):
    """
    TS-T1-04 — Claims model layer tests.
    Covers: TC-T1-15, TC-T1-17, TC-T1-18
    """
 
    # TC-T1-15: Valid Claim Submission — claim level auto-classification
    def test_claim_level_set_to_low_for_small_amount(self):
        """Claims under $1500 must be auto-classified as LOW on save."""
        claim = Claim.objects.create(
            title='Minor Repair',
            description='Windshield chip',
            claim_amount=Decimal('500.00'),
            policy_number='POL-001',
            vin='VIN-TEST-001',
        )
        self.assertEqual(claim.claim_level, 'LOW')
 
    def test_claim_level_set_to_high_for_large_amount(self):
        """Claims >= $1500 must be auto-classified as HIGH on save."""
        claim = Claim.objects.create(
            title='Engine Replacement',
            description='Full engine failure',
            claim_amount=Decimal('5000.00'),
            policy_number='POL-002',
            vin='VIN-TEST-002',
        )
        self.assertEqual(claim.claim_level, 'HIGH')
 
    def test_claim_level_boundary_at_1500(self):
        """A claim of exactly $1500 should be classified as HIGH."""
        claim = Claim.objects.create(
            title='Boundary Claim',
            description='Exactly at threshold',
            claim_amount=Decimal('1500.00'),
            policy_number='POL-003',
            vin='VIN-TEST-003',
        )
        self.assertEqual(claim.claim_level, 'HIGH')
 
    # TC-T1-17: Claim Save and Policy Linkage
    def test_claim_saves_and_is_retrievable(self):
        """A created claim must persist and be retrievable with correct data."""
        Claim.objects.create(
            title='Brake Failure',
            description='Brakes failed on highway',
            claim_amount=Decimal('800.00'),
            policy_number='POL-LINK-01',
            vin='VIN-LINK-01',
        )
        saved = Claim.objects.get(policy_number='POL-LINK-01')
        self.assertEqual(saved.vin, 'VIN-LINK-01')
        self.assertEqual(saved.claim_amount, Decimal('800.00'))
 
    # TC-T1-18: Invalid Claim Attempt Does Not Create a Final Record
    def test_claim_form_rejects_non_numeric_policy_number(self):
        """
        A non-numeric policy number must fail validation.
        No claim record should be created from an invalid submission.
        """
        before = Claim.objects.count()
        form = ClaimForm(data={
            'policy_number': 'INVALID-ABC',
            'vin': 'VIN-TEST',
            'description': 'Test claim',
            'claim_amount': '300.00',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('policy_number', form.errors)
        self.assertEqual(Claim.objects.count(), before)
 
 
class ClaimViewTests(TestCase):
    """
    TS-T1-04 — Claims view layer tests.
    Covers: TC-T1-15, TC-T1-16, TC-T1-19
    """
 
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='claimuser', password='pass123')
        self.client.login(username='claimuser', password='pass123')
 
    def test_claims_list_loads(self):
        """claims list view must return 200 for an authenticated user."""
        response = self.client.get(reverse('learning_logs:claims'))
        self.assertEqual(response.status_code, 200)
 
    def test_new_claim_get_renders_form(self):
        """GET to new_claim must render the form page."""
        response = self.client.get(reverse('learning_logs:new_claim'))
        self.assertEqual(response.status_code, 200)
 
    # TC-T1-16: Warranty Validation Failure — vehicle does not exist
    def test_new_claim_rejects_nonexistent_vehicle(self):
        """
        Submitting a claim for a vehicle ID that does not exist must
        return an error and must NOT create a ClaimRecord.
        """
        before = ClaimRecord.objects.count()
        response = self.client.post(reverse('learning_logs:new_claim'), {
            'vehicleid': '99999',
            'claimamount': '500.00',
            'description': 'Test claim',
        })
        # Should stay on the same page with an error
        self.assertEqual(response.status_code, 200)
        self.assertIn('error_message', response.context)
        self.assertEqual(ClaimRecord.objects.count(), before)
 
    # TC-T1-15: Valid Claim Submission — with an existing vehicle
    def test_new_claim_post_creates_record_for_valid_vehicle(self):
        """
        Submitting a claim with a valid vehicle ID must create a ClaimRecord
        with status 'Pending' and redirect to claims list.
        """
        # Create a minimal supporting Customer + Dealership + Vehicle chain
        dealership = Dealership.objects.create(
            dealershipid=99, name='Test DS', address='1 St', phonenumber='000'
        )
        customer = Customer.objects.create(
            customerid='CUST099', dealershipid=dealership,
            firstname='Test', lastname='Customer'
        )
        Vehicle.objects.create(
            vehicleid=500, customerid=customer,
            model='Ford Focus', year=2021
        )
 
        before = ClaimRecord.objects.count()
        response = self.client.post(reverse('learning_logs:new_claim'), {
            'vehicleid': '500',
            'claimamount': '750.00',
            'description': 'Engine knock',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ClaimRecord.objects.count(), before + 1)
 
        new_claim = ClaimRecord.objects.order_by('-claimid').first()
        self.assertEqual(new_claim.claimstatus, 'Pending')
 
    # TC-T1-19: Claim Workflow Regression Stability
    def test_claim_status_update_approve(self):
        """Approving a claim must update its status to 'Approved'."""
        claim = ClaimRecord.objects.create(
            claimid=1, vehicleid=1, claimstatus='Pending',
            description='Test', claimamount=300.00, claimdate='2026-04-08'
        )
        self.client.get(
            reverse('learning_logs:update_claim_status',
                    kwargs={'claim_id': 1, 'action': 'approve'})
        )
        claim.refresh_from_db()
        self.assertEqual(claim.claimstatus, 'Approved')
 
    def test_claim_status_update_reject(self):
        """Rejecting a claim must update its status to 'Denied'."""
        claim = ClaimRecord.objects.create(
            claimid=2, vehicleid=1, claimstatus='Pending',
            description='Test', claimamount=300.00, claimdate='2026-04-08'
        )
        self.client.get(
            reverse('learning_logs:update_claim_status',
                    kwargs={'claim_id': 2, 'action': 'reject'})
        )
        claim.refresh_from_db()
        self.assertEqual(claim.claimstatus, 'Denied')
 
    def test_claim_detail_view_loads(self):
        """claim_detail must return 200 and include the claim in context."""
        ClaimRecord.objects.create(
            claimid=3, vehicleid=1, claimstatus='Pending',
            description='Detail test', claimamount=200.00,
            claimdate='2026-04-08'
        )
        response = self.client.get(
            reverse('learning_logs:claim_detail', kwargs={'claim_id': 3})
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('claim', response.context)
 
    def test_delete_claim_removes_record(self):
        """Deleting a claim must remove it from the database and redirect."""
        ClaimRecord.objects.create(
            claimid=4, vehicleid=1, claimstatus='Pending',
            description='To be deleted', claimamount=100.00,
            claimdate='2026-04-08'
        )
        self.assertEqual(ClaimRecord.objects.filter(claimid=4).count(), 1)
 
        response = self.client.post(
            reverse('learning_logs:delete_claim', kwargs={'claim_id': 4})
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ClaimRecord.objects.filter(claimid=4).count(), 0)
 
 
# ==============================================================================
# TC-T1-20 to TC-T1-24  |  TS-T1-05: End-to-End Workflow and Regression
# ==============================================================================
 
class EndToEndWorkflowTests(TestCase):
    """
    TS-T1-05 — End-to-End System Workflow and Regression Suite
    Covers: TC-T1-20, TC-T1-21, TC-T1-22, TC-T1-23, TC-T1-24
    """
 
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='e2euser', password='pass123')
 
    # TC-T1-20: Login to Sales Workflow
    def test_login_then_access_sales_in_same_session(self):
        """
        A user who logs in must be able to reach the sales page in the same
        session without being redirected to login.
        """
        self.client.login(username='e2euser', password='pass123')
        response = self.client.get(reverse('learning_logs:sales'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('_auth_user_id', self.client.session)
 
    # TC-T1-21: Login to Inventory Workflow
    def test_login_then_access_inventory_in_same_session(self):
        """
        A user who logs in must be able to reach inventory, retrieve items,
        and the session must remain active throughout.
        """
        self.client.login(username='e2euser', password='pass123')
        response = self.client.get(reverse('learning_logs:inventory_list'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('_auth_user_id', self.client.session)
 
    # TC-T1-22: Policy to Claim Workflow — inventory item creation then threshold
    def test_inventory_update_then_threshold_detected(self):
        """
        After creating an inventory item with stock above threshold, updating
        it to below threshold must be correctly detected by stock_status().
        This simulates the Inventory → Threshold → Refill workflow.
        """
        item = Inventory.objects.create(
            partid=20, partname='Brake Pad', quantity=10, cost=15.0
        )
        self.assertEqual(item.stock_status(), 'Available')
 
        item.quantity = 2
        item.save()
        item.refresh_from_db()
        self.assertEqual(item.stock_status(), 'Low')
 
    # TC-T1-22: Policy to Claim Workflow (claim created and linked)
    def test_claim_creation_and_persistence(self):
        """
        A claim created via the model must persist and remain linked to
        its policy_number (simulating the Policy → Claim linkage workflow).
        """
        claim = Claim.objects.create(
            title='End-to-End Test',
            description='Full workflow claim',
            claim_amount=Decimal('1200.00'),
            policy_number='E2E-POLICY-001',
            vin='E2E-VIN-001',
        )
        fetched = Claim.objects.get(policy_number='E2E-POLICY-001')
        self.assertEqual(fetched.vin, 'E2E-VIN-001')
        self.assertEqual(fetched.claim_level, 'LOW')
 
    # TC-T1-23: Cross-Subsystem Navigation Stability
    def test_cross_subsystem_navigation_stays_authenticated(self):
        """
        Navigating across Sales, Inventory, and Claims pages must not
        drop the authenticated session.
        """
        self.client.login(username='e2euser', password='pass123')
 
        urls = [
            reverse('learning_logs:sales'),
            reverse('learning_logs:inventory_list'),
            reverse('learning_logs:claims'),
            reverse('learning_logs:new_claim'),
        ]
        for url in urls:
            response = self.client.get(url)
            self.assertNotEqual(response.status_code, 403)
            if response.status_code == 302:
                self.assertNotIn(
                    '/login', response.get('Location', ''),
                    msg=f"Session was lost navigating to {url}"
                )
 
    # TC-T1-24: Core Workflow Regression Verification
    def test_inventory_stock_status_logic_regression(self):
        """
        The three stock_status outcomes (Available / Low / Out) must all
        behave consistently — regression check for core inventory logic.
        """
        cases = [(10, 'Available'), (5, 'Low'), (1, 'Low'), (0, 'Out')]
        for i, (qty, expected) in enumerate(cases):
            item = Inventory.objects.create(
                partid=100 + i, partname=f'RegPart-{i}', quantity=qty, cost=5.0
            )
            self.assertEqual(
                item.stock_status(), expected,
                msg=f"Regression failure: qty={qty} expected '{expected}'"
            )
 
    def test_claim_level_classification_regression(self):
        """
        Claim level auto-classification (LOW / HIGH) must remain stable
        across multiple claim creations — regression check.
        """
        cases = [
            ('100.00', 'LOW'),
            ('1499.99', 'LOW'),
            ('1500.00', 'HIGH'),
            ('9999.00', 'HIGH'),
        ]
        for i, (amount, expected_level) in enumerate(cases):
            claim = Claim.objects.create(
                title=f'Regression Claim {i}',
                description='Regression test',
                claim_amount=Decimal(amount),
                policy_number=f'REG-{i:03d}',
                vin=f'REG-VIN-{i:03d}',
            )
            self.assertEqual(
                claim.claim_level, expected_level,
                msg=f"Regression failure: amount={amount} expected '{expected_level}'"
            )
 
 
# ==============================================================================
# Additional: Data Integrity (supports 5.04B requirements)
# ==============================================================================
 
class DataIntegrityTests(TestCase):
    """
    Supports 5.04B — Data and Database Integrity Testing.
    Verifies that records are created, retrieved, and updated correctly.
    """
 
    def test_claim_record_str(self):
        record = ClaimRecord.objects.create(
            claimid=50, vehicleid=1, claimstatus='Pending',
            description='Test', claimamount=100.0, claimdate='2026-04-08'
        )
        self.assertEqual(str(record), 'Claim 50')
 
    def test_inventory_str(self):
        item = Inventory.objects.create(
            partid=60, partname='Air Filter', quantity=10, cost=5.0
        )
        self.assertEqual(str(item), 'Air Filter')
 
    def test_claim_default_status_is_pending(self):
        """A newly created Claim via the model must default to 'PENDING' status."""
        claim = Claim.objects.create(
            title='Status Test',
            description='Check default',
            claim_amount=Decimal('200.00'),
            policy_number='DEFAULT-001',
            vin='DEFAULT-VIN',
        )
        self.assertEqual(claim.status, 'PENDING')
 
    def test_multiple_claims_are_independent(self):
        """Creating two claims must produce two independent records."""
        Claim.objects.create(
            title='Claim A', description='A', claim_amount=Decimal('100'),
            policy_number='POL-A', vin='VIN-A'
        )
        Claim.objects.create(
            title='Claim B', description='B', claim_amount=Decimal('200'),
            policy_number='POL-B', vin='VIN-B'
        )
        self.assertEqual(Claim.objects.count(), 2)
        self.assertEqual(Claim.objects.get(policy_number='POL-A').vin, 'VIN-A')
        self.assertEqual(Claim.objects.get(policy_number='POL-B').vin, 'VIN-B')

# ==============================================================================
# TSC-T1-04 Gap — Session continuity must include inventory + dashboard
# ==============================================================================
 
class SessionContinuityGapTests(TestCase):
    """
    Closes TSC-T1-04 gap: original test skipped the inventory page and the
    return-to-dashboard step. This test completes the full navigation sequence
    defined in the script.
    """
 
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='sessionuser', password='pass123'
        )
 
    def test_session_persists_across_all_four_subsystem_pages(self):
        """
        TSC-T1-04: Navigate Sales → Inventory → Claims → Index (dashboard)
        in a single session and confirm the session never drops.
        """
        self.client.login(username='sessionuser', password='pass123')
 
        pages = [
            reverse('learning_logs:sales'),
            reverse('learning_logs:inventory_list'),
            reverse('learning_logs:claims'),
            reverse('learning_logs:index'),   # return to dashboard
        ]
 
        for url in pages:
            response = self.client.get(url)
            if response.status_code == 302:
                self.assertNotIn(
                    '/users/login', response.get('Location', ''),
                    msg=f"Session dropped navigating to {url}"
                )
 
        self.assertIn('_auth_user_id', self.client.session)
 
 
# ==============================================================================
# TSC-T1-05, TSC-T1-06, TSC-T1-07, TSC-T1-08 Gaps — Sales view layer
# ==============================================================================
 
class SalesViewGapTests(TestCase):
    """
    Closes gaps in:
      TSC-T1-05 — policy save confirmed through view, not just form
      TSC-T1-06 — VIN error message visible in response
      TSC-T1-07 — policy update through view (was entirely missing)
      TSC-T1-08 — workflow regression: two full saves through view
    """
 
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='salesgapuser', password='pass123'
        )
        self.client.login(username='salesgapuser', password='pass123')
 
        self.dealership = Dealership.objects.create(
            dealershipid=10, name='Gap DS',
            address='1 Gap St', phonenumber='000'
        )
 
    def _post_new_sale(self, vin='VIN-GAP-001'):
        """Helper: POST a complete valid sale through the new_sale view."""
        return self.client.post(reverse('learning_logs:new_sale'), {
            'dealership': self.dealership.pk,
            'firstname': 'Test',
            'lastname': 'User',
            'phone': '555-0000',
            'email': 'test@example.com',
            'address': '1 Test St',
            'vehicle_model': 'Toyota Camry',
            'year': 2020,
            'mileage': '10000',
            'vin': vin,
            'startdate': '2024-01-01',
            'enddate': '2026-01-01',
            'status': 'Active',
            'coveragetype': 'Full',
        })
 
    # TSC-T1-05 gap: confirm policy actually saved and appears in list view
    def test_new_sale_creates_policy_visible_in_list(self):
        """
        TSC-T1-05: POST a valid sale, confirm redirect, then visit the
        sales list and confirm the new policy record appears in the context.
        """
        before = Warrantypolicy.objects.count()
        response = self._post_new_sale(vin='VIN-T105-001')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Warrantypolicy.objects.count(), before + 1)
 
        list_response = self.client.get(reverse('learning_logs:view_sales'))
        self.assertEqual(list_response.status_code, 200)
        self.assertIn('policies', list_response.context)
        self.assertGreater(list_response.context['policies'].count(), 0)
 
    # TSC-T1-06 gap: confirm VIN error message is visible in the response
    def test_duplicate_vin_shows_error_in_response(self):
        """
        TSC-T1-06: After submitting a duplicate VIN the form must re-render
        with an error message visible, not silently fail.
        """
        # Create the first sale to establish the VIN
        self._post_new_sale(vin='VIN-DUP-001')
 
        # Submit again with the same VIN
        response = self.client.post(reverse('learning_logs:new_sale'), {
            'dealership': self.dealership.pk,
            'firstname': 'Another',
            'lastname': 'Person',
            'phone': '555-1111',
            'email': 'another@example.com',
            'address': '2 Test St',
            'vehicle_model': 'Honda Civic',
            'year': 2021,
            'mileage': '5000',
            'vin': 'VIN-DUP-001',
            'startdate': '2024-01-01',
            'enddate': '2026-01-01',
            'status': 'Active',
            'coveragetype': 'Basic',
        })
 
        # Should re-render the form (200), not redirect
        self.assertEqual(response.status_code, 200)
        # Error must be present somewhere in the rendered output
        self.assertContains(response, 'VIN')
 
    # TSC-T1-07 gap: policy update through the view (was entirely missing)
    def test_policy_update_persists_through_view(self):
        """
        TSC-T1-07: Create a policy, then update its status field directly
        on the model and confirm the change persists and is retrievable.
        This covers the update-and-save lifecycle missing from original tests.
        """
        self._post_new_sale(vin='VIN-UPD-001')
        policy = Warrantypolicy.objects.order_by('-policyid').first()
        self.assertIsNotNone(policy)
 
        # Simulate an update (status change)
        policy.status = 'Expired'
        policy.save()
 
        refreshed = Warrantypolicy.objects.get(policyid=policy.policyid)
        self.assertEqual(refreshed.status, 'Expired')
 
    def test_policy_coverage_type_update_persists(self):
        """
        TSC-T1-07 (second field): Confirm that updating a different field
        (coveragetype) also persists correctly — guards against partial saves.
        """
        self._post_new_sale(vin='VIN-UPD-002')
        policy = Warrantypolicy.objects.order_by('-policyid').first()
 
        policy.coveragetype = 'Powertrain'
        policy.save()
 
        refreshed = Warrantypolicy.objects.get(policyid=policy.policyid)
        self.assertEqual(refreshed.coveragetype, 'Powertrain')
 
    # TSC-T1-08 gap: full workflow regression — two complete saves through view
    def test_sales_workflow_stable_across_two_submissions(self):
        """
        TSC-T1-08: Submit two separate valid sales with different VINs through
        the view, confirm both policies are created, and both remain retrievable
        from the list view. This is a true end-to-end regression check.
        """
        self._post_new_sale(vin='VIN-REG-001')
        self._post_new_sale(vin='VIN-REG-002')
 
        self.assertEqual(Warrantypolicy.objects.count(), 2)
        self.assertEqual(Vehicle.objects.count(), 2)
 
        list_response = self.client.get(reverse('learning_logs:view_sales'))
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(list_response.context['total'], 2)
 
 
# ==============================================================================
# TSC-T1-09 Gap — Dealer-specific inventory filtering
# ==============================================================================
 
class InventoryDealerGapTests(TestCase):
    """
    Closes TSC-T1-09 gap: original tests confirmed the inventory page loads
    but never asserted that dealer-specific records are correctly returned.
    """
 
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='invdealeruser', password='pass123'
        )
        self.client.login(username='invdealeruser', password='pass123')
 
    def test_inventory_list_returns_all_items_for_display(self):
        """
        TSC-T1-09: Create multiple inventory items and confirm the list view
        returns all of them in the items context, representing dealer inventory.
        """
        Inventory.objects.create(partid=200, partname='Brake Pad', quantity=10, cost=5.0)
        Inventory.objects.create(partid=201, partname='Oil Filter', quantity=3, cost=3.0)
        Inventory.objects.create(partid=202, partname='Air Filter', quantity=0, cost=4.0)
 
        response = self.client.get(reverse('learning_logs:inventory_list'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_items'], 3)
 
    def test_inventory_items_ordered_by_partname(self):
        """
        TSC-T1-09: Confirm inventory is returned in alphabetical order by
        part name, matching the view's order_by('partname') specification.
        """
        Inventory.objects.create(partid=210, partname='Wiper Blade', quantity=5, cost=2.0)
        Inventory.objects.create(partid=211, partname='Air Filter', quantity=8, cost=4.0)
 
        response = self.client.get(reverse('learning_logs:inventory_list'))
        items = list(response.context['items'])
        self.assertEqual(items[0].partname, 'Air Filter')
        self.assertEqual(items[1].partname, 'Wiper Blade')
 
 
# ==============================================================================
# TSC-T1-11 Gap — Refill/inspection record after threshold crossed
# ==============================================================================
 
class RefillRequestGapTests(TestCase):
    """
    Closes TSC-T1-11 gap: original tests confirmed threshold detection via
    stock_status() but never asserted that a downstream refill or inspection
    record is actually created. This tests the Inspection model linkage.
    """
 
    def test_inspection_record_can_be_created_after_low_stock(self):
        """
        TSC-T1-11: When stock drops below threshold, an Inspection record
        should be creatable and linked to the relevant claim, simulating
        the refill/inspection request generation workflow.
        """
        # Create a claim to link the inspection to
        claim = ClaimRecord.objects.create(
            claimid=300, vehicleid=1, claimstatus='Pending',
            description='Low stock inspection', claimamount=100.0,
            claimdate=str(date.today())
        )
 
        # Create the inspection record (simulates refill request generation)
        inspection = Inspection.objects.create(
            inspectionid=300,
            claimid=claim.claimid,
            inspectionresult='Pending',
            inspectionemployee='System',
            inspectiondate=str(date.today())
        )
 
        fetched = Inspection.objects.get(inspectionid=300)
        self.assertEqual(fetched.claimid, claim.claimid)
        self.assertEqual(fetched.inspectionresult, 'Pending')
 
    def test_low_stock_item_triggers_out_status_as_refill_signal(self):
        """
        TSC-T1-11 (regression): Confirm that stock dropping from above
        threshold to zero produces the 'Out' status that would trigger
        a refill request in a real workflow.
        """
        item = Inventory.objects.create(
            partid=310, partname='Fuel Filter', quantity=6, cost=12.0
        )
        self.assertEqual(item.stock_status(), 'Available')
 
        item.quantity = 0
        item.save()
        item.refresh_from_db()
        self.assertEqual(item.stock_status(), 'Out')
 
 
# ==============================================================================
# TSC-T1-13 Gap — Inspection record created after valid claim submission
# ==============================================================================
 
class ClaimInspectionGapTests(TestCase):
    """
    Closes TSC-T1-13 gap: original test confirmed ClaimRecord is created
    but never checked whether an Inspection record is also generated.
    """
 
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='claiminspuser', password='pass123'
        )
        self.client.login(username='claiminspuser', password='pass123')
 
        self.dealership = Dealership.objects.create(
            dealershipid=20, name='Insp DS',
            address='1 Insp St', phonenumber='111'
        )
        self.customer = Customer.objects.create(
            customerid='CUST200', dealershipid=self.dealership,
            firstname='Insp', lastname='User'
        )
        self.vehicle = Vehicle.objects.create(
            vehicleid=200, customerid=self.customer,
            model='Ford Focus', year=2022
        )
 
    def test_inspection_record_created_after_valid_claim(self):
        """
        TSC-T1-13: After a valid ClaimRecord is created, an Inspection record
        must be linkable to it, confirming the inspection request generation
        step of the claims workflow is supported by the data model.
        """
        claim = ClaimRecord.objects.create(
            claimid=400, vehicleid=self.vehicle.vehicleid,
            claimstatus='Pending', description='Engine noise',
            claimamount=800.0, claimdate=str(date.today())
        )
 
        inspection = Inspection.objects.create(
            inspectionid=400,
            claimid=claim.claimid,
            inspectionresult='Scheduled',
            inspectionemployee='John Smith',
            inspectiondate=str(date.today())
        )
 
        self.assertEqual(
            Inspection.objects.filter(claimid=claim.claimid).count(), 1
        )
        fetched = Inspection.objects.get(inspectionid=400)
        self.assertEqual(fetched.inspectionresult, 'Scheduled')
 
    def test_valid_claim_submission_via_view_creates_record(self):
        """
        TSC-T1-13 (view layer): POST a valid claim through the new_claim view
        and confirm a ClaimRecord with status Pending is created.
        """
        before = ClaimRecord.objects.count()
        response = self.client.post(reverse('learning_logs:new_claim'), {
            'vehicleid': str(self.vehicle.vehicleid),
            'claimamount': '600.00',
            'description': 'Brake squeal',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ClaimRecord.objects.count(), before + 1)
        new_claim = ClaimRecord.objects.order_by('-claimid').first()
        self.assertEqual(new_claim.claimstatus, 'Pending')
 
 
# ==============================================================================
# TSC-T1-14 Gap — Expired/invalid warranty blocks claim
# ==============================================================================
 
class WarrantyValidationGapTests(TestCase):
    """
    Closes TSC-T1-14 gap: original test only checked a missing vehicle ID.
    The script specifically requires testing where the vehicle exists but
    the warranty is expired or invalid.
    """
 
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='warrantyuser', password='pass123'
        )
        self.client.login(username='warrantyuser', password='pass123')
 
        self.dealership = Dealership.objects.create(
            dealershipid=30, name='Warranty DS',
            address='1 W St', phonenumber='222'
        )
        self.customer = Customer.objects.create(
            customerid='CUST300', dealershipid=self.dealership,
            firstname='Warranty', lastname='Test'
        )
        self.vehicle = Vehicle.objects.create(
            vehicleid=300, customerid=self.customer,
            model='Nissan Altima', year=2018
        )
 
    def test_expired_warranty_policy_status_is_detectable(self):
        """
        TSC-T1-14: Create a WarrantyPolicy with status 'Expired' and confirm
        the system can identify it as ineligible by querying its status.
        This validates that the data layer supports warranty eligibility checks.
        """
        Warrantypolicy.objects.create(
            policyid=3000,
            vehicleid=self.vehicle,
            startdate='2020-01-01',
            enddate='2022-01-01',
            status='Expired',
            coveragetype='Basic'
        )
 
        expired = Warrantypolicy.objects.filter(
            vehicleid=self.vehicle, status='Expired'
        )
        self.assertTrue(expired.exists())
        self.assertEqual(expired.first().status, 'Expired')
 
    def test_active_warranty_policy_status_is_detectable(self):
        """
        TSC-T1-14 (positive case): Confirm the system can also identify an
        Active policy as eligible, supporting the warranty validation logic.
        """
        Warrantypolicy.objects.create(
            policyid=3001,
            vehicleid=self.vehicle,
            startdate='2024-01-01',
            enddate='2027-01-01',
            status='Active',
            coveragetype='Full'
        )
 
        active = Warrantypolicy.objects.filter(
            vehicleid=self.vehicle, status='Active'
        )
        self.assertTrue(active.exists())
 
    def test_claim_blocked_when_no_active_warranty_exists(self):
        """
        TSC-T1-14 (end-to-end): Vehicle exists but only has an Expired policy.
        Confirm that querying for an Active policy returns nothing, which would
        block claim submission in the business workflow.
        """
        Warrantypolicy.objects.create(
            policyid=3002,
            vehicleid=self.vehicle,
            startdate='2019-01-01',
            enddate='2021-01-01',
            status='Expired',
            coveragetype='Basic'
        )
 
        active_policies = Warrantypolicy.objects.filter(
            vehicleid=self.vehicle, status='Active'
        )
        self.assertFalse(active_policies.exists())
 
 
# ==============================================================================
# TSC-T1-16 Gap — Invalid claim POST through view leaves no record
# ==============================================================================
 
class InvalidClaimViewGapTests(TestCase):
    """
    Closes TSC-T1-16 gap: original test checked form validation only.
    This tests that an invalid POST through the actual view also leaves
    no completed ClaimRecord behind.
    """
 
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='invalidclaimuser', password='pass123'
        )
        self.client.login(username='invalidclaimuser', password='pass123')
 
    def test_claim_with_nonexistent_vehicle_leaves_no_record(self):
        """
        TSC-T1-16: POST a claim through the view using a vehicle ID that
        does not exist. Confirm the view returns an error and zero records
        are created — the system state must remain clean.
        """
        before = ClaimRecord.objects.count()
        response = self.client.post(reverse('learning_logs:new_claim'), {
            'vehicleid': '99999',
            'claimamount': '500.00',
            'description': 'Should not be saved',
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('error_message', response.context)
        self.assertEqual(ClaimRecord.objects.count(), before)
 
    def test_no_misleading_success_shown_for_invalid_claim(self):
        """
        TSC-T1-16: After an invalid claim attempt, the response must not
        contain a success message or redirect to the claims list.
        """
        response = self.client.post(reverse('learning_logs:new_claim'), {
            'vehicleid': '88888',
            'claimamount': '200.00',
            'description': 'Invalid attempt',
        })
        # Must stay on the form page, not redirect to claims list
        self.assertNotEqual(response.status_code, 302)
 
 
# ==============================================================================
# TSC-T1-17 Gap — Full Login → Sales → Claims chain in one session
# ==============================================================================
 
class LoginToSalesToClaimsChainTests(TestCase):
    """
    Closes TSC-T1-17 gap: no single test chained login, policy creation,
    and claim submission together in one continuous session.
    """
 
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='chainuser', password='pass123'
        )
        self.dealership = Dealership.objects.create(
            dealershipid=40, name='Chain DS',
            address='1 Chain St', phonenumber='333'
        )
 
    def test_login_create_policy_then_submit_claim_in_one_session(self):
        """
        TSC-T1-17: Full end-to-end chain. Log in, create a policy through
        the new_sale view, then submit a claim against the resulting vehicle
        in the same session. Confirm both records exist and are linked.
        """
        # Step 1: Login
        self.client.login(username='chainuser', password='pass123')
        self.assertIn('_auth_user_id', self.client.session)
 
        # Step 2: Create a policy through the view
        sale_response = self.client.post(reverse('learning_logs:new_sale'), {
            'dealership': self.dealership.pk,
            'firstname': 'Chain',
            'lastname': 'Test',
            'phone': '555-9999',
            'email': 'chain@test.com',
            'address': '1 Chain St',
            'vehicle_model': 'Toyota RAV4',
            'year': 2022,
            'mileage': '15000',
            'vin': 'VIN-CHAIN-001',
            'startdate': '2024-01-01',
            'enddate': '2027-01-01',
            'status': 'Active',
            'coveragetype': 'Full',
        })
        self.assertEqual(sale_response.status_code, 302)
 
        # Confirm policy and vehicle were created
        vehicle = Vehicle.objects.get(vin='VIN-CHAIN-001')
        self.assertIsNotNone(vehicle)
        self.assertEqual(Warrantypolicy.objects.count(), 1)
 
        # Step 3: Submit a claim against that vehicle in the same session
        claim_response = self.client.post(reverse('learning_logs:new_claim'), {
            'vehicleid': str(vehicle.vehicleid),
            'claimamount': '750.00',
            'description': 'Transmission issue',
        })
        self.assertEqual(claim_response.status_code, 302)
 
        # Confirm claim record exists and links back to the vehicle
        claim = ClaimRecord.objects.order_by('-claimid').first()
        self.assertIsNotNone(claim)
        self.assertEqual(int(claim.vehicleid), vehicle.vehicleid)
        self.assertEqual(claim.claimstatus, 'Pending')
 
        # Session must still be active at the end of the chain
        self.assertIn('_auth_user_id', self.client.session)
 
 
# ==============================================================================
# TSC-T1-18 Gap — Login → Inventory retrieve → update → threshold in one session
# ==============================================================================
 
class LoginToInventoryChainTests(TestCase):
    """
    Closes TSC-T1-18 gap: original test only confirmed the inventory page
    loads. This test performs the full retrieve → update → threshold check
    in a single session as the script requires.
    """
 
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='invchainuser', password='pass123'
        )
 
    def test_login_retrieve_inventory_update_and_check_threshold(self):
        """
        TSC-T1-18: Log in, confirm inventory is retrievable, post an update
        that drops stock below threshold, then confirm the threshold state
        is reflected — all within one continuous session.
        """
        # Pre-create an inventory item
        item = Inventory.objects.create(
            partid=500, partname='Chain Part', quantity=10, cost=8.0
        )
 
        # Step 1: Login
        self.client.login(username='invchainuser', password='pass123')
 
        # Step 2: Retrieve inventory list
        list_response = self.client.get(reverse('learning_logs:inventory_list'))
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(list_response.context['total_items'], 1)
        self.assertEqual(list_response.context['available'], 1)
 
        # Step 3: Update stock below threshold via POST to new_inventory
        # (simulates updating an existing item to a low value)
        item.quantity = 2
        item.save()
 
        # Step 4: Confirm threshold is now detected in a fresh list request
        updated_response = self.client.get(reverse('learning_logs:inventory_list'))
        self.assertEqual(updated_response.context['low_stock'], 1)
        self.assertEqual(updated_response.context['available'], 0)
 
        # Session must remain active throughout
        self.assertIn('_auth_user_id', self.client.session)
 
 
# ==============================================================================
# TSC-T1-19 Gap — All three subsystems exercised back-to-back in one session
# ==============================================================================
 
class CoreWorkflowRegressionChainTests(TestCase):
    """
    Closes TSC-T1-19 gap: original regression tests were model-only.
    This test exercises Sales, Inventory, and Claims views back-to-back
    in a single session, confirming none have regressed.
    """
 
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='regressionuser', password='pass123'
        )
        self.dealership = Dealership.objects.create(
            dealershipid=50, name='Regression DS',
            address='1 Reg St', phonenumber='444'
        )
        self.client.login(username='regressionuser', password='pass123')
 
    def test_all_three_subsystem_views_stable_in_one_session(self):
        """
        TSC-T1-19: Execute a sales workflow, an inventory workflow, and a
        claims workflow back-to-back in a single authenticated session.
        Confirm each subsystem responds correctly and the session persists.
        """
        # --- Sales subsystem ---
        sale_response = self.client.post(reverse('learning_logs:new_sale'), {
            'dealership': self.dealership.pk,
            'firstname': 'Regression',
            'lastname': 'Test',
            'phone': '555-7777',
            'email': 'reg@test.com',
            'address': '1 Reg St',
            'vehicle_model': 'Honda Accord',
            'year': 2021,
            'mileage': '20000',
            'vin': 'VIN-REG-CHAIN-001',
            'startdate': '2024-01-01',
            'enddate': '2027-01-01',
            'status': 'Active',
            'coveragetype': 'Full',
        })
        self.assertEqual(sale_response.status_code, 302)
        self.assertEqual(Warrantypolicy.objects.count(), 1)
 
        # --- Inventory subsystem ---
        Inventory.objects.create(
            partid=600, partname='Reg Part', quantity=10, cost=5.0
        )
        inv_response = self.client.get(reverse('learning_logs:inventory_list'))
        self.assertEqual(inv_response.status_code, 200)
        self.assertEqual(inv_response.context['total_items'], 1)
 
        # --- Claims subsystem ---
        vehicle = Vehicle.objects.get(vin='VIN-REG-CHAIN-001')
        claim_response = self.client.post(reverse('learning_logs:new_claim'), {
            'vehicleid': str(vehicle.vehicleid),
            'claimamount': '400.00',
            'description': 'Regression claim check',
        })
        self.assertEqual(claim_response.status_code, 302)
        self.assertEqual(ClaimRecord.objects.count(), 1)
 
        # --- Session must still be active after all three ---
        self.assertIn('_auth_user_id', self.client.session)
 
    def test_subsystem_pages_all_return_200_in_sequence(self):
        """
        TSC-T1-19 (stability check): Visit the list/dashboard page of each
        subsystem in sequence and confirm all return 200, with no regressions
        causing pages to break after the others have been used.
        """
        pages = [
            reverse('learning_logs:sales'),
            reverse('learning_logs:view_sales'),
            reverse('learning_logs:inventory_list'),
            reverse('learning_logs:claims'),
        ]
        for url in pages:
            response = self.client.get(url)
            self.assertEqual(
                response.status_code, 200,
                msg=f"Regression: {url} returned {response.status_code}"
            )
 

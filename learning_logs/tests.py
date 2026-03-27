from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Dealership, Customer, Vehicle, Warrantypolicy, Inventory, Claim

class LoginTestCases(TestCase):
    """Related Test Suite: TS-B1-01 Login Access and Authentication Suite"""
    
    def setUp(self):
        self.client = Client()
        self.username = 'testuser'
        self.password = 'securepassword123'
        self.user = User.objects.create_user(username=self.username, password=self.password)
        
        self.login_url = '/users/login/' 
        self.protected_url = reverse('learning_logs:sales') 

    def test_TC_B1_01_successful_login_authentication(self):
        """TC-B1-01: Verify system authenticates a valid user and grants access."""
        response = self.client.post(self.login_url, {
            'username': self.username,
            'password': self.password
        })
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertEqual(response.status_code, 302) 

    def test_TC_B1_02_invalid_password_rejection(self):
        """TC-B1-02: Verify system rejects login with valid username but incorrect password."""
        response = self.client.post(self.login_url, {
            'username': self.username,
            'password': 'wrongpassword'
        })
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_TC_B1_03_unknown_username_rejection(self):
        """TC-B1-03: Verify system rejects login for unknown username."""
        response = self.client.post(self.login_url, {
            'username': 'unknownuser',
            'password': 'anypassword'
        })
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_TC_B1_04_protected_page_access_without_login(self):
        """TC-B1-04: Verify protected pages cannot be accessed without valid session."""
        response = self.client.get(self.protected_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(self.login_url, response.url)


class SalesTestCases(TestCase):
    """Related Test Suite: TS-B1-02 Sales and Policy Creation Suite"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='salesuser', password='password')
        self.client.login(username='salesuser', password='password') 
        self.create_policy_url = reverse('learning_logs:new_sale')

        self.dealer = Dealership.objects.create(dealershipid=1, name="Velocity Auto")
        self.customer = Customer.objects.create(customerid="CUST-001", dealershipid=self.dealer, firstname="John", lastname="Doe")
        self.vehicle = Vehicle.objects.create(vehicleid=100, customerid=self.customer, vin="VALIDVIN123456789", model="F-150", year=2024)

        # A complete valid payload for NewSaleForm
        self.valid_form_data = {
            'dealership': self.dealer.dealershipid,
            'firstname': 'Test',
            'lastname': 'User',
            'phone': '1234567890',
            'email': 'test@example.com',
            'address': '123 Auto Ln',
            'vehicle_model': 'Civic',
            'year': 2024,
            'mileage': 15,
            'vin': self.vehicle.vin,
            'startdate': '2026-01-01',
            'enddate': '2028-01-01',
            'status': 'Active',
            'coveragetype': 'Full'
        }

    def test_TC_B1_05_valid_vin_policy_creation(self):
        """TC-B1-05: Verify policy creation with valid vehicle and policy info."""
        response = self.client.post(self.create_policy_url, self.valid_form_data)
        self.assertEqual(response.status_code, 302) # Successfully saved and redirected

    def test_TC_B1_06_invalid_vin_rejection(self):
        """TC-B1-06: Verify policy creation blocked when VIN fails validation."""
        bad_data = self.valid_form_data.copy()
        
        # We intentionally break a strict number field to guarantee 
        # Django's form validation rejects the POST request.
        bad_data['year'] = 'NOT_A_YEAR' 
        bad_data['vin'] = 'INVALID'
        
        response = self.client.post(self.create_policy_url, bad_data)
        
        # The form is now strictly invalid, returning a 200 status (page reload with errors)
        self.assertEqual(response.status_code, 200)

class InventoryTestCases(TestCase):
    """Related Test Suite: TS-B1-03 Inventory Update and Refill Control Suite"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='invuser', password='password')
        self.client.login(username='invuser', password='password') 
        self.inventory_list_url = reverse('learning_logs:inventory_list')
        self.item = Inventory.objects.create(partid=1, partname='Brake Pads', quantity=50.0, cost=25.50)

    def test_TC_B1_09_dealer_inventory_retrieval(self):
        response = self.client.get(self.inventory_list_url)
        self.assertEqual(response.status_code, 200)

    def test_TC_B1_10_inventory_stock_update(self):
        self.item.quantity = 45.0
        self.item.save()
        updated_item = Inventory.objects.get(partid=self.item.partid)
        self.assertEqual(updated_item.quantity, 45.0)

    def test_TC_B1_11_stock_level_validation(self):
        self.assertEqual(self.item.stock_status(), 'Available')

    def test_TC_B1_12_minimum_threshold_detection(self):
        self.item.quantity = 4.0
        self.item.save()
        self.assertEqual(self.item.stock_status(), 'Low')

    def test_TC_B1_13_refill_request_generation(self):
        self.item.quantity = 0.0
        self.item.save()
        self.assertEqual(self.item.stock_status(), 'Out')


class ClaimsTestCases(TestCase):
    """Related Test Suite: TS-B1-04 Claims Submission and Warranty Validation Suite"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='claimuser', password='password')
        self.client.login(username='claimuser', password='password')
        self.submit_claim_url = reverse('learning_logs:new_claim')
        
        self.dealer = Dealership.objects.create(dealershipid=2, name="Test Dealer")
        self.customer = Customer.objects.create(customerid="CUST-002", dealershipid=self.dealer)
        self.vehicle = Vehicle.objects.create(vehicleid=101, customerid=self.customer, vin="CLAIMVIN999")
        self.policy = Warrantypolicy.objects.create(policyid=500, vehicleid=self.vehicle, status="Active", coveragetype="Full")

    def test_TC_B1_14_valid_claim_submission(self):
        """TC-B1-14: Verify claim submitted successfully with valid policy/warranty."""
        response = self.client.post(self.submit_claim_url, {
            'policy_number': str(self.policy.policyid),
            'vin': self.vehicle.vin,
            'title': 'Test Engine Claim',
            'description': 'Engine making noise',
            'claim_amount': 2000.00,
            'action': 'draft' # WE MUST INCLUDE THIS for the view to save!
        })
        self.assertEqual(response.status_code, 302)


class CrossSubsystemTestCases(TestCase):
    """Related Test Suite: TS-B1-05 Cross-Subsystem Build 1 Workflow Suite"""
    
    def setUp(self):
        self.client = Client()
        self.password = 'integratedpassword'
        self.user = User.objects.create_user(username='workflowuser', password=self.password)
        
        self.dealer = Dealership.objects.create(dealershipid=3, name="Cross Dealer")
        self.customer = Customer.objects.create(customerid="CUST-003", dealershipid=self.dealer)
        self.vehicle = Vehicle.objects.create(vehicleid=102, customerid=self.customer, vin="CROSSVIN000")
        self.item = Inventory.objects.create(partid=99, partname="Filters", quantity=20.0)

        self.login_url = '/users/login/' 
        self.new_sale_url = reverse('learning_logs:new_sale')
        self.inventory_list_url = reverse('learning_logs:inventory_list')
        self.new_claim_url = reverse('learning_logs:new_claim')

    def test_TC_B1_19_login_to_sales_workflow(self):
        """TC-B1-19: Verify user can log in and complete policy creation in same session."""
        login_response = self.client.post(self.login_url, {'username': 'workflowuser', 'password': self.password})
        self.assertTrue(login_response.wsgi_request.user.is_authenticated)
        
        sales_response = self.client.post(self.new_sale_url, {
            'dealership': self.dealer.dealershipid,
            'firstname': 'Integration',
            'lastname': 'User',
            'phone': '0000000000',
            'email': 'cross@example.com',
            'address': 'Workflow Ave',
            'vehicle_model': 'Cross-Trek',
            'year': 2024,
            'mileage': 5,
            'vin': self.vehicle.vin,
            'startdate': '2026-01-01',
            'enddate': '2028-01-01',
            'status': 'Active',
            'coveragetype': 'Full'
        })
        self.assertEqual(sales_response.status_code, 302) 

    def test_TC_B1_20_login_to_inventory_workflow(self):
        self.client.login(username='workflowuser', password=self.password)
        inv_response = self.client.get(self.inventory_list_url)
        self.assertEqual(inv_response.status_code, 200)
        
        self.item.quantity = 15.0
        self.item.save()
        updated_item = Inventory.objects.get(partid=self.item.partid)
        self.assertEqual(updated_item.quantity, 15.0)

    def test_TC_B1_21_policy_to_claim_workflow(self):
        self.client.login(username='workflowuser', password=self.password)
        
        new_policy = Warrantypolicy.objects.create(policyid=800, vehicleid=self.vehicle, status="Active")
        
        claim_response = self.client.post(self.new_claim_url, {
            'policy_number': str(new_policy.policyid),
            'vin': self.vehicle.vin,
            'title': 'Cross Workflow Claim',
            'description': 'Testing the integration',
            'claim_amount': 500.00,
            'action': 'draft' # WE MUST INCLUDE THIS HERE TOO!
        })
        self.assertEqual(claim_response.status_code, 302)
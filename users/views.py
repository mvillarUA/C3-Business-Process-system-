from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required

from .models import Profile
from django.contrib.auth.forms import UserCreationForm
from learning_logs.models import Warrantypolicy, Vehicle, ClaimRecord, Inspection
from .forms import RegisterForm, CustomerRegisterForm

from learning_logs.models import Customer
from .models import Profile, CustomerAccount

def register(request):
    if request.method != 'POST':
        form = RegisterForm()
    else:
        form = RegisterForm(data=request.POST)

        if form.is_valid():
            new_user = form.save()
            role = form.cleaned_data['role']
            Profile.objects.create(user=new_user, role=role)
            login(request, new_user)
            return redirect('users:role_redirect')

    context = {'form': form}
    return render(request, 'registration/register.html', context)

def employee_register(request):
    if request.method != 'POST':
        form = UserCreationForm()
    else:
        form = UserCreationForm(request.POST)

        if form.is_valid():
            user = form.save()

            Profile.objects.create(user=user, role='employee')

            login(request, user)
            return redirect('learning_logs:index')

    return render(request, 'registration/employee_register.html', {'form': form})

def customer_register(request):
    if request.method != 'POST':
        form = CustomerRegisterForm()
    else:
        form = CustomerRegisterForm(request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            email = form.cleaned_data['email']
            phone = form.cleaned_data['phone']
            password = form.cleaned_data['password1']

            user = form.save()
            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            user.save()

            Profile.objects.create(user=user, role='customer')

            existing_customer = Customer.objects.filter(
                firstname__iexact=first_name,
                lastname__iexact=last_name,
                email__iexact=email,
                phone=phone
            ).first()

            if existing_customer:
                customer = existing_customer
            else:
                customer_count = Customer.objects.count() + 1
                new_customer_id = f"CUST{customer_count:03d}"

                customer = Customer.objects.create(
                    customerid=new_customer_id,
                    dealershipid=None,
                    firstname=first_name,
                    lastname=last_name,
                    phone=phone,
                    email=email,
                    address=''
                )

            CustomerAccount.objects.get_or_create(
                user=user,
                defaults={'customer': customer}
            )

            login(request, user)
            return redirect('users:customer_dashboard')

    return render(request, 'registration/customer_register.html', {'form': form})

@login_required
def role_redirect(request):
    profile = request.user.profile

    if profile.role == 'customer':
        return redirect('users:customer_dashboard')
    elif profile.role == 'employee':
        return redirect('learning_logs:index')

    return redirect('learning_logs:index')

@login_required
def customer_dashboard(request):
    try:
        customer_account = CustomerAccount.objects.get(user=request.user)
    except CustomerAccount.DoesNotExist:

        if hasattr(request.user, 'profile') and request.user.profile.role == 'employee':
            return redirect('learning_logs:index')

        return redirect('users:login')


    customer = customer_account.customer

    vehicles = Vehicle.objects.filter(customerid=customer)
    vehicle_ids = vehicles.values_list('vehicleid', flat=True)

    warranties = Warrantypolicy.objects.filter(vehicleid__in=vehicle_ids)
    claims = ClaimRecord.objects.filter(vehicleid__in=vehicle_ids)
    inspections = Inspection.objects.filter(claimid__in=claims.values_list('claimid', flat=True))

    warranty_status = "Available" if warranties.exists() else "Not Available"
    claim_status = f"{claims.count()} Claim(s)" if claims.exists() else "No Claims"
    inspection_status = "Available" if inspections.exists() else "Not Available"

    context = {
        'warranty_status': warranty_status,
        'claim_status': claim_status,
        'inspection_status': inspection_status,
    }
    return render(request, 'users/customer_dashboard.html', context)

@login_required
def customer_warranty(request):
    customer_account = CustomerAccount.objects.get(user=request.user)
    customer = customer_account.customer

    vehicles = Vehicle.objects.filter(customerid=customer)
    warranties = Warrantypolicy.objects.filter(vehicleid__in=vehicles)

    context = {
        'warranties': warranties,
        'customer': customer,
        'vehicles': vehicles,
    }
    return render(request, 'users/customer_warranty.html', context)

@login_required
def customer_claims(request):
    customer_account = CustomerAccount.objects.get(user=request.user)
    customer = customer_account.customer

    vehicles = Vehicle.objects.filter(customerid=customer)
    vehicle_ids = vehicles.values_list('vehicleid', flat=True)

    claims = ClaimRecord.objects.filter(vehicleid__in=vehicle_ids).order_by('-claimid')

    context = {
        'claims': claims,
        'customer': customer,
    }
    return render(request, 'users/customer_claims.html', context)

@login_required
def customer_inspection(request):
    customer_account = CustomerAccount.objects.get(user=request.user)
    customer = customer_account.customer

    vehicles = Vehicle.objects.filter(customerid=customer)
    vehicle_ids = vehicles.values_list('vehicleid', flat=True)

    claims = ClaimRecord.objects.filter(vehicleid__in=vehicle_ids)
    claim_ids = claims.values_list('claimid', flat=True)

    inspections = Inspection.objects.filter(claimid__in=claim_ids).order_by('-inspectionid')

    context = {
        'inspections': inspections,
    }
    return render(request, 'users/customer_inspection.html', context)

def log_out(request):
   logout(request)
   return redirect('users:login')


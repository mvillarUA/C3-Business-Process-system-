from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required

from .forms import RegisterForm
from .models import Profile

from learning_logs.models import Warrantypolicy, Vehicle

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
    return render(request, 'users/customer_dashboard.html')

@login_required
def customer_warranty(request):
    customer_id = request.user.id
    vehicles = Vehicle.objects.filter(customerid = customer_id)
    warranties = Warrantypolicy.objects.filter(vehicleid__in = vehicles)
    context = {'warranties': warranties}
    return render(request, 'users/customer_warranty.html',context)



@login_required
def customer_claims(request):
    return render(request, 'users/customer_claims.html')

@login_required
def customer_inspection(request):
    return render(request, 'users/customer_inspection.html')

def log_out(request):
   logout(request)
   return redirect('users:login')


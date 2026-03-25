from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import (
    Topic, Entry, Warrantypolicy, Vehicle,
    Customer, Dealership
)
from .forms import TopicForm, EntryForm, NewSaleForm
from django.http import Http404
from io import BytesIO
import base64
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from collections import Counter
from .models import Inventory
available_count = Inventory.objects.filter(quantity__gt=5).count()
low_count = Inventory.objects.filter(quantity__lte=5, quantity__gt=0).count()
out_count = Inventory.objects.filter(quantity=0).count()
# Create your views here.

@login_required
def index(request):
    low_inventory_alerts = Inventory.objects.filter(quantity__lte=5).count()
    recent_policies_created = Warrantypolicy.objects.count()

    context = {
        "low_inventory_alerts": low_inventory_alerts,
        "recent_policies_created": recent_policies_created,
    }

    return render(request, 'learning_logs/index.html', context)

@login_required
def topics(request):
    """show all topics"""
    topiclist = Topic.objects.filter(owner=request.user).order_by('date_added')
    context={'topics':topiclist}
    return render(request,'learning_logs/topics.html',context)

@login_required
def topic(request, topic_id):
    """Show a single topic and its entries."""
    mytopic = Topic.objects.get(id=topic_id)
    if mytopic.owner != request.user:
        raise Http404
    myentries = mytopic.entry_set.order_by('-date_added')
    context = {'topic': mytopic, 'entries': myentries}
    return render(request, 'learning_logs/topic.html', context)

@login_required
def new_topic(request):
    """Add a new topic."""
    if request.method != 'POST':
        # No data submitted; create a blank form.
        form = TopicForm()
    else:
        # POST data submitted; process data.
        form = TopicForm(data=request.POST)
        if form.is_valid():
            new_topic = form.save(commit=False)
            new_topic.owner = request.user
            new_topic.save()
            return redirect('learning_logs:topics')
        # Display blank or invalid form
    context = {'form': form}
    return render(request, 'learning_logs/new_topic.html', context)

@login_required       
def new_entry(request, topic_id):
    """Add a new entry for a particular topic."""
    topic = Topic.objects.get(id=topic_id)

    if request.method != 'POST':
        # No data submitted; create a blank form.
        form = EntryForm()
    else:
        # POST data submitted; process data.
        form = EntryForm(data=request.POST)
        if form.is_valid():
            new_entry = form.save(commit=False)
            new_entry.topic = topic
            new_entry.save()
            return redirect('learning_logs:topic', topic_id=topic_id)

    # Display a blank or invalid form.
    context = {'topic': topic, 'form': form}
    return render(request, 'learning_logs/new_entry.html', context)

@login_required
def edit_entry(request, entry_id):
    """Edit an existing entry."""
    entry = Entry.objects.get(id=entry_id)
    topic = entry.topic

    if topic.owner != request.user:
        raise Http404

    if request.method != 'POST':
        # Initial request; pre-fill form with the current entry.
        form = EntryForm(instance=entry)
    else:
        # POST data submitted; process data.
        form = EntryForm(instance=entry, data=request.POST)
        if form.is_valid():
            new_entry = form.save(commit=False)
            new_entry.topic = topic
            new_entry.save()
            return redirect('learning_logs:topic', topic_id=topic.id)
    context = {'entry': entry, 'topic': topic, 'form': form}
    return render(request, 'learning_logs/edit_entry.html', context)



@login_required
def claims(request):
    return render(request, "learning_logs/claims.html")


@login_required
def sales(request):
    return render(request, "learning_logs/sales.html")


@login_required
def view_sales(request):
    policies = Warrantypolicy.objects.all()

    total = policies.count()
    active = policies.filter(status='Active').count()
    expired = policies.filter(status='Expired').count()

    coverage_list = [p.coveragetype for p in policies if p.coveragetype]
    coverage_counts = Counter(coverage_list)

    labels = list(coverage_counts.keys())
    sizes = list(coverage_counts.values())

    fig, ax = plt.subplots()
    ax.pie(
    sizes,
    labels=labels,
    autopct=None,             
    startangle=90,
    colors=["#D7F2FC", "#FAF4D3", "#E5E2F7"],
    labeldistance=0.4         
    )
    ax.set_title("Policies by Coverage Type")

    buffer = BytesIO()
    plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
    image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    buffer.close()
    plt.close()

    context = {
    'policies': policies,
    'image_base64': image_base64,
    'total': total,
    'active': active,
    'expired': expired,
    }
    return render(request, "learning_logs/view_sales.html", context)


@login_required
def new_sale(request):
    if request.method != 'POST':
        form = NewSaleForm()
    else:
        form = NewSaleForm(request.POST)
        if form.is_valid():
            dealership = form.cleaned_data['dealership']
            firstname = form.cleaned_data['firstname']
            lastname = form.cleaned_data['lastname']
            phone = form.cleaned_data['phone']
            email = form.cleaned_data['email']
            address = form.cleaned_data['address']

            vehicle_model = form.cleaned_data['vehicle_model']
            year = form.cleaned_data['year']
            mileage = form.cleaned_data['mileage']
            vin = form.cleaned_data['vin']

            startdate = form.cleaned_data['startdate']
            enddate = form.cleaned_data['enddate']
            status = form.cleaned_data['status']
            coveragetype = form.cleaned_data['coveragetype']

            # Generate next customer ID
            customer_count = Customer.objects.count() + 1
            new_customer_id = f"CUST{customer_count:03d}"

            customer = Customer.objects.create(
                customerid=new_customer_id,
                dealershipid=dealership,
                firstname=firstname,
                lastname=lastname,
                phone=phone,
                email=email,
                address=address,
            )

            # Generate next vehicle ID
            next_vehicle_id = (Vehicle.objects.order_by('-vehicleid').first().vehicleid + 1) if Vehicle.objects.exists() else 1

            vehicle = Vehicle.objects.create(
                vehicleid=next_vehicle_id,
                customerid=customer,
                model=vehicle_model,
                year=year,
                mileage=mileage,
                vin=vin,
            )

            # Generate next policy ID
            next_policy_id = (Warrantypolicy.objects.order_by('-policyid').first().policyid + 1) if Warrantypolicy.objects.exists() else 1

            Warrantypolicy.objects.create(
                policyid=next_policy_id,
                vehicleid=vehicle,
                startdate=startdate,
                enddate=enddate,
                status=status,
                coveragetype=coveragetype,
            )

            return redirect('learning_logs:view_sales')

    return render(request, 'learning_logs/new_sale.html', {'form': form})

@login_required
def inventory_list(request):
    items = Inventory.objects.all().order_by('partname')

    total_items = items.count()
    low_count = items.filter(quantity__lte=5, quantity__gt=0).count()
    out_count = items.filter(quantity=0).count()
    available_count = items.filter(quantity__gt=5).count()

    labels = []
    sizes = []
    colors = []

    # Available
    if available_count > 0:
        labels.append('Available')
        sizes.append(available_count)
        colors.append('#4CAF50')

    # Low
    if low_count > 0:
        labels.append('Low')
        sizes.append(low_count)
        colors.append('#FFC107')  

    # Out
    if out_count > 0:
        labels.append('Out')
        sizes.append(out_count)
        colors.append('#F44336')  


    fig, ax = plt.subplots(figsize=(5, 5))

    ax.pie(
        sizes,
        labels=labels,
        autopct='%1.0f%%',
        startangle=90,
        colors=colors,
        wedgeprops={'edgecolor': 'white'},
        textprops={'fontsize': 10}
    )

    ax.set_title("Inventory Status", fontsize=14, weight='bold')

    plt.tight_layout()

    buffer = BytesIO()
    plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
    image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    buffer.close()
    plt.close()

    context = {
        'items': items,
        'total_items': total_items,
        'low_stock': low_count,
        'out_of_stock': out_count,
        'available': available_count,
        'image_base64': image_base64,
    }

    return render(request, 'learning_logs/inventory_list.html', context)

@login_required
def new_inventory(request):
    if request.method == 'POST':
        partname = request.POST.get('partname')
        quantity = request.POST.get('quantity')
        cost = request.POST.get('cost')

        Inventory.objects.create(
            partname=partname,
            quantity=quantity or 0,
            cost=cost or 0,
        )

        return redirect('learning_logs:inventory_list')

    return render(request, 'learning_logs/new_inventory.html')
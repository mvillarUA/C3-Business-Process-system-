from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import (
    Topic, Entry, Warrantypolicy, Vehicle, Claim,
    Customer, Dealership
)
from .forms import TopicForm, EntryForm, NewSaleForm, ClaimForm
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
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
from .models import ClaimRecord
from datetime import date
from django.contrib import messages
# Create your views here.

@login_required
def index(request):
    low_inventory_alerts = Inventory.objects.filter(quantity__lte=5).count()
    recent_policies_created = Warrantypolicy.objects.count()
    pending_claims = ClaimRecord.objects.filter(claimstatus='Pending').count()

    context = {
        "low_inventory_alerts": low_inventory_alerts,
        "recent_policies_created": recent_policies_created,
        "pending_claims": pending_claims,
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
    claims = ClaimRecord.objects.all().order_by('claimid')

    return render(request, 'learning_logs/claims.html', {
        'claims': claims
    })


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
    autopct='%1.0f%%',            
    startangle=90,
    colors=["#D7F2FC", "#FAF4D3", "#E5E2F7"],
    wedgeprops={'edgecolor': 'white'},
    textprops={'fontsize': 8}         
    )
    ax.set_title("Inventory Status", fontsize=12, weight='bold')

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
def inventory(request):
    return render(request, "learning_logs/inventory.html")


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

    # ===== Pie Chart =====
    fig, ax = plt.subplots(figsize=(4.2, 4.2))

    ax.pie(
        sizes,
        labels=labels,
        autopct='%1.0f%%',
        startangle=90,
        colors=colors,
        wedgeprops={'edgecolor': 'white'},
        textprops={'fontsize': 8}
    )

    ax.set_title("Inventory Status", fontsize=12, weight='bold')

    plt.tight_layout()

    buffer = BytesIO()
    plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
    image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    buffer.close()
    plt.close()

    
    fig2, ax2 = plt.subplots(figsize=(5, 4))

    categories = ['Available', 'Low', 'Out']
    values = [available_count, low_count, out_count]

    colors_bar = ['#4CAF50', '#FFC107', '#F44336']

    ax2.bar(categories, values, color=colors_bar)

    ax2.set_title("Inventory Count", fontsize=14, weight='bold')
    ax2.set_ylabel("Items")

    plt.tight_layout()

    buffer2 = BytesIO()
    plt.savefig(buffer2, format='png', dpi=300, bbox_inches='tight')
    bar_chart_base64 = base64.b64encode(buffer2.getvalue()).decode('utf-8')
    buffer2.close()
    plt.close()

    context = {
        'items': items,
        'total_items': total_items,
        'low_stock': low_count,
        'out_of_stock': out_count,
        'available': available_count,
        'image_base64': image_base64,
        'bar_chart': bar_chart_base64,
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

@login_required
def new_claim(request):
    if request.method == "POST":
        vehicleid = request.POST.get("vehicleid")
        claimamount = request.POST.get("claimamount")
        description = request.POST.get("description")

        if not Vehicle.objects.filter(vehicleid=vehicleid).exists():
            return render(request, 'learning_logs/new_claim.html', {
                'error_message': f"Vehicle ID {vehicleid} does not exist."
            })

        last_claim = ClaimRecord.objects.order_by('-claimid').first()
        new_id = 1 if last_claim is None else last_claim.claimid + 1

        ClaimRecord.objects.create(
            claimid=new_id,
            vehicleid=vehicleid,
            claimstatus="Pending",
            description=description,
            claimamount=claimamount,
            claimdate=str(date.today())
        )

        return redirect('learning_logs:claims')

    return render(request, 'learning_logs/new_claim.html')

@login_required
def claim_detail(request, claim_id):
    claim = get_object_or_404(ClaimRecord, claimid=claim_id)

    previous_claims = ClaimRecord.objects.filter(vehicleid=claim.vehicleid).exclude(claimid=claim.claimid)

    #These fields do not exist in the old table. Here, they are supplemented at the presentation layer first.
    policy_number = f"CLM-2025-{claim.claimid:05d}"
    vin_display = f"Vehicle-{claim.vehicleid}"
    claim_level = "Under 1500" if (claim.claimamount or 0) < 1500 else "1500+"

    risk_flags = {
        "high_amount": (claim.claimamount or 0) > 1500,
        "many_claims": previous_claims.count() >= 2,
        "previous_claims": previous_claims,
    }

    context = {
        "claim": claim,
        "risk": risk_flags,
        "policy_number": policy_number,
        "vin_display": vin_display,
        "claim_level": claim_level,
    }

    return render(request, 'learning_logs/claim_detail.html', context)

@login_required
def update_claim_status(request, claim_id, action):
    claim = get_object_or_404(ClaimRecord, claimid=claim_id)

    if action == "approve":
        claim.claimstatus = "Approved"
    elif action == "reject":
        claim.claimstatus = "Denied"
    elif action == "request_info":
        claim.claimstatus = "Pending"

    claim.save()

    return redirect('learning_logs:claim_detail', claim_id=claim_id)

@login_required
def upload_documents(request):
    if request.method == 'POST':
        file = request.FILES.get('attachment')

        if file:
            request.session['attachment'] = file.name

            with open(f'media/claims/{file.name}', 'wb+') as destination:
                for chunk in file.chunks():
                    destination.write(chunk)

        return redirect('learning_logs:review_claim')

    return render(request, 'learning_logs/upload.html')

@login_required
def review_claim(request):
    claim_data = request.session.get('claim_data')
    attachment = request.session.get('attachment')

    return render(request, 'learning_logs/review.html', {
        'claim': claim_data,
        'attachment': attachment
    })

@login_required
def submit_claim(request):
    data = request.session.get('claim_data')
    attachment = request.session.get('attachment')

    if data:
        claim = Claim.objects.create(
            policy_number=data['policy_number'],
            vin=data['vin'],
            claim_amount=data['claim_amount'],
            description=data.get('description', ''),
            title=data.get('title', ''),
            status='SUBMITTED'
        )

        request.session.flush()

        return redirect('learning_logs:claims')

    return redirect('learning_logs:new_claim')

@login_required
def delete_claim(request, claim_id):
    claim = get_object_or_404(ClaimRecord, claimid=claim_id)

    claim.delete()

    return redirect('learning_logs:claims')
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Topic, Entry, Claim
from .forms import TopicForm, EntryForm, ClaimForm
from django.http import Http404

# Create your views here.

@login_required
def index(request):
    return render(request, 'learning_logs/index.html')

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
    claims = Claim.objects.all().order_by('-date_created')
    return render(request, "learning_logs/claims.html", {'claims': claims})

@login_required
def new_claim(request):
    if request.method == 'POST':
        form = ClaimForm(request.POST)

        if form.is_valid():
            # request.session['claim_data'] = form.cleaned_data
            data = form.cleaned_data
            data['claim_amount'] = float(data['claim_amount'])
            request.session['claim_data'] = data
            return redirect('learning_logs:upload_documents')
    else:
        form = ClaimForm()
        print("Claim Details Must be Valid")

    return render(request, 'learning_logs/new_claim.html', {'form': form})

@login_required
def sales(request):
    return render(request, "learning_logs/sales.html")


@login_required
def inventory(request):
    return render(request, "learning_logs/inventory.html")

@login_required
def claim_detail(request, claim_id):
    claim = Claim.objects.get(id=claim_id)
    previous_claims = Claim.objects.filter(vin=claim.vin).exclude(id=claim.id)
    
    risk_flags = {
    "high_amount": claim.claim_amount > 1500,
    "many_claims": previous_claims.count() >= 2,
    "previous_claims": previous_claims,
    }

    return render(request, 'learning_logs/claim_detail.html', {
        'claim': claim,
        'risk': risk_flags
    })


@login_required
def update_claim_status(request, claim_id, status):
    claim = Claim.objects.get(id=claim_id)
    claim.status = status
    claim.save()
    return redirect('learning_logs:claim_detail', claim_id=claim.id)

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
        title=data.get('title', 'N/A')   
    )
        
        request.session.flush()

        return redirect('learning_logs:claims')
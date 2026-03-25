from django.db import models
from django import forms
from django.contrib.auth.models import User

# Create your models here.

class Topic(models.Model):
    # A topic the user is learning about
    text = models.CharField(max_length=200)
    date_added = models.DateTimeField(auto_now_add=True)

    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        # Return a string representation of the model
        return self.text

class Entry(models.Model):
    # Something specific learned about a topic
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    text = models.TextField()
    date_added = models.DateTimeField(auto_now_add=True)
    class Meta:
        verbose_name_plural = 'Entries'
    
    def __str__(self):
    # Return a string representation of the model
        return f"{self.text[:50]}..."
    
class Claim(models.Model):
    POLICY_LEVEL_CHOICES = [
        ('LOW', 'Under 1500'),
        ('HIGH', '1500+'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('MORE_INFO', 'More Info Required'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    claim_amount = models.DecimalField(max_digits=10, decimal_places=2)
    claim_level = models.CharField(max_length=10, choices=POLICY_LEVEL_CHOICES, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    date_created = models.DateTimeField(auto_now_add=True)
    policy_number = models.CharField(max_length=100, default='')
    vin = models.CharField(max_length=100, default='')
    attachment = models.FileField(upload_to='claims/', blank=True, null=True)

    def save(self, *args, **kwargs):
        # AUTO CLASSIFY CLAIM LEVEL
        if self.claim_amount < 1500:
            self.claim_level = 'LOW'
        else:
            self.claim_level = 'HIGH'
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
    
class ClaimForm(forms.ModelForm):
    class Meta:
        model = Claim
        fields = ['policy_number', 'vin', 'title', 'description', 'claim_amount']

    def new_claim(request):
        if request.method != 'POST':
            form = ClaimForm()
        else:
            form = ClaimForm(data=request.POST)
            if form.is_valid():
                form.save
                return redirect('learning_logs:claims')
        
        return render(request, 'learning_logs/new_claims.html', {'form': form})
    
    inspection_status = models.CharField(
    max_length=20,
    choices=[
        ('SCHEDULED','Scheduled'),
        ('COMPLETED','Completed'),
        ('EXPIRED','Expired')
    ],
    default='SCHEDULED'
)
#learning_logs/forms.py
from django import forms
from .models import Topic, Entry, Claim

class TopicForm(forms.ModelForm):
    class Meta:
        model = Topic
        fields = ['text']
        labels = {'text': 'Enter text'}

class EntryForm(forms.ModelForm):
    class Meta:
        model = Entry
        fields = ['text']
        labels = {'text': 'Entry:'}
        widgets = {'text': forms.Textarea(attrs={'cols': 80})}

class ClaimForm(forms.ModelForm):
    class Meta:
        model = Claim
        fields = ['policy_number', 'vin', 'description', 'claim_amount']

def clean_policy_number(self):
    policy = self.cleaned_data['policy_number']
    
    if not policy.isdigit():
        raise forms.ValidationError("Policy number must be numeric")
    
    return policy
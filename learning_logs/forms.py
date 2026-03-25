from django import forms
from .models import Topic, Entry, Dealership, Inventory

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

class NewSaleForm(forms.Form):
    dealership = forms.ModelChoiceField(
        queryset=Dealership.objects.all(),
        label='Dealership',
        widget=forms.Select(attrs={
            'class': 'w-full rounded border border-gray-300 bg-gray-50 px-3 py-2'
        })
    )

    firstname = forms.CharField(
        label='Customer First Name',
        widget=forms.TextInput(attrs={
            'class': 'w-full rounded border border-gray-300 bg-gray-50 px-3 py-2'
        })
    )

    lastname = forms.CharField(
        label='Customer Last Name',
        widget=forms.TextInput(attrs={
            'class': 'w-full rounded border border-gray-300 bg-gray-50 px-3 py-2'
        })
    )

    phone = forms.CharField(
        label='Phone',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full rounded border border-gray-300 bg-gray-50 px-3 py-2'
        })
    )

    email = forms.CharField(
        label='Email',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full rounded border border-gray-300 bg-gray-50 px-3 py-2'
        })
    )

    address = forms.CharField(
        label='Address',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full rounded border border-gray-300 bg-gray-50 px-3 py-2'
        })
    )

    vehicle_model = forms.CharField(
        label='Vehicle Model',
        widget=forms.TextInput(attrs={
            'class': 'w-full rounded border border-gray-300 bg-gray-50 px-3 py-2',
            'placeholder': 'Toyota Camry'
        })
    )

    year = forms.IntegerField(
        label='Year',
        widget=forms.NumberInput(attrs={
            'class': 'w-full rounded border border-gray-300 bg-gray-50 px-3 py-2',
            'placeholder': '2020'
        })
    )

    mileage = forms.CharField(
        label='Mileage',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full rounded border border-gray-300 bg-gray-50 px-3 py-2',
            'placeholder': '45000'
        })
    )

    vin = forms.CharField(
        label='VIN',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full rounded border border-gray-300 bg-gray-50 px-3 py-2',
            'placeholder': 'VIN001'
        })
    )

    startdate = forms.DateField(
        label='Start Date',
        widget=forms.DateInput(attrs={
          'type': 'date',
          'class': 'w-full rounded border border-gray-300 bg-gray-50 px-3 py-2'
        })
    )

    enddate = forms.DateField(
        label='End Date',
        widget=forms.DateInput(attrs={
           'type': 'date',
           'class': 'w-full rounded border border-gray-300 bg-gray-50 px-3 py-2'
        })
    )

    status = forms.ChoiceField(
        choices=[
           ('Active', 'Active'),
           ('Expired', 'Expired'),
        ],
        label='Status',
        widget=forms.Select(attrs={
        'class': 'w-full rounded border border-gray-300 bg-gray-50 px-3 py-2'
    })
    )

    coveragetype = forms.ChoiceField(
        choices=[
        ('Full', 'Full'),
        ('Basic', 'Basic'),
        ('Powertrain', 'Powertrain'),
       ],
        label='Coverage Type',
        widget=forms.Select(attrs={
        'class': 'w-full rounded border border-gray-300 bg-gray-50 px-3 py-2'
    })
    )

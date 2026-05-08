from django import forms
from .models import ContactMessage, QuoteRequest

class ContactForm(forms.ModelForm):
    website_hp = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'style': 'display:none;', 'autocomplete': 'off', 'tabindex': '-1'}),
        label=''
    )
    
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'phone', 'company', 'subject', 'message', 
                   'category', 'budget_range', 'timeline', 'attachment']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'Your Full Name *', 'required': 'required'}),
            'email': forms.EmailInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'your.email@example.com *', 'required': 'required'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number (optional)'}),
            'company': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Company/Organization (optional)'}),
            'subject': forms.TextInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'Subject *', 'required': 'required'}),
            'message': forms.Textarea(attrs={'class': 'form-control form-control-lg', 'rows': 6, 'placeholder': 'Your message... *', 'required': 'required'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'budget_range': forms.Select(attrs={'class': 'form-select'}),
            'timeline': forms.Select(attrs={'class': 'form-select'}),
            'attachment': forms.FileInput(attrs={'class': 'form-control'}),
        }
    
    def clean_website_hp(self):
        value = self.cleaned_data.get('website_hp')
        if value:
            raise forms.ValidationError('Spam detected')
        return value
    
    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if len(name) < 2:
            raise forms.ValidationError('Name must be at least 2 characters.')
        return name
    
    def clean_message(self):
        message = self.cleaned_data.get('message', '').strip()
        if len(message) < 10:
            raise forms.ValidationError('Message must be at least 10 characters.')
        return message

class QuoteRequestForm(forms.ModelForm):
    website_hp = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'style': 'display:none;', 'autocomplete': 'off'}),
        label=''
    )
    
    class Meta:
        model = QuoteRequest
        fields = ['name', 'email', 'phone', 'company', 'project_name', 
                   'project_type', 'project_description', 'technologies',
                   'has_design', 'budget_range', 'timeline', 'attachment']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your Full Name *'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'your.email@example.com *'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number (optional)'}),
            'company': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Company/Organization (optional)'}),
            'project_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Project Name *'}),
            'project_type': forms.Select(attrs={'class': 'form-select'}),
            'project_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 6, 'placeholder': 'Describe your project in detail... *'}),
            'technologies': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Preferred technologies (comma-separated)'}),
            'has_design': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'budget_range': forms.Select(attrs={'class': 'form-select'}),
            'timeline': forms.Select(attrs={'class': 'form-select'}),
            'attachment': forms.FileInput(attrs={'class': 'form-control'}),
        }
    
    def clean_website_hp(self):
        value = self.cleaned_data.get('website_hp')
        if value:
            raise forms.ValidationError('Spam detected')
        return value
    
    def clean_project_description(self):
        description = self.cleaned_data.get('project_description', '').strip()
        if len(description) < 20:
            raise forms.ValidationError('Please provide a more detailed description (at least 20 characters).')
        return description

class FAQSearchForm(forms.Form):
    q = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'Search FAQs...'})
    )

class FAQFeedbackForm(forms.Form):
    FEEDBACK_CHOICES = [('helpful', 'Helpful'), ('not_helpful', 'Not Helpful')]
    feedback = forms.ChoiceField(choices=FEEDBACK_CHOICES, widget=forms.HiddenInput())

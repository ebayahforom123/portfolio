from django import forms
from django.core.validators import EmailValidator
from apps.contact.models import ContactMessage


class ContactForm(forms.ModelForm):
    """Contact form with honeypot spam protection"""

    honeypot = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'style': 'display:none;'}),
        label='Leave empty'
    )

    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Your Name',
                'required': 'required',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'your.email@example.com',
                'required': 'required',
            }),
            'subject': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Subject',
                'required': 'required',
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control form-control-lg',
                'rows': 6,
                'placeholder': 'Your message...',
                'required': 'required',
            }),
        }

    def clean_honeypot(self):
        """Check honeypot field is empty"""
        honeypot = self.cleaned_data.get('honeypot')
        if honeypot:
            raise forms.ValidationError('Spam detected')
        return honeypot

    def clean_name(self):
        """Clean and validate name"""
        name = self.cleaned_data.get('name', '').strip()
        if len(name) < 2:
            raise forms.ValidationError('Name must be at least 2 characters')
        return name

    def clean_message(self):
        """Clean and validate message"""
        message = self.cleaned_data.get('message', '').strip()
        if len(message) < 10:
            raise forms.ValidationError('Message must be at least 10 characters')
        return message


class ProjectFilterForm(forms.Form):
    """Form for filtering projects"""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search projects...',
        })
    )
    technology = forms.CharField(
        required=False,
        widget=forms.HiddenInput()
    )
    project_type = forms.ChoiceField(
        required=False,
        choices=[('', 'All Types')] + [
            ('web', 'Web Application'),
            ('mobile', 'Mobile App'),
            ('desktop', 'Desktop Application'),
            ('api', 'API/Backend'),
            ('library', 'Library/Package'),
            ('design', 'UI/UX Design'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-select',
        })
    )
    sort_by = forms.ChoiceField(
        required=False,
        choices=[
            ('-created_at', 'Newest'),
            ('created_at', 'Oldest'),
            ('title', 'Name A-Z'),
            ('-title', 'Name Z-A'),
        ],
        initial='-created_at',
        widget=forms.Select(attrs={
            'class': 'form-select',
        })
    )
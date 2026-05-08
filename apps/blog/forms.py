from django import forms
from .models import Comment, Subscriber
from django.core.validators import EmailValidator


class CommentForm(forms.ModelForm):
    """Form for blog comments with spam protection"""

    honeypot = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'style': 'display:none;',
            'autocomplete': 'off',
        }),
        label=''
    )

    class Meta:
        model = Comment
        fields = ['name', 'email', 'website', 'body']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your Name *',
                'required': 'required',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your Email *',
                'required': 'required',
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your Website (optional)',
            }),
            'body': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Your Comment *',
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
        name = self.cleaned_data.get('name', '').strip()
        if len(name) < 2:
            raise forms.ValidationError('Name must be at least 2 characters.')
        return name

    def clean_body(self):
        body = self.cleaned_data.get('body', '').strip()
        if len(body) < 5:
            raise forms.ValidationError('Comment must be at least 5 characters.')

        # Check for excessive links (spam indicator)
        import re
        url_count = len(re.findall(r'https?://', body))
        if url_count > 3:
            raise forms.ValidationError('Too many links in comment. Please reduce.')

        return body


class SearchForm(forms.Form):
    """Blog search form"""
    q = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search blog posts...',
            'aria-label': 'Search',
        })
    )


class NewsletterForm(forms.Form):
    """Newsletter subscription form"""
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email',
        })
    )
    name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your Name (optional)',
        })
    )
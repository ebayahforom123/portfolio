from django.shortcuts import render, redirect
from django.views.generic import View, TemplateView
from django.contrib import messages
from .models import ContactMessage, ContactInfo, FAQ
from django.utils import timezone


class ContactView(View):
    template_name = "pages/contact.html"
    
    def get(self, request):
        context = {
            'contact_info': ContactInfo.objects.first(),
            'site_settings': self._get_site_settings(),
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()
        
        # Simple validation
        if not name or not email or not message:
            messages.error(request, 'Please fill in all required fields.')
            return redirect('contact:contact')
        
        # Save to database
        ContactMessage.objects.create(
            name=name,
            email=email,
            subject=subject or 'No Subject',
            message=message,
            ip_address=self._get_ip(request),
        )
        
        messages.success(request, 'Thank you for your message! I will get back to you soon.')
        return redirect('contact:contact')
    
    def _get_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '')
    
    def _get_site_settings(self):
        try:
            from apps.portfolio.models import SiteSettings
            return SiteSettings.objects.first()
        except:
            return None


class FAQView(TemplateView):
    template_name = "pages/faq.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['faqs'] = FAQ.objects.filter(is_active=True)
        return context


class FAQSearchView(View):
    def get(self, request):
        query = request.GET.get('q', '')
        faqs = FAQ.objects.filter(question__icontains=query, is_active=True)
        return render(request, 'pages/faq.html', {'faqs': faqs, 'query': query})


class FAQFeedbackView(View):
    def post(self, request, faq_id):
        faq = FAQ.objects.get(id=faq_id)
        feedback = request.POST.get('feedback')
        if feedback == 'helpful':
            faq.helpful_count += 1
        else:
            faq.not_helpful_count += 1
        faq.save()
        return redirect('contact:faq')


class QuoteRequestView(TemplateView):
    template_name = "pages/quote_request.html"


class QuoteSuccessView(TemplateView):
    template_name = "pages/quote_success.html"


class ContactSuccessView(TemplateView):
    template_name = "pages/contact_success.html"


class ContactInfoAPIView(View):
    def get(self, request):
        from django.http import JsonResponse
        info = ContactInfo.objects.first()
        return JsonResponse({'email': info.email if info else ''})

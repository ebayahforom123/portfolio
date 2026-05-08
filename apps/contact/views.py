from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import View, TemplateView, ListView, DetailView
from django.urls import reverse, reverse_lazy
from django.http import JsonResponse, Http404
from django.contrib import messages
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.db.models import Count
from django.core.cache import cache
from .models import ContactMessage, ContactInfo, FAQ, QuoteRequest
from .forms import (
    ContactForm, QuoteRequestForm, FAQSearchForm,
    FAQFeedbackForm
)
import json


class ContactView(View):
    """Main contact page with form"""
    template_name = 'pages/contact.html'

    def get(self, request):
        """Display contact form"""
        form = ContactForm()
        contact_info = ContactInfo.load()

        context = {
            'form': form,
            'contact_info': contact_info,
            'page_title': 'Contact Me',
            'meta_title': contact_info.meta_title or 'Contact',
            'meta_description': contact_info.meta_description or 'Get in touch',
        }

        return render(request, self.template_name, context)

    def post(self, request):
        """Handle contact form submission"""
        form = ContactForm(request.POST, request.FILES)
        contact_info = ContactInfo.load()

        # reCAPTCHA validation if enabled
        if contact_info.use_recaptcha:
            recaptcha_response = request.POST.get('g-recaptcha-response')
            if not self._validate_recaptcha(recaptcha_response):
                messages.error(request, 'Please complete the reCAPTCHA.')
                return render(request, self.template_name, {
                    'form': form,
                    'contact_info': contact_info,
                })

        if form.is_valid():
            # Save contact message
            contact_message = form.save(commit=False)

            # Add tracking info
            contact_message.ip_address = self._get_client_ip(request)
            contact_message.user_agent = request.META.get('HTTP_USER_AGENT', '')
            contact_message.referrer = request.META.get('HTTP_REFERER', '')
            contact_message.session_key = request.session.session_key

            contact_message.save()

            # Send auto-reply if enabled
            if contact_info.auto_reply_enabled:
                self._send_auto_reply(contact_message, contact_info)

            # Notify admin if enabled
            if contact_info.notify_admin:
                self._notify_admin(contact_message, contact_info)

            # Success message
            messages.success(
                request,
                'Thank you for your message! I will get back to you as soon as possible.'
            )

            # If AJAX request, return JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Message sent successfully!',
                    'message_id': str(contact_message.uuid),
                })

            return redirect('contact:contact_success', uuid=contact_message.uuid)

        # Form validation failed
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'errors': form.errors,
            }, status=400)

        return render(request, self.template_name, {
            'form': form,
            'contact_info': contact_info,
        })

    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '')

    def _validate_recaptcha(self, response):
        """Validate Google reCAPTCHA"""
        if not response:
            return False

        import requests
        contact_info = ContactInfo.load()

        data = {
            'secret': contact_info.recaptcha_secret_key,
            'response': response,
        }

        try:
            r = requests.post(
                'https://www.google.com/recaptcha/api/siteverify',
                data=data
            )
            result = r.json()
            return result.get('success', False)
        except Exception:
            return False

    def _send_auto_reply(self, contact_message, contact_info):
        """Send auto-reply confirmation email to sender"""
        subject = contact_info.auto_reply_subject or f'Re: {contact_message.subject}'

        context = {
            'contact': contact_message,
            'contact_info': contact_info,
            'site_url': settings.SITE_URL if hasattr(settings, 'SITE_URL') else '',
        }

        # Use custom message or default template
        if contact_info.auto_reply_message:
            html_message = contact_info.auto_reply_message
        else:
            html_message = render_to_string(
                'emails/auto_reply.html', context
            )

        text_message = render_to_string(
            'emails/auto_reply.txt', context
        )

        try:
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[contact_message.email],
            )
            email.attach_alternative(html_message, "text/html")
            email.send(fail_silently=True)

            # Update tracking
            contact_message.email_sent = True
            contact_message.email_sent_at = timezone.now()
            contact_message.save(update_fields=['email_sent', 'email_sent_at'])

        except Exception as e:
            # Log error but don't show to user
            print(f"Failed to send auto-reply: {e}")

    def _notify_admin(self, contact_message, contact_info):
        """Send notification to admin"""
        notification_email = contact_info.notification_email or contact_info.email

        context = {
            'contact': contact_message,
            'contact_info': contact_info,
            'admin_url': f"{settings.SITE_URL}/admin/contact/contactmessage/{contact_message.id}/change/",
        }

        subject = f'New Contact Message: {contact_message.subject}'
        html_message = render_to_string('emails/admin_notification.html', context)
        text_message = render_to_string('emails/admin_notification.txt', context)

        try:
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[notification_email],
            )
            email.attach_alternative(html_message, "text/html")
            email.send(fail_silently=True)
        except Exception as e:
            print(f"Failed to send admin notification: {e}")


class ContactSuccessView(TemplateView):
    """Success page after contact form submission"""
    template_name = 'pages/contact_success.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['message_id'] = self.kwargs.get('uuid', '')
        context['contact_info'] = ContactInfo.load()
        return context


class FAQView(TemplateView):
    """FAQ listing page"""
    template_name = 'pages/faq.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Cache FAQs for 30 minutes
        cache_key = 'faq_data'
        faq_data = cache.get(cache_key)

        if not faq_data:
            faqs = FAQ.objects.filter(is_active=True).order_by(
                '-is_featured', 'category', 'order'
            )

            # Group by category
            categories = {}
            for faq in faqs:
                category_name = faq.get_category_display()
                if category_name not in categories:
                    categories[category_name] = []
                categories[category_name].append(faq)

            faq_data = categories
            cache.set(cache_key, faq_data, 60 * 30)

        context['faq_categories'] = faq_data
        context['search_form'] = FAQSearchForm()
        context['contact_info'] = ContactInfo.load()
        context['page_title'] = 'FAQ'

        return context


class FAQSearchView(View):
    """Search FAQs"""

    def get(self, request):
        query = request.GET.get('q', '').strip()

        if query:
            faqs = FAQ.objects.filter(
                question__icontains=query,
                is_active=True
            ) | FAQ.objects.filter(
                answer__icontains=query,
                is_active=True
            )
        else:
            faqs = FAQ.objects.none()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            results = []
            for faq in faqs:
                results.append({
                    'id': faq.id,
                    'question': faq.question,
                    'answer': faq.answer,
                    'slug': faq.slug,
                    'category': faq.get_category_display(),
                })
            return JsonResponse({'results': results})

        return render(request, 'pages/faq.html', {
            'faqs': faqs,
            'query': query,
            'search_form': FAQSearchForm(initial={'q': query}),
            'page_title': f'FAQ Search: {query}',
        })


class FAQFeedbackView(View):
    """Handle helpful/not helpful feedback for FAQs"""

    def post(self, request, faq_id):
        faq = get_object_or_404(FAQ, id=faq_id, is_active=True)
        feedback = request.POST.get('feedback', '')

        if feedback == 'helpful':
            faq.helpful_count += 1
            faq.save(update_fields=['helpful_count'])
            message = 'Thank you for your feedback!'
        elif feedback == 'not_helpful':
            faq.not_helpful_count += 1
            faq.save(update_fields=['not_helpful_count'])
            message = 'Thank you for your feedback. We will improve this answer.'
        else:
            return JsonResponse({'error': 'Invalid feedback'}, status=400)

        # Get updated counts
        faq.refresh_from_db()

        return JsonResponse({
            'success': True,
            'message': message,
            'helpful_count': faq.helpful_count,
            'not_helpful_count': faq.not_helpful_count,
            'helpful_percentage': faq.helpful_percentage,
        })


class QuoteRequestView(View):
    """Handle project quote requests"""
    template_name = 'pages/quote_request.html'

    def get(self, request):
        form = QuoteRequestForm()
        return render(request, self.template_name, {
            'form': form,
            'contact_info': ContactInfo.load(),
            'page_title': 'Request a Quote',
        })

    def post(self, request):
        form = QuoteRequestForm(request.POST)

        if form.is_valid():
            quote_request = form.save(commit=False)

            # Add tracking
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                quote_request.ip_address = x_forwarded_for.split(',')[0].strip()
            else:
                quote_request.ip_address = request.META.get('REMOTE_ADDR', '')

            quote_request.save()

            # Notify admin
            self._notify_admin(quote_request)

            messages.success(
                request,
                'Your quote request has been submitted! I will review it and get back to you shortly.'
            )

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Quote request submitted successfully!',
                })

            return redirect('contact:quote_success')

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'errors': form.errors,
            }, status=400)

        return render(request, self.template_name, {
            'form': form,
            'contact_info': ContactInfo.load(),
        })

    def _notify_admin(self, quote_request):
        """Notify admin about new quote request"""
        contact_info = ContactInfo.load()
        notification_email = contact_info.notification_email or contact_info.email

        context = {
            'quote': quote_request,
            'admin_url': f"{settings.SITE_URL}/admin/contact/quoterequest/{quote_request.id}/change/",
        }

        subject = f'New Quote Request: {quote_request.project_name}'
        html_message = render_to_string('emails/quote_notification.html', context)

        try:
            send_mail(
                subject,
                '',
                settings.DEFAULT_FROM_EMAIL,
                [notification_email],
                html_message=html_message,
                fail_silently=True
            )
        except Exception as e:
            print(f"Failed to send quote notification: {e}")


class QuoteSuccessView(TemplateView):
    """Success page after quote request"""
    template_name = 'pages/quote_success.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['contact_info'] = ContactInfo.load()
        return context


class ContactInfoAPIView(View):
    """API endpoint for contact information"""

    def get(self, request):
        """Return contact info as JSON"""
        contact_info = ContactInfo.load()

        data = {
            'email': contact_info.email,
            'phone': contact_info.phone,
            'whatsapp': contact_info.whatsapp,
            'address': contact_info.address,
            'city': contact_info.city,
            'state': contact_info.state,
            'country': contact_info.country,
            'working_hours': contact_info.working_hours,
            'timezone': contact_info.timezone,
            'has_map': bool(contact_info.google_maps_embed),
            'social_links': [],
        }

        for link in contact_info.get_social_links():
            data['social_links'].append({
                'name': link['name'],
                'url': link['url'],
                'icon': link['icon'],
            })

        return JsonResponse(data)
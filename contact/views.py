import logging

from django.conf import settings
from django.contrib import messages
from django.core.mail import EmailMessage
from django.shortcuts import redirect
from django.views.decorators.http import require_POST

from .forms import ContactMessageForm

logger = logging.getLogger(__name__)


@require_POST
def contact_submit(request):
    form = ContactMessageForm(request.POST)
    next_url = request.POST.get("next") or "/contact/"

    if not form.is_valid():
        messages.error(request, "Please check the form and try again.")
        return redirect(next_url)

    if form.cleaned_data.get("website"):
        # Silent success for bots.
        messages.success(request, "Thank you — your message has been sent.")
        return redirect(next_url)

    name = form.cleaned_data["name"].strip()
    email = form.cleaned_data["email"].strip()
    phone = (form.cleaned_data.get("phone") or "").strip() or "—"
    body = form.cleaned_data["message"].strip()

    recipient = getattr(settings, "CONTACT_TO_EMAIL", "info@yeshualifeug.com")
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None) or recipient

    subject = f"Website contact from {name}"
    text = (
        f"New message from the Yeshua Life contact form\n\n"
        f"Name: {name}\n"
        f"Email: {email}\n"
        f"Phone: {phone}\n\n"
        f"Message:\n{body}\n"
    )

    try:
        mail = EmailMessage(
            subject=subject,
            body=text,
            from_email=from_email,
            to=[recipient],
            reply_to=[email],
        )
        mail.send(fail_silently=False)
    except Exception:
        logger.exception("Contact form email failed (to=%s)", recipient)
        messages.error(
            request,
            "Sorry — we could not send your message right now. "
            "Please email info@yeshualifeug.com directly.",
        )
        return redirect(next_url)

    messages.success(request, "Thank you — your message has been sent to info@yeshualifeug.com.")
    return redirect(next_url)

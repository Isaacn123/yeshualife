from django import forms


class ContactMessageForm(forms.Form):
    name = forms.CharField(
        max_length=120,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Your Name",
                "autocomplete": "name",
            }
        ),
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "Your Email",
                "autocomplete": "email",
            }
        ),
    )
    phone = forms.CharField(
        max_length=40,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Phone Number",
                "autocomplete": "tel",
            }
        ),
    )
    message = forms.CharField(
        max_length=2000,
        required=True,
        widget=forms.Textarea(
            attrs={
                "class": "form-control yl-contact__message",
                "placeholder": "Your Message",
                "rows": 4,
            }
        ),
    )
    # Honeypot — leave empty; bots often fill it.
    website = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "yl-contact__hp",
                "tabindex": "-1",
                "autocomplete": "off",
                "aria-hidden": "true",
            }
        ),
    )

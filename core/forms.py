from django import forms


class MonitorForm(forms.Form):
    pair_name = forms.CharField(
        label='Pair Name',
        max_length=100,
        widget=forms.TextInput(
            attrs={'placeholder': 'Pair Name', 'class': 'input w-full'}
        ),
    )

    threshold_depth = forms.FloatField(
        label='Threshold Depth (Inches)',
        widget=forms.NumberInput(
            attrs={
                'class': 'input w-full',
                'placeholder': '0.0',
                'min': '0.0',
            }
        ),
    )

    pair_id = forms.IntegerField(
        label='Pair ID',
        required=False,
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Pair ID',
                'class': 'input w-full disabled:text-black',
                'disabled': 'disabled',
            }
        ),
    )

    token = forms.CharField(
        label='API Token',
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={
                'id': 'tokenField',
                'placeholder': 'API Token',
                'class': 'pr-[50px] w-full input inline-block disabled:text-black',
                'type': 'password',
                'disabled': 'disabled',
            },
        ),
    )

    location = forms.CharField(
        label='Location',
        max_length=100,
        widget=forms.TextInput(
            attrs={'placeholder': 'Location of the Monitor', 'class': 'input w-full'}
        ),
    )

    emails = forms.CharField(
        label='Emails',
        widget=forms.EmailInput(
            attrs={
                'placeholder': 'email1@example.com,email2@example.com',
                'class': 'input w-full',
                'multiple': 'multiple',
            }
        ),
    )

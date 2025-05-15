from django import forms

class MonitorForm(forms.Form):
    pair_name = forms.CharField(
        label="Pair Name", 
        max_length=100,
        widget=forms.TextInput(
            attrs={"placeholder": "Pair Name", "class": "input w-full"}
        ),
    )

    threshold_depth = forms.IntegerField(
        widget=forms.NumberInput(
            attrs={
                "class": "input w-full",
                "placeholder": "0",
                "min": "0",
            }
        ),
    )

    api_token = forms.CharField(
        label="API Token", 
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={"placeholder": "API Token", "class": "input w-full disabled:text-black", "disabled": "disabled"}
        ),
    )

    location = forms.CharField(
        label="Location", 
        max_length=100,
        widget=forms.TextInput(
            attrs={"placeholder": "Location of the Monitor", "class": "input w-full"}
        ),
    )
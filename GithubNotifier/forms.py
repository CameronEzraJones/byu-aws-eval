from django import forms


class GitHubOrganizationSearchForm(forms.Form):
    organization = forms.CharField()

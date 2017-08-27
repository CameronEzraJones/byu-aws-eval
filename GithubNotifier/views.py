import json
import os
import re
import time
import urllib.request

import boto3
from django.conf import settings
from django.core.mail import send_mail
from django.http import Http404, HttpResponse
from django.shortcuts import render, redirect
from django.template.loader import render_to_string

from .forms import GitHubOrganizationSearchForm


# Create your views here.
def send_emails_to_nameless_members(request):
    print('Send email to nameless members')
    members = json.loads(request.POST['nameless_members'])
    for member in members:
        msg_plain = render_to_string('email/email.txt', {'login_name': member['login']})
        msg_html = render_to_string('email/email.html', {'login_name': member['login']})
        send_mail('Please update your GitHub name', msg_plain, 'cjones@example.com',
                  [member['email'] or 'no-email-given@gmail.com'], fail_silently=False,
                  html_message=msg_html)
    return HttpResponse(status=204)
    pass


def save_nameless_members_to_aws(request):
    print('Save nameless members to aws')
    organization = request.POST['organization']
    members = request.POST['nameless_members']
    filename = '{0}-{1}.txt'.format(organization, int(time.time()))
    f = open(filename, 'w')
    f.write(members)
    f.close()
    s3 = boto3.client('s3')
    s3.upload_file(filename, settings.AWS_BUCKET_NAME, filename)
    os.remove(filename)
    return HttpResponse(status=204)
    pass


def index(request):
    organization = request.GET.get('organization')
    if organization:
        return redirect('members/{0}'.format(organization))
    form = GitHubOrganizationSearchForm()
    return render(request, 'GithubNotifier/index.html', {'form': form})


def get_member_name_and_email(member):
    github_api_host = settings.GITHUB_API_HOST
    github_user_path = '/users/{0}'.format(member['login'])
    github_url = github_api_host + github_user_path
    headers = settings.GITHUB_API_HEADERS
    try:
        github_request = urllib.request.Request(github_url, headers=headers)
        with urllib.request.urlopen(github_request) as f:
            contents = f.read().decode('utf-8')
            user_details = json.loads(contents)
            return user_details['name'], user_details['email']
    except:
        return None, None
    pass


def get_next_url(headers):
    if 'Link' in headers:
        links = headers['Link'].split(', ')
        for link in links:
            link_info = link.split('; ')
            if re.search('rel="(.*)"', link_info[1])[1] == 'next':
                return re.search('<(.*)>', link_info[0])[1]
    return None


def members(request, organization):
    github_api_host = settings.GITHUB_API_HOST
    github_org_members_path = '/orgs/{0}/members'
    github_url = github_api_host + github_org_members_path.format(organization)
    members = []
    nameless_members = []
    headers = settings.GITHUB_API_HEADERS
    try:
        while github_url != '' and github_url is not None:
            github_request = urllib.request.Request(github_url, headers=headers)
            with urllib.request.urlopen(github_request) as f:
                contents = f.read().decode('utf-8')
                members_retrieved = json.loads(contents)
                for member in members_retrieved:
                    member['name'], member['email'] = get_member_name_and_email(member)
                    if member['name'] is None:
                        nameless_members.append(member)
                    members.append(member)
            github_url = get_next_url(f.info())
    except:
        raise Http404('Organization {0} does not exist'.format(organization))
    return render(request, 'GithubNotifier/members.html',
                  {'organization': organization, 'org_members': members,
                   'nameless_members': json.dumps(nameless_members)})

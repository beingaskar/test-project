from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q
from django.core.mail import send_mail

from .utils import create_random_string
from .forms import AuthenticationForm, UserRegistrationForm, ProfileEditForm
from .models import UserProfile


def home(request):
    temp_dict = {}
    reg_form = UserRegistrationForm()
    if request.user.is_authenticated():
        if request.user.is_staff:
            return HttpResponseRedirect('/admin')
        else:
            return HttpResponseRedirect('/dashboard')
    if request.POST:
        print "posted"
        reg_form = UserRegistrationForm(request.POST)
        if reg_form.is_valid():
            print "valid form"
            user_profile_obj = reg_form.save(commit=False)
            user_obj = User.objects.create_user(username=create_random_string(),
                                                email=request.POST['email'], password=request.POST['password'])
            user_profile_obj.user = user_obj
            user_profile_obj.save()

            User.objects.filter(~Q(id=user_obj.id) & Q(email=user_obj.email)).delete()

            # Below task will be made to run in background using celery
            # Email sending code. Will be using django templated email.
            try:
                send_mail('Demo App - Registration', 'Thankyou for registration.', 'askar@demoapp.com',
                                            [request.POST['email']], fail_silently=False)

            except:
                pass

            user_login = authenticate(username=request.POST['email'], password=request.POST['password'])
            if user_login:
                login(request, user_login)
                return HttpResponseRedirect('/dashboard/?new-user')
            else:
                temp_dict['error_message'] = "Invalid Credentials."
    temp_dict['form'] = reg_form
    return render_to_response(
        'home.html',
        temp_dict, context_instance=RequestContext(request))


def login_user(request):
    if request.user.is_authenticated():
        if request.user.is_staff:
            return HttpResponseRedirect('/admin')
        else:
            return HttpResponseRedirect('/dashboard')

    temp_dict = {}
    form = AuthenticationForm()
    if request.POST:
        form = AuthenticationForm(request.POST)
        email = request.POST['username']
        password = request.POST['password']
        user_login = authenticate(username=email, password=password)
        if user_login:
            login(request, user_login)
            return HttpResponseRedirect('/dashboard/')
        else:
            temp_dict['error_message'] = "Invalid Credentials."

    temp_dict['form'] = form
    return render_to_response(
        'login.html',
        temp_dict, context_instance=RequestContext(request))


@login_required()
def dashboard(request):
    if request.user.is_staff:
        return HttpResponseRedirect('/admin')

    try:
        user_profile = UserProfile.objects.get(user=request.user)
    except:
        return HttpResponseRedirect('/')

    temp_dict = {}
    if 'new-user' in request.GET:
        messages.success(request, "Thank you for registering. We assure you a good time ahead.")
    temp_dict['user_profile'] = user_profile
    return render_to_response(
        'dashboard.html',
        temp_dict, context_instance=RequestContext(request))


def logout_user(request):
    logout(request)
    return HttpResponseRedirect('/')


def user_profile(request):
    temp_dict = {}
    if request.user.is_staff:
        return HttpResponseRedirect('/admin')

    try:
        user_profile = UserProfile.objects.get(user=request.user)
    except:
        return HttpResponseRedirect('/')

    form = ProfileEditForm(instance=user_profile)
    if request.POST:
        print "posted"
        form = ProfileEditForm(request.POST, instance=user_profile)
        if form.is_valid():
            user_profile = form.save(commit=False)
            user_profile.user = request.user
            user_profile.save()

    temp_dict['form'] = form
    temp_dict['user_profile'] = user_profile
    return render_to_response(
        'profile.html',
        temp_dict, context_instance=RequestContext(request))
import os
import subprocess
from random import randint, shuffle
import datetime
import requests

from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.template import loader
from django.db.models import Q

from aesthetics_labeling.models import Comparison, Participant, ComparisonAssignment, TextQuestionResponse
from aesthetics_labeling.constants import TAGS
from labeling_interface.settings import BASE_DIR, BASE_URL

from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, REDIRECT_FIELD_NAME
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.sites.shortcuts import get_current_site
from django.template.response import TemplateResponse
from django.utils.http import is_safe_url

UNIQUE_IMAGES_PER_PERSON = 80

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def index(request):
    template = loader.get_template('index.html')
    return HttpResponse(template.render({}, request))

def email_in_use(request):
    template = loader.get_template('email_in_use.html')
    return HttpResponse(template.render({}, request))

def underage(request):
    template = loader.get_template('underage.html')
    return HttpResponse(template.render({}, request))

def informed_consent(request):
    template = loader.get_template('informed_consent.html')
    return HttpResponse(template.render({}, request))

def prep_image(image_path):
    """
    prepare an image for hosting
    image_path should be the path to an image
    """
    url = '/' + BASE_URL + 'aesthetics_labeling/static/images'
    new_dir = os.path.join(BASE_DIR, 'aesthetics_labeling/static/images/')
    directory, image_name = os.path.split(image_path)
    if not os.path.exists(image_path): 
        print('Image not found:', image_path)
        return None
    new_path = os.path.join(new_dir, image_name)
    new_url = os.path.join(url, image_name)
    if not os.path.exists(new_dir): os.mkdir(new_dir)
    if not os.path.exists(new_path): os.symlink(image_path, new_path)
    return new_url

def remove_broken_image(image):
    Comparison.objects.filter(
              Q(image_a=image)
            | Q(image_b=image)
    ).delete()

def handle_submission(request, comparison_id):
    data = request.POST
    comparison = Comparison.objects.get(id=comparison_id)
    comparison_assignment = ComparisonAssignment.objects.get(comparison=comparison, assigned_participant=request.user)
    comparison_assignment.finish_time = datetime.datetime.now()
    comparison_assignment.label = int(data['comparison_result'])
    if 'image_a_broken' in data:
        comparison.image_a.broken = True
        #remove_broken_image(comparison.image_a)
    if 'image_b_broken' in data:
        comparison.image_b.broken = True
        #remove_broken_image(comparison.image_b)
    comparison_assignment.save()

def get_next_question(user, assignments=None):
    if assignments is None:
        queryset = ComparisonAssignment.objects.filter(
            label=ComparisonAssignment.UNLABELED,
            assigned_participant=user,
        ).order_by('id')
    else:
        queryset = assignments.filter(
            label=ComparisonAssignment.UNLABELED
        ).order_by('id')
    if queryset.count() > 0:
        return queryset[0].comparison
    else:
        return None
    
def assign_images(user, common=True, unique=True):
    # assign some common image pairs
    assignments = []
    if common:
        common_image_pairs = list(Comparison.objects.filter(
            common=True
        ).all())
        shuffle(common_image_pairs)
        for pair in common_image_pairs:
            reverse = (randint(0,1) == 1)
            assignment = ComparisonAssignment(
                assigned_participant=user,
                comparison=pair,
                reverse=reverse
            )
            if not pair.assigned: 
                pair.assigned = True
                pair.save()
            assignments.append(assignment)
    
    # assign some other image pairs
    if unique:
        new_image_pairs = Comparison.objects.filter(
            common=False,
            assigned=False
        )
        for pair in new_image_pairs[:UNIQUE_IMAGES_PER_PERSON]:
            assignment = ComparisonAssignment(
                assigned_participant=user,
                comparison=pair
            )
            if not pair.assigned:
                pair.assigned = True
                pair.save()
            assignments.append(assignment)
    ComparisonAssignment.objects.bulk_create(assignments)

"""def update_user(user, data):
    if 'gender' in data:
        user.gender = data['gender']
    else:
        user.gender = ''
    if 'race' in data:
        user.race = data['race']
    else:
        user.race = ''
    if 'education' in data:
        user.education = data['education']
    else:
        user.education = 0
    if 'language' in data:
        user.language = data['language']
    else:
        user.language = ''
    user.save()"""
    
def aesthetics_labeling_homepage(request):
    """
    This should check if the user is logged in. If they are, show them a "most recent question" prompt
    If they're not, it should show two links: start and login.
    """
    if request.user.is_authenticated:
        most_recent_question = get_next_question(request.user)
        template = loader.get_template('aesthetics_labeling_homepage_authenticated.html')
        context = {'most_recent_question': most_recent_question}
        return HttpResponse(template.render(context, request))
    else:
        template = loader.get_template('aesthetics_labeling_homepage_default.html')
        return HttpResponse(template.render({}, request))
    
def request_additional(request):
    assign_images(request.user, common=False, unique=True)
    next_question = get_next_question(request.user)
    return redirect('/' + BASE_URL + 'aesthetics_labeling/' + str(next_question.id))

def login_view(request):
    if request.method == 'GET':
        form = AuthenticationForm(request)
        redirect_to = request.POST.get(REDIRECT_FIELD_NAME,
                                   request.GET.get(REDIRECT_FIELD_NAME, ''))
        current_site = get_current_site(request)
        context = {
            'form': form,
            REDIRECT_FIELD_NAME: redirect_to,
            'site': current_site,
            'site_name': current_site.name,
        }
        return TemplateResponse(request, 'registration/login.html', context)
    elif request.method == 'POST':
        
        resp = requests.post(
            'https://www.google.com/recaptcha/api/siteverify',
             data = {
                 'secret':'your_secret_key',
                 'response':request.POST['g-recaptcha-response']
             }
            )
        if not str(resp.json()['success']):
            return redirect('/' + BASE_URL + 'aesthetics_labeling/')
        
        username = request.POST['username']
        password = request.POST['password']
        form = AuthenticationForm(request, data=request.POST)
        redirect_to = request.POST.get(REDIRECT_FIELD_NAME, request.GET.get(REDIRECT_FIELD_NAME, ''))
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            user.ip = get_client_ip(request)
            user.save()
            next_question = get_next_question(user)
            if next_question is None:
                return redirect('/' + BASE_URL + 'aesthetics_labeling/')
            else:
                return redirect('/' + BASE_URL + 'aesthetics_labeling/' + str(next_question.id))
        else:
            form = AuthenticationForm(request)
            current_site = get_current_site(request)
            context = {
                'form': form,
                REDIRECT_FIELD_NAME: redirect_to,
                'site': current_site,
                'site_name': current_site.name,
            }
            return TemplateResponse(request, 'registration/login.html', context)
        
        

def image(request, static_path):
    if static_path[-5:] == '.jpeg' or static_path[-4:] == '.jpg':
        try:
            with open(os.path.join(BASE_DIR, 'aesthetics_labeling/static/', static_path), "rb") as f:
                return HttpResponse(f.read(), content_type="image/jpeg")
        except IOError:
            red = Image.new('RGBA', (1, 1), (255,0,0,0))
            response = HttpResponse(content_type="image/jpeg")
            red.save(response, "JPEG")
            return response
    elif static_path == 'js/comparison.js':
        with open('aesthetics_labeling/static/js/comparison.js', 'r') as f:
            return HttpResponse(f.read(), content_type='text/js')
            
@login_required
def comparison(request, comparison_id):
    # If this is a GET, send back a page
    if request.method == 'GET':
        assignments = ComparisonAssignment.objects.filter(assigned_participant=request.user)
        n_completed = assignments.exclude(label=ComparisonAssignment.UNLABELED).count()
        n_total = assignments.count()

        comparison = Comparison.objects.get(id=comparison_id)
        image_a_path = prep_image(comparison.image_a.image_path)
        image_b_path = prep_image(comparison.image_b.image_path)
        
        # handle missing images
        if image_a_path is None:
            comparison.image_a.broken = True
            remove_broken_image(comparison.image_a)
            comparison.save()
        if image_b_path is None:
            comparison.image_b.broken = True
            remove_broken_image(comparison.image_b)
            comparison.save()
        if image_a_path is None or image_b_path is None:
            next_question = get_next_question(request.user, assignments)
            return redirect('/aesthetics_labeling/' + str(next_question.id))
        
        possible_comparison_assignments = assignments.filter(comparison=comparison)
        if len(possible_comparison_assignments) == 0:
            comparison_assignment = ComparisonAssignment(
                assigned_participant=request.user, 
                comparison=comparison, 
                start_time=datetime.datetime.now()
            )
        else:
            comparison_assignment = possible_comparison_assignments[0]
            comparison_assignment.start_time = datetime.datetime.now()
        comparison_assignment.save()

        #image_a_tag_ids = comparison.image_a.tags.split(',')
        #image_b_tag_ids = comparison.image_b.tags.split(',')
        #image_a_tags = ','.join([TAGS[int(i)] for i in image_a_tag_ids if i != '0'])
        #image_b_tags = ','.join([TAGS[int(i)] for i in image_b_tag_ids if i != '0'])

        # load template
        template = loader.get_template('comparison.html')
        context = {
            'n_completed': n_completed,
            'n_total': n_total,
            'percentage': int(n_completed / n_total * 100),
            'image_a_path': image_b_path if comparison_assignment.reverse else image_a_path,
            'image_b_path': image_a_path if comparison_assignment.reverse else image_b_path,
            'ComparisonAssignment': ComparisonAssignment,
        }
        
        return HttpResponse(template.render(context, request))
    # if this is a POST process the data and redirect to the next page
    elif request.method == 'POST':
        handle_submission(request, comparison_id)
        # figure out if we're headed to the question page
        assignments = ComparisonAssignment.objects.filter(assigned_participant=request.user)
        n_completed = assignments.exclude(label=ComparisonAssignment.UNLABELED).count()
        if n_completed > 50:
            questions_answered = (TextQuestionResponse.objects.filter(user=request.user).count() > 0)
            if not questions_answered:
                return redirect('/' + BASE_URL + 'aesthetics_labeling/text_questions')
        next_question = get_next_question(request.user, assignments)
        if next_question is None:
            return redirect('/' + BASE_URL + 'aesthetics_labeling/')
        else:
            return redirect('/' + BASE_URL + 'aesthetics_labeling/' + str(next_question.id))

@login_required
def text_questions(request):
    if request.method == 'GET':
        template = loader.get_template('text_questions.html')
        return HttpResponse(template.render({}, request))
    elif request.method == 'POST':
        resp = requests.post(
            'https://www.google.com/recaptcha/api/siteverify',
             data = {
                 'secret':'your_secret_key',
                 'response':request.POST['g-recaptcha-response']
             }
            )
        if not str(resp.json()['success']):
            return redirect('/' + BASE_URL + 'aesthetics_labeling/')
        
        # make a db entry
        tqr = TextQuestionResponse(
            question_1=request.POST['q1'],
            question_2=request.POST['q2'],
            question_3=request.POST['q3'],
            question_4=request.POST['q4'],
            user=request.user,
            completion_time = datetime.datetime.now(),
            ip=get_client_ip(request)
        )
        tqr.save()
        
        next_question = get_next_question(request.user)
        if next_question is None:
            return redirect('/' + BASE_URL + 'aesthetics_labeling/')
        else:
            return redirect('/' + BASE_URL + 'aesthetics_labeling/' + str(next_question.id))
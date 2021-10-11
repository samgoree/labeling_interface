import os
import subprocess
import random
import datetime


from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.template import loader
from django.db.models import Q

from aesthetics_labeling.models import Comparison, Participant, ComparisonAssignment
from aesthetics_labeling.constants import TAGS
from labeling_interface.settings import BASE_DIR, BASE_URL

from django.contrib.auth.decorators import login_required
from django.contrib.auth import login

UNIQUE_IMAGES_PER_PERSON = 80

def index(request):
    template = loader.get_template('index.html')
    return HttpResponse(template.render({}, request))

def email_in_use(request):
    template = loader.get_template('email_in_use.html')
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
        remove_broken_image(comparison.image_a)
    if 'image_b_broken' in data:
        comparison.image_b.broken = True
        remove_broken_image(comparison.image_b)
    comparison_assignment.save()

def get_next_question(user):
    queryset = ComparisonAssignment.objects.filter(
        label=ComparisonAssignment.UNLABELED,
        assigned_participant=user,
    ).order_by('id')
    if queryset.count() > 0:
        return queryset[0].comparison
    else:
        return None
    
def create_user(data):
    if 'gender' in data:
        gender = data['gender']
    else:
        gender = ''
    if 'race' in data:
        race = data['race']
    else:
        race = ''
    if 'education' in data:
        education = data['education']
    else:
        education = 0
    if 'language' in data:
        language = data['language']
    else:
        language = ''
    
    
    user = Participant(
        email = data['email'],
        age = int(data['age']),
        gender = gender,
        race = race,
        education = int(education),
        language = language
    )
    user.set_password(data['password'])
    user.save()
    
    assign_images(user)
    
    return user

def assign_images(user, common=True, unique=True):
    # assign some common image pairs
    assignments = []
    if common:
        common_image_pairs = list(Comparison.objects.filter(
            common=True
        ).all())
        random.shuffle(common_image_pairs)
        for pair in common_image_pairs:
            reverse = (random.randint(0,1) == 1)
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

def update_user(user, data):
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
    user.save()
    
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
    
def demographics(request):
    if request.method == 'GET':
        template = loader.get_template('demographics.html')
        return HttpResponse(template.render({}, request))
    elif request.method == 'POST':
        if 'email' not in request.POST:
            # we're editing an existing user's data
            update_user(request.user, request.POST)
            next_question = get_next_question(request.user)
            if next_question is None:
                return redirect('/' + BASE_URL + 'aesthetics_labeling/')
            else:
                return redirect('/' + BASE_URL + 'aesthetics_labeling/' + str(next_question.id))
            
        elif len(Participant.objects.filter(email=request.POST['email'])) > 0:
            return redirect('/' + BASE_URL + 'aesthetics_labeling/email_in_use')
        else:
            # create the new user account
            user = create_user(request.POST)
            # login to the new account
            login(request, user)
            # redirect to the next question
            next_question = get_next_question(user)
            if next_question is None:
                return redirect('/' + BASE_URL + 'aesthetics_labeling/')
            else:
                return redirect('/' + BASE_URL + 'aesthetics_labeling/' + str(next_question.id))

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
            next_question = get_next_question()
            return redirect('/aesthetics_labeling/' + str(next_question.id))
        
        possible_comparison_assignments = ComparisonAssignment.objects.filter(comparison=comparison, assigned_participant=request.user, finish_time__isnull=True)
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
        next_question = get_next_question(request.user)
        if next_question is None:
            return redirect('/' + BASE_URL + 'aesthetics_labeling/')
        else:
            return redirect('/' + BASE_URL + 'aesthetics_labeling/' + str(next_question.id))

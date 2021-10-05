import os
import subprocess
import shutil


from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.template import loader
from django.db.models import Q

from aesthetics_labeling.models import Comparison
from aesthetics_labeling.constants import TAGS
from labeling_interface.settings import BASE_DIR, BASE_URL

from django.contrib.auth.decorators import login_required

# Create your views here.

def index(request):
    template = loader.get_template('index.html')
    return HttpResponse(template.render({}, request))

def prep_image(image_path):
    """
    prepare an image for hosting
    image_path should be the path to an image
    """
    url = '/static/images/'
    new_dir = os.path.join(BASE_DIR, 'aesthetics_labeling/static/images/')
    directory, image_name = os.path.split(image_path)
    if not os.path.exists(image_path): 
        print('Image not found:', image_path)
        return None
    new_path = os.path.join(new_dir, image_name)
    new_url = os.path.join(url, image_name)
    if not os.path.exists(new_dir): os.mkdir(new_dir)
    shutil.copyfile(image_path, new_path)
    return new_url

def remove_broken_image(image):
    Comparison.objects.filter(
              Q(image_a=image)
            | Q(image_b=image)
    ).delete()

def handle_submission(data, comparison_id):
    # TODO
    comparison = Comparison.objects.get(id=comparison_id)
    comparison.label = int(data['comparison_result'])
    if 'image_a_broken' in data:
        comparison.image_a.broken = True
        remove_broken_image(comparison.image_a)
    if 'image_b_broken' in data:
        comparison.image_b.broken = True
        remove_broken_image(comparison.image_b)
    comparison.save()

def get_next_question(user):
    # TODO
    queryset = Comparison.objects.filter(
        label=Comparison.UNLABELED,
        
    ).order_by('id')
    if queryset.count() > 0:
        return queryset[0]
    else:
        return None
    
def create_user(data):
    
    user = Participant(
        email = data['email'],
        age = int(data['age']),
        gender = data['gender'],
        race = data['race'],
        education = int(data['education']),
        language = data['language']
    )
    user.save()
    
    # assign some common image pairs
    common_image_pairs = list(Comparison.objects.filter(
        common=True
    ).all())
    common_image_pairs.shuffle()
    assignments = []
    for pair in common_image_pairs:
        assignment = ComparisonAssignment(
            user,
            pair
        )
        if not pair.assigned: 
            pair.assigned = True
            pair.save()
        assignments.append(assignment)
    
    # assign some other image pairs
    new_image_pairs = Comparison.objects.filter(
        common=False,
        assigned=False
    )
    for pair in new_image_pairs:
        assignment = ComparisonAssignment(
            user,
            pair
        )
        if not pair.assigned: 
            pair.assigned = True
            pair.save()
        assignments.append(assignment)
    ComparisonAssignment.objects.bulk_create(assignments)
    
    return user

def aesthetics_labeling_homepage(request):
    """
    This should check if the user is logged in. If they are, show them a "most recent question" prompt
    If they're not, it should show two links: start and login.
    """
    if request.user.is_authenticated:
        most_recent_question = get_next_question()
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
        user = create_user(request.POST)
        next_question = get_next_question(user)
        if next_question is None:
            return redirect(BASE_URL + 'aesthetics_labeling/')
        else:
            return redirect(BASE_URL + 'aesthetics_labeling/' + str(next_question.id))

@login_required
def comparison(request, comparison_id):
    # TODO Change to user-based system
    # If this is a GET, send back a page
    if request.method == 'GET':
        n_completed = Comparison.objects.exclude(label=Comparison.UNLABELED).count()
        n_total = Comparison.objects.count()

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
            'image_a_path': image_a_path,
            'image_b_path': image_b_path,
            'Comparison': Comparison,
        }
        return HttpResponse(template.render(context, request))
    # if this is a POST process the data and redirect to the next page
    elif request.method == 'POST':
        handle_submission(request.POST, comparison_id)
        next_question = get_next_question()
        if next_question is None:
            return redirect('/aesthetics_labeling/')
        else:
            return redirect('/aesthetics_labeling/' + str(next_question.id))

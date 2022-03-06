from django.core.management.base import BaseCommand, CommandError
from aesthetics_labeling.models import Participant
from aesthetics_labeling.views import assign_images

import os
import tarfile
import datetime
import time

def create_user(email, password):
    """if 'gender' in data:
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
    
    """
    user = Participant(
        email = email,
        ip = ''
        #age = int(data['age']),
        #gender = gender,
        #race = race,
        #education = int(education),
        #language = language
    )
    user.set_password(password)
    user.save()
    
    assign_images(user)
    
    return user

class Command(BaseCommand):
    help = ('Create participants from a txt file with emails and output the email-password list into another file')

    def add_arguments(self, parser):
        parser.add_argument('txt_in', type=str)
        parser.add_argument('csv_out', type=str)
        
    def handle(self, *args, **options):
        txt_path = options['txt_in']
        with open(txt_path) as f:
            emails = f.read().split('\n')
        with open(options['csv_out'], 'w') as f:
            for email in emails:
                if Participant.objects.filter(email=email).count() == 0:
                    password = Participant.objects.make_random_password()
                    f.write(email + ',' + password + '\n')
                    create_user(email, password)
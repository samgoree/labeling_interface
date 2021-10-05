# import_snapshots.py
# creates a Django command to import snapshots into the db from a directory
# the directory should be structured like the russell-1000 data

from django.core.management.base import BaseCommand, CommandError
from aesthetics_labeling.models import Image

import os
import tarfile
import datetime
import time

class Command(BaseCommand):
    help = 'Load the snapshots and websites from a directory. The directory should' + \
           'be structured like the russell-1000 data: each site is a .tar.gz file,' + \
           "with the website's name, and contains snapshots named based on date."

    def add_arguments(self, parser):
        parser.add_argument('directory', type=str)
        parser.add_argument('txt', type=str)

    def handle(self, *args, **options):
        directory = options['directory']
        data_fpath = options['txt']
        if not os.path.exists(directory):
            raise IOError("The provided directory doesn't exist")
        images = []
        for i,line in enumerate(open(data_fpath).readlines()):
            data = line.split(' ')
            assert len(data) == 15
            ind = data[0]
            image_id = data[1]
            aesthetic_rating_distribution = data[2:12]
            semantic_tags = data[12:14]
            challenge_id = data[14]
            print('Processing', ind)
            image_path = os.path.join(directory, image_id + '.jpg')
            images.append(Image(image_path=image_path, tags=','.join(semantic_tags)))
            if i % 10000 == 0: 
                Image.objects.bulk_create(images)
                images = []
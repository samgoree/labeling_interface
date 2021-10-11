# import_snapshots.py
# creates a Django command to import snapshots into the db from a directory
# requires two arguments: directory and txt. txt should be the path to a file
# where the first token on each line is the name of an image
# directory should be the directory where those images are located

from django.core.management.base import BaseCommand, CommandError
from aesthetics_labeling.models import Image

import os
import tarfile
import datetime
import time

class Command(BaseCommand):
    help = 'Load images from a directory based on a metadata text file like the AADB dataset'

    def add_arguments(self, parser):
        parser.add_argument('directory', type=str)

    def handle(self, *args, **options):
        directory = options['directory']
        if not os.path.exists(directory):
            raise IOError("The provided directory doesn't exist")
        images = []
        for i,image_fname in enumerate(os.listdir(directory)):
            image_path = os.path.join(directory, image_fname)
            if os.path.exists(image_path):
                images.append(Image(image_path=image_path))
            else:
                print('Error path does not exist:', image_path)
            if i % 10000 == 0:
                Image.objects.bulk_create(images)
                images = []
        Image.objects.bulk_create(images)
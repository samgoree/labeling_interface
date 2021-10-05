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
    help = 'Load images from a directory based on a metadata text file like the AADB dataset'

    def add_arguments(self, parser):
        parser.add_argument('directory', type=str)
        parser.add_argument('txt', type=str)

    def handle(self, *args, **options):
        directory = options['directory']
        data_fpath = options['txt']
        if not os.path.exists(directory):
            raise IOError("The provided directory doesn't exist")
        images = []
        data_lines = open(data_fpath).readlines()
        print('Loading data file with {} lines.'.format(len(data_lines)))
        for i,line in enumerate(data_lines[1:]):
            data = line.split(' ')
            image_fname = data[0]
            image_path = os.path.join(directory, image_fname)
            if os.path.exists(image_path):
                images.append(Image(image_path=image_path))
            else:
                print('Error path does not exist:', image_path)
            if i % 10000 == 0:
                Image.objects.bulk_create(images)
                images = []
        Image.objects.bulk_create(images)
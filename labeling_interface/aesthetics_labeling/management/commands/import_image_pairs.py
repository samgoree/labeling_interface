# import_snapshots.py
# creates a Django command to import snapshots into the db from a directory
# requires two arguments: directory and txt. txt should be the path to a file
# where the first token on each line is the name of an image
# directory should be the directory where those images are located

from django.core.management.base import BaseCommand, CommandError
from aesthetics_labeling.models import Image, Comparison

import os
import tarfile
import datetime
import time

class Command(BaseCommand):
    help = ('Load image pairs from a CSV file to show to participants. '
            + 'If --common is added, the pairs will be shown to ALL participants '
            + 'otherwise, each pair will be shown to one.')

    def add_arguments(self, parser):
        parser.add_argument('csv', type=str)
        parser.add_argument('--common',
            action='store_true')

    def handle(self, *args, **options):
        csv_path = options['csv']
        common = options['common']
        if not os.path.exists(csv_path):
            raise IOError("The provided file doesn't exist")
        comparisons = []
        data_lines = open(csv_path).readlines()
        print('Loading data file with {} lines.'.format(len(data_lines)))
        print('Common:', common)
        for i,line in enumerate(data_lines[1:]):
            path_1, path_2 = line.split(',')
            im_1 = Image.objects.filter(image_path=path_1.strip())[0]
            im_2 = Image.objects.filter(image_path=path_2.strip())[0]
            comparisons.append(Comparison(image_a=im_1, image_b=im_2, common=common))
        Comparison.objects.bulk_create(comparisons)
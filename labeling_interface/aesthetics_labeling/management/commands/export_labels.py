# export_labels.py
# export labels as a csv file

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Max
from aesthetics_labeling.models import Comparison, Image

import datetime
import os

class Command(BaseCommand):
    help = 'Export all labeled examples'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        if not os.path.exists('exports/'):
            os.mkdir('exports')
        outfile_path = 'exports/labels_' \
            + datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S') + '.csv'
        outfile = open(outfile_path, 'w')
        outfile.write(
            'image_path_1,image_path_2,similarity,label\n'
        )
        for comparison in Comparison.objects.all():
            for im in (
                comparison.image_a,
                comparison.image_b
            ):
                outfile.write(im.image_path + ',')
            outfile.write(str(comparison.label_similarity) + ',' + str(comparison.label) + '\n')
        outfile.close()

        if Image.objects.filter(broken__exact=1).count() > 0:
            broken_images_file_path = 'exports/broken_images_' \
                + datetime.datetime.now().strftime('%Y-%m-%d-%H:%M:%S') + '.csv'
            broken_images_file = open(broken_sites_file_path, 'w')
            broken_images_file.write('path,broken\n')
            for im in Image.objects.filter(broken__exact=1).all():
                broken_sites_file.write(im.image_path + ',' + str(im.broken) + '\n')
            broken_sites_file.close()
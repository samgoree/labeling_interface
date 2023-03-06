# Image Aesthetics Comparison Labeling Interface

this repository contains source code used to study aesthetic preferences for pairs of images. For design details, see [our paper](https://samgoree.github.io/assets/IAQA_and_feminist_aesthetics.pdf)

To deploy a similar interface for your project you will need a collection of images, a newline-separated list of usernames. After running `python manage.py migrate` to set up the database, use the commands `import_images_aadb` and `create_participants` to load. If your data scheme differs significantly from ours, edit the scripts in `labeling_interface/aesthetics_labeling/management/commands/`.

Make sure to set the django security key and setup [google recaptcha](https://www.google.com/recaptcha/about/) to check for botspam.

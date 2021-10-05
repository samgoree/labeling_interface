from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import validate_comma_separated_integer_list
NUM_TAGS = 0

# Create your models here.

class Image(models.Model):
    """
    represents a single image of a website
    """
    image_path = models.CharField(max_length=200)
    #tags = models.CharField(max_length=max(NUM_TAGS, 1), validators=[validate_comma_separated_integer_list])
    broken = models.BooleanField(default=False)

class Comparison(models.Model):
    """
    model a comparison between multiple snapshots
    """
    
    image_a = models.ForeignKey(Image, on_delete=models.CASCADE, related_name='comparison_as_a')
    image_b = models.ForeignKey(Image, on_delete=models.CASCADE, related_name='comparison_as_b')
    common = models.BooleanField(default=False) # common to all participants
    assigned = models.BooleanField(default=False)


class Participant(AbstractUser):
    NO_RESPONSE = 0
    YES = 1
    NO = 2
    
    age_choices = [
        (1, 'Under 18'),
        (2, '18-24 years old'),
        (3, '25-34 years old'),
        (4, '35-44 years old'),
        (5, '45-54 years old'),
        (6, '55 years old or older')
    ]
    edu_choices = [
        (NO_RESPONSE, 'Choose not to specify'),
        (1, 'Less than a high school diploma'),
        (2, 'High school degree or equivalent (e.g. GED)'),
        (3, 'Some college, no degree'),
        (4, 'Associate degree (e.g. AA, AS)'),
        (5, 'Bachelor’s degree (e.g. BA, BS)'),
        (6, 'Master’s degree (e.g. MA, MS, MEd)'),
        (7, 'Professional degree (e.g. MD, DDS, DVM)'),
        (8, 'Doctorate (e.g. PhD, EdD)')
    ]
    
    username = None
    email = models.EmailField('email address', unique=True)
    age = models.IntegerField(choices=age_choices, default=1)
    gender = models.TextField()
    race = models.TextField()
    education = models.IntegerField(choices=edu_choices, default=NO_RESPONSE)
    language = models.TextField()

    USERNAME_FIELD = 'id'
    REQUIRED_FIELDS = []

    
class ComparisonAssignment(models.Model):
    """
    assign a comparison to a participant
    """
    assigned_participant = models.ForeignKey(Participant, on_delete=models.CASCADE)
    comparison = models.ForeignKey(Comparison, on_delete=models.CASCADE)
    
    UNLABELED = 0
    A_BETTER = 1
    B_BETTER = 2
    SIMILAR_GOOD = 3
    SIMILAR_BAD = 4
    DIFFERENT = 5
    choices = [
        (UNLABELED, 'Unlabeled'),
        (A_BETTER, 'I prefer A'),
        (B_BETTER, 'I prefer B'),
        (SIMILAR_GOOD, 'Similarly Good'),
        (SIMILAR_BAD, 'Similarly Bad'),
        (DIFFERENT, 'Too different')
    ]

    label = models.IntegerField(choices=choices, default=UNLABELED)
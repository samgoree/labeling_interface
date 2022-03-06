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
    
    username = None
    email = models.EmailField('email address', unique=True)
    ip = models.TextField()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    def __str__(self):
        return ('Participant, id:'+  str(self.id) 
                + ', email: ' + str(self.email)
        )

class TextQuestionResponse(models.Model):
    """
    free text responses from participants
    """
    question_1 = models.TextField()
    question_2 = models.TextField()
    question_3 = models.TextField()
    question_4 = models.TextField()
    user = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name='text_question_response')
    ip = models.TextField()
    completion_time = models.DateTimeField(null=True)
    
class ComparisonAssignment(models.Model):
    """
    represents an assignment of a comparison to a participant
    """
    
    class Meta:
        indexes = [
            models.Index(fields=['assigned_participant', 'comparison'])
        ]
    
    assigned_participant = models.ForeignKey(Participant, on_delete=models.CASCADE)
    comparison = models.ForeignKey(Comparison, on_delete=models.CASCADE)
    start_time = models.DateTimeField(null=True)
    finish_time = models.DateTimeField(null=True)
    reverse = models.BooleanField(default=False)
    
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
    
    def __str__(self):
        return ('ComparisonAssignment, id:' + str(self.id) 
                + ', assigned participant id: ' + str(self.assigned_participant.id)
                + ', label:' + ComparisonAssignment.choices[self.label][1]
        )
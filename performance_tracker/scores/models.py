from typing import Iterable
from django.db import models
from django.contrib.postgres.fields import ArrayField
from users.models import UserProfiles

class Score(models.Model):
    user_profile = models.ForeignKey(UserProfiles, on_delete=models.CASCADE)

    SHOTS_CHOICES = [
        ('40-Shots', '40 shots'),
        ('60-Shots', '60 shots'),
    ]
    match_type = models.CharField(max_length=10, choices=SHOTS_CHOICES)
    # Storing shot series scores
    # Storing shot scores as a list (10 scores per series)
    series_1 = ArrayField(models.IntegerField(), size=10, blank=True, null=True)
    series_2 = ArrayField(models.IntegerField(), size=10, blank=True, null=True)
    series_3 = ArrayField(models.IntegerField(), size=10, blank=True, null=True)
    series_4 = ArrayField(models.IntegerField(), size=10, blank=True, null=True)
    series_5 = ArrayField(models.IntegerField(), size=10, blank=True, null=True)  # Only for 60-Shots
    series_6 = ArrayField(models.IntegerField(), size=10, blank=True, null=True)  # Only for 60-Shots
    # series total cols
    s1t = models.IntegerField(null=True, editable=False)  # Sum of series_1
    s2t = models.IntegerField(null=True, editable=False)  # Sum of series_2
    s3t = models.IntegerField(null=True, editable=False)  # Sum of series_3
    s4t = models.IntegerField(null=True, editable=False)  # Sum of series_4
    s5t = models.IntegerField(null=True, editable=False)  # Sum of series_5 (only for 60-Shots)
    s6t = models.IntegerField(null=True, editable=False)  # Sum of series_6 (only for 60-Shots)
    total = models.IntegerField(null=True)
    # weekdays and date 
    date = models.DateField(null=True)  # Automatically saves the current date
    day = models.CharField(max_length=10, null=True, editable=False)  # Day of the month
    # functions of this
    average = models.DecimalField(max_digits=5, decimal_places=1,null=True, editable=False)  # Average score of the series
    current_time = models.DateTimeField(auto_now_add=True)  # Timestamp of when the score was recorded
    duration = models.IntegerField(null=True, blank=False)  # Duration in minutes
    notes = models.TextField(blank=True, null=True)  # Optional training notes
    adjustment_made = models.BooleanField(default=False)  # Checkbox to track adjustments
    adjustment_comment = models.TextField(blank=True, null=True)  # Comment on adjustments 
    
    def clean(self):
        """Ensures match type and shot series structure are logically valid."""
        if self.match_type == "40-Shots":
            self.series_5 = None  # Ensure no extra series
            self.series_6 = None

        elif self.match_type == "60-Shots":
            if not self.series_5:
                self.series_5 = []
            if not self.series_6:
                self.series_6 = []


    def save(self, *args, **kwargs):
        #Calculate and update series total, average before saving
        self.s1t = sum(self.series_1) if self.series_1 else 0
        self.s2t = sum(self.series_2) if self.series_2 else 0
        self.s3t = sum(self.series_3) if self.series_3 else 0
        self.s4t = sum(self.series_4) if self.series_4 else 0
        self.s5t = sum(self.series_5) if self.series_5 else 0
        self.s6t = sum(self.series_6) if self.series_6 else 0
        self.total = self.s1t + self.s2t + self.s3t + self.s4t + self.s5t + self.s6t

        series_list = [self.series_1, self.series_2, self.series_3, self.series_4, self.series_5, self.series_6]
        all_shots = [shot for series in series_list if series is not None for shot in series]  # Flatten the list
        if all_shots:
            self.average = sum(all_shots) / len(all_shots)
        else:
            self.average = 0
        if self.date:
            self.day = self.date.strftime("%A")

        if self.duration and self.duration < 0:
            self.duration = 0  # Prevent negative values
        elif self.duration and self.duration > 240:
            self.duration = 240  # Limit to max 4 hours
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user_profile.username} - {self.match_type} ({self.current_time.strftime('%Y-%m-%d')})"
     
class pdfScore(models.Model):
        user_profile = models.ForeignKey(UserProfiles, on_delete=models.CASCADE)

        SHOTS_CHOICES = [
        ('40-Shots', '40 shots'),
        ('60-Shots', '60 shots'),
    ]
        match_type = models.CharField(max_length=10, choices=SHOTS_CHOICES)
        # Storing shot series scores
        # Storing shot scores as a list (10 scores per series)
        series_1 = ArrayField(models.DecimalField(max_digits=5,decimal_places=2), size=10, blank=True, null=True)
        series_2 = ArrayField(models.DecimalField(max_digits=5,decimal_places=2), size=10, blank=True, null=True)
        series_3 = ArrayField(models.DecimalField(max_digits=5,decimal_places=2), size=10, blank=True, null=True)
        series_4 = ArrayField(models.DecimalField(max_digits=5,decimal_places=2), size=10, blank=True, null=True)
        series_5 = ArrayField(models.DecimalField(max_digits=5,decimal_places=2), size=10, blank=True, null=True)  # Only for 60-Shots
        series_6 = ArrayField(models.DecimalField(max_digits=5,decimal_places=2), size=10, blank=True, null=True)  # Only for 60-Shots
        # series total cols
        s1t = models.DecimalField(max_digits=5,decimal_places=2,null=True, editable=False)  # Sum of series_1
        s2t = models.DecimalField(max_digits=5,decimal_places=2,null=True, editable=False)   # Sum of series_2
        s3t = models.DecimalField(max_digits=5,decimal_places=2,null=True, editable=False)   # Sum of series_3
        s4t = models.DecimalField(max_digits=5,decimal_places=2,null=True, editable=False)   # Sum of series_4
        s5t = models.DecimalField(max_digits=5,decimal_places=2,null=True, editable=False)   # Sum of series_5 (only for 60-Shots)
        s6t = models.DecimalField(max_digits=5,decimal_places=2,null=True, editable=False)   # Sum of series_6 (only for 60-Shots)
        total = models.DecimalField(max_digits=5,decimal_places=2,null=True, editable=False) 
        s1mpi= models.DecimalField(max_digits=5,decimal_places=2,null=True, editable=False)  # mpi of first series
        s2mpi= models.DecimalField(max_digits=5,decimal_places=2,null=True, editable=False)  # mpi of second series
        s3mpi= models.DecimalField(max_digits=5,decimal_places=2,null=True, editable=False)  # mpi of third series
        s4mpi= models.DecimalField(max_digits=5,decimal_places=2,null=False, editable=False) # mpi of fourth series
        s5mpi= models.DecimalField(max_digits=5,decimal_places=2,null=False, editable=False) # mpi of fifth series
        s6mpi= models.DecimalField(max_digits=5,decimal_places=2,null=False, editable=False) # mpi of sixth series
        fmpi= models.DecimalField(max_digits=5,decimal_places=2,null=False, editable=False)
        # date and day cols
        date = models.DateField(null=True)  # Automatically saves the current date
        day = models.CharField(max_length=10, null=True, editable=False)  # Day of the month
        # functions of this
        average_shot_score = models.DecimalField(max_digits=5,decimal_places=2,null=True, editable=False)  # Average score of the series
        average_series_score = models.DecimalField(max_digits=5,decimal_places=2,null=True, editable=False)
        current_time = models.DateTimeField(auto_now_add=True)  # Timestamp of when the score was recorded
        duration = models.IntegerField(null=True, blank=False)  # Duration in minutes
        notes = models.TextField(blank=True, null=True)  # Optional training notes
        adjustment_made = models.BooleanField(default=False)  # Checkbox to track adjustments
        adjustment_comment = models.TextField(blank=True, null=True)  # Comment on adjustments 

        def clean(self):
            """Ensures match type and shot series structure are logically valid."""
            if self.match_type == "40-Shots":
                self.series_5 = None  # Ensure no extra series
                self.series_6 = None

            elif self.match_type == "60-Shots":
                if not self.series_5:
                    self.series_5 = []
                if not self.series_6:
                    self.series_6 = []

        def save(self, *args, **kwargs):
            #Calculate and update series total, average before saving
            self.s1t = sum(self.series_1) if self.series_1 else 0
            self.s2t = sum(self.series_2) if self.series_2 else 0
            self.s3t = sum(self.series_3) if self.series_3 else 0
            self.s4t = sum(self.series_4) if self.series_4 else 0
            self.s5t = sum(self.series_5) if self.series_5 else 0
            self.s6t = sum(self.series_6) if self.series_6 else 0
            self.total = self.s1t + self.s2t + self.s3t + self.s4t + self.s5t + self.s6t

            series_list = [self.series_1, self.series_2, self.series_3, self.series_4, self.series_5, self.series_6]
            all_shots = [shot for series in series_list if series is not None for shot in series]  # Flatten the list
            if all_shots:
                self.average_shot_score = sum(all_shots) / len(all_shots)
                self.average_series_score = sum(series_list) / len(series_list)
            else:
                self.average_shot_score = 0
                self.average_series_score = 0
            if self.date:
                self.day = self.date.strftime("%A")

            if self.duration and self.duration < 0:
                self.duration = 0  # Prevent negative values
            elif self.duration and self.duration > 240:
                self.duration = 240  # Limit to max 4 hours
            super().save(*args, **kwargs)

        def __str__(self):
            return f"{self.user.username} - {self.match_type} ({self.current_time.strftime('%Y-%m-%d')})"  

# Create your models here.

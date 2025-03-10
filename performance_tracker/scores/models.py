from typing import Iterable
from django.db import models
from django.contrib.postgres.fields import ArrayField
from users.models import UserProfiles

class pdfScore(models.Model):
        user_profile = models.ForeignKey(UserProfiles, on_delete=models.CASCADE)

        SHOTS_CHOICES = [
        ('40-Shots', '40 shots'),
        ('60-Shots', '60 shots'),
    ]
        match_type = models.CharField(max_length=10, choices=SHOTS_CHOICES)
        # Storing shot series scores
        # Storing shot scores as a list (10 scores per series)
        series_1 = ArrayField(models.DecimalField(max_digits=3,decimal_places=1), size=10, blank=True, null=True)
        series_2 = ArrayField(models.DecimalField(max_digits=3,decimal_places=1), size=10, blank=True, null=True)
        series_3 = ArrayField(models.DecimalField(max_digits=3,decimal_places=1), size=10, blank=True, null=True)
        series_4 = ArrayField(models.DecimalField(max_digits=3,decimal_places=1), size=10, blank=True, null=True)
        series_5 = ArrayField(models.DecimalField(max_digits=3,decimal_places=1), size=10, blank=True, null=True)  # Only for 60-Shots
        series_6 = ArrayField(models.DecimalField(max_digits=3,decimal_places=1), size=10, blank=True, null=True)  # Only for 60-Shots
        # series total cols
        s1t = models.DecimalField(max_digits=5,decimal_places=1,null=True, editable=False)  # Sum of series_1
        s2t = models.DecimalField(max_digits=5,decimal_places=1,null=True, editable=False)   # Sum of series_2
        s3t = models.DecimalField(max_digits=5,decimal_places=1,null=True, editable=False)   # Sum of series_3
        s4t = models.DecimalField(max_digits=5,decimal_places=1,null=True, editable=False)   # Sum of series_4
        s5t = models.DecimalField(max_digits=5,decimal_places=1,null=True, editable=False)   # Sum of series_5 (only for 60-Shots)
        s6t = models.DecimalField(max_digits=5,decimal_places=1,null=True, editable=False)   # Sum of series_6 (only for 60-Shots)
        # total score 
        total = models.DecimalField(max_digits=5,decimal_places=1,null=True, editable=False)
        # inner tens
        inner_tens = models.DecimalField(max_digits=3,decimal_places=0, null=True, editable=False)
        # mpi values
        s1mpi = ArrayField(models.DecimalField(max_digits=4, decimal_places=1), size=2, blank=True, null=True)  # MPI for series 1
        s2mpi = ArrayField(models.DecimalField(max_digits=4, decimal_places=1), size=2, blank=True, null=True)  # MPI for series 2
        s3mpi = ArrayField(models.DecimalField(max_digits=4, decimal_places=1), size=2, blank=True, null=True)  # MPI for series 3
        s4mpi = ArrayField(models.DecimalField(max_digits=4, decimal_places=1), size=2, blank=True, null=True)  # MPI for series 4
        s5mpi = ArrayField(models.DecimalField(max_digits=4, decimal_places=1), size=2, blank=True, null=True)  # MPI for series 5
        s6mpi = ArrayField(models.DecimalField(max_digits=4, decimal_places=1), size=2, blank=True, null=True)  # MPI for series 6
        fmpi = ArrayField(models.DecimalField(max_digits=4, decimal_places=1), size=2, blank=True, null=True)  # First MPI
        gps1 = models.DecimalField(max_digits=4, decimal_places=2, null=True)
        gps2 = models.DecimalField(max_digits=4, decimal_places=2, null=True)
        gps3 = models.DecimalField(max_digits=4, decimal_places=2, null=True)
        gps4 = models.DecimalField(max_digits=4, decimal_places=2, null=True)
        gps5 = models.DecimalField(max_digits=4, decimal_places=2, null=True)
        gps6 = models.DecimalField(max_digits=4, decimal_places=2, null=True)
        gps = models.DecimalField(max_digits=4, decimal_places=2, null=True)
        # date and day cols
        date = models.DateField(null=True)  # Automatically saves the current date
        day = models.CharField(max_length=10, null=True, editable=False)  # Day of the month
        # functions of this
        average_shot_score = models.DecimalField(max_digits=5,decimal_places=1,null=True, editable=False)  # Average score of the series
        average_series_score = models.DecimalField(max_digits=5,decimal_places=1,null=True, editable=False)
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
            """Calculate shot average, series average, and ensure valid duration before saving."""
            # Flatten all shots into a list
            series_list = [self.series_1, self.series_2, self.series_3, self.series_4, self.series_5, self.series_6]
            all_shots = [shot for series in series_list if series is not None for shot in series]  
            # Calculate average shot score
            if all_shots:
                self.average_shot_score = sum(all_shots) / len(all_shots)
            else:
                self.average_shot_score = 0
            # Calculate average series score
            valid_series_totals = [self.s1t, self.s2t, self.s3t, self.s4t, self.s5t, self.s6t]
            valid_series_totals = [total for total in valid_series_totals if total is not None]
            if valid_series_totals:
                self.average_series_score = sum(valid_series_totals) / len(valid_series_totals)
            else:
                self.average_series_score = 0
            # Ensure the date field correctly sets the day
            if self.date:
                self.day = self.date.strftime("%A")
            # Validate and limit duration (must be between 0 and 240 minutes)
            if self.duration is None or self.duration < 0:
                self.duration = 0  
            elif self.duration > 240:
                self.duration = 240  
            super().save(*args, **kwargs)

        def __str__(self):
                return f"{self.user_profile.user.username} - {self.match_type} ({self.current_time.strftime('%Y-%m-%d')})"

class manualscore(models.Model):
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
    total = models.FloatField(null=True)
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


class activities(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(UserProfiles, on_delete=models.CASCADE)
    activity_category = models.CharField(max_length=150)
    activity_name = models.CharField(max_length=150)
    duration = models.CharField(max_length=150)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.activity
# Create your models here.

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.core.exceptions import ValidationError


class UserProfilesManager(BaseUserManager):
    def create_user(self, first_name, last_name, email, username, password=None, role='Shooter'):
        """Create and return a regular user with an email and password."""
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(first_name=first_name, last_name=last_name,email=email, username=username, role=role)
        user.set_password(password)  # Automatically hashes the password
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, first_name='', last_name=''):
        """Create and return a superuser with an email and password."""
        return self.create_user(first_name, last_name, email, username, password, role='Admin')


class UserProfiles(AbstractBaseUser, PermissionsMixin):

    ROLE_CHOICES = [
        ('Shooter', 'Shooter'),
        ('Coach', 'Coach'),
        ('Admin', 'Admin'),
    ]

    id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=128)
    email = models.EmailField(max_length=150, unique=True)
    mobile_number = models.CharField(max_length=15, unique=True, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], null=True, blank=True)
    role = models.CharField(max_length=150, choices = ROLE_CHOICES, default = 'Shooter')
    created_at = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    coaching_specialization = models.CharField(max_length=255, null=True, blank=True)
    years_of_experience = models.PositiveIntegerField(null=True, blank=True)
    coach = models.ForeignKey('self',on_delete=models.SET_NULL,null=True,blank=True,related_name='trained_shooters',default=None)
    affiliated_club = models.CharField(max_length=255, null=True, blank=True)
    

    def clean(self):
        """Ensures role-based constraints."""
        super().clean()

        if self.role == "Admin":
            if self.coach is not None:
                raise ValidationError("Admins cannot have a coach assigned.")
            self.is_staff = True
            self.is_superuser = True
            self.is_active = True  # Admins are always active

        elif self.role == "Coach":
            if self.coach is not None:
                raise ValidationError("Coaches cannot have a coach assigned.")
            self.is_staff = True
            self.is_superuser = False
            self.is_active = True  # Coaches require admin approval

        else:  # Shooter
            if self.coach and self.coach.role != "Coach":
                raise ValidationError("Assigned coach must have the role 'Coach'.")
            self.is_staff = False
            self.is_superuser = False
            self.is_active = True

        # Ensure coaching fields are only filled for coaches
        if self.role != "Coach":
            self.coaching_specialization = None
            self.years_of_experience = None
    def save(self, *args, **kwargs):
        self.clean()
        super(UserProfiles, self).save(*args, **kwargs)

    objects = UserProfilesManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    def __str__(self):
        return self.username
    
class CoachShooterRelation(models.Model):
    coach = models.ForeignKey(UserProfiles, on_delete=models.CASCADE, related_name= "assigned_shooters")
    shooter = models.ForeignKey(UserProfiles, on_delete=models.CASCADE, related_name= "assigned_coach")
    status = models.CharField(max_length=12, choices=[('Pending', 'Pending'), ('Accepted','Accepted')], default='Pending')
    max_shooters = models.PositiveIntegerField(default=10)  # Set default max limit
    accepting_shooters = models.BooleanField(default=True)
    def __str__(self):
        return f"{self.coach.username } - { self.shooter.username } ({self.status})"
    def current_shooters_count(self):
        """Returns the number of shooters currently assigned to this coach."""
        return CoachShooterRelation.objects.filter(coach=self.coach, status="Accepted").count()

    def update_accepting_status(self):
        """Automatically update the accepting_shooters flag based on max limit."""
        self.accepting_shooters = self.current_shooters_count() < self.max_shooters
        self.save()

class DayPlanner(models.Model):
    coach = models.ForeignKey(UserProfiles, on_delete=models.CASCADE, related_name="coach_planner")  # Coach
    shooter = models.ForeignKey(UserProfiles, on_delete=models.CASCADE, related_name="shooter_planner", null=True, blank=True)  # Shooter
    date = models.DateField()
    time = models.TimeField()
    activity = models.CharField(max_length=255)
    shared_with_shooter = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.activity} for {self.shooter.username if self.shooter else 'No Shooter'}"
    
class Event(models.Model):
    COACH = 'coach'
    SHOOTER = 'shooter'
    BOTH = 'both'
    
    VISIBILITY_CHOICES = [
        (COACH, 'Only Coaches'),
        (SHOOTER, 'Only Shooters'),
        (BOTH, 'Both Coaches & Shooters'),
    ]

    title = models.CharField(max_length=255)
    date = models.DateField()
    location = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(UserProfiles, on_delete=models.CASCADE)
    visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES, default=BOTH)
    assigned_shooters = models.ManyToManyField(UserProfiles, related_name='assigned_events', blank=True)

    def __str__(self):
        return self.title

 


# Create your models here.

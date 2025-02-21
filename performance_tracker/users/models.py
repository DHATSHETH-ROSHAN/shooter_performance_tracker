from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


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
    REQUIRED_FIELDS = ['First_Name', 'Last_Name', 'email', 'password']
    id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=128)
    email = models.EmailField(max_length=150, unique=True)
    role = models.CharField(max_length=150, choices = ROLE_CHOICES, default = 'Shooter')
    created_at = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserProfilesManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    def __str__(self):
        return self.username

# Create your models here.

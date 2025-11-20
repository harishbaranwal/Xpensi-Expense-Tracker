from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserProfileForm


# Create your views here.

@login_required
def user_profile(request):
    """
    View to display and edit the user's profile.
    Allows modifying first name, last name, and email for n8n alert configuration.
    """
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('users:profile')
    else:
        form = UserProfileForm(instance=request.user)

    return render(request, 'users/profile.html', {
        'form': form,
        'user': request.user
    })

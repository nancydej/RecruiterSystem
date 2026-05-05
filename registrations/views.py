from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from .models import Event, Registration

#++++++++++++++++++++++++++++
#    REGISTER FOR EVENT
#++++++++++++++++++++++++++++
def register_event(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    user = request.user

    # prevent duplicate registration
    if Registration.objects.filter(recruiter=user, event=event).exists():
        return redirect('my_registrations')

    approved_count = Registration.objects.filter(
        event=event,
        status='Approved'
    ).count()

    status = 'Approved' if approved_count < event.capacity else 'Pending'

    Registration.objects.create(
        recruiter=user,
        event=event,
        status=status
    )

    return redirect('my_registrations')

#++++++++++++++++++++++++++++
#   CANCEL REGISTRATION
#++++++++++++++++++++++++++++

def cancel_registration(request, registration_id):
    reg = get_object_or_404(Registration, pk=registration_id)
    event = reg.event

    days_before = (event.event_date - timezone.now()).days

    if days_before >= 14:
        reg.status = 'Cancelled_Full_Refund'
    elif 7 <= days_before < 14:
        reg.status = 'Cancelled_Partial_Refund'
    else:
        reg.status = 'Cancelled_No_Refund'

    reg.cancel_datetime = timezone.now()
    reg.cancelled_by = "recruiter"
    reg.save()

    return redirect('my_registrations')

#++++++++++++++++++++++++++++
#     VIEW REGISTRATIONS
#++++++++++++++++++++++++++++

def my_registrations(request):
    regs = Registration.objects.filter(recruiter=request.user)
    return render(request, 'registrations/my_registrations.html', {'regs': regs})
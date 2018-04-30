from django.views import generic
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.models import User
from django.views import View
from django.contrib.auth.decorators import login_required

from .models import Event, Comment
from .forms import CommentForm


# Create your views here.


class EventList(LoginRequiredMixin, generic.ListView):
    model = Event
    template_name = 'events/list_of_events.html'
    context_object_name = 'events'

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Event.objects.all()
        else:
            return Event.objects.all()


class EventDisplay(generic.DetailView):
    model = Event
    template_name = 'events/detail.html'
    context_object_name = 'event'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = Comment.objects.all()
        # context['attending'] = self.attendees.all
        return context


class CommentCreate(generic.CreateView):
    model = Comment
    template_name = 'events/detail.html'
    fields = ('comment',)

    def form_valid(self, form):
        new_comment = form.save(commit=False)
        #new_comment.event = self.get_object()
        new_comment.created_by = self.get_object()
        return super().form_valid(form)

    #def post(self, request, *args, **kwargs):
    #    self.object = self.get_object()
      #  return super().post(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('events:event-detail', kwargs={'pk':self.object.pk})


class EventDetail(View):

    def get(self, request, *args, **kwargs):
        view = EventDisplay.as_view()
        return view(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        view = CommentCreate.as_view()
        return view(request, *args, **kwargs)


@login_required()
def event_detail(request, pk):

    event = get_object_or_404(Event, pk=pk)

    comments = event.comments.all()

    attending = event.attendees.all()

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            new_comment = form.save(commit=False)
            new_comment.event = event
            new_comment.created_by = request.user
            new_comment.save()
            messages.success(request, 'Comment was created successfully')
            return redirect('events:event-detail', pk=event.pk)
    else:
        form = CommentForm()

    return render(request, 'events/detail.html', {'event': event, 'comments': comments,
                                                  'form': form, 'attending': attending,
                                                  })


class EventFormMixin(object):
    def form_valid(self, form):
        form.instance.creator = self.request.user
        return super().form_valid(form)


class EventCreate(LoginRequiredMixin, SuccessMessageMixin, EventFormMixin, generic.CreateView):
    model = Event
    template_name = 'events/create_form.html'
    fields = ('category', 'name', 'details', 'venue', 'time', 'date')
    context_object_name = 'event'
    success_message = "%(name)s was created successfully"


class EventUpdate(LoginRequiredMixin, SuccessMessageMixin, EventFormMixin, generic.UpdateView):
    model = Event
    template_name = 'events/update_form.html'
    template_name_suffix = '_update_form'
    fields = ('category', 'name', 'details', 'venue', 'time', 'date', 'creator')
    success_message = "%(name)s was updated successfully"


class EventDelete(LoginRequiredMixin, SuccessMessageMixin, generic.DeleteView):
    model = Event
    template_name = 'events/delete.html'
    success_url = reverse_lazy('events:event-list')
    context_object_name = 'event'
    success_message = "%(name)s was deleted successfully"


@login_required()
def attend_event(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    attendee = User.objects.get(username=request.user)

    if Event.objects.filter(pk=event_id, attendees=attendee).exists():
        messages.success(request, "You are already attending before")
    else:
        event.attendees.add(attendee)
        messages.success(request, 'You are now attending {0}'.format(event.name))
    return redirect('events:event-detail', pk=event.pk)
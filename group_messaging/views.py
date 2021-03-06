"""semi-views for the `group_messaging` application
These are not really views - rather context generator
functions, to be used separately, when needed.

For example, some other application can call these
in order to render messages within the page.

Notice that :mod:`urls` module decorates all these functions
and turns them into complete views
"""
from coffin.template.loader import get_template
from django.forms import IntegerField
from django.http import HttpResponse
from django.http import HttpResponseNotAllowed
from django.http import HttpResponseForbidden
from django.utils import simplejson
from group_messaging.models import Message
from group_messaging.models import SenderList
from group_messaging.models import get_personal_group_by_user_id

class InboxView(object):
    """custom class-based view
    to be used for pjax use and for generation
    of content in the traditional way, where
    the only the :method:`get_context` would be used.
    """
    template_name = None #used only for the "GET" method
    http_method_names = ('GET', 'POST')

    def render_to_response(self, context, template_name=None):
        """like a django's shortcut, except will use
        template_name from self, if `template_name` is not given.
        Also, response is packaged as json with an html fragment
        for the pjax consumption
        """
        if template_name is None:
            template_name = self.template_name
        template = get_template(self.template_name)
        html = template.render(context)
        json = simplejson.dumps({'html': html})
        return HttpResponse(json, mimetype='application/json')
            

    def get(self, request, *args, **kwargs):
        """view function for the "GET" method"""
        context = self.get_context(request, *args, **kwargs)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        """view function for the "POST" method"""
        pass

    def dispatch(self, request, *args, **kwargs):
        """checks that the current request method is allowed
        and calls the corresponding view function"""
        if request.method not in self.http_method_names:
            return HttpResponseNotAllowed()
        view_func = getattr(self, request.method.lower())
        return view_func(request, *args, **kwargs)

    def get_context(self, request, *args, **kwargs):
        """Returns the context dictionary for the "get"
        method only"""
        return {}

    def as_view(self):
        """returns the view function - for the urls.py"""
        def view_function(request, *args, **kwargs):
            """the actual view function"""
            if request.user.is_authenticated() and request.is_ajax():
                view_method = getattr(self, request.method.lower())
                return view_method(request, *args, **kwargs)
            else:
                return HttpResponseForbidden()

        return view_function


class NewThread(InboxView):
    """view for creation of new thread"""
    template_name = 'create_thread.html'# contains new thread form
    http_method_list = ('GET', 'POST')

    def post(self, request):
        """creates a new thread on behalf of the user
        response is blank, because on the client side we just 
        need to go back to the thread listing view whose
        content should be cached in the client'
        """
        username = IntegerField().clean(request.POST['to_username'])
        user = User.objects.get(username=username)
        recipient = get_personal_group_by_user_id(user.id)
        Message.objects.create_thread(
                        sender=request.user,
                        recipients=[recipient],
                        text=request.POST['text']
                    )
        return HttpResponse('', mimetype='application/json')


class NewResponse(InboxView):
    """view to create a new response"""
    http_method_list = ('POST',)

    def post(self, request):
        parent_id = IntegerField().clean(request.POST['parent_id'])
        parent = Message.objects.get(id=parent_id)
        message = Message.objects.create_response(
                                        sender=request.user,
                                        text=request.POST['text'],
                                        parent=parent
                                    )
        return self.render_to_response(
            {'message': message}, template_name='stored_message.htmtl'
        )

class ThreadsList(InboxView):
    """shows list of threads for a given user"""  
    template_name = 'threads_list.html'
    http_method_list = ('GET',)

    def get_context(self, request):
        """returns thread list data"""
        threads = Message.objects.get_threads_for_user(request.user)
        threads = threads.values('id', 'headline')
        return {'threads': threads}


class SendersList(InboxView):
    """shows list of senders for a user"""
    template_name = 'senders_list.html'
    http_method_names = ('GET',)

    def get_context(self, request):
        """get data about senders for the user"""
        senders = SenderList.objects.get_senders_for_user(request.user)
        senders = senders.values('id', 'username')
        return {'senders': senders}


class ThreadDetails(InboxView):
    """shows entire thread in the unfolded form"""
    template_name = 'thread_details.html'
    http_method_names = ('GET',)

    def get_context(self, request):
        """shows individual thread"""
        thread_id = IntegerField().clean(request.GET['thread_id'])
        #todo: assert that current thread is the root
        messages = Message.objects.filter(root__id=thread_id)
        messages = messages.values('html')
        return {'messages': messages}

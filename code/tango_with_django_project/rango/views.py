from django.shortcuts import render
from django.shortcuts import redirect
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from rango.models import Category, Page, UserProfile
from rango.forms import CategoryForm, PageForm, UserProfileForm
from datetime import datetime
from rango.webhose_search import run_query
from registration.backends.simple.views import RegistrationView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import authenticate, login
from django.views.generic import DetailView, ListView, FormView
from django.shortcuts import get_object_or_404

# Create your views here.
def get_server_side_cookie(request, cookie, default_val=None):
    val = request.session.get(cookie)
    if not val:
        val = default_val
    return val

def visitor_cookie_handler(request):
    # Get the number of visits to the site.
    # We use the COOKIES.get() function to obtain the visits cookie.
    # If the cookie exists, the value returned is casted to an integer.
    # If the cookie doesn't exist, then the default value of 1 is used.
    visits = int(get_server_side_cookie(request, 'visits', '1'))

    last_visit_cookie = get_server_side_cookie(request, 'last_visit', str(datetime.now()) )

    last_visit_time = datetime.strptime(last_visit_cookie[:-7], "%Y-%m-%d %H:%M:%S")
    #last_visit_time = datetime.now()
    # If it's been more than a day since the last visit...
    if (datetime.now() - last_visit_time).seconds > 0:
        visits = visits + 1
        #update the last visit cookie now that we have updated the count
        request.session['last_visit'] = str(datetime.now())
    else:
        visits = 1
        # set the last visit cookie 
        request.session['last_visit'] = last_visit_cookie
    # update/set the visits cookie
    request.session['visits'] = visits




def index(request):
    #context_dict = {'boldmessage': "Crunchie, creamy, cookie, candy, cupcake!"}

    request.session.set_test_cookie()

    category_list = Category.objects.order_by('-likes')[:5]

    page_list = Page.objects.order_by('-views')[:5]

    context_dict = {'categories': category_list, 'pages': page_list}

    visitor_cookie_handler(request)

    context_dict['visits'] = request.session['visits']

    print(request.session['visits'])

    response = render(request, 'rango/index.html', context=context_dict)
    
    return response
    

def about(request):
    if request.session.test_cookie_worked():
        print("TEST COOKIE WORKED!")
        request.session.delete_test_cookie()
    # To complete the exercise in chapter 4, we need to remove the following line
    # return HttpResponse("Rango says here is the about page. <a href='/rango/'>View index page</a>")

    # and replace it with a pointer to ther about.html template using the render method
    return render(request, 'rango/about.html',{})

class show_category(DetailView):
    template_name='rango/category.html'

    def get(self,request,*args,**kwargs):
        try:
            self.category=Category.objects.get(slug=self.kwargs['category_name_slug'])
            self.pages = Page.objects.filter(category=self.category)
        except category.DoesNotExist:
            self.category = None
            self.pages = None
        context_dict={
            'category':self.category,
            'pages':self.pages,
            'query':self.query
        }
        return render(request,self.template_name,context_dict)


    def post(self,request,*args,**kwargs):
        self.query = request.POST['query'].strip()
        result_list=[]
        if self.query:
            # Run our Webhose function to get the results list!
            result_list = run_query(self.query)
        context_dict={
            'category':self.category,
            'pages':self.pages,
            'query':self.query,
            'result_list':result_list
        }
        return render(request,self.template_name,context_dict)


class add_category(FormView):
    template_name = 'rango/add_category.html'
    form_class = CategoryForm
    success_url = '/'

    def form_valid(self,form):
        # if form is valid save it to database
        form.save(commit=True)
        return super(add_category,self).form_valid(form)


class add_page(DetailView):
    template_name = 'rango/add_page.html'

    def get_object(self):
        # helper function to get object
        obj = get_object_or_404(Category,
                                slug=self.kwargs['category_name_slug'])
        return obj

    def get(self,request,*args,**kwargs):
        context_dict = {'form':PageForm(),'category':self.get_object()}
        return render(request,self.template_name,context_dict)

    def post(self,request,*args,**kwargs):
        form = PageForm(request.POST)
        if form.is_valid():
            if self.get_object():
                page = form.save(commit=False)
                page.category = self.get_object()
                page.views = 0
                page.save()
            return redirect('show_category',kwargs['category_name_slug'])
        else:
            return redirect('add_page',kwargs['category_name_slug'])

def search(request):
    result_list = []
    if request.method == 'POST':
        query = request.POST['query'].strip()
        if query:
             # Run our Webhose function to get the results list!
             result_list = run_query(query)
    return render(request, 'rango/search.html', {'result_list': result_list})


def register(request):
    registered = False
    if request.method == 'POST':
        user_form = UserForm(data=request.POST)
        profile_form = UserProfileForm(data=request.POST)

        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()
            user.set_password(user.password)
            user.save()

            profile = profile_form.save(commit=False)
            profile.user = user
            if 'picture' in request.FILES:
                profile.picture = request.FILES['picture']
                profile.save()
                registered = True
            else:
                print(user_form.errors, profile_form.errors)
    else:
## ON the PDF of tangowithdjango19,the e.g is like that:
  #          else:
  #              print(user_form.errors, profile_form.errors)
  #  	else:
		# user_form = UserForm()
  #      	profile_form = UserProfileForm()
    	
        user_form = UserForm()
        profile_form = UserProfileForm()

    return render(request,
                  'rango/register.html',
                  {'user_form': user_form,
                   'profile_form': profile_form,
                   'registered': registered
                  })

def track_url(request):
    page_id = None
    if request.method == 'GET':
        if 'page_id' in request.GET:
            page_id = request.GET['page_id']
    if page_id:
        try:
            page = Page.objects.get(id=page_id)
            page.views = page.views + 1
            page.save()
            return redirect(page.url)
        except:
            return HttpResponse("Page id {0} not found".format(page_id))
    print("No page_id in get string")
    return redirect(reverse('index'))

@login_required
def register_profile(request):
    form = UserProfileForm()
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES)
        if form.is_valid():
            user_profile = form.save(commit=False)
            user_profile.user = request.user
            user_profile.save()
            
            return redirect('index')
        else:
            print(form.errors)

    context_dict = {'form':form}
    
    return render(request, 'rango/profile_registration.html', context_dict)

class RangoRegistrationView(RegistrationView):
    def get_success_url(self, user):
        return reverse('register_profile')

@login_required
def profile(request, username):
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return redirect('index')
    
    userprofile = UserProfile.objects.get_or_create(user=user)[0]
    form = UserProfileForm({'website': userprofile.website, 'picture': userprofile.picture})
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=userprofile)
        if form.is_valid():
            form.save(commit=True)
            return redirect('profile', user.username)
        else:
            print(form.errors)
    
    return render(request, 'rango/profile.html', {'userprofile': userprofile, 'selecteduser': user, 'form': form})

@login_required
def list_profiles(request):
#    user_list = User.objects.all()
    userprofile_list = UserProfile.objects.all()
    return render(request, 'rango/list_profiles.html', { 'userprofile_list' : userprofile_list})

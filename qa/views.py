from django.http import HttpResponse
from django.shortcuts import render
from django.template import RequestContext, loader
from django.shortcuts import get_object_or_404, render, render_to_response
from django.contrib.auth import authenticate, login
from django.http import HttpResponseRedirect, HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from qa.models import *
import datetime
from qa.forms import UserForm, UserProfileForm

from django.core.mail import send_mail

def search(request):
    if request.method == 'POST':
        word = request.POST['word']
        latest_question_list = Question.objects.filter(question_text__contains=word)
        paginator = Paginator(latest_question_list, 10)
        page = request.GET.get('page')
        try:
            questions = paginator.page(page)
        except PageNotAnInteger:
        # If page is not an integer, deliver first page.
            questions = paginator.page(1)
        except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
            questions = paginator.page(paginator.num_pages)

        latest_noans_list = Question.objects.order_by('-pub_date').filter(tags__slug__contains=word,answer__isnull=True)[:10]
        top_questions = Question.objects.order_by('-reward').filter(tags__slug__contains=word,answer__isnull=True,reward__gte=1)[:10]
        count = Question.objects.count
        count_a = Answer.objects.count

        template = loader.get_template('qa/index.html')
        context = RequestContext(request, {
        'questions': questions,
        'totalcount': count,
        'anscount': count_a,
        'noans': latest_noans_list,
        'reward': top_questions,
        })
    return HttpResponse(template.render(context))

def tag(request, tag):
    word = tag
    latest_question_list = Question.objects.filter(tags__slug__contains=word)
    paginator = Paginator(latest_question_list, 10)
    page = request.GET.get('page')
    try:
        questions = paginator.page(page)
    except PageNotAnInteger:
    # If page is not an integer, deliver first page.
        questions = paginator.page(1)
    except EmptyPage:
    # If page is out of range (e.g. 9999), deliver last page of results.
        questions = paginator.page(paginator.num_pages)

    latest_noans_list = Question.objects.order_by('-pub_date').filter(tags__slug__contains=word,answer__isnull=True)[:10]
    top_questions = Question.objects.order_by('-reward').filter(tags__slug__contains=word,answer__isnull=True,reward__gte=1)[:10]
    count = Question.objects.count
    count_a = Answer.objects.count

    template = 'qa/index.html'
    context = request, {
    'questions': questions,
    'totalcount': count,
    'anscount': count_a,
    'noans': latest_noans_list,
    'reward': top_questions,
    }
    return render(request, template,context)
  
def index(request):
    latest_question_list = Question.objects.order_by('-pub_date')
    latest_noans_list = Question.objects.order_by('-pub_date').filter(answer__isnull=True)[:10]
    top_questions = Question.objects.order_by('-reward').filter(answer__isnull=True,reward__gte=1)[:10]

    count = Question.objects.count
    count_a = Answer.objects.count

    paginator = Paginator(latest_question_list, 10)
    page = request.GET.get('page')
    try:
        questions = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        questions = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        questions = paginator.page(paginator.num_pages)

    template = 'qa/index.html'
    context = {
        'questions': questions,
        'totalcount': count,
        'anscount': count_a,
        'noans': latest_noans_list,
        'reward': top_questions,
    }
    return render(request, 'qa/index.html',context)


def profile(request, user_id):
    user_ob = User.objects.get(id=user_id)
    user = UserProfile.objects.get(user=user_ob)
    return render(request, 'qa/profile.html', {'user': user})

def add(request):
    template = loader.get_template('qa/add.html')
    context = RequestContext(request)

    if request.user.is_anonymous():
        return HttpResponseRedirect("/login/")

    if request.method == 'POST':
        question_text = request.POST['question']
        tags_text = request.POST['tags']
        user_id = request.POST['user']
        user_ob = User.objects.get(id=user_id)
        user = UserProfile.objects.get(user=user_ob)

        if question_text.strip() == '':
            return render(request, 'qa/add.html', {'message': 'Empty'})

        pub_date = datetime.datetime.now()
        q = Question()
        q.question_text = question_text
        q.pub_date = pub_date
        q.user_data = user
        q.save()

        tags = tags_text.split(',')
        for tag in tags:
            try:
                t = Tag.objects.get(slug=tag)
                q.tags.add(t)
            except Tag.DoesNotExist:
                t=Tag()
                t.slug = tag
                t.save()
                q.tags.add(t)

        #send_mail('QA: Your Question has been Posted.', 'Thank you for posting the question, '+question_text+'. We will notify you once someone posts an answer.', 'admin@test.com', [request.user.email], fail_silently=False)

        return HttpResponseRedirect('/')
    return HttpResponse(template.render(context))

def comment(request, answer_id):

    if request.user.is_anonymous():
        return HttpResponseRedirect("/login/")

    if request.method == 'POST':
        comment_text = request.POST['comment']
        user_id = request.POST['user']
        user_ob = User.objects.get(id=user_id)
        user = UserProfile.objects.get(user=user_ob)
        user.points += 1
        user.save()

        if comment_text.strip() == '':
            return render(request, 'qa/comment.html', {'answer_id': answer_id, 'message': 'Empty'})

        pub_date = datetime.datetime.now()
        a = Answer.objects.get(pk=answer_id)
        q_id = a.question_id
        c = Comment()
        c.answer = a
        c.comment_text = comment_text
        c.pub_date = pub_date
        c.user_data = user
        c.save()

        try:
            question = Question.objects.get(pk=q_id)
            question.views += 1
            question.save()
            answer_list = question.answer_set.order_by('-votes')

            paginator = Paginator(answer_list, 10)
            page = request.GET.get('page')
            try:
                answers = paginator.page(page)
            except PageNotAnInteger:
                # If page is not an integer, deliver first page.
                answers = paginator.page(1)
            except EmptyPage:
                # If page is out of range (e.g. 9999), deliver last page of results.
                answers = paginator.page(paginator.num_pages)

        except Question.DoesNotExist:
            raise Http404("Question does not exist")
        return render(request, 'qa/detail.html', {'answers': answers, 'question': question}, )

    template = loader.get_template('qa/comment.html')
    context = RequestContext(request, {'answer_id': answer_id})
    return HttpResponse(template.render(context))

def detail(request, question_id):
    try:
        question = Question.objects.get(pk=question_id)
        question.views += 1
        question.save()
        answer_list = question.answer_set.order_by('-votes')

        paginator = Paginator(answer_list, 10)
        page = request.GET.get('page')
        try:
            answers = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            answers = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            answers = paginator.page(paginator.num_pages)

    except Question.DoesNotExist:
        raise Http404("Question does not exist")
    return render(request, 'qa/detail.html', {'answers': answers, 'question': question}, )

def answer(request, question_id):
    if request.user.is_anonymous():
        return HttpResponseRedirect("/login/")

    try:
        question = Question.objects.get(pk=question_id)
    except Question.DoesNotExist:
        raise Http404("Question does not exist")
    return render(request, 'qa/answer.html', {'question': question})

def add_answer(request):
    if request.method == 'POST':
        answer_text = request.POST['answer']
        question_id = request.POST['question']
        user_id = request.POST['user']

        question = Question.objects.get(pk=question_id)
        user_ob = User.objects.get(id=user_id)
        user = UserProfile.objects.get(user=user_ob)
        user.points += 5
        user.save()

        if answer_text.strip() == '':
            return render(request, 'qa/answer.html', {'question': question, 'message': 'Empty'})

        a = Answer()
        pub_date = datetime.datetime.now()
        a.answer_text = answer_text
        a.question = question
        a.user_data = user
        a.pub_date = pub_date
        a.save()

        answer_list = question.answer_set.order_by('-votes')

        paginator = Paginator(answer_list, 10)
        page = request.GET.get('page')
        try:
            answers = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            answers = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            answers = paginator.page(paginator.num_pages)

        return render(request, 'qa/detail.html', {'question': question, 'answers': answers})

    return render(request, 'qa/detail.html', {'question': question})

def vote(request, user_id, answer_id, question_id, op_code):

    user_ob = User.objects.get(id=user_id)
    user = UserProfile.objects.get(user=user_ob)
    answer = Answer.objects.get(pk=answer_id)
    question = Question.objects.get(pk=question_id)

    answer_list = question.answer_set.order_by('-votes')

    paginator = Paginator(answer_list, 10)
    page = request.GET.get('page')
    try:
        answers = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        answers = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        answers = paginator.page(paginator.num_pages)

    if Answer.objects.filter(id=answer_id, user_data=user).exists():
        return render(request, 'qa/detail.html', {'question': question, 'answers': answers, 'message':"You cannot vote on your answer!"})

    if Voter.objects.filter(answer_id=answer_id, user=user).exists():
        return render(request, 'qa/detail.html', {'question': question, 'answers': answers, 'message':"You've already cast vote on this answer!"})

    if op_code == '0':
        answer.votes += 1
        u = answer.user_data
        u.points += 10
        u.points += question.reward
        u.save()
    if op_code == '1':
        answer.votes -= 1
        u = answer.user_data
        u.points -= 10
        u.save()
    answer.save()

    answer_list = question.answer_set.order_by('-votes')

    paginator = Paginator(answer_list, 10)
    page = request.GET.get('page')
    try:
        answers = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        answers = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        answers = paginator.page(paginator.num_pages)

    v = Voter()
    v.user = user
    v.answer = answer
    v.save()

    return render(request, 'qa/detail.html', {'question': question, 'answers': answers})

def thumb(request, user_id, question_id, op_code):

    user_ob = User.objects.get(id=user_id)
    user = UserProfile.objects.get(user=user_ob)
    question = Question.objects.get(pk=question_id)

    answer_list = question.answer_set.order_by('-votes')

    paginator = Paginator(answer_list, 10)
    page = request.GET.get('page')
    try:
        answers = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        answers = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        answers = paginator.page(paginator.num_pages)

    if QVoter.objects.filter(question_id=question_id, user=user).exists():
        return render(request, 'qa/detail.html', {'question': question, 'answers': answers, 'message':"You've already cast vote on this question!"})

    if op_code == '0':
        question.reward += 5
        u = question.user_data
        u.points += 5
        u.save()
    if op_code == '1':
        question.reward -= 5
        u = question.user_data
        u.points -= 5
        u.save()
    question.save()

    answer_list = question.answer_set.order_by('-votes')

    paginator = Paginator(answer_list, 10)
    page = request.GET.get('page')
    try:
        answers = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        answers = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        answers = paginator.page(paginator.num_pages)

    v = QVoter()
    v.user = user
    v.question = question
    v.save()

    return render(request, 'qa/detail.html', {'question': question, 'answers': answers})

def register(request):
    context = RequestContext(request)

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
            print (user_form.errors, profile_form.errors)

    else:
        user_form = UserForm()
        profile_form = UserProfileForm()

    return render(request,
            'qa/register.html',
            {'user_form': user_form, 'profile_form': profile_form, 'registered': registered})

def user_login(request):
    
    context = RequestContext(request)

    
    if request.method == 'POST':
        
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(username=username, password=password)

        if user:
            if user.is_active:
                login(request, user)
                return HttpResponseRedirect('/')
            else:
                return HttpResponse("Your account is disabled.")
        else:
            # Bad login details were provided. So we can't log the user in.
           # print "Invalid login details: {0}, {1}".format(username, password)
            return HttpResponse("Invalid login details supplied.")

    else:
        return render(request, 'qa/login.html')

from django.contrib.auth import logout

def user_logout(request):
    logout(request)
    return HttpResponseRedirect('/')
    
    
    

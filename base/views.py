from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Q
from zmq import Message
from .models import Room, Topic, Message
from .forms import RoomForm

# rooms = [
#     {"id": 1, "name": "Let's learn python!"},
#     {"id": 2, "name": "Design with me"},
#     {"id": 3, "name": "Frontend developers"},
# ]

def loginPage(request):
    page = 'login'
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        username = request.POST.get('username').lower()
        password = request.POST.get('password')
        try:
            user = User.objects.get(username = username)
        except:
            messages.error(request, "Wrong username or password")
        
        user = authenticate(request, username = username, password = password)

        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, "Wrong username or password")
        
    context = {"page": page}
    return render(request, 'base/login_register.html', context)

def registerPage(request):
    form = UserCreationForm()
    page = 'register'
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False) # bu saqlaydi lekin shu yerda muzlatib qoyadi
            user.username = user.username.lower()
            user.save() # bu haqiqiy saqlash
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, "An error occured during registration!")
    context = {'page': page, 'form': form}
    return render(request, 'base/login_register.html', context)

def logoutUser(request):
    logout(request)
    return redirect('home')

def home(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    rooms = Room.objects.filter(
        Q(topic__name__icontains=q) | # & qilinsa va degani boladi
        Q(name__icontains=q) |
        Q(description__icontains=q)
    ) # agarda i olib tashlansa casesensitive bolib qoladi
    room_messages = Message.objects.filter(Q(room__topic__name__icontains=q))
    print(room_messages)
    topics = Topic.objects.all()
    context = {'rooms': rooms, "topics": topics, "count_room": len(rooms),
    'room_messages': room_messages}
    return render(request, 'base/home.html', context)

def room(request, pk):
    room = Room.objects.get(id=pk) # get faqatgina bitta elementni olishni bildiradi
    room_messages = room.message_set.all() # bu roomga boglangan messagelarni olib berishga hizmat qiladi
    
    participants = room.participants.all() 
    if request.method == 'POST':
        message = Message.objects.create(
            user=request.user,
            room=room,
            body=request.POST.get('body')
        )
        room.participants.add(request.user)
        return redirect('room', pk=room.id)
    context = {"room": room, 'room_messages': room_messages,
    "participants": participants
    }
    return render(request, 'base/room.html', context)


def userProfile(request, pk):
    user = User.objects.get(id=pk)
    rooms = user.room_set.all()
    room_message = user.message_set.all()
    topics = Topic.objects.all()
    context = {'user': user, 'rooms': rooms, 'room_message': room_message, 
    'topics': topics
    }
    return render(request, 'base/profile.html', context)

@login_required(login_url='login')
def createRoom(request):
    form = RoomForm()

    # if request.user != room.host:
    #     return HttpResponse("You are not allowed here!")

    if request.method == "POST":
        form = RoomForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("home")
    context = {"form": form}
    return render(request, 'base/room_form.html', context)

@login_required(login_url='login')
def updateRoom(request, pk):
    room = Room.objects.get(id=pk)
    form = RoomForm(instance=room)

    if request.user != room.host:
        return HttpResponse("You are not allowed here!")
    
    if request.method == "POST":
        form = RoomForm(request.POST, instance=room)
        if form.is_valid():
            room = form.save(freeze=False)
            room.host = request.user
            room.save()
            return redirect('home')

    context = {"form": form}
    return render(request, 'base/room_form.html', context)


@login_required(login_url='login')
def deleteRoom(request, pk):
    room = Room.objects.get(id=pk)
    context = {"obj": room}

    if request.user != room.host:
        return HttpResponse("You are not allowed here!")

    if request.method == "POST":
        room.delete()
        return redirect('home')
    return render(request, 'base/delete.html', context)


@login_required(login_url='login')
def deleteMessage(request, pk):
    message = Message.objects.get(id=pk)
    context = {"obj": message}

    if request.user != message.user:
        return HttpResponse("You are not allowed here!")

    if request.method == "POST":
        message.delete()
        return redirect('home')
    return render(request, 'base/delete.html', context)

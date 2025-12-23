from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.core.mail import EmailMessage
from django.urls import reverse
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str

from .forms import RegisterForm, LoginForm
from .tokens import account_activation_token
from .models import CustomUser


def register_view(request):
    form = RegisterForm()
    
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # usuario só ativa apos confirmar email 
            user.save()
            
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = account_activation_token.make_token(user)
            link = request.build_absolute_uri(
                reverse('activate', kwargs={'uidb64': uid, 'token': token})
            )
            email = EmailMessage(
                'Ative sua conta',
                f'Olá!\n\nClique no link abaixo para ativar sua conta:\n\n{link}\n\nSe você não criou esta conta, ignore este email.',
                to=[user.email]
            )
            email.send()
            
            messages.success(request, 'Conta criada com sucesso! Verifique seu email para ativar sua conta.')
            return redirect('login')
    else:
        form = RegisterForm()
            
    return render(request, 'accounts/register.html', {'form': form})            

def activate_view(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = CustomUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        user = None

    if user and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, 'Sua conta foi ativada com sucesso!')
        return redirect('activation_success') # redireciona para a pagina de login após ativação
    else:
        return HttpResponse('Link inválido')

def activation_success(request):
    return render(request, 'accounts/activation_succss.html')

def login_view(request):
    form = LoginForm()
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(request, email=email, password=password)

            if user is None:
                form.add_error(None, 'Email ou senha inválidos.')
            elif not user.is_active:
                form.add_error(None, 'Conta inativa. Verifique seu email para ativar sua conta.')
            else:                
                login(request, user)
                return redirect('home')

    return render(request, 'accounts/login.html', {'form': form})

def resend_activation_email(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            messages.error(request, 'Email não encontrado.')
            return redirect('resend_activation_email')
        
        if user.is_active:
            messages.info(request, 'Sua conta já está ativa. Faça login.')
            return redirect('login')
        
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = account_activation_token.make_token(user)
        
        link = request.build_absolute_uri(
            reverse('activate', kwargs={'uidb64': uid, 'token': token})
        )
        
        email = EmailMessage(
            'Reenvio do link de ativação',
            f'Olá!\n\nClique no link abaixo para ativar sua conta:\n\n{link}\n\nSe você não criou esta conta, ignore este email.',
            to=[user.email]
        )
        email.send()
        
        messages.success(request, 'Link de ativação reenviado! Verifique seu email.')
        return redirect('login')
    
    return render(request, 'accounts/resend_activation_email.html')

@login_required
def home_view(request):
    return render(request, 'accounts/home.html')
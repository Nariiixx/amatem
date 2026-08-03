from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout, get_user_model
from django.contrib.auth.hashers import make_password
from django.core.mail import EmailMessage
from django.urls import reverse
from django.contrib.auth.decorators import login_required

from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str

from .forms import RegisterForm, LoginForm, ProfileForm, ResetPasswordForm
from .tokens import account_activation_token
from .models import CustomUser, PasswordResetToken, Profile
from .utils import  create_reset_token

# autenticação 

User = get_user_model()
def create_activate_link(request, user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = account_activation_token.make_token(user)
    
    return request.build_absolute_uri(
        reverse(
            'activate',
            kwargs={
                'uidb64': uid,
                'token': token
            }
        )
    )

def send_activation_email(request, user):
    link = create_activate_link(request, user)
    
    # TODO: implementar o utils.py enviar email
    email_message = EmailMessage(
        "ative sua conta",
        f"Olá!\n\nClique no link abaixo para ativar sua conta:\n\n{link}\n\nSe você não criou esta conta, ignore este email.",
        to=[user.email]
    )
    email_message.send()

def register_view(request):
    
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # usuario só ativa apos confirmar email 
            user.save()
            
            
            send_activation_email(request, user)
            
            messages.success(request, 'Conta criada com sucesso! Verifique seu email para ativar sua conta.')
            return redirect('login')
    else:
        form = RegisterForm()
            
    return render(request, 'accounts/register.html', {'form': form})            

def activate_view(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = get_user_model().objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, get_user_model().DoesNotExist):
        user = None

    if user and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, 'Sua conta foi ativada com sucesso!')
        return redirect('activation_success') # redireciona para a pagina de login após ativação
    else:
        messages.error(request, 'Link de ativação inválido ou expirado.')
        return redirect('login')  # redireciona para a pagina de login se o link for inválido

def activation_success(request):
    return render(request, 'accounts/activation_success.html')

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
            user = get_user_model().objects.get(email=email)
        except get_user_model().DoesNotExist:   #se o email não for encontrado redireciona para pagina resend_activation 
            pass
            return redirect('resend_activation_email')
        
        if user.is_active:      #verifica se a conta esta ativa 
            messages.info(request, 'Sua conta já está ativa. Faça login.')
            return redirect('login')
        
        link = create_activate_link(request, user)   #cria o link de ativação
        
        # TODO: implementar o utils.py enviar email
        email = EmailMessage(      #o email que vai ser enviado
            'Reenvio do link de ativação',
            f'Olá!\n\nClique no link abaixo para ativar sua conta:\n\n{link}\n\nSe você não criou esta conta, ignore este email.',
            to=[user.email]
        )
        email.send()   #envia o email
        
        messages.success(request, 'Link de ativação reenviado! Verifique seu email.')   #mostra uma mensagem notificando que foi enviado o email
        return redirect('login')
    
    return render(request, 'accounts/resend_activation_email.html')

def logout_view(request):
    #não foi colocado no home----------------------------------------------------------------+
    logout(request)    #encerra a sessão do usuário
    return redirect('login') #redireciona para a pagina de login

#password

def request_password_reset(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        
        try:
            user = User.objects.get(email=email)
            token_obj = create_reset_token(user)
            reset_link = request.build_absolute_uri(reverse('reset_password', args=[token_obj.token]))   #envia o link pra resetar a senha pelo email
            
            # TODO: implementar o utils.py enviar email
            email = EmailMessage(      #o email que vai ser enviado
            'Redefinição de senha',
            f'Olá!\n\nClique no link abaixo para redefinir sua senha:\n\n{reset_link}\n\nSe você não criou esta conta, ignore este email.',
            to=[user.email]
            )
            email.send()   #envia o email
            #send_mail(reset_link)
        except User.DoesNotExist:
            pass #nunca revela se existe ou não
    return render(request, 'accounts/request_reset.html')

def reset_password(request, token):
    token_obj = get_object_or_404(PasswordResetToken, token=token)
    
    if token_obj.is_expired():
        token_obj.delete()
        return render(request, 'accounts/token_expired.html')
    
    form = ResetPasswordForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = token_obj.user
        user.set_password(form.cleaned_data["password1"])
        user.save()
        
        token_obj.delete()
        
        messages.success(request, "Senha redefinida com sucesso! Faça login com sua nova senha.")
        return redirect('login')
       
    return render(request, "accounts/ResetPassword.html", {"form": form})

#home

@login_required
def home_view(request):
    return render(request, 'accounts/home.html')

#profile

@login_required
def profile_edit(request):
    #serve pra configurar o perfil do usuario
    profile = request.user.profile
    
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('my_profile')
    else:
        form = ProfileForm(instance=profile)
            
    return render(request, 'accounts/profile_edit.html', {'form': form})

#PENDENTE--------------------------
@login_required
def my_profile(request):
    return render(request, 'accounts/profile_view.html', {'profile_user': request.user})

#PENDENTE------------------------------------
@login_required
def profile_view(request, username):
    user = get_object_or_404(CustomUser, username=username)
    return render(request, 'accounts/profile_view.html', {'profile_user': user})
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout, get_user_model
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str

from .forms import RegisterForm, LoginForm, ProfileForm, ResetPasswordForm
from .tokens import account_activation_token
from .models import PasswordResetToken
from .utils import create_reset_token, send_email_notification

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

    return send_email_notification(
        "Ative sua conta",
        f"Olá!\n\nClique no link abaixo para ativar sua conta:\n\n{link}\n\n"
        f"Se você não criou esta conta, ignore este email.",
        user.email
    )


def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # usuario só ativa apos confirmar email
            user.save()

            sent = send_activation_email(request, user)

            if sent:
                messages.success(request, 'Conta criada com sucesso! Verifique seu email para ativar sua conta.')
            else:
                messages.warning(
                    request,
                    'Conta criada, mas houve um problema ao enviar o email de ativação. '
                    'Tente reenviar pela página de login.'
                )
            return redirect('login')
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form})


def activate_view(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, 'Sua conta foi ativada com sucesso!')
        return redirect('activation_success')
    else:
        messages.error(request, 'Link de ativação inválido ou expirado.')
        return redirect('login')


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


@require_POST
def resend_activation_email(request):
    email = request.POST.get('email')

    try:
        user = User.objects.get(email=email)
        if not user.is_active:
            link = create_activate_link(request, user)
            send_email_notification(
                'Reenvio do link de ativação',
                f'Olá!\n\nClique no link abaixo para ativar sua conta:\n\n{link}\n\n'
                f'Se você não criou esta conta, ignore este email.',
                user.email
            )
    except User.DoesNotExist:
        pass  # não revela se o email existe ou não

    # mensagem genérica sempre igual, exista o email ou não, esteja ativo ou não
    messages.info(request, 'Se o email existir em nossa base, enviaremos um link de ativação.')
    return redirect('login')


def logout_view(request):
    logout(request)
    return redirect('login')


# password

@require_POST
def request_password_reset(request):
    email = request.POST.get('email')

    try:
        user = User.objects.get(email=email)
        token_obj = create_reset_token(user)
        reset_link = request.build_absolute_uri(reverse('reset_password', args=[token_obj.token]))

        send_email_notification(
            'Redefinição de senha',
            f'Olá!\n\nClique no link abaixo para redefinir sua senha:\n\n{reset_link}\n\n'
            f'Se você não solicitou isso, ignore este email.',
            user.email
        )
    except User.DoesNotExist:
        pass  # nunca revela se existe ou não

    messages.info(request, 'Se o email existir em nossa base, enviaremos as instruções de redefinição.')
    return redirect('request_password_reset')


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


# home

@login_required
def home_view(request):
    return render(request, 'accounts/home.html')


# profile

@login_required
def profile_edit(request):
    profile = request.user.profile

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('my_profile')
    else:
        form = ProfileForm(instance=profile)

    return render(request, 'accounts/profile_edit.html', {'form': form})


@login_required
def my_profile(request):
    return render(request, 'accounts/profile_view.html', {'profile_user': request.user})


@login_required
def profile_view(request, username):
    user = get_object_or_404(User, username=username)

    # TODO: ajustar quando o campo Profile.is_public existir
    # if user != request.user and not user.profile.is_public:
    #     messages.error(request, 'Este perfil é privado.')
    #     return redirect('home')

    return render(request, 'accounts/profile_view.html', {'profile_user': user})
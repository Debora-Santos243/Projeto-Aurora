import kivy
import re
import webbrowser
import pygame
import cv2
import os
import json
import calendar
import pandas as pd
import sqlite3
import spacy
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.uix.image import Image
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.graphics.texture import Texture
from kivy.uix.relativelayout import RelativeLayout
from kivy.clock import Clock
from kivy.uix.popup import Popup
from kivy.uix.dropdown import DropDown
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner, SpinnerOption
from kivy.uix.togglebutton import ToggleButton
from kivy.properties import StringProperty
from kivy.lang import Builder
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from openpyxl import Workbook, load_workbook
from kivy.animation import Animation
from kivy.uix.floatlayout import FloatLayout


# Define o caminho completo para a pasta "app_aurora"
caminho_app_aurora = os.path.abspath("app_aurora")

# Se o diretório "app_aurora" não existir, cria ele
if not os.path.exists(caminho_app_aurora):
    os.makedirs(caminho_app_aurora)

# Define os caminhos para os arquivos utilizadores.txt e perfis.xlsx na pasta "app_aurora"
caminho_utilizadores = os.path.join(caminho_app_aurora, 'utilizadores.txt')
caminho_perfis = os.path.join(caminho_app_aurora, 'perfis.xlsx')

Builder.load_string('''
<MySpinnerOption>:
    background_normal: ''
    background_color: (0.2, 0.8, 0.8, 1)
    color: (0, 0, 0, 1)
''')

class TelaLogin(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tela_criar_utilizador = kwargs.get('tela_criar_utilizador')  # Recebe a instância de TelaCriarUtilizador
        self.carregar_imagem()
        Window.bind(on_resize=self.atualizar_imagem)

    # Carrega a imagem de fundo
    def carregar_imagem(self):
        try:
            with self.canvas.before:
                # Carrega a imagem de fundo
                self.background = Image(source='logo.png', allow_stretch=True, keep_ratio=False)
                # Bind the texture size to the image size
                self.bind(size=self.atualizar_imagem, pos=self.atualizar_imagem)
        except Exception as e:
            print(f"Erro ao carregar imagem de fundo: {e}")

        # Adiciona os widgets de entrada de texto para o nome de usuário e senha
        layout = BoxLayout(orientation='vertical', padding=[25, 50], spacing=10, size_hint=(None, None), size=(300, 400),
                            pos_hint={'center_x': 0.5, 'center_y': 0.5})
        self.add_widget(layout)

        username_layout = BoxLayout(size_hint_y=None, height=30, spacing=10)
        username_label = Label(text='Utilizador:', size_hint=(None, None), size=(100, 30), color=(0, 0, 0, 1))
        self.username_input = TextInput(multiline=False, size_hint=(None, None), width=200, height=30, foreground_color=(0, 0, 0, 1))
        username_layout.add_widget(username_label)
        username_layout.add_widget(self.username_input)
        layout.add_widget(username_layout)

        password_layout = BoxLayout(size_hint_y=None, height=30, spacing=10)
        password_label = Label(text='Password:', size_hint=(None, None), size=(100, 30), color=(0, 0, 0, 1))
        self.password_input = TextInput(password=True, multiline=False, size_hint=(None, None), width=200, height=30, foreground_color=(0, 0, 0, 1))
        password_layout.add_widget(password_label)
        password_layout.add_widget(self.password_input)
        layout.add_widget(password_layout)

        # Adiciona os botões de login, criar novo utilizador e esqueci a palavra-passe
        button_layout = BoxLayout(size_hint_y=None, height=40, spacing=10)
        self.login_button = Button(text='Login', size_hint=(None, None), size=(150, 40), background_normal='', 
                                   background_color=(0.2, 0.8, 0.8, 1), color=(0, 0, 0, 1),
                                    font_size='15sp', halign='center')
        self.login_button.bind(on_press=self.verificar_login)
        button_layout.add_widget(self.login_button)

        self.create_user_button = Button(text='Criar Novo Utilizador', size_hint=(None, None), size=(175, 40), background_normal='', 
                                         background_color=(0.2, 0.8, 0.8, 1), color=(0, 0, 0, 1),font_size='15sp', halign='center')
        self.create_user_button.bind(on_press=self.ir_para_tela_criar_utilizador)
        button_layout.add_widget(self.create_user_button)

        layout.add_widget(button_layout)

        # Adiciona o texto "Esqueci a Palavra-passe" como um label com formatação de texto sublinhado
        forgot_password_label = Label(text='[u]Esqueci a Palavra-passe[/u]', markup=True, size_hint=(None, None), size=(200, 30), color=(0, 0, 0, 1),
                                      halign='center', valign='middle')
        forgot_password_label.bind(on_touch_down=self.ir_para_tela_esqueci_password)
        layout.add_widget(forgot_password_label)

        self.status_label = Label(size_hint=(None, None))
        layout.add_widget(self.status_label)

    def atualizar_imagem(self, instance, *args):
        self.background.size = self.size
        self.background.pos = self.pos

    def verificar_login(self, instance):
        username = self.username_input.text
        password = self.password_input.text

        if self.tela_criar_utilizador and username in self.tela_criar_utilizador.utilizadores:
            if self.tela_criar_utilizador.utilizadores[username]['senha'] == password:
                self.manager.username = username
                self.status_label.text = 'Login bem sucedido!'

                # Salva os dados do login
                self.salvar_dados()

                self.manager.current = 'tela_principal'
            else:
                self.status_label.text = 'Senha incorreta'
        else:
            self.status_label.text = 'Utilizador não encontrado'

    def salvar_dados(self):
        # Recupera os dados inseridos pelo usuário
        username = self.username_input.text
        password = self.password_input.text

        # Verifica se ambos os campos foram preenchidos
        if username != '' and password != '':
            # Salva os dados no arquivo de texto
            with open('utilizadores.txt', 'a') as file:
                file.write(f'{username}, {password}\n')

            # Continua com a lógica para salvar no arquivo Excel
        else:
            # Exibe uma mensagem de erro se algum campo estiver em branco
            self.status_label.text = 'O nome de usuário e a senha devem ser preenchidos!'

    def on_login(self):
        # Verifica as credenciais e faz login
        if self.verificar_credenciais():
            # Se as credenciais forem válidas, armazene o nome de usuário
            self.manager.username = self.username_input.text
            self.manager.current = 'tela_perfil'

    def ir_para_tela_criar_utilizador(self, instance):
        self.manager.current = 'tela_criar_utilizador'

    def ir_para_tela_esqueci_password(self, instance, touch):
        # Verifica se o toque ocorreu dentro do texto "Esqueci a Palavra-passe"
        if instance.collide_point(*touch.pos):
            # Define a próxima tela como a tela onde o usuário pode redefinir a senha
            self.manager.current = 'tela_redefinir_senha'

class TelaCriarUtilizador(Screen):
    def __init__(self, **kwargs):
        super(TelaCriarUtilizador, self).__init__(**kwargs)
        self.utilizadores = self.carregar_utilizadores()

        # Define a cor de fundo da tela como o azul especificado (#a3d7da)
        with self.canvas.before:
            Color(0.6392, 0.8431, 0.8549, 1)  # Valores RGB de #a3d7da
            self.rect = Rectangle(size=self.size, pos=self.pos)

        # Atualiza o retângulo quando o tamanho da tela é alterado
        self.bind(size=self.atualizar_retangulo, pos=self.atualizar_retangulo)

        # Adiciona os widgets de entrada de texto para criar um novo utilizador
        email_label = Label(text='Email:', size_hint=(None, None), pos_hint={'center_x': 0.3, 'center_y': 0.6}, color=(0, 0, 0, 1))
        self.add_widget(email_label)
        self.email_input = TextInput(multiline=False, size_hint=(None, None), width=200, height=30,
                                     pos_hint={'center_x': 0.5, 'center_y': 0.6})
        self.add_widget(self.email_input)

        username_label = Label(text='Utilizador:', size_hint=(None, None), pos_hint={'center_x': 0.3, 'center_y': 0.5}, color=(0, 0, 0, 1))
        self.add_widget(username_label)
        self.username_input = TextInput(multiline=False, size_hint=(None, None), width=200, height=30,
                                        pos_hint={'center_x': 0.5, 'center_y': 0.5})
        self.add_widget(self.username_input)

        password_label = Label(text='Password:', size_hint=(None, None), pos_hint={'center_x': 0.3, 'center_y': 0.4}, color=(0, 0, 0, 1))
        self.add_widget(password_label)
        self.password_input = TextInput(password=True, multiline=False, size_hint=(None, None), width=200, height=30,
                                        pos_hint={'center_x': 0.5, 'center_y': 0.4})
        self.add_widget(self.password_input)

        # Adiciona o botão para criar um novo utilizador
        button_width = 150
        button_height = 40

        self.create_user_button = Button(text='Criar Utilizador', size_hint=(None, None), size=(button_width, button_height),
                                         pos_hint={'center_x': 0.5, 'center_y': 0.3}, 
                                         background_normal='', background_color=(0.2, 0.8, 0.8, 1), color=(0, 0, 0, 1),
                                         font_size='15sp', halign='center')
        self.create_user_button.bind(on_press=self.criar_novo_utilizador)
        self.add_widget(self.create_user_button)

        # Adiciona o botão para retornar à tela de login
        self.return_to_login_button = Button(text='Voltar ao Login', size_hint=(None, None), size=(button_width, button_height),
                                             pos_hint={'center_x': 0.5, 'center_y': 0.2}, 
                                             background_normal='', background_color=(0.2, 0.8, 0.8, 1),
                                             color=(0, 0, 0, 1), font_size='15sp', halign='center')
        self.return_to_login_button.bind(on_press=self.retornar_para_tela_login)
        self.add_widget(self.return_to_login_button)

        self.status_label = Label(size_hint=(None, None), pos_hint={'center_x': 0.5, 'center_y': 0.1})
        self.add_widget(self.status_label)

    def atualizar_retangulo(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def criar_novo_utilizador(self, instance):
        email = self.email_input.text
        username = self.username_input.text
        password = self.password_input.text

        if email.strip() == '' or username.strip() == '' or password.strip() == '':
            self.status_label.text = 'Todos os campos devem ser preenchidos'
        elif not self.validar_email(email):
            self.status_label.text = 'Endereço de email inválido'
        elif len(password) < 8:
            self.status_label.text = 'A senha deve ter pelo menos 8 caracteres'
        elif username in self.utilizadores:
            self.status_label.text = 'Nome de utilizador já existe'
        else:
            # Armazena os dados do novo utilizador
            self.utilizadores[username] = {'email': email, 'senha': password}
            self.status_label.text = f'Novo utilizador criado: {username}'
        self.salvar_utilizadores()

    def carregar_utilizadores(self):
        try:
            with open(caminho_utilizadores, 'r') as file:
                return eval(file.read())  # Avalia o conteúdo do arquivo como um dicionário
        except FileNotFoundError:
            return {'admin': {'email': 'admin@example.com', 'senha': '1234'}}  # Utilizador padrão

    def salvar_utilizadores(self):
        with open(caminho_utilizadores, 'w') as file:
            file.write(json.dumps(self.utilizadores))  # Escreve o dicionário de utilizadores no arquivo como uma string

    def validar_email(self, email):
        # Expressão regular para validar endereços de email
        regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(regex, email)

    def retornar_para_tela_login(self, instance):
        self.manager.current = 'tela_login'

class TelaRedefinirSenha(Screen):
    def __init__(self, **kwargs):
        super(TelaRedefinirSenha, self).__init__(**kwargs)

        # Define a cor de fundo da tela como o azul especificado (#a3d7da)
        with self.canvas.before:
            Color(0.6392, 0.8431, 0.8549, 1)  # Valores RGB de #a3d7da
            self.rect = Rectangle(size=self.size, pos=self.pos)

        # Atualiza o retângulo quando o tamanho da tela é alterado
        self.bind(size=self.atualizar_retangulo, pos=self.atualizar_retangulo)

        layout = GridLayout(cols=2, padding=[25, 50], spacing=[10, 10], size_hint=(None, None), size=(300, 400),
                            pos_hint={'center_x': 0.5, 'center_y': 0.4})
        self.add_widget(layout)

        label = Label(text='Redefinir Senha:', size_hint=(None, None), size=(150, 30), color=(0, 0, 0, 1))
        layout.add_widget(label)

        self.new_password_input = TextInput(multiline=False, password=True, size_hint=(None, None), width=200, height=30,
                                            pos_hint={'center_x': 0.5, 'center_y': 0.4}, foreground_color=(0, 0, 0, 1))
        layout.add_widget(self.new_password_input)

        redefinir_button = Button(text='Redefinir', size_hint=(None, None), size=(150, 40), pos_hint={'center_x': 0.7, 'center_y': 0.3}, 
                                  background_normal='', background_color=(0.2, 0.8, 0.8, 1), color=(0, 0, 0, 1), font_size='15sp', halign='center')
        redefinir_button.bind(on_press=self.redefinir_senha)
        layout.add_widget(redefinir_button)

        # Botão "Voltar ao Login"
        voltar_button = Button(text='Voltar ao Login', size_hint=(None, None), size=(150, 40), pos_hint={'center_x': 0.3, 'center_y': 0.3}, 
                               background_normal='', background_color=(0.2, 0.8, 0.8, 1), color=(0, 0, 0, 1), font_size='15sp', halign='center')
        voltar_button.bind(on_press=self.voltar_para_login)
        layout.add_widget(voltar_button)

    def redefinir_senha(self, instance):
        nova_senha = self.new_password_input.text
        # Aqui você pode implementar a lógica para redefinir a senha
        print("Nova senha:", nova_senha)

    def atualizar_retangulo(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def voltar_para_login(self, instance):
        # Define a próxima tela como a tela de login
        self.manager.current = 'tela_login'

class TelaPerfil(Screen):
    def __init__(self, **kwargs):
        super(TelaPerfil, self).__init__(**kwargs)
        
        # Define a cor de fundo da tela como o azul especificado (#a3d7da)
        with self.canvas.before:
            Color(0.6392, 0.8431, 0.8549, 1)  # Valores RGB de #a3d7da
            self.rect = Rectangle(size=self.size, pos=self.pos)

        # Atualiza o retângulo quando o tamanho da tela é alterado
        self.bind(size=self.atualizar_retangulo, pos=self.atualizar_retangulo)

        # Adiciona os widgets para visualizar e editar o perfil
        self.info_label = Label(text='', size_hint=(None, None), pos_hint={'center_x': 0.5, 'center_y': 0.7}, color=(0, 0, 0, 1))  # Definindo a cor do texto como preto
        self.add_widget(self.info_label)

        self.edit_button = Button(text='Editar Perfil', size_hint=(None, None), size=(150, 50), pos_hint={'center_x': 0.5, 'center_y': 0.4}, 
                                  background_normal='', background_color=(0.2, 0.8, 0.8, 1), color=(0, 0, 0, 1), font_size='15sp', halign='center')
        self.edit_button.bind(on_press=self.editar_perfil)
        self.add_widget(self.edit_button)

        self.create_profile_button = Button(text='Criar Perfil', size_hint=(None, None), size=(150, 50), pos_hint={'center_x': 0.5, 'center_y': 0.3}, 
                                  background_normal='', background_color=(0.2, 0.8, 0.8, 1), color=(0, 0, 0, 1), font_size='15sp', halign='center')
        self.create_profile_button.bind(on_press=self.criar_perfil)
        self.add_widget(self.create_profile_button)
        
        # Adiciona o botão "Voltar à Tela Principal"
        self.back_to_main_button = Button(text='Voltar à Tela Principal', size_hint=(None, None), size=(200, 50), pos_hint={'center_x': 0.5, 'center_y': 0.2}, 
                                  background_normal='', background_color=(0.2, 0.8, 0.8, 1), color=(0, 0, 0, 1), font_size='15sp', halign='center')
        self.back_to_main_button.bind(on_press=self.voltar_a_tela_principal)
        self.add_widget(self.back_to_main_button)

    def atualizar_retangulo(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def visualizar_perfil(self):
        # Obtém o nome de usuário da tela de login
        username = self.manager.get_screen('tela_login').username_input.text
        # Obtém os utilizadores da instância atual de TelaCriarUtilizador
        utilizadores = self.manager.get_screen('tela_criar_utilizador').utilizadores
        # Verifica se o usuário existe nos dados armazenados
        if username in utilizadores:
            # Recupera os dados do perfil atual
            user_data = utilizadores[username]
            self.info_label.text = f'Email: {user_data["email"]}\nUtilizador: {username}'
        else:
            self.info_label.text = 'Perfil não encontrado'

    def on_pre_enter(self):
        # Chama o método para visualizar o perfil ao entrar na tela
        self.visualizar_perfil()

    def editar_perfil(self, instance):
        # Recupera o nome de usuário atualmente logado do gerenciador de tela
        username = self.manager.username

        # Acesse uma instância válida de TelaCriarPerfil
        tela_criar_perfil = self.manager.get_screen('tela_criar_perfil')
        
        # Carregar dados do perfil do usuário
        tela_criar_perfil.carregar_dados_perfil(username)
        
        # Altera para a tela de criação de perfil
        self.manager.current = 'tela_criar_perfil'

    def criar_perfil(self, instance):
        # Define a transição para a tela de criação de perfil
        self.manager.current = 'tela_criar_perfil'

    def voltar_a_tela_principal(self, instance):
        self.manager.current = 'tela_principal'

class TelaPrincipal(Screen):
    def __init__(self, **kwargs):
        super(TelaPrincipal, self).__init__(**kwargs)
        
        # Define a cor de fundo da tela principal como azul
        with self.canvas.before:
            Color(0.6392, 0.8431, 0.8549, 1)  # Azul
            self.rect = Rectangle(size=self.size, pos=self.pos)

        # Atualiza o retângulo quando o tamanho da tela é alterado
        self.bind(size=self.atualizar_retangulo, pos=self.atualizar_retangulo)

        layout = GridLayout(cols=1, padding=[25, 50], spacing=10, size_hint=(None, None), size=(300, 500), pos_hint={'center_x': 0.5, 'center_y': 0.65})
        self.add_widget(layout)

        # Adiciona os botões à tela principal
        botoes = ['Perfil', 'Projeto Aurora', 'Especialidades Médicas', 'Parcerias', 'Áudios','Quiz','Diário','Marcação de Consultas','Consulta de Emergência']
        for texto in botoes:
            botao = Button(text=texto, size_hint=(None, None), size=(300, 50), 
                            background_normal='', background_color=(0.2, 0.8, 0.8, 1), color=(0, 0, 0, 1), font_size='15sp', halign='center')
            if texto == 'Perfil':
                botao.bind(on_press=self.ir_para_tela_perfil)
            elif texto == 'Projeto Aurora':
                botao.bind(on_press=self.ir_para_tela_projeto_aurora)
            elif texto == 'Áudios':
                botao.bind(on_press=self.ir_para_tela_audios)
            elif texto == 'Especialidades Médicas':
                botao.bind(on_press=self.ir_para_tela_especialidades_medicas)
            elif texto == 'Parcerias':
                botao.bind(on_press=self.ir_para_tela_parcerias)
            elif texto == 'Quiz':
                botao.bind(on_press=self.ir_para_tela_quiz)    
            elif texto == 'Diário':
                botao.bind(on_press=self.ir_para_tela_diario) 
            elif texto == 'Marcação de Consultas':
                botao.bind(on_press=self.ir_para_tela_marcacao_de_consultas)
                botao.background_color = (0, 1, 0, 1)  # Cor de fundo verde para destacar
            elif texto == 'Consulta de Emergência':
                botao.bind(on_press=self.ir_para_tela_videochamada)
                botao.background_color = (1, 0, 0, 1)  # Cor de fundo vermelha para destacar
            else:
                botao = Button(text=texto, size_hint=(None, None), size=(300, 50))
                # Nenhum evento é associado a estes botões por enquanto
            layout.add_widget(botao)

        # Adiciona o botão de logout
        logout_button = Button(text='Logout', size_hint=(None, None), size=(100, 50), pos_hint={'center_x': 0.53, 'center_y': 0.05}, 
                                  background_normal='', background_color=(0.2, 0.8, 0.8, 1), color=(0, 0, 0, 1), font_size='15sp', halign='center')
        logout_button.bind(on_press=self.logout)
        self.add_widget(logout_button)

    def atualizar_retangulo(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def ir_para_tela_perfil(self, instance):
        self.manager.current = 'tela_perfil'

    def ir_para_tela_projeto_aurora(self, instance):
        self.manager.current = 'tela_projeto_aurora'
    
    def ir_para_tela_audios(self, instance):
        self.manager.current = 'tela_audios'

    def ir_para_tela_quiz(self, instance):
        self.manager.current = 'tela_quiz'
    
    def ir_para_tela_diario(self, instance):
        self.manager.current = 'tela_diario'

    def ir_para_tela_especialidades_medicas(self, instance):
        self.manager.current = 'tela_especialidades_medicas'

    def ir_para_tela_parcerias(self, instance):
        self.manager.current = 'tela_parcerias'
    
    def ir_para_tela_marcacao_de_consultas(self,instance):
        self.manager.current = 'tela_marcacao_de_consultas'
    
    def ir_para_tela_videochamada(self, instance):
        self.manager.current = 'tela_videochamada'

    def logout(self, instance):
        self.manager.current = 'tela_login'
        # Reiniciar campos de entrada de texto e mensagem de status
        self.parent.get_screen('tela_login').username_input.text = ''
        self.parent.get_screen('tela_login').password_input.text = ''
        self.parent.get_screen('tela_login').status_label.text = ''

class TelaCriarPerfil(Screen):
    def __init__(self, **kwargs):
        super(TelaCriarPerfil, self).__init__(**kwargs)
        self.perfis_criados = []

        # Define a cor de fundo da tela como o azul especificado (#a3d7da)
        with self.canvas.before:
            Color(0.6392, 0.8431, 0.8549, 1)  # Valores RGB de #a3d7da
            self.rect = Rectangle(size=self.size, pos=self.pos)

        # Atualiza o retângulo quando o tamanho da tela é alterado
        self.bind(size=self.atualizar_retangulo, pos=self.atualizar_retangulo)

        # Adiciona os campos de entrada para criar o perfil
        nome_label = Label(text='Nome Completo:', size_hint=(None, None), pos_hint={'center_x': 0.3, 'center_y': 0.9}, halign='left', text_size=(None, None), color=(0, 0, 0, 1))
        self.add_widget(nome_label)
        self.nome_input = TextInput(multiline=False, size_hint=(None, None), width=200, height=30, pos_hint={'center_x': 0.7, 'center_y': 0.9}, foreground_color=(0, 0, 0, 1), background_color=(1, 1, 1, 1))
        self.add_widget(self.nome_input)

        data_nasc_label = Label(text='Data de Nascimento (DD/MM/AAAA):', size_hint=(None, None), pos_hint={'center_x': 0.3, 'center_y': 0.8}, halign='left', text_size=(None, None), color=(0, 0, 0, 1))
        self.add_widget(data_nasc_label)
        self.data_nasc_input = TextInput(multiline=False, size_hint=(None, None), width=200, height=30, pos_hint={'center_x': 0.7, 'center_y': 0.8}, foreground_color=(0, 0, 0, 1), background_color=(1, 1, 1, 1))
        self.add_widget(self.data_nasc_input)

        cc_label = Label(text='CC:', size_hint=(None, None), pos_hint={'center_x': 0.3, 'center_y': 0.7}, halign='left', text_size=(None, None), color=(0, 0, 0, 1))
        self.add_widget(cc_label)
        self.cc_input = TextInput(multiline=False, size_hint=(None, None), width=200, height=30, pos_hint={'center_x': 0.7, 'center_y': 0.7}, foreground_color=(0, 0, 0, 1), background_color=(1, 1, 1, 1))
        self.add_widget(self.cc_input)
        
        nif_label = Label(text='NIF:', size_hint=(None, None), pos_hint={'center_x': 0.3, 'center_y': 0.6}, halign='left', text_size=(None, None), color=(0, 0, 0, 1))
        self.add_widget(nif_label)
        self.nif_input = TextInput(multiline=False, size_hint=(None, None), width=200, height=30, pos_hint={'center_x': 0.7, 'center_y': 0.6}, foreground_color=(0, 0, 0, 1), background_color=(1, 1, 1, 1))
        self.add_widget(self.nif_input)

        morada_label = Label(text='Morada:', size_hint=(None, None), pos_hint={'center_x': 0.3, 'center_y': 0.5}, halign='left', text_size=(None, None), color=(0, 0, 0, 1))
        self.add_widget(morada_label)
        self.morada_input = TextInput(multiline=False, size_hint=(None, None), width=200, height=30, pos_hint={'center_x': 0.7, 'center_y': 0.5}, foreground_color=(0, 0, 0, 1), background_color=(1, 1, 1, 1))
        self.add_widget(self.morada_input)

        ss_label = Label(text='Sistema de Saúde:', size_hint=(None, None), pos_hint={'center_x': 0.3, 'center_y': 0.4}, halign='left', text_size=(None, None), color=(0, 0, 0, 1))
        self.add_widget(ss_label)
        self.ss_input = TextInput(multiline=False, size_hint=(None, None), width=200, height=30, pos_hint={'center_x': 0.7, 'center_y': 0.4}, foreground_color=(0, 0, 0, 1), background_color=(1, 1, 1, 1))
        self.add_widget(self.ss_input)

        doenças_label = Label(text='Doenças Conhecidas:', size_hint=(None, None), pos_hint={'center_x': 0.3, 'center_y': 0.3}, halign='left', text_size=(None, None), color=(0, 0, 0, 1))
        self.add_widget(doenças_label)
        self.doenças_input = TextInput(multiline=False, size_hint=(None, None), width=200, height=30, pos_hint={'center_x': 0.7, 'center_y': 0.3}, foreground_color=(0, 0, 0, 1), background_color=(1, 1, 1, 1))
        self.add_widget(self.doenças_input)

        # Adiciona o botão para criar o perfil
        criar_perfil_button = Button(text='Criar Perfil', size_hint=(None, None), size=(150, 50), pos_hint={'center_x': 0.5, 'center_y': 0.2}, 
                                  background_normal='', background_color=(0.2, 0.8, 0.8, 1), color=(0, 0, 0, 1), font_size='15sp', halign='center')
        criar_perfil_button.bind(on_press=self.criar_perfil)
        self.add_widget(criar_perfil_button)

        # Adiciona o botão para voltar à tela de perfil
        voltar_button = Button(text='Voltar', size_hint=(None, None), size=(150, 50), pos_hint={'center_x': 0.5, 'center_y': 0.1}, 
                                  background_normal='', background_color=(0.2, 0.8, 0.8, 1), color=(0, 0, 0, 1), font_size='15sp', halign='center')
        voltar_button.bind(on_press=self.voltar)
        self.add_widget(voltar_button)

        self.status_label = Label(size_hint=(None, None), pos_hint={'center_x': 0.5, 'center_y': 0.05}, halign='left', text_size=(None, None))
        self.add_widget(self.status_label)

    def atualizar_retangulo(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def criar_perfil(self, instance):
        nome = self.nome_input.text
        data_nasc = self.data_nasc_input.text
        cc = self.cc_input.text
        nif = self.nif_input.text
        morada = self.morada_input.text
        ss = self.ss_input.text
        doencas = self.doenças_input.text 

        # Verificar se todos os campos obrigatórios estão preenchidos
        if nome.strip() == '' or data_nasc.strip() == '' or nif.strip() == '' or morada.strip() == '' or ss.strip() == '':
            self.status_label.text = 'Todos os campos obrigatórios devem ser preenchidos'
            return

        # Criar um novo perfil
        novo_perfil = {
            'nome': nome,  # Adicionando o nome completo ao perfil
            'data_nasc': data_nasc,
            'cc': cc,
            'nif': nif,
            'morada': morada, 
            'ss': ss,
            'doencas': doencas  
        }

        # Criar um DataFrame com os dados do novo perfil
        df = pd.DataFrame([novo_perfil])

        # Adicionar o novo perfil ao DataFrame de perfis criados
        if hasattr(self, 'df_perfis'):
            self.df_perfis = pd.concat([self.df_perfis, df], ignore_index=True)
        else:
            self.df_perfis = df

        # Salvar o DataFrame em um arquivo Excel
        self.df_perfis.to_excel('perfis.xlsx', index=False)

        self.status_label.text = 'Perfil criado e salvo com sucesso!'

    def carregar_dados_perfil(self, username):
        try:
            # Carregar o arquivo Excel
            df = pd.read_excel('perfis.xlsx')
            # Filtrar os dados do perfil do usuário
            perfil = df[df['nome'] == username].iloc[0]  # Alterado para filtrar pelo nome completo
            # Preencher os campos de entrada com os dados do perfil
            self.nome_input.text = str(perfil['nome'])  # Convertendo para string
            self.data_nasc_input.text = str(perfil['data_nasc'])  # Convertendo para string
            self.cc_input.text = str(perfil['cc'])  # Convertendo para string
            self.nif_input.text = str(perfil['nif'])  # Convertendo para string
            self.morada_input.text = str(perfil['morada'])  # Convertendo para string
            self.ss_input.text = str(perfil['ss'])  # Convertendo para string
            self.doenças_input.text = str(perfil['doencas'])  # Convertendo para string
            self.status_label.text = ''  # Limpar o status anterior, se houver
        except Exception as e:
            self.status_label.text = f"Erro ao carregar dados do perfil: {str(e)}"

    def salvar_dados(self):
        # Recupera os dados inseridos pelo usuário
        username = self.username_input.text
        email = self.email_input.text
        password = self.password_input.text

        # Verifica se todos os campos foram preenchidos
        if username != '' and email != '' and password != '':
            # Salva os dados no arquivo de texto
            with open('utilizadores.txt', 'a') as file:
                file.write(f'{username}, {email}, {password}\n')

            # Continua com a lógica para salvar no arquivo Excel
        else:
            # Exibe uma mensagem de erro se algum campo estiver em branco
            self.status_label.text = 'Todos os campos devem ser preenchidos!'

    def voltar(self, instance):
        self.manager.current = 'tela_perfil'

class TelaProjetoAurora(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.carregar_interface()
        Window.bind(on_resize=self.atualizar_interface)

    def carregar_interface(self):
        with self.canvas:
            # Carrega a imagem de fundo
            self.background = Image(source='logo.png', allow_stretch=True, keep_ratio=False)
            self.bind(size=self.atualizar_imagem)
            self.bind(pos=self.atualizar_imagem)
            self.add_widget(self.background)

        texto_projeto = ("[b]Caracterização do projeto:[/b]\n\n"
                        "O Projeto Aurora surge para abordar o estigmatizado associado à saúde mental, proporcionando recursos acessíveis, incluindo uma plataforma online, workshops e parcerias com profissionais de saúde.\n"
                        "Almejando construir comunidades de apoio, integrar atividades terapêuticas e promover práticas como mindfulness.\n"
                        "O projeto compromete-se a fornecer acompanhamento contínuo, eventos de sensibilização e avaliação constante.\n"
                        "Em resumo, o Projeto Aurora pretende iluminar o caminho para a saúde mental, oferecendo uma rede de suporte inclusiva e educativa.")

        self.botao_projeto = Button(text=texto_projeto, size_hint=(None, None), pos_hint={'center_x': 0.5, 'center_y': 0.5}, markup=True,
                                    background_normal='', background_color=(0.6392, 0.8431, 0.8549, 0.5), color=(0, 0, 0, 1),
                                    font_size='15sp', halign='center')
        self.botao_projeto.bind(size=self.atualizar_interface)
        self.botao_projeto.bind(texture_size=self.atualizar_interface)
        self.add_widget(self.botao_projeto)

        # Adiciona o botão para voltar à tela principal
        self.voltar_button = Button(text='Voltar à Tela Principal', size_hint=(None, None), size=(200, 50), pos_hint={'center_x': 0.5, 'center_y': 0.1}, 
                                  background_normal='', background_color=(0.2, 0.8, 0.8, 1), color=(0, 0, 0, 1), font_size='15sp', halign='center')
        self.voltar_button.bind(on_press=self.voltar_tela_principal)
        self.add_widget(self.voltar_button)
   
    def atualizar_interface(self, *args):
        self.botao_projeto.text_size = (Window.width, None)
        texto_width, texto_height = self.botao_projeto.texture_size  # Obtém o tamanho do texto
        texto_x, texto_y = self.botao_projeto.pos  # Obtém a posição do texto
        
        # Calcula a posição do botão para alinhá-lo com o texto e centralizá-lo
        botao_x = texto_x + (self.botao_projeto.width - texto_width) / 2  # Centraliza o botão horizontalmente
        botao_y = texto_y - texto_height  # Move o botão para baixo do texto
        self.botao_projeto.size = (texto_width, texto_height)
        self.botao_projeto.pos = (botao_x, botao_y)

    def atualizar_imagem(self, *args):
        self.background.pos = self.pos
        self.background.size = self.size

    def voltar_tela_principal(self, instance):
        self.manager.current = 'tela_principal'

class TelaAudios(Screen):
    def __init__(self, **kwargs):
        super(TelaAudios, self).__init__(**kwargs)

        # Define a cor de fundo da tela como o azul especificado (#a3d7da)
        with self.canvas.before:
            Color(0.6392, 0.8431, 0.8549, 1)  # Valores RGB de #a3d7da
            self.rect = Rectangle(size=self.size, pos=self.pos)

        # Atualiza o retângulo quando o tamanho da tela é alterado
        self.bind(size=self.atualizar_retangulo, pos=self.atualizar_retangulo)

        layout = GridLayout(cols=1, padding=[25, 50], spacing=10, size_hint=(None, None), size=(300, 400), pos_hint={'center_x': 0.5, 'center_y': 0.5})
        self.add_widget(layout)

        # Adicionar os botões à tela de áudios
        botoes = ['Mindfulness', 'Hipnose']
        for texto in botoes:
            botao = Button(text=texto, size_hint=(None, None), size=(300, 50), 
                            background_normal='', background_color=(0.2, 0.8, 0.8, 1), color=(0, 0, 0, 1), font_size='15sp', halign='center')
            if texto == 'Mindfulness':
                botao.bind(on_press=self.abrir_tela_mindfullness)
            elif texto == 'Hipnose':
                botao.bind(on_press=self.abrir_tela_hipnose)
            layout.add_widget(botao)

        # Adiciona o botão para voltar à tela principal
        voltar_button = Button(text='Voltar à Tela Principal', size_hint=(None, None), size=(200, 50), pos_hint={'center_x': 0.5, 'center_y': 0.1}, 
                                  background_normal='', background_color=(0.2, 0.8, 0.8, 1), color=(0, 0, 0, 1), font_size='15sp', halign='center')
        voltar_button.bind(on_press=self.voltar_tela_principal)
        self.add_widget(voltar_button)

    def atualizar_retangulo(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def abrir_tela_mindfullness(self, instance):
        self.manager.current = 'tela_mindfullness'
   
    def abrir_tela_hipnose(self, instance):
        self.manager.current = 'tela_hipnose'

    def voltar_tela_principal(self, instance):
        self.manager.current = 'tela_principal'

class Mindfullness(Screen):
    def __init__(self, **kwargs):
        super(Mindfullness, self).__init__(**kwargs)

        # Define a cor de fundo da tela como o azul especificado (#a3d7da)
        with self.canvas.before:
            Color(0.6392, 0.8431, 0.8549, 1)  # Valores RGB de #a3d7da
            self.rect = Rectangle(size=self.size, pos=self.pos)

        # Atualiza o retângulo quando o tamanho da tela é alterado
        self.bind(size=self.atualizar_retangulo, pos=self.atualizar_retangulo)

        # Cria um layout vertical para os textos e botões
        layout = BoxLayout(orientation='vertical', size_hint=(None, None), size=(400, 400), pos_hint={'center_x': 0.5, 'center_y': 0.55})

        # Primeiro texto e botão para assistir ao primeiro vídeo no YouTube
        texto_video1 = "Andy Puddicombe: Tudo que é preciso são 10 minutos consciente"
        label1 = Label(text=texto_video1, size_hint=(None, None), size=(300, 50), color=(0, 0, 0, 1), pos_hint={'center_x': 0.5})
        layout.add_widget(label1)

        btn_assistir1 = Button(text="Assistir no YouTube", size_hint=(None, None), size=(200, 50), pos_hint={'center_x': 0.5}, 
                                background_normal='', background_color=(0.2, 0.8, 0.8, 1), color=(0, 0, 0, 1), font_size='15sp', halign='center')
        btn_assistir1.bind(on_press=lambda x: self.abrir_hiperligacao("https://www.youtube.com/watch?v=qzR62JJCMBQ"))
        layout.add_widget(btn_assistir1)

        # Segundo texto e botão para assistir ao segundo vídeo no YouTube
        texto_video2 = "Guided Mindfulness Meditation on Self-Love and Self-Worth"
        label2 = Label(text=texto_video2, size_hint=(None, None), size=(300, 50), color=(0, 0, 0, 1), pos_hint={'center_x': 0.5})
        layout.add_widget(label2)

        btn_assistir2 = Button(text="Assistir no YouTube", size_hint=(None, None), size=(200, 50), pos_hint={'center_x': 0.5}, 
                                background_normal='', background_color=(0.2, 0.8, 0.8, 1), color=(0, 0, 0, 1), font_size='15sp', halign='center')
        btn_assistir2.bind(on_press=lambda x: self.abrir_hiperligacao("https://www.youtube.com/watch?v=zzNmOEJUg-s"))
        layout.add_widget(btn_assistir2)

        # Primeiro texto e botão para assistir ao primeiro vídeo no YouTube
        texto_video1 = "Emoções Agitadas"
        label1 = Label(text=texto_video1, size_hint=(None, None), size=(300, 50), color=(0, 0, 0, 1), pos_hint={'center_x': 0.5})
        layout.add_widget(label1)

        btn_assistir1 = Button(text="Assistir no YouTube", size_hint=(None, None), size=(200, 50), pos_hint={'center_x': 0.5}, 
                                background_normal='', background_color=(0.2, 0.8, 0.8, 1), color=(0, 0, 0, 1), font_size='15sp', halign='center')
        btn_assistir1.bind(on_press=lambda x: self.abrir_hiperligacao("https://youtu.be/fEovJopklmk"))
        layout.add_widget(btn_assistir1)

        # Segundo texto e botão para assistir ao segundo vídeo no YouTube
        texto_video2 = "Meditação para iniciantes"
        label2 = Label(text=texto_video2, size_hint=(None, None), size=(300, 50), color=(0, 0, 0, 1), pos_hint={'center_x': 0.5})
        layout.add_widget(label2)

        btn_assistir2 = Button(text="Assistir no YouTube", size_hint=(None, None), size=(200, 50), pos_hint={'center_x': 0.5}, 
                                background_normal='', background_color=(0.2, 0.8, 0.8, 1), color=(0, 0, 0, 1), font_size='15sp', halign='center')
        btn_assistir2.bind(on_press=lambda x: self.abrir_hiperligacao("https://youtu.be/KQOAVZew5l8"))
        layout.add_widget(btn_assistir2)

        self.add_widget(layout)

        # Botão para voltar à tela anterior
        btn_voltar = Button(text="Voltar à Tela Audios",size_hint=(None, None), size=(200, 50), pos_hint={'center_x': 0.5, 'center_y': 0.1}, 
                                background_normal='', background_color=(0.2, 0.8, 0.8, 1), color=(0, 0, 0, 1), font_size='15sp', halign='center')
        btn_voltar.bind(on_press=self.voltar_tela_anterior)
        self.add_widget(btn_voltar)

    def abrir_hiperligacao(self, link):
        # Abre o link no navegador padrão
        webbrowser.open(link)
    
    def atualizar_retangulo(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def voltar_tela_anterior(self, instance):
        # Retorna à tela anterior
        self.manager.current = 'tela_audios'

class TelaHipnose(Screen):
    def __init__(self, **kwargs):
        super(TelaHipnose, self).__init__(**kwargs)

        # Define a cor de fundo da tela como o azul especificado (#a3d7da)
        with self.canvas.before:
            Color(0.6392, 0.8431, 0.8549, 1)  # Valores RGB de #a3d7da
            self.rect = Rectangle(size=self.size, pos=self.pos)

        # Atualiza o retângulo quando o tamanho da tela é alterado
        self.bind(size=self.atualizar_retangulo, pos=self.atualizar_retangulo)

        layout = GridLayout(cols=1, padding=[25, 50], spacing=10, size_hint=(None, None), size=(300, 400),
                                  pos_hint={'center_x': 0.5, 'center_y': 0.5})
        self.add_widget(layout)

        self.audio_button_autohipnose = Button(text='Reproduzir Autohipnose', size_hint=(None, None), size=(300, 50), 
                            background_normal='', background_color=(0.2, 0.8, 0.8, 1), color=(0, 0, 0, 1), font_size='15sp', halign='center')
        self.audio_button_autohipnose.bind(on_press=self.toggle_reproducao_autohipnose)
        layout.add_widget(self.audio_button_autohipnose)

        self.audio_button_espelho = Button(text='Reproduzir Espelho', size_hint=(None, None), size=(300, 50), 
                            background_normal='', background_color=(0.2, 0.8, 0.8, 1), color=(0, 0, 0, 1), font_size='15sp', halign='center')
        self.audio_button_espelho.bind(on_press=self.toggle_reproducao_espelho)
        layout.add_widget(self.audio_button_espelho)

        voltar_button = Button(text='Voltar à Tela de Áudios', size_hint=(None, None), size=(200, 50), pos_hint={'center_x': 0.5, 'center_y': 0.1}, 
                               background_normal='', background_color=(0.2, 0.8, 0.8, 1), color=(0, 0, 0, 1), font_size='15sp', halign='center')
        voltar_button.bind(on_press=self.voltar_tela_audios)
        self.add_widget(voltar_button)

        self.estado_reproducao_autohipnose = 'pausado'  # Pode ser 'pausado', 'reproduzindo' ou 'parado'
        self.estado_reproducao_espelho = 'pausado'

        self.inicializar_audio()

    def atualizar_retangulo(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def inicializar_audio(self):
        pygame.mixer.init()
        self.caminho_autohipnose = os.path.join(caminho_app_aurora, 'autohipnose.mp3')
        self.caminho_espelho = os.path.join(caminho_app_aurora, 'ESPELHO.mp3')
        pygame.mixer.music.load(self.caminho_autohipnose)
        pygame.mixer.music.set_endevent(pygame.USEREVENT)

        self.sound_espelho = pygame.mixer.Sound(self.caminho_espelho)

    def toggle_reproducao_autohipnose(self, instance):
        if self.estado_reproducao_autohipnose == 'pausado':
            self.reproduzir_audio_autohipnose()
        elif self.estado_reproducao_autohipnose == 'reproduzindo':
            self.pausar_audio_autohipnose()
        elif self.estado_reproducao_autohipnose == 'parado':
            self.reproduzir_audio_autohipnose()

    def toggle_reproducao_espelho(self, instance):
        if self.estado_reproducao_espelho == 'pausado':
            self.reproduzir_audio_espelho()
        elif self.estado_reproducao_espelho == 'reproduzindo':
            self.pausar_audio_espelho()
        elif self.estado_reproducao_espelho == 'parado':
            self.reproduzir_audio_espelho()

    def reproduzir_audio_autohipnose(self):
        pygame.mixer.music.play()
        self.audio_button_autohipnose.text = 'Pausar Autohipnose'
        self.estado_reproducao_autohipnose = 'reproduzindo'

    def pausar_audio_autohipnose(self):
        pygame.mixer.music.pause()
        self.audio_button_autohipnose.text = 'Reproduzir Autohipnose'
        self.estado_reproducao_autohipnose = 'pausado'

    def reproduzir_audio_espelho(self):
        self.sound_espelho.play()
        self.audio_button_espelho.text = 'Pausar Espelho'
        self.estado_reproducao_espelho = 'reproduzindo'

    def pausar_audio_espelho(self):
        self.sound_espelho.stop()
        self.audio_button_espelho.text = 'Reproduzir Espelho'
        self.estado_reproducao_espelho = 'pausado'

    def voltar_tela_audios(self, instance):
        pygame.mixer.music.stop()
        self.sound_espelho.stop()
        self.manager.current = 'tela_audios'
        self.estado_reproducao_autohipnose = 'parado'
        self.estado_reproducao_espelho = 'parado'

class MySpinnerOption(SpinnerOption):
    pass

class TelaMarcacaoDeConsultas(Screen):
    def __init__(self, **kwargs):
        super(TelaMarcacaoDeConsultas, self).__init__(**kwargs)
        self.title = 'Marcação de Consultas'
        self.selected_date = None  
        self.selected_specialty = None  
        self.selected_hour = None  

        self.current_date = datetime.now()

        with self.canvas.before:
            Color(0.6392, 0.8431, 0.8549, 1)  
            self.rect = Rectangle(size=self.size, pos=self.pos)

        self.bind(size=self.atualizar_retangulo, pos=self.atualizar_retangulo)

        layout = BoxLayout(orientation='vertical')
        self.add_widget(layout)

        header = BoxLayout(size_hint_y=None, height=50)
        btn_prev_month = Button(text='<', on_press=self.prev_month,
                                background_normal='', background_color=(0.2, 0.8, 0.8, 1), color=(0, 0, 0, 1),
                                font_size='15sp', halign='center')
        btn_next_month = Button(text='>', on_press=self.next_month,
                                background_normal='', background_color=(0.2, 0.8, 0.8, 1), color=(0, 0, 0, 1),
                                font_size='15sp', halign='center')
        self.lbl_current_month = Label(text=self.current_month(), halign='center', valign='middle', color=(0, 0, 0, 1))
        header.add_widget(btn_prev_month)
        header.add_widget(self.lbl_current_month)
        header.add_widget(btn_next_month)
        layout.add_widget(header)

        self.calendar_layout = GridLayout(cols=7, spacing=5, size_hint_y=0.9)
        self.populate_calendar()
        calendar_scroll = ScrollView()
        calendar_scroll.add_widget(self.calendar_layout)
        layout.add_widget(calendar_scroll)

        self.specialties_dropdown = Spinner(
            text='Selecione a Especialidade',
            values=['Psiquiatria', 'Psicologia Clínica', 'Psicologia da Educação', 'Neurologia',
                    'Suporte de Grupo Online', 'Emergência e Crise', 'Nutrição e Saúde Física'],
            size_hint_y=None,
            height=50, background_normal='', background_color=(0.2, 0.8, 0.8, 1), color=(0, 0, 0, 1),
            option_cls=MySpinnerOption
        )
        self.specialties_dropdown.bind(text=self.on_specialty_selected)
        layout.add_widget(self.specialties_dropdown)

        self.mark_consultation_button = Button(text="Marcar Consulta", size_hint_y=None, height=50, disabled=True,
                                               background_normal='', background_color=(0.2, 0.8, 0.8, 1),
                                               color=(0, 0, 0, 1), font_size='15sp', halign='center')
        self.mark_consultation_button.bind(on_press=self.mark_consultation)
        layout.add_widget(self.mark_consultation_button)

        self.hours_dropdown = Spinner(
            text='Selecionar Hora',
            values=['9:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00', '19:00'],
            size_hint_y=None,
            height=50, background_normal='', background_color=(0.2, 0.8, 0.8, 1), color=(0, 0, 0, 1),
            option_cls=MySpinnerOption
        )
        self.hours_dropdown.bind(text=self.on_hour_selected)
        layout.add_widget(self.hours_dropdown)

        back_button = Button(text="Voltar à tela principal", size_hint_y=None, height=50,
                             background_normal='', background_color=(0.2, 0.8, 0.8, 1), color=(0, 0, 0, 1),
                             font_size='15sp', halign='center')
        back_button.bind(on_press=self.voltar_a_tela_principal)
        layout.add_widget(back_button)

    def current_month(self):
        return self.current_date.strftime("%B %Y")

    def populate_calendar(self):
        self.calendar_layout.clear_widgets()

        days = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sab']
        for day in days:
            self.calendar_layout.add_widget(Label(text=day, halign='center', color=(0, 0, 0, 1)))

        first_day_of_month = datetime(self.current_date.year, self.current_date.month, 1)
        days_in_month = calendar.monthrange(self.current_date.year, self.current_date.month)[1]

        for day in range(1, days_in_month + 1):
            date = datetime(self.current_date.year, self.current_date.month, day)
            btn = Button(text=str(day), size_hint_y=None, height=50,
                         disabled=date < datetime.now() or date.month != self.current_date.month,
                         background_normal='', background_color=(0.2, 0.8, 0.8, 1), color=(0, 0, 0, 1),
                         font_size='15sp', halign='center')
            btn.bind(on_press=self.select_date)
            self.calendar_layout.add_widget(btn)

    def select_date(self, instance):
        self.selected_date = instance.text
        self.mark_consultation_button.disabled = False

    def on_specialty_selected(self, spinner, text):
        self.selected_specialty = text

    def on_hour_selected(self, spinner, text):
        self.selected_hour = text

    def prev_month(self, instance):
        self.current_date -= relativedelta(months=1)
        self.lbl_current_month.text = self.current_month()
        self.populate_calendar()

    def next_month(self, instance):
        self.current_date += relativedelta(months=1)
        self.lbl_current_month.text = self.current_month()
        self.populate_calendar()

    def mark_consultation(self, instance):
        if self.selected_date and self.selected_specialty and self.selected_hour:
            selected_date = f"{self.selected_date} {self.current_month()} às {self.selected_hour}"
            popup = Popup(title='Consulta Marcada',
                        content=Label(text=f'Consulta marcada para {self.selected_specialty} em {selected_date}'),
                        size_hint=(None, None), size=(600, 200),
                        background_color=(0.2, 0.8, 0.8, 1))  # Define o fundo azul
            popup.open()
        else:
            if not self.selected_date:
                message = 'Selecione uma data antes de marcar a consulta.'
            elif not self.selected_hour:
                message = 'Selecione uma hora antes de marcar a consulta.'
            else:
                message = 'Selecione uma especialidade antes de marcar a consulta.'
            popup = Popup(title='Erro', content=Label(text=message),
                        size_hint=(None, None), size=(600, 200),
                        background_color=(0.2, 0.8, 0.8, 1))  # Define o fundo azul
            popup.open()
    
    def atualizar_retangulo(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def voltar_a_tela_principal(self, instance):
        self.manager.current = 'tela_principal'

class TelaEspecialidadesMedicas(Screen):
    def __init__(self, **kwargs):
        super(TelaEspecialidadesMedicas, self).__init__(**kwargs)
        self.adicionar_interface()

    def adicionar_interface(self):
        # Define a cor de fundo da tela como o azul especificado (#a3d7da)
        with self.canvas.before:
            Color(0.6392, 0.8431, 0.8549, 1)  # Valores RGB de #a3d7da
            self.rect = Rectangle(size=self.size, pos=self.pos)

        # Atualiza o retângulo quando o tamanho da tela é alterado
        self.bind(size=self.atualizar_retangulo, pos=self.atualizar_retangulo)

        layout = GridLayout(cols=1, padding=[25, 50], spacing=10, size_hint=(None, None), size=(300, 400), pos_hint={'center_x': 0.5, 'center_y': 0.6})
        self.add_widget(layout)

        # Adicionar os botões das especialidades médicas
        especialidades = ['Psiquiatria', 'Psicologia Clínica','Psicologia da Educação', 'Neurologia', 'Forum', 'Emergência e Crise', 'Nutrição e Saúde Física']
        for especialidade in especialidades:
            botao_especialidade = Button(text=especialidade, size_hint=(None, None), size=(300, 50),
                                background_normal='', background_color=(0.2, 0.8, 0.8, 1), color=(0, 0, 0, 1), font_size='15sp', halign='center')
            botao_especialidade.bind(on_press=lambda event, especialidade=especialidade: self.abrir_tela_especialidade(especialidade))
            layout.add_widget(botao_especialidade)

        # Adiciona o botão para voltar à tela principal
        voltar_button = Button(text='Voltar à Tela Principal', size_hint=(None, None), size=(200, 50), pos_hint={'center_x': 0.53, 'center_y': 0.1}, 
                                background_normal='', background_color=(0.2, 0.8, 0.8, 1), color=(0, 0, 0, 1), font_size='15sp', halign='center')
        voltar_button.bind(on_press=self.voltar_tela_principal)
        self.add_widget(voltar_button)

    def atualizar_retangulo(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def abrir_tela_especialidade(self, especialidade):
        # Criar e adicionar uma nova tela para a especialidade selecionada
        nova_tela = None
        if especialidade == 'Psiquiatria':
            nova_tela = TelaPsiquiatria(name='tela_psiquiatria')
        elif especialidade == 'Psicologia Clínica':
            nova_tela = TelaPsicologia(name='tela_psicologia')
        elif especialidade == 'Psicologia da Educação':
            nova_tela = TelaPsicologiaEducacao(name='tela_psicologiaeducacao')
        elif especialidade == 'Forum':
            nova_tela = TelaForum(name='tela_Forum')
        elif especialidade == 'Neurologia':
            nova_tela = TelaNeurologia(name='tela_neurologia')
        elif especialidade == 'Emergência e Crise':
            nova_tela = TelaEmergenciaeCrise(name='tela_emergenciaecrise')
        elif especialidade == 'Nutrição e Saúde Física':
            nova_tela = TelaNSF(name='tela_nutricao')
        # Adicione mais condições conforme necessário para outras especialidades
        if nova_tela:
            self.manager.add_widget(nova_tela)
            # Mudar para a nova tela
            self.manager.current = nova_tela.name
            
    def voltar_tela_principal(self, instance):
        self.manager.current = 'tela_principal'

class TelaParcerias(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.carregar_imagem()
        Window.bind(on_resize=self.atualizar_imagem)

    # Carrega a imagem de fundo e adiciona o texto
    def carregar_imagem(self):
        with self.canvas:
            # Carrega a imagem de fundo
            self.background = Rectangle(source='par.png',
                                    size=Window.size, pos=self.pos)

        # Adiciona o texto da especialidade selecionada
        label_parceria = ("[b]Parcerias: [/b]\n\n"
                         "[b]EmotiCare:[/b] Uma rede colaborativa que oferece cuidado emocional abrangente, conectando indivíduos a profissionais qualificados e recursos eficazes para o gerenciamento de emoções.\n\n"
                         "[b]InnerStrength:[/b]Uma colaboração dedicada a fortalecer a força interior dos participantes, fornecendo ferramentas e apoio para cultivar resiliência e autoconfiança.\n\n"
                         "[b]PsycheSync:[/b]Uma coalizão que visa sincronizar mente e espírito, fornecendo acesso a práticas e recursos que promovem a harmonia mental e o bem-estar holístico.\n\n"
                         "[b]Calm Connections:[/b] Parceria com uma plataforma de bem-estar para oferecer conteúdo relaxante e técnicas de gestão do stresse.\n\n"
                         "[b]Balance Boost:[/b] Parceria com marcas de estilo de vida saudável para integrar recursos de nutrição e exercício físico à aplicação.")

        self.label_parceria = Button(text= label_parceria, size_hint=(None, None), pos_hint={'center_x': 0.5, 'center_y': 0.5}, markup=True,
                                    background_normal='', background_color=(1, 1, 1, 0.6), color=(0, 0, 0, 1),
                                    font_size='15sp', halign='center')
        self.label_parceria.bind(size=self.atualizar_interface)
        self.label_parceria.bind(texture_size=self.atualizar_interface)
        self.add_widget(self.label_parceria)

        # Adiciona o botão para voltar à tela principal
        voltar_button = Button(text='Voltar à Tela Principal', size_hint=(None, None), size=(300, 50), pos_hint={'center_x': 0.5, 'center_y': 0.1}, 
                                background_normal='', background_color=(0, 0.5608, 0.2235, 0.7), color=(0, 0, 0, 1), font_size='15sp', halign='center')
        voltar_button.bind(on_press=self.voltar_tela_principal)
        self.add_widget(voltar_button)

    def atualizar_imagem(self, instance, width, height):
        self.background.size = width, height

    def atualizar_interface(self, *args):
        self.label_parceria.text_size = (Window.width, None)
        texto_width, texto_height = self.label_parceria.texture_size  # Obtém o tamanho do texto
        texto_x, texto_y = self.label_parceria.pos  # Obtém a posição do texto

        # Calcula a posição do botão para alinhá-lo com o texto e centralizá-lo
        botao_x = texto_x + (self.label_parceria.width - texto_width) / 2  # Centraliza o botão horizontalmente
        botao_y = texto_y - texto_height  # Move o botão para baixo do texto
        self.label_parceria.size = (texto_width, texto_height)
        self.label_parceria.pos = (botao_x, botao_y)

    def voltar_tela_principal(self, instance):
        # Voltar para a tela principal
        self.manager.current = 'tela_principal'
        
class TelaPsiquiatria(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.carregar_imagem()
        Window.bind(on_resize=self.atualizar_imagem)

    # Carrega a imagem de fundo e adiciona o texto
    def carregar_imagem(self):
        with self.canvas:
            # Carrega a imagem de fundo
            self.background = Rectangle(source='psiquiatria.png',
                                    size=Window.size, pos=self.pos)

        # Adiciona o texto da especialidade selecionada
        label_psiquiatria = ("[b]Psiquiatria: [/b]\n"
                         "É uma especialidade médica que se concentra no diagnóstico, tratamento e prevenção de distúrbios mentais.\n"
                         "Os psiquiatras são médicos que podem prescrever medicamentos e realizar terapias para tratar uma variedade de\n"
                         "condições, como depressão, ansiedade, transtorno bipolar, esquizofrenia, entre outras.\n\n"
                         "[b]Pedopsiquiatria: [/b]\n"
                         "Especialidade médica que se dedica à prevenção, diagnóstico e tratamento de perturbações psicológicas \n"
                         "com início na idade pediátrica.")

        self.label_psiquiatria = Button(text= label_psiquiatria, size_hint=(None, None), pos_hint={'center_x': 0.5, 'center_y': 0.5}, markup=True,
                                    background_normal='', background_color=(1, 1, 1, 0.6), color=(0, 0, 0, 1),
                                    font_size='15sp', halign='center')
        self.label_psiquiatria.bind(size=self.atualizar_interface)
        self.label_psiquiatria.bind(texture_size=self.atualizar_interface)
        self.add_widget(self.label_psiquiatria)

        # Adiciona o botão para voltar à tela especialidades médicas
        voltar_button = Button(text='Voltar à Tela Especialidades Médicas', size_hint=(None, None), size=(300, 50), pos_hint={'center_x': 0.5, 'center_y': 0.1}, 
                                background_normal='', background_color=(0, 0.5608, 0.2235, 0.7), color=(0, 0, 0, 1), font_size='15sp', halign='center')
        voltar_button.bind(on_press=self.voltar_tela_especialidades)
        self.add_widget(voltar_button)

    def atualizar_imagem(self, instance, width, height):
        self.background.size = width, height

    def atualizar_interface(self, *args):
        self.label_psiquiatria.text_size = (Window.width, None)
        texto_width, texto_height = self.label_psiquiatria.texture_size  # Obtém o tamanho do texto
        texto_x, texto_y = self.label_psiquiatria.pos  # Obtém a posição do texto
        # Calcula a posição do botão para alinhá-lo com o texto e centralizá-lo
        botao_x = texto_x + (self.label_psiquiatria.width - texto_width) / 2  # Centraliza o botão horizontalmente
        botao_y = texto_y - texto_height  # Move o botão para baixo do texto
        self.label_psiquiatria.size = (texto_width, texto_height)
        self.label_psiquiatria.pos = (botao_x, botao_y)

    def voltar_tela_especialidades(self, instance):
        # Voltar para a tela de especialidades médicas
        self.manager.current = 'tela_especialidades_medicas'

class TelaPsicologia(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.carregar_imagem()
        Window.bind(on_resize=self.atualizar_imagem)

    # Carrega a imagem de fundo e adiciona o texto
    def carregar_imagem(self):
        with self.canvas:
            # Carrega a imagem de fundo
            self.background = Rectangle(source='psicologia.jpg',
                                    size=Window.size, pos=self.pos)

        # Adiciona o texto da especialidade selecionada
        label_psicologia = ("[b]Psicologia Clínica: [/b]\n\n"
                         "Os psicólogos clínicos são profissionais de saúde mental que avaliam, diagnosticam e tratam distúrbios psicológicos \n"
                         "e emocionais. Eles utilizam abordagens terapêuticas baseadas em evidências para ajudar os pacientes a lidar com \n"
                         "problemas como transtornos de humor, traumas, problemas de relacionamento, entre outros.\n"
                         "[b]Diferentes abordagens: [/b]")

        self.label_psicologia = Button(text=label_psicologia, size_hint=(None, None), pos_hint={'center_x': 0.5, 'center_y': 0.9}, markup=True,
                                    background_normal='', background_color=(1, 1, 1, 0.5), color=(0, 0, 0, 1),
                                    font_size='15sp', halign='center')
        self.label_psicologia.bind(size=self.atualizar_interface)
        self.label_psicologia.bind(texture_size=self.atualizar_interface)
        self.add_widget(self.label_psicologia)

        # Adiciona um layout vertical para os botões das abordagens
        layout = BoxLayout(orientation='vertical', spacing=5, size_hint=(None, None), size=(300, 30), pos_hint={'center_x': 0.5, 'center_y': 0.5})
        layout.bind(minimum_height=layout.setter('height'))
        self.add_widget(layout)

        # Adicionar os botões das abordagens da Psicologia
        abordagens = ['Psicoterapia', 'Psico-Oncologia','Neuropsicologia', 'Terapia Cognitivo-Comportamental (TCC)', 'Terapia Familiar e Terapia de Casais', 
                      'Psicologia do Desenvolvimento', 'Aconselhamento em Dependência Química', 'Educação Parental e Orientação Parental', 
                      'Terapia Expressiva e Arteterapia', 'Terapia Sexual e Saúde Sexual']
        for abordagem in abordagens:
            botao_abordagem = Button(text=abordagem, size_hint=(None, None), size=(300, 30), 
                                background_normal='', background_color=(1, 0.647, 0, 0.7), color=(0, 0, 0, 1), font_size='15sp', halign='center')
            botao_abordagem.bind(on_press=lambda event, abordagem=abordagem: self.abrir_tela_abordagem(abordagem))
            layout.add_widget(botao_abordagem)

        # Adiciona o botão para voltar à tela especialidades médicas
        voltar_button = Button(text='Voltar à Tela Especialidades Médicas', size_hint=(None, None), size=(300, 50), pos_hint={'center_x': 0.5, 'center_y': 0.1}, 
                                background_normal='', background_color=(1, 0.647, 0, 1), color=(0, 0, 0, 1), font_size='15sp', halign='center')
        voltar_button.bind(on_press=self.voltar_tela_especialidades)
        self.add_widget(voltar_button)

    def atualizar_imagem(self, instance, width, height):
        self.background.size = width, height

    def atualizar_interface(self, *args):
        self.label_psicologia.text_size = (Window.width, None)
        texto_width, texto_height = self.label_psicologia.texture_size  # Obtém o tamanho do texto
        texto_x, texto_y = self.label_psicologia.pos  # Obtém a posição do texto
        # Calcula a posição do botão para alinhá-lo com o texto e centralizá-lo
        botao_x = texto_x + (self.label_psicologia.width - texto_width) / 2  # Centraliza o botão horizontalmente
        botao_y = texto_y - texto_height  # Move o botão para baixo do texto
        self.label_psicologia.size = (texto_width, texto_height)
        self.label_psicologia.pos = (botao_x, botao_y)

    def abrir_tela_abordagem(self, abordagem):
        if abordagem == 'Psicoterapia':
            # Verifica se a tela já existe no gerenciador de tela
            if 'tela_psicoterapia' not in self.manager.screen_names:
                # Se não existir, cria e adiciona uma nova tela TelaPsicoterapia ao gerenciador de tela
                nova_tela = TelaPsicoterapia(name='tela_psicoterapia')
                self.manager.add_widget(nova_tela)

            # Muda para a tela 'tela_psicoterapia'
            self.manager.current = 'tela_psicoterapia'
        elif abordagem == 'Psico-Oncologia':
            # Verifica se a tela já existe no gerenciador de tela
            if 'tela_psico_oncologia' not in self.manager.screen_names:
                # Se não existir, cria e adiciona uma nova tela TelaPsicoOncologia ao gerenciador de tela
                nova_tela = TelaPsicoOncologia(name='tela_psico_oncologia')
                self.manager.add_widget(nova_tela)

            # Muda para a tela 'tela_psico_oncologia'
            self.manager.current = 'tela_psico_oncologia'

        elif abordagem == 'Neuropsicologia':
            # Verifica se a tela já existe no gerenciador de tela
            if 'tela_neuropsicologia' not in self.manager.screen_names:
                # Se não existir, cria e adiciona uma nova tela TelaNeuropsicologia ao gerenciador de tela
                nova_tela = TelaNeuropsicologia(name='tela_neuropsicologia')
                self.manager.add_widget(nova_tela)

            # Muda para a tela 'tela_neuropsicologia'
            self.manager.current = 'tela_neuropsicologia'

        elif abordagem == 'Terapia Cognitivo-Comportamental (TCC)':
            # Verifica se a tela já existe no gerenciador de tela
            if 'tela_tcc' not in self.manager.screen_names:
                # Se não existir, cria e adiciona uma nova tela TelaTCC ao gerenciador de tela
                nova_tela = TelaTCC(name='tela_tcc')
                self.manager.add_widget(nova_tela)

            # Muda para a tela 'tela_tcc'
            self.manager.current = 'tela_tcc'

        elif abordagem == 'Terapia Familiar e Terapia de Casais':
            # Verifica se a tela já existe no gerenciador de tela
            if 'tela_tftc' not in self.manager.screen_names:
                # Se não existir, cria e adiciona uma nova tela TelaTFTC ao gerenciador de tela
                nova_tela = TelaTFTC(name='tela_tftc')
                self.manager.add_widget(nova_tela)

            # Muda para a tela 'tela_tftc'
            self.manager.current = 'tela_tftc'
        
        elif abordagem == 'Psicologia do Desenvolvimento':
            # Verifica se a tela já existe no gerenciador de tela
            if 'tela_psicologia_desenvolvimento' not in self.manager.screen_names:
                # Se não existir, cria e adiciona uma nova tela TelaPsicologia_Desenvolvimento ao gerenciador de tela
                nova_tela = TelaPsicologia_Desenvolvimento(name='tela_psicologia_desenvolvimento')
                self.manager.add_widget(nova_tela)

            # Muda para a tela 'tela_psicologia_desenvolvimento'
            self.manager.current = 'tela_psicologia_desenvolvimento'

        elif abordagem == 'Aconselhamento em Dependência Química':
            # Verifica se a tela já existe no gerenciador de tela
            if 'tela_adq' not in self.manager.screen_names:
                # Se não existir, cria e adiciona uma nova tela TelaADQ ao gerenciador de tela
                nova_tela = TelaADQ(name='tela_adq')
                self.manager.add_widget(nova_tela)

            # Muda para a tela 'tela_adq'
            self.manager.current = 'tela_adq'

        elif abordagem == 'Educação Parental e Orientação Parental':
            # Verifica se a tela já existe no gerenciador de tela
            if 'tela_epop' not in self.manager.screen_names:
                # Se não existir, cria e adiciona uma nova tela TelaEPOP ao gerenciador de tela
                nova_tela = TelaEPOP(name='tela_epop')
                self.manager.add_widget(nova_tela)

            # Muda para a tela 'tela_epop'
            self.manager.current = 'tela_epop'

        elif abordagem == 'Terapia Expressiva e Arteterapia':
            # Verifica se a tela já existe no gerenciador de tela
            if 'tela_arteterapia' not in self.manager.screen_names:
                # Se não existir, cria e adiciona uma nova tela TelaArteterapia ao gerenciador de tela
                nova_tela = TelaArteterapia(name='tela_arteterapia')
                self.manager.add_widget(nova_tela)

            # Muda para a tela 'tela_arteterapia'
            self.manager.current = 'tela_arteterapia'

        elif abordagem == 'Terapia Sexual e Saúde Sexual':
            # Verifica se a tela já existe no gerenciador de tela
            if 'tela_tsss' not in self.manager.screen_names:
                # Se não existir, cria e adiciona uma nova tela TelaTSSS ao gerenciador de tela
                nova_tela = TelaTSSS(name='tela_tsss')
                self.manager.add_widget(nova_tela)

            # Muda para a tela 'tela_tsss'
            self.manager.current = 'tela_tsss'

    def voltar_tela_especialidades(self, instance):
        # Voltar para a tela de especialidades médicas
        self.manager.current = 'tela_especialidades_medicas'

class TelaPsicoterapia(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.carregar_imagem()
        Window.bind(on_resize=self.atualizar_imagem)

    # Carrega a imagem de fundo e adiciona o texto
    def carregar_imagem(self):
        with self.canvas:
            # Carrega a imagem de fundo
            self.background = Rectangle(source='psicoterapia.jpg',
                                    size=Window.size, pos=self.pos)

        # Adiciona o texto da especialidade selecionada
        label_psicoterapia = ("[b]Psicoterapia: [/b]\n\n"
                              "A psicoterapia é uma prática terapêutica comum dentro da saúde mental. Envolve sessões regulares com um \n"
                              "terapeuta para explorar pensamentos, emoções e comportamentos, com o objetivo de promover o bem-estar \n"
                              "emocional e resolver problemas psicológicos.")
                              

        self.label_psicoterapia = Button(text=label_psicoterapia, size_hint=(None, None), pos_hint={'center_x': 0.5, 'center_y': 0.5}, markup=True,
                                    background_normal='', background_color=(1, 1, 1, 0.5), color=(0, 0, 0, 1),
                                    font_size='15sp', halign='center')
        self.label_psicoterapia.bind(size=self.atualizar_interface)
        self.label_psicoterapia.bind(texture_size=self.atualizar_interface)
        self.add_widget(self.label_psicoterapia)

        # Adiciona o botão para voltar à tela especialidades médicas
        voltar_button = Button(text='Voltar à Tela Psicologia', size_hint=(None, None), size=(300, 50), pos_hint={'center_x': 0.5, 'center_y': 0.1}, 
                                background_normal='', background_color=(1, 0.647, 0, 0.7), color=(0, 0, 0, 1), font_size='15sp', halign='center')
        voltar_button.bind(on_press=self.voltar_tela_psicologia)
        self.add_widget(voltar_button)
    
    def atualizar_imagem(self, instance, width, height):
        self.background.size = width, height

    def atualizar_interface(self, *args):
        self.label_psicoterapia.text_size = (Window.width, None)
        texto_width, texto_height = self.label_psicoterapia.texture_size  # Obtém o tamanho do texto
        texto_x, texto_y = self.label_psicoterapia.pos  # Obtém a posição do texto
        # Calcula a posição do botão para alinhá-lo com o texto e centralizá-lo
        botao_x = texto_x + (self.label_psicoterapia.width - texto_width) / 2  # Centraliza o botão horizontalmente
        botao_y = texto_y - texto_height  # Move o botão para baixo do texto
        self.label_psicoterapia.size = (texto_width, texto_height)
        self.label_psicoterapia.pos = (botao_x, botao_y)

    def voltar_tela_psicologia(self, instance):
        # Voltar para a tela de psicologia
        self.manager.current = 'tela_psicologia'

class TelaPsicoOncologia(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.carregar_imagem()
        Window.bind(on_resize=self.atualizar_imagem)

    # Carrega a imagem de fundo e adiciona o texto
    def carregar_imagem(self):
        with self.canvas:
            # Carrega a imagem de fundo
            self.background = Rectangle(source='psico_oncologia.jpg',
                                    size=Window.size, pos=self.pos)

        # Adiciona o texto da especialidade selecionada
        label_psico_oncologia = ("[b]Psico-Oncologia: [/b]\n\n"
                              "Especialidade com enfoque na doença oncológica quer na sua dimensão física, psicológica, \n"
                              "social como comportamental, com foco na compreensão do impacto psicoemocional do diagnóstico\n"
                              "de cancro, dos protocolos terapêuticos e do prognóstico no doente, nas famílias/cuidadores e \n"
                              "nos profissionais de saúde em todas as fases da doença.")
                              

        self.label_psico_oncologia = Button(text=label_psico_oncologia, size_hint=(None, None), pos_hint={'center_x': 0.5, 'center_y': 0.5}, markup=True,
                                    background_normal='', background_color=(1, 1, 1, 0.5), color=(0, 0, 0, 1),
                                    font_size='15sp', halign='center')
        self.label_psico_oncologia.bind(size=self.atualizar_interface)
        self.label_psico_oncologia.bind(texture_size=self.atualizar_interface)
        self.add_widget(self.label_psico_oncologia)

        # Adiciona o botão para voltar à tela especialidades médicas
        voltar_button = Button(text='Voltar à Tela Psicologia', size_hint=(None, None), size=(300, 50), pos_hint={'center_x': 0.5, 'center_y': 0.1}, 
                                background_normal='', background_color=(1, 0.647, 0, 0.7), color=(0, 0, 0, 1), font_size='15sp', halign='center')
        voltar_button.bind(on_press=self.voltar_tela_psicologia)
        self.add_widget(voltar_button)
    
    def atualizar_imagem(self, instance, width, height):
        self.background.size = width, height

    def atualizar_interface(self, *args):
        self.label_psico_oncologia.text_size = (Window.width, None)
        texto_width, texto_height = self.label_psico_oncologia.texture_size  # Obtém o tamanho do texto
        texto_x, texto_y = self.label_psico_oncologia.pos  # Obtém a posição do texto
        # Calcula a posição do botão para alinhá-lo com o texto e centralizá-lo
        botao_x = texto_x + (self.label_psico_oncologia.width - texto_width) / 2  # Centraliza o botão horizontalmente
        botao_y = texto_y - texto_height  # Move o botão para baixo do texto
        self.label_psico_oncologia.size = (texto_width, texto_height)
        self.label_psico_oncologia.pos = (botao_x, botao_y)

    def voltar_tela_psicologia(self, instance):
        # Voltar para a tela de psicologia
        self.manager.current = 'tela_psicologia'

class TelaNeuropsicologia(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.carregar_imagem()
        Window.bind(on_resize=self.atualizar_imagem)

    # Carrega a imagem de fundo e adiciona o texto
    def carregar_imagem(self):
        with self.canvas:
            # Carrega a imagem de fundo
            self.background = Rectangle(source='neuropsicologia.jpg',
                                    size=Window.size, pos=self.pos)

        # Adiciona o texto da especialidade selecionada
        label_neuropsicologia = ("[b]Neuropsicologia: [/b]\n\n"
                              "Esta especialidade se concentra no estudo das relações entre o cérebro e o comportamento humano.\n"
                              "Neuropsicólogos avaliam e tratam distúrbios neurológicos que afetam o funcionamento cognitivo e emocional,\n"
                              "como lesões cerebrais traumáticas, demência, doença de Alzheimer e distúrbios do desenvolvimento.")
                              

        self.label_neuropsicologia = Button(text=label_neuropsicologia, size_hint=(None, None), pos_hint={'center_x': 0.5, 'center_y': 0.5}, markup=True,
                                    background_normal='', background_color=(1, 1, 1, 0.7), color=(0, 0, 0, 1),
                                    font_size='15sp', halign='center')
        self.label_neuropsicologia.bind(size=self.atualizar_interface)
        self.label_neuropsicologia.bind(texture_size=self.atualizar_interface)
        self.add_widget(self.label_neuropsicologia)

        # Adiciona o botão para voltar à tela especialidades médicas
        voltar_button = Button(text='Voltar à Tela Psicologia', size_hint=(None, None), size=(300, 50), pos_hint={'center_x': 0.5, 'center_y': 0.1}, 
                                background_normal='', background_color=(1, 0.647, 0, 0.7), color=(0, 0, 0, 1), font_size='15sp', halign='center')
        voltar_button.bind(on_press=self.voltar_tela_psicologia)
        self.add_widget(voltar_button)
    
    def atualizar_imagem(self, instance, width, height):
        self.background.size = width, height

    def atualizar_interface(self, *args):
        self.label_neuropsicologia.text_size = (Window.width, None)
        texto_width, texto_height = self.label_neuropsicologia.texture_size  # Obtém o tamanho do texto
        texto_x, texto_y = self.label_neuropsicologia.pos  # Obtém a posição do texto
        # Calcula a posição do botão para alinhá-lo com o texto e centralizá-lo
        botao_x = texto_x + (self.label_neuropsicologia.width - texto_width) / 2  # Centraliza o botão horizontalmente
        botao_y = texto_y - texto_height  # Move o botão para baixo do texto
        self.label_neuropsicologia.size = (texto_width, texto_height)
        self.label_neuropsicologia.pos = (botao_x, botao_y)


    def voltar_tela_psicologia(self, instance):
        # Voltar para a tela de psicologia
        self.manager.current = 'tela_psicologia'

class TelaTCC(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.carregar_imagem()
        Window.bind(on_resize=self.atualizar_imagem)

    # Carrega a imagem de fundo e adiciona o texto
    def carregar_imagem(self):
        with self.canvas:
            # Carrega a imagem de fundo
            self.background = Rectangle(source='tcc.jpg',
                                    size=Window.size, pos=self.pos)

        # Adiciona o texto da especialidade selecionada
        label_tcc = ("[b]Terapia Cognitivo-Comportamental (TCC): [/b]\n\n"
                    "A TCC é uma abordagem terapêutica amplamente utilizada que se concentra na identificação e modificação\n"
                    "de padrões de pensamento e comportamento negativos. É eficaz no tratamento de uma variedade de\n"
                    "distúrbios, incluindo depressão, ansiedade, transtornos alimentares e transtorno obsessivo-compulsivo.")
                              

        self.label_tcc = Button(text=label_tcc, size_hint=(None, None), pos_hint={'center_x': 0.5, 'center_y': 0.5}, markup=True,
                                    background_normal='', background_color=(1, 1, 1, 0.7), color=(0, 0, 0, 1),
                                    font_size='15sp', halign='center')
        self.label_tcc.bind(size=self.atualizar_interface)
        self.label_tcc.bind(texture_size=self.atualizar_interface)
        self.add_widget(self.label_tcc)

        # Adiciona o botão para voltar à tela especialidades médicas
        voltar_button = Button(text='Voltar à Tela Psicologia', size_hint=(None, None), size=(300, 50), pos_hint={'center_x': 0.5, 'center_y': 0.1}, 
                                background_normal='', background_color=(1, 0.647, 0, 0.7), color=(0, 0, 0, 1), font_size='15sp', halign='center')
        voltar_button.bind(on_press=self.voltar_tela_psicologia)
        self.add_widget(voltar_button)
    
    def atualizar_imagem(self, instance, width, height):
        self.background.size = width, height

    def atualizar_interface(self, *args):
        self.label_tcc.text_size = (Window.width, None)
        texto_width, texto_height = self.label_tcc.texture_size  # Obtém o tamanho do texto
        texto_x, texto_y = self.label_tcc.pos  # Obtém a posição do texto
        # Calcula a posição do botão para alinhá-lo com o texto e centralizá-lo
        botao_x = texto_x + (self.label_tcc.width - texto_width) / 2  # Centraliza o botão horizontalmente
        botao_y = texto_y - texto_height  # Move o botão para baixo do texto
        self.label_tcc.size = (texto_width, texto_height)
        self.label_tcc.pos = (botao_x, botao_y)

    def voltar_tela_psicologia(self, instance):
        # Voltar para a tela de psicologia
        self.manager.current = 'tela_psicologia'

class TelaTFTC(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.carregar_imagem()
        Window.bind(on_resize=self.atualizar_imagem)

    # Carrega a imagem de fundo e adiciona o texto
    def carregar_imagem(self):
        with self.canvas:
            # Carrega a imagem de fundo
            self.background = Rectangle(source='tftc.png',
                                    size=Window.size, pos=self.pos)

        # Adiciona o texto da especialidade selecionada
        label_tftc = ("[b]Terapia Familiar e Terapia de Casais: [/b]\n\n"
                    "Essas especialidades se concentram nas dinâmicas familiares e nos relacionamentos interpessoais. \n"
                    "Os terapeutas familiares e de casais trabalham com indivíduos, casais e famílias para resolver conflitos,\n"
                    "melhorar a comunicação e fortalecer os laços emocionais.")
                              

        self.label_tftc = Button(text=label_tftc, size_hint=(None, None), pos_hint={'center_x': 0.5, 'center_y': 0.5}, markup=True,
                                    background_normal='', background_color=(1, 1, 1, 0.7), color=(0, 0, 0, 1),
                                    font_size='15sp', halign='center')
        self.label_tftc.bind(size=self.atualizar_interface)
        self.label_tftc.bind(texture_size=self.atualizar_interface)
        self.add_widget(self.label_tftc)

        # Adiciona o botão para voltar à tela especialidades médicas
        voltar_button = Button(text='Voltar à Tela Psicologia', size_hint=(None, None), size=(300, 50), pos_hint={'center_x': 0.5, 'center_y': 0.1}, 
                                background_normal='', background_color=(1, 0.647, 0, 0.7), color=(0, 0, 0, 1), font_size='15sp', halign='center')
        voltar_button.bind(on_press=self.voltar_tela_psicologia)
        self.add_widget(voltar_button)
    
    def atualizar_imagem(self, instance, width, height):
        self.background.size = width, height

    def atualizar_interface(self, *args):
        self.label_tftc.text_size = (Window.width, None)
        texto_width, texto_height = self.label_tftc.texture_size  # Obtém o tamanho do texto
        texto_x, texto_y = self.label_tftc.pos  # Obtém a posição do texto
        # Calcula a posição do botão para alinhá-lo com o texto e centralizá-lo
        botao_x = texto_x + (self.label_tftc.width - texto_width) / 2  # Centraliza o botão horizontalmente
        botao_y = texto_y - texto_height  # Move o botão para baixo do texto
        self.label_tftc.size = (texto_width, texto_height)
        self.label_tftc.pos = (botao_x, botao_y)

    def voltar_tela_psicologia(self, instance):
        # Voltar para a tela de psicologia
        self.manager.current = 'tela_psicologia'

class TelaPsicologia_Desenvolvimento(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.carregar_imagem()
        Window.bind(on_resize=self.atualizar_imagem)

    # Carrega a imagem de fundo e adiciona o texto
    def carregar_imagem(self):
        with self.canvas:
            # Carrega a imagem de fundo
            self.background = Rectangle(source='psicologia_desenvolvimento.jpg',
                                    size=Window.size, pos=self.pos)

        # Adiciona o texto da especialidade selecionada
        label_psicologia_desenvolvimento = ("[b]Psicologia do Desenvolvimento: [/b]\n\n"
                    "Esta especialidade estuda como as pessoas se desenvolvem ao longo da vida, desde a infância até a\n"
                    "idade adulta e a velhice. Os psicólogos do desenvolvimento investigam áreas como o desenvolvimento\n"
                    "cognitivo, emocional, social e moral, e como esses aspectos influenciam o bem-estar mental.")
                              

        self.label_psicologia_desenvolvimento = Button(text=label_psicologia_desenvolvimento, size_hint=(None, None), pos_hint={'center_x': 0.5, 'center_y': 0.5}, markup=True,
                                    background_normal='', background_color=(1, 1, 1, 0.7), color=(0, 0, 0, 1),
                                    font_size='15sp', halign='center')
        self.label_psicologia_desenvolvimento.bind(size=self.atualizar_interface)
        self.label_psicologia_desenvolvimento.bind(texture_size=self.atualizar_interface)
        self.add_widget(self.label_psicologia_desenvolvimento)

        # Adiciona o botão para voltar à tela especialidades médicas
        voltar_button = Button(text='Voltar à Tela Psicologia', size_hint=(None, None), size=(300, 50), pos_hint={'center_x': 0.5, 'center_y': 0.1}, 
                                background_normal='', background_color=(1, 0.647, 0, 0.7), color=(0, 0, 0, 1), font_size='15sp', halign='center')
        voltar_button.bind(on_press=self.voltar_tela_psicologia)
        self.add_widget(voltar_button)
    
    def atualizar_imagem(self, instance, width, height):
        self.background.size = width, height

    def atualizar_interface(self, *args):
        self.label_psicologia_desenvolvimento.text_size = (Window.width, None)
        texto_width, texto_height = self.label_psicologia_desenvolvimento.texture_size  # Obtém o tamanho do texto
        texto_x, texto_y = self.label_psicologia_desenvolvimento.pos  # Obtém a posição do texto
        # Calcula a posição do botão para alinhá-lo com o texto e centralizá-lo
        botao_x = texto_x + (self.label_psicologia_desenvolvimento.width - texto_width) / 2  # Centraliza o botão horizontalmente
        botao_y = texto_y - texto_height  # Move o botão para baixo do texto
        self.label_psicologia_desenvolvimento.size = (texto_width, texto_height)
        self.label_psicologia_desenvolvimento.pos = (botao_x, botao_y)

    def voltar_tela_psicologia(self, instance):
        # Voltar para a tela de psicologia
        self.manager.current = 'tela_psicologia'

class TelaADQ(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.carregar_imagem()
        Window.bind(on_resize=self.atualizar_imagem)

    # Carrega a imagem de fundo e adiciona o texto
    def carregar_imagem(self):
        with self.canvas:
            # Carrega a imagem de fundo
            self.background = Rectangle(source='adq.jpg',
                                    size=Window.size, pos=self.pos)

        # Adiciona o texto da especialidade selecionada
        label_adq = ("[b]Aconselhamento em Dependência Química: [/b]\n\n"
                    "Fornecer informações educativas sobre saúde mental, incluindo sintomas de distúrbios comuns, \n"
                    "estratégias de confrontação saudáveis e dicas para melhorar o autocuidado e o gestão do stress.")
                              

        self.label_adq = Button(text=label_adq, size_hint=(None, None), pos_hint={'center_x': 0.5, 'center_y': 0.5}, markup=True,
                                    background_normal='', background_color=(1, 1, 1, 0.7), color=(0, 0, 0, 1),
                                    font_size='15sp', halign='center')
        self.label_adq.bind(size=self.atualizar_interface)
        self.label_adq.bind(texture_size=self.atualizar_interface)
        self.add_widget(self.label_adq)

        # Adiciona o botão para voltar à tela especialidades médicas
        voltar_button = Button(text='Voltar à Tela Psicologia', size_hint=(None, None), size=(300, 50), pos_hint={'center_x': 0.5, 'center_y': 0.1}, 
                                background_normal='', background_color=(1, 0.647, 0, 0.7), color=(0, 0, 0, 1), font_size='15sp', halign='center')
        voltar_button.bind(on_press=self.voltar_tela_psicologia)
        self.add_widget(voltar_button)
    
    def atualizar_imagem(self, instance, width, height):
        self.background.size = width, height

    def atualizar_interface(self, *args):
        self.label_adq.text_size = (Window.width, None)
        texto_width, texto_height = self.label_adq.texture_size  # Obtém o tamanho do texto
        texto_x, texto_y = self.label_adq.pos  # Obtém a posição do texto
        # Calcula a posição do botão para alinhá-lo com o texto e centralizá-lo
        botao_x = texto_x + (self.label_adq.width - texto_width) / 2  # Centraliza o botão horizontalmente
        botao_y = texto_y - texto_height  # Move o botão para baixo do texto
        self.label_adq.size = (texto_width, texto_height)
        self.label_adq.pos = (botao_x, botao_y)

    def voltar_tela_psicologia(self, instance):
        # Voltar para a tela de psicologia
        self.manager.current = 'tela_psicologia'

class TelaEPOP(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.carregar_imagem()
        Window.bind(on_resize=self.atualizar_imagem)

    # Carrega a imagem de fundo e adiciona o texto
    def carregar_imagem(self):
        with self.canvas:
            # Carrega a imagem de fundo
            self.background = Rectangle(source='epop.jpg',
                                    size=Window.size, pos=self.pos)

        # Adiciona o texto da especialidade selecionada
        label_epop = ("[b]Educação Parental e Orientação Parental: [/b]\n\n"
                    "Fornecer orientações e recursos para pais e cuidadores sobre como apoiar a saúde mental de seus filhos,\n"
                    "incluindo estratégias de criação, deteção precoce de problemas e intervenções preventivas.")
                              

        self.label_epop = Button(text=label_epop, size_hint=(None, None), pos_hint={'center_x': 0.5, 'center_y': 0.5}, markup=True,
                                    background_normal='', background_color=(1, 1, 1, 0.7), color=(0, 0, 0, 1),
                                    font_size='15sp', halign='center')
        self.label_epop.bind(size=self.atualizar_interface)
        self.label_epop.bind(texture_size=self.atualizar_interface)
        self.add_widget(self.label_epop)

        # Adiciona o botão para voltar à tela especialidades médicas
        voltar_button = Button(text='Voltar à Tela Psicologia', size_hint=(None, None), size=(300, 50), pos_hint={'center_x': 0.5, 'center_y': 0.1}, 
                                background_normal='', background_color=(1, 0.647, 0, 0.7), color=(0, 0, 0, 1), font_size='15sp', halign='center')
        voltar_button.bind(on_press=self.voltar_tela_psicologia)
        self.add_widget(voltar_button)
    
    def atualizar_imagem(self, instance, width, height):
        self.background.size = width, height

    def atualizar_interface(self, *args):
        self.label_epop.text_size = (Window.width, None)
        texto_width, texto_height = self.label_epop.texture_size  # Obtém o tamanho do texto
        texto_x, texto_y = self.label_epop.pos  # Obtém a posição do texto
        # Calcula a posição do botão para alinhá-lo com o texto e centralizá-lo
        botao_x = texto_x + (self.label_epop.width - texto_width) / 2  # Centraliza o botão horizontalmente
        botao_y = texto_y - texto_height  # Move o botão para baixo do texto
        self.label_epop.size = (texto_width, texto_height)
        self.label_epop.pos = (botao_x, botao_y)

    def voltar_tela_psicologia(self, instance):
        # Voltar para a tela de psicologia
        self.manager.current = 'tela_psicologia'

class TelaArteterapia(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.carregar_imagem()
        Window.bind(on_resize=self.atualizar_imagem)

    # Carrega a imagem de fundo e adiciona o texto
    def carregar_imagem(self):
        with self.canvas:
            # Carrega a imagem de fundo
            self.background = Rectangle(source='arteterapia.jpg',
                                    size=Window.size, pos=self.pos)

        # Adiciona o texto da especialidade selecionada
        label_arteterapia = ("[b]Terapia Expressiva e Arteterapia: [/b]\n\n"
                    "Incluir recursos para terapia expressiva, como arte, música, dança e escrita terapêutica,\n"
                    "que podem ajudar os usuários a explorar e expressar seus pensamentos, sentimentos e experiências\n"
                    "de maneira criativa e não verbal.")
                              

        self.label_arteterapia = Button(text=label_arteterapia, size_hint=(None, None), pos_hint={'center_x': 0.5, 'center_y': 0.5}, markup=True,
                                    background_normal='', background_color=(1, 1, 1, 0.7), color=(0, 0, 0, 1),
                                    font_size='15sp', halign='center')
        self.label_arteterapia.bind(size=self.atualizar_interface)
        self.label_arteterapia.bind(texture_size=self.atualizar_interface)
        self.add_widget(self.label_arteterapia)


        # Adiciona o botão para voltar à tela especialidades médicas
        voltar_button = Button(text='Voltar à Tela Psicologia', size_hint=(None, None), size=(300, 50), pos_hint={'center_x': 0.5, 'center_y': 0.1}, 
                                background_normal='', background_color=(1, 0.647, 0, 0.7), color=(0, 0, 0, 1), font_size='15sp', halign='center')
        voltar_button.bind(on_press=self.voltar_tela_psicologia)
        self.add_widget(voltar_button)
    
    def atualizar_imagem(self, instance, width, height):
        self.background.size = width, height

    def atualizar_interface(self, *args):
        self.label_arteterapia.text_size = (Window.width, None)
        texto_width, texto_height = self.label_arteterapia.texture_size  # Obtém o tamanho do texto
        texto_x, texto_y = self.label_arteterapia.pos  # Obtém a posição do texto
        # Calcula a posição do botão para alinhá-lo com o texto e centralizá-lo
        botao_x = texto_x + (self.label_arteterapia.width - texto_width) / 2  # Centraliza o botão horizontalmente
        botao_y = texto_y - texto_height  # Move o botão para baixo do texto
        self.label_arteterapia.size = (texto_width, texto_height)
        self.label_arteterapia.pos = (botao_x, botao_y)

    def voltar_tela_psicologia(self, instance):
        # Voltar para a tela de psicologia
        self.manager.current = 'tela_psicologia'

class TelaTSSS(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.carregar_imagem()
        Window.bind(on_resize=self.atualizar_imagem)

    # Carrega a imagem de fundo e adiciona o texto
    def carregar_imagem(self):
        with self.canvas:
            # Carrega a imagem de fundo
            self.background = Rectangle(source='tsss.jpg',
                                    size=Window.size, pos=self.pos)

        # Adiciona o texto da especialidade selecionada
        label_tsss = ("[b]Terapia Sexual e Saúde Sexual: [/b]\n\n"
                    "Oferecer informações e suporte relacionados a questões de saúde sexual e identidade de \n"
                    "género, incluindo educação sexual, terapia sexual e aconselhamento sobre relacionamentos íntimos.")
                              

        self.label_tsss = Button(text=label_tsss, size_hint=(None, None), pos_hint={'center_x': 0.5, 'center_y': 0.5}, markup=True,
                                    background_normal='', background_color=(1, 1, 1, 0.7), color=(0, 0, 0, 1),
                                    font_size='15sp', halign='center')
        self.label_tsss.bind(size=self.atualizar_interface)
        self.label_tsss.bind(texture_size=self.atualizar_interface)
        self.add_widget(self.label_tsss)

        # Adiciona o botão para voltar à tela especialidades médicas
        voltar_button = Button(text='Voltar à Tela Psicologia', size_hint=(None, None), size=(300, 50), pos_hint={'center_x': 0.5, 'center_y': 0.1}, 
                                background_normal='', background_color=(1, 0.647, 0, 0.7), color=(0, 0, 0, 1), font_size='15sp', halign='center')
        voltar_button.bind(on_press=self.voltar_tela_psicologia)
        self.add_widget(voltar_button)
    
    def atualizar_imagem(self, instance, width, height):
        self.background.size = width, height

    def atualizar_interface(self, *args):
        self.label_tsss.text_size = (Window.width, None)
        texto_width, texto_height = self.label_tsss.texture_size  # Obtém o tamanho do texto
        texto_x, texto_y = self.label_tsss.pos  # Obtém a posição do texto
        # Calcula a posição do botão para alinhá-lo com o texto e centralizá-lo
        botao_x = texto_x + (self.label_tsss.width - texto_width) / 2  # Centraliza o botão horizontalmente
        botao_y = texto_y - texto_height  # Move o botão para baixo do texto
        self.label_tsss.size = (texto_width, texto_height)
        self.label_tsss.pos = (botao_x, botao_y)

    def voltar_tela_psicologia(self, instance):
        # Voltar para a tela de psicologia
        self.manager.current = 'tela_psicologia'

class TelaPsicologiaEducacao(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.carregar_imagem()
        Window.bind(on_resize=self.atualizar_imagem)

    # Carrega a imagem de fundo e adiciona o texto
    def carregar_imagem(self):
        with self.canvas:
            # Carrega a imagem de fundo
            self.background = Rectangle(source='psicologiaeducacao.jpg',
                                    size=Window.size, pos=self.pos)

        # Adiciona o texto da especialidade selecionada
        label_psicologiaeducacao = ("[b]Psicologia Educação: [/b]\n\n"
                         "Avaliação e monitorização dos processos psicológicos que constituem o processo educativo através da \n"
                         "compreensão do processo de ensino e aprendizagem.\n"
                         "[b]Diferentes abordagens: [/b]")

        self.label_psicologiaeducacao = Button(text=label_psicologiaeducacao, size_hint=(None, None), pos_hint={'center_x': 0.5, 'center_y': 0.6}, markup=True,
                                    background_normal='', background_color=(1, 1, 1, 0.7), color=(0, 0, 0, 1),
                                    font_size='15sp', halign='center')
        self.label_psicologiaeducacao.bind(size=self.atualizar_interface)
        self.label_psicologiaeducacao.bind(texture_size=self.atualizar_interface)
        self.add_widget(self.label_psicologiaeducacao)

        # Adiciona um layout vertical para os botões das abordagens
        layout = BoxLayout(orientation='vertical', spacing=5, size_hint=(None, None), size=(300, 30), pos_hint={'center_x': 0.5, 'center_y': 0.4})
        layout.bind(minimum_height=layout.setter('height'))
        self.add_widget(layout)

        # Adicionar os botões das abordagens da Psicologia
        abordagens = ['Psicoeducação', 'Orientação Vocacional']
        for abordagem in abordagens:
            botao_abordagem = Button(text=abordagem, size_hint=(None, None), size=(300, 30), 
                                background_normal='', background_color=(1, 0.647, 0, 0.7), color=(0, 0, 0, 1), font_size='15sp', halign='center')
            botao_abordagem.bind(on_press=lambda event, abordagem=abordagem: self.abrir_tela_abordagem(abordagem))
            layout.add_widget(botao_abordagem)

        # Adiciona o botão para voltar à tela especialidades médicas
        voltar_button = Button(text='Voltar à Tela Especialidades Médicas', size_hint=(None, None), size=(300, 50), pos_hint={'center_x': 0.5, 'center_y': 0.1}, 
                                background_normal='', background_color=(1, 0.647, 0, 0.7), color=(0, 0, 0, 1), font_size='15sp', halign='center')
        voltar_button.bind(on_press=self.voltar_tela_especialidades)
        self.add_widget(voltar_button)

    def atualizar_imagem(self, instance, width, height):
        self.background.size = width, height

    def atualizar_interface(self, *args):
        self.label_psicologiaeducacao.text_size = (Window.width, None)
        texto_width, texto_height = self.label_psicologiaeducacao.texture_size  # Obtém o tamanho do texto
        texto_x, texto_y = self.label_psicologiaeducacao.pos  # Obtém a posição do texto
        # Calcula a posição do botão para alinhá-lo com o texto e centralizá-lo
        botao_x = texto_x + (self.label_psicologiaeducacao.width - texto_width) / 2  # Centraliza o botão horizontalmente
        botao_y = texto_y - texto_height  # Move o botão para baixo do texto
        self.label_psicologiaeducacao.size = (texto_width, texto_height)
        self.label_psicologiaeducacao.pos = (botao_x, botao_y)

    def abrir_tela_abordagem(self, abordagem):
        if abordagem == 'Psicoeducação':
            # Verifica se a tela já existe no gerenciador de tela
            if 'tela_psicoeducacao' not in self.manager.screen_names:
                # Se não existir, cria e adiciona uma nova tela TelaPsicoeducação ao gerenciador de tela
                nova_tela = TelaPsicoeducação(name='tela_psicoeducacao')
                self.manager.add_widget(nova_tela)

            # Muda para a tela 'tela_psicoeducacao'
            self.manager.current = 'tela_psicoeducacao'
        
        elif abordagem == 'Orientação Vocacional':
            # Verifica se a tela já existe no gerenciador de tela
            if 'tela_orientacao' not in self.manager.screen_names:
                # Se não existir, cria e adiciona uma nova tela TelaOrientação ao gerenciador de tela
                nova_tela = TelaOrientação(name='tela_orientacao')
                self.manager.add_widget(nova_tela)

            # Muda para a tela 'tela_orientacao'
            self.manager.current = 'tela_orientacao'

    def voltar_tela_especialidades(self, instance):
        # Voltar para a tela de especialidades médicas
        self.manager.current = 'tela_especialidades_medicas'

class TelaPsicoeducação(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.carregar_imagem()
        Window.bind(on_resize=self.atualizar_imagem)

    # Carrega a imagem de fundo e adiciona o texto
    def carregar_imagem(self):
        with self.canvas:
            # Carrega a imagem de fundo
            self.background = Rectangle(source='psicoeducacao.jpg',
                                    size=Window.size, pos=self.pos)

        # Adiciona o texto da especialidade selecionada
        label_psicoeducacao = ("[b]Psicoeducação: [/b]\n\n"
                    "Fornecer informações educativas sobre saúde mental, incluindo sintomas de distúrbios comuns, \n"
                    "estratégias de confrontação saudáveis e dicas para melhorar o autocuidado e o gestão do stress.")
                              

        self.label_psicoeducacao = Button(text=label_psicoeducacao, size_hint=(None, None), pos_hint={'center_x': 0.5, 'center_y': 0.5}, markup=True,
                                    background_normal='', background_color=(1, 1, 1, 0.7), color=(0, 0, 0, 1),
                                    font_size='15sp', halign='center')
        self.label_psicoeducacao.bind(size=self.atualizar_interface)
        self.label_psicoeducacao.bind(texture_size=self.atualizar_interface)
        self.add_widget(self.label_psicoeducacao)

        # Adiciona o botão para voltar à tela especialidades médicas
        voltar_button = Button(text='Voltar à Tela Psicologia da Educação', size_hint=(None, None), size=(300, 50), pos_hint={'center_x': 0.5, 'center_y': 0.1}, 
                                background_normal='', background_color=(1, 0.647, 0, 0.7), color=(0, 0, 0, 1), font_size='15sp', halign='center')
        voltar_button.bind(on_press=self.voltar_tela_psicologiaeducacao)
        self.add_widget(voltar_button)
    
    def atualizar_imagem(self, instance, width, height):
        self.background.size = width, height

    def atualizar_interface(self, *args):
        self.label_psicoeducacao.text_size = (Window.width, None)
        texto_width, texto_height = self.label_psicoeducacao.texture_size  # Obtém o tamanho do texto
        texto_x, texto_y = self.label_psicoeducacao.pos  # Obtém a posição do texto
        # Calcula a posição do botão para alinhá-lo com o texto e centralizá-lo
        botao_x = texto_x + (self.label_psicoeducacao.width - texto_width) / 2  # Centraliza o botão horizontalmente
        botao_y = texto_y - texto_height  # Move o botão para baixo do texto
        self.label_psicoeducacao.size = (texto_width, texto_height)
        self.label_psicoeducacao.pos = (botao_x, botao_y)

    def voltar_tela_psicologiaeducacao(self, instance):
        # Voltar para a tela de psicologia
        self.manager.current = 'tela_psicologiaeducacao'

class TelaOrientação(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.carregar_imagem()
        Window.bind(on_resize=self.atualizar_imagem)

    # Carrega a imagem de fundo e adiciona o texto
    def carregar_imagem(self):
        with self.canvas:
            # Carrega a imagem de fundo
            self.background = Rectangle(source='orientacao.jpg',
                                    size=Window.size, pos=self.pos)

        # Adiciona o texto da especialidade selecionada
        label_orientacao = ("[b]Orientação Vocacional: [/b]\n\n"
                    "Conjunto de técnicas que visam avaliar as áreas que possibilitem um aumento do autoconhecimento do\n"
                    "jovem para que possa escolher o projeto de vida profissional de forma mais informada.")
                              

        self.label_orientacao = Button(text=label_orientacao, size_hint=(None, None), pos_hint={'center_x': 0.5, 'center_y': 0.5}, markup=True,
                                    background_normal='', background_color=(1, 1, 1, 0.7), color=(0, 0, 0, 1),
                                    font_size='15sp', halign='center')
        self.label_orientacao.bind(size=self.atualizar_interface)
        self.label_orientacao.bind(texture_size=self.atualizar_interface)
        self.add_widget(self.label_orientacao)

        # Adiciona o botão para voltar à tela especialidades médicas
        voltar_button = Button(text='Voltar à Tela Psicologia da Educação', size_hint=(None, None), size=(300, 50), pos_hint={'center_x': 0.5, 'center_y': 0.1}, 
                                background_normal='', background_color=(1, 0.647, 0, 0.7), color=(0, 0, 0, 1), font_size='15sp', halign='center')
        voltar_button.bind(on_press=self.voltar_tela_psicologiaeducacao)
        self.add_widget(voltar_button)
    
    def atualizar_imagem(self, instance, width, height):
        self.background.size = width, height

    def atualizar_interface(self, *args):
        self.label_orientacao.text_size = (Window.width, None)
        texto_width, texto_height = self.label_orientacao.texture_size  # Obtém o tamanho do texto
        texto_x, texto_y = self.label_orientacao.pos  # Obtém a posição do texto
        # Calcula a posição do botão para alinhá-lo com o texto e centralizá-lo
        botao_x = texto_x + (self.label_orientacao.width - texto_width) / 2  # Centraliza o botão horizontalmente
        botao_y = texto_y - texto_height  # Move o botão para baixo do texto
        self.label_orientacao.size = (texto_width, texto_height)
        self.label_orientacao.pos = (botao_x, botao_y)

    def voltar_tela_psicologiaeducacao(self, instance):
        # Voltar para a tela de psicologia educação
        self.manager.current = 'tela_psicologiaeducacao'

class TelaNeurologia(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.carregar_imagem()
        Window.bind(on_resize=self.atualizar_imagem)
    
    # Carrega a imagem de fundo e adiciona o texto
    def carregar_imagem(self):
        with self.canvas:
            # Carrega a imagem de fundo
            self.background = Rectangle(source='neuro.jpg',
                                    size=Window.size, pos=self.pos)

        # Adiciona o texto da especialidade selecionada
        label_adq = ("[b]Neurologia: [/b]\n\n"
                    "Neurologia é a especialidade médica que trata dos distúrbios estruturais do sistema nervoso.\n"
                    "Especificamente, ela lida com o diagnóstico e tratamento de todas as categorias de doenças\n"
                    "que envolvem os sistemas nervoso central, periférico e autônomo, parassimpático e simpático incluindo os seus revestimentos,vasos sanguíneos, e todos os tecidos efetores, como os músculos.")
                              

        self.label_adq = Button(text=label_adq, size_hint=(None, None), pos_hint={'center_x': 0.5, 'center_y': 0.5}, markup=True,
                                    background_normal='', background_color=(1, 1, 1, 0.7), color=(0, 0, 0, 1),
                                    font_size='15sp', halign='center')
        self.label_adq.bind(size=self.atualizar_interface)
        self.label_adq.bind(texture_size=self.atualizar_interface)
        self.add_widget(self.label_adq)

        # Adiciona o botão para voltar à tela especialidades médicas
        voltar_button = Button(text='Voltar à Tela Especialidades Médicas', size_hint=(None, None), size=(300, 50), pos_hint={'center_x': 0.5, 'center_y': 0.1}, 
                                background_normal='', background_color=(0, 0.5608, 0.2235, 0.7), color=(0, 0, 0, 1), font_size='15sp', halign='center')
        voltar_button.bind(on_press=self.voltar_tela_especialidades)
        self.add_widget(voltar_button)
    
    def atualizar_imagem(self, instance, width, height):
        self.background.size = width, height

    def atualizar_interface(self, *args):
        self.label_adq.text_size = (Window.width, None)
        texto_width, texto_height = self.label_adq.texture_size  # Obtém o tamanho do texto
        texto_x, texto_y = self.label_adq.pos  # Obtém a posição do texto
        # Calcula a posição do botão para alinhá-lo com o texto e centralizá-lo
        botao_x = texto_x + (self.label_adq.width - texto_width) / 2  # Centraliza o botão horizontalmente
        botao_y = texto_y - texto_height  # Move o botão para baixo do texto
        self.label_adq.size = (texto_width, texto_height)
        self.label_adq.pos = (botao_x, botao_y)

    def voltar_tela_especialidades(self, instance):
        # Voltar para a tela de especialidades médicas
        self.manager.current = 'tela_especialidades_medicas'

class VideoCapture(Screen):
    def __init__(self, **kwargs):
        super(VideoCapture, self).__init__(**kwargs)
        self.capture = None  # Inicializa a captura de vídeo

        # Define a cor de fundo da tela como o azul especificado (#a3d7da)
        with self.canvas.before:
            Color(0.6392, 0.8431, 0.8549, 1)  # Valores RGB de #a3d7da
            self.rect = Rectangle(size=self.size, pos=self.pos)

        # Atualiza o retângulo quando o tamanho da tela é alterado
        self.bind(size=self.atualizar_retangulo, pos=self.atualizar_retangulo)
        
    def on_enter(self):
        # Inicializa a captura de vídeo
        if not self.capture:
            self.capture = cv2.VideoCapture(0)
            if not self.capture.isOpened():
                print("Erro ao abrir a câmera.")
                return
            layout = BoxLayout(orientation='vertical')
            self.image = Image()
            self.image.flip_vertical = True
            layout.add_widget(self.image)
            self.button_desligar_chamada = Button(text='Desligar Chamada', size_hint=(None, None), size=(150, 50), pos_hint={'center_x': 0.5, 'center_y': 0.1}, 
                                background_normal='', background_color=(0.2, 0.8, 0.8, 1), color=(0, 0, 0, 1), font_size='15sp', halign='center')
            self.button_desligar_chamada.bind(on_press=self.desligar_chamada)
            layout.add_widget(self.button_desligar_chamada)
            Clock.schedule_interval(self.update, 1.0 / 30.0)
            self.add_widget(layout)

    def update(self, dt):
        if self.capture is None or not self.capture.isOpened():
            return
        # Lê o próximo frame do vídeo
        ret, frame = self.capture.read()
        if ret:
            # Corrige a inversão da imagem
            frame = cv2.flip(frame, 0)

            # Converte o frame de BGR para RGB
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Cria uma textura da imagem
            buf = frame.tobytes()
            texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='rgb')
            texture.blit_buffer(buf, colorfmt='rgb', bufferfmt='ubyte')

            # Atualiza a imagem exibida
            self.image.texture = texture

    def desligar_chamada(self, instance):
        self.manager.current = 'tela_principal'
        # Certifique-se de liberar a captura de vídeo quando sair da tela de videochamada
        if self.capture:
            self.capture.release()
            self.capture = None
    
    def atualizar_retangulo(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

class TelaForum(Screen):
    def __init__(self, **kwargs):
        super(TelaForum, self).__init__(**kwargs)
        self.all_messages = []
        self.filtered_messages = []
        self.topics = set()
        self.connection = sqlite3.connect('forum.db')
        self.cursor = self.connection.cursor()
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS messages 
                           (id INTEGER PRIMARY KEY, topic TEXT, content TEXT)''')
        self.connection.commit()
        self.load_messages()

    # Adicione esta linha para definir o atributo filter_input
        self.filter_input = TextInput(hint_text='Filtrar por tópico', size_hint=(1, None), height=40)


    def load_messages(self):
        self.cursor.execute("SELECT * FROM messages")
        rows = self.cursor.fetchall()
        for row in rows:
            topic, message = row[1], row[2]
            self.all_messages.append((topic, message))
            self.topics.add(topic)

    def on_enter(self):
        main_layout = BoxLayout(orientation='vertical', spacing=10, padding=10)

        title_label = Label(text='Meu Fórum', size_hint=(1, 0.1), font_size='24sp', color=(0, 0.5, 1, 1))

        scroll_view = ScrollView(size_hint=(1, 0.6))
        self.message_label = BoxLayout(orientation='vertical', spacing=5, size_hint_y=None)
        scroll_view.add_widget(self.message_label)

        self.message_input = TextInput(hint_text='Digite sua mensagem aqui', size_hint=(1, None), height=40)
        send_button = Button(text='Enviar', size_hint=(1, None), height=40, background_color=(0, 0.5, 1, 1))
        send_button.bind(on_press=self.send_message)

        self.topic_layout = BoxLayout(orientation='horizontal', size_hint=(1, None), height=40, spacing=5)
        self.topic_input = TextInput(hint_text='Digite o título do tópico', size_hint=(0.7, None), height=40)
        topic_button = Button(text='Criar Tópico', size_hint=(0.3, None), height=40, background_color=(0, 0.5, 1, 1))
        topic_button.bind(on_press=self.create_topic)
        self.topic_layout.add_widget(self.topic_input)
        self.topic_layout.add_widget(topic_button)

        exit_button = Button(text='Sair do Fórum', size_hint=(1, None), height=40, background_color=(1, 0.5, 0, 1))
        exit_button.bind(on_press=self.exit_forum)

        filter_input = TextInput(hint_text='Filtrar por tópico', size_hint=(1, None), height=40)
        filter_button = Button(text='Filtrar', size_hint=(1, None), height=40, background_color=(0, 0.5, 1, 1))
        filter_button.bind(on_press=self.filter_messages)

        main_layout.add_widget(title_label)
        main_layout.add_widget(scroll_view)
        main_layout.add_widget(self.message_input)
        main_layout.add_widget(send_button)
        main_layout.add_widget(self.topic_layout)
        main_layout.add_widget(filter_input)
        main_layout.add_widget(filter_button)
        main_layout.add_widget(exit_button)

        self.add_widget(main_layout)

    def send_message(self, instance):
        message = self.message_input.text.strip()
        if message:
            topic = self.topic_input.text.strip() or "Geral"
            new_message = f'Tópico: {topic}\n{message}'
            message_widget = Label(text=new_message, size_hint_y=None, height=100, color=(0, 0.5, 1, 1), font_size='16sp')
            self.message_label.add_widget(message_widget)
            self.all_messages.append((topic, message))
            self.cursor.execute("INSERT INTO messages (topic, content) VALUES (?, ?)", (topic, message))
            self.connection.commit()
            if not self.filtered_messages:
                self.filtered_messages.append(new_message)
            self.message_input.text = ''
            self.topic_input.text = ''
            self.topics.add(topic)

    def create_topic(self, instance):
        topic_title = self.topic_input.text
        if topic_title:
            new_topic = Label(text=f'Tópico: {topic_title}')
            self.message_label.add_widget(new_topic)
            self.topics.add(topic_title)
            self.message_input.text = ''

    def exit_forum(self, instance):
        self.manager.current = 'tela_especialidades_medicas'

    def filter_messages(self, instance):
        filter_text = self.filter_input.text.lower().strip()
        if filter_text:
            self.filtered_messages = [message for message in self.all_messages if filter_text in message[0].lower() or filter_text in message[1].lower()]
        else:
            self.filtered_messages = self.all_messages
        self.update_message_label()

    def update_message_label(self):
        self.message_label.clear_widgets()
        for topic, message in self.filtered_messages:
            message_widget = Label(text=f'Tópico: {topic}\n{message}', size_hint_y=None, height=100, color=(0, 0.5, 1, 1), font_size='16sp')
            self.message_label.add_widget(message_widget)

class TelaEmergenciaeCrise(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.carregar_imagem()
        Window.bind(on_resize=self.atualizar_imagem)
    
    # Carrega a imagem de fundo e adiciona o texto
    def carregar_imagem(self):
        with self.canvas:
            # Carrega a imagem de fundo
            self.background = Rectangle(source='eme.jpg',
                                    size=Window.size, pos=self.pos)

        # Adiciona o texto da especialidade selecionada
        label_adq = ("[b]Emergência e Crise: [/b]\n\n"
                    "[b]Respira fundo:[/b]Respira profundamente....Concentra-te em inspirar e expirar lentamente para ajudar a reduzir a ansiedade.\n\n"
                    "[b]Liga para um amigo ou familiar:[/b]Entrar em contato com alguém próximo pode oferecer apoio emocional e ajudar a aliviar a sensação de solidão.\n\n"
                    "[b]Procura ajuda profissional:[/b]Se estiveres a sentir-te em perigo ou em crise grave, não hesite em ligar para uma linha de apoio de saúde mental ou para os serviços de emergência locais.\n\n"
                    "[b]Utiliza recursos de apoio:[/b]Liga para linhas de apoio de saúde mental. Existem muitas organizações que oferecem suporte emocional e orientação, mesmo fora do horário comercial.\n\n"
                    "[b]Faz o que gostas:[/b]Tenta realizar atividades que costumam ajudar-te a sentir-te melhor, como caminhar ao ar livre, ouvir música relaxante, praticar exercícios de respiração ou meditar.\n\n"
                    "[b]Anota os teus pensamentos e sentimentos:[/b]Escrever em um diário pode ajudar-te a processar as tuas emoções e organizar os teus pensamentos.\n\n"
                    "[b]LEMBRA-TE de que não estás sozinho/a:[/b]Muitas pessoas passam por momentos difíceis na vida, e existem pessoas e recursos disponíveis para ajudar a superar qualquer problema.")
                              
        self.label_adq = Button(text=label_adq, size_hint=(None, None), pos_hint={'center_x': 0.5, 'center_y': 0.5}, markup=True,
                                    background_normal='', background_color=(1, 1, 1, 0.7), color=(0, 0, 0, 1),
                                    font_size='15sp', halign='center')
        self.label_adq.bind(size=self.atualizar_interface)
        self.label_adq.bind(texture_size=self.atualizar_interface)
        self.add_widget(self.label_adq)

        # Adiciona o botão para voltar à tela especialidades médicas
        voltar_button = Button(text='Voltar à Tela Especialidades Médicas', size_hint=(None, None), size=(300, 50), pos_hint={'center_x': 0.5, 'center_y': 0.1}, 
                                background_normal='', background_color=(0, 0.5608, 0.2235, 0.7), color=(0, 0, 0, 1), font_size='15sp', halign='center')
        voltar_button.bind(on_press=self.voltar_tela_especialidades)
        self.add_widget(voltar_button)
    
    def atualizar_imagem(self, instance, width, height):
        self.background.size = width, height

    def atualizar_interface(self, *args):
        self.label_adq.text_size = (Window.width, None)
        texto_width, texto_height = self.label_adq.texture_size  # Obtém o tamanho do texto
        texto_x, texto_y = self.label_adq.pos  # Obtém a posição do texto
        # Calcula a posição do botão para alinhá-lo com o texto e centralizá-lo
        botao_x = texto_x + (self.label_adq.width - texto_width) / 2  # Centraliza o botão horizontalmente
        botao_y = texto_y - texto_height  # Move o botão para baixo do texto
        self.label_adq.size = (texto_width, texto_height)
        self.label_adq.pos = (botao_x, botao_y)

    def voltar_tela_especialidades(self, instance):
        # Voltar para a tela de especialidades médicas
        self.manager.current = 'tela_especialidades_medicas'

class TelaNSF(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.carregar_imagem()
        Window.bind(on_resize=self.atualizar_imagem)
        
    # Carrega a imagem de fundo e adiciona o texto
    def carregar_imagem(self):
        with self.canvas:
            # Carrega a imagem de fundo
            self.background = Rectangle(source='nutri.jpg',
                                    size=Window.size, pos=self.pos)

        # Adiciona o texto da especialidade selecionada
        label_psiquiatria = ("[b]Nutrição e Saúde Física: [/b]\n\n"
                         "A nutrição desempenha um papel crucial na saúde física e mental, especialmente em doenças neurológicas. Uma alimentação equilibrada, rica em antioxidantes, fibras e ácidos gordos ómega-3, pode ajudar a reduzir a inflamação e o stress oxidativo, fatores comuns em condições como Alzheimer, Parkinson e esclerose múltipla.\n"
                         "Além disso, manter níveis saudáveis de açúcar no sangue e promover um microbioma intestinal saudável através de alimentos ricos em fibras e probióticos é essencial para a saúde cerebral.\n"
                         "O controlo do peso e a prática regular de exercício físico também são fundamentais, pois podem reduzir o risco de doenças neurodegenerativas e promover a neuroplasticidade.\n"
                         "Adaptar a dieta às necessidades individuais, como a utilização da dieta cetogénica em algumas formas de epilepsia, também pode ser benéfico.\n"
                         "Em suma, uma abordagem holística que combine nutrição adequada e atividade física é essencial para apoiar a saúde cerebral e melhorar a qualidade de vida em pessoas com doenças neurológicas")

        self.label_psiquiatria = Button(text= label_psiquiatria, size_hint=(None, None), pos_hint={'center_x': 0.5, 'center_y': 0.5}, markup=True,
                                    background_normal='', background_color=(1, 1, 1, 0.6), color=(0, 0, 0, 1),
                                    font_size='15sp', halign='center')
        self.label_psiquiatria.bind(size=self.atualizar_interface)
        self.label_psiquiatria.bind(texture_size=self.atualizar_interface)
        self.add_widget(self.label_psiquiatria)

        # Adiciona o botão para voltar à tela especialidades médicas
        voltar_button = Button(text='Voltar à Tela Especialidades Médicas', size_hint=(None, None), size=(300, 50), pos_hint={'center_x': 0.5, 'center_y': 0.1}, 
                                background_normal='', background_color=(0, 0.5608, 0.2235, 0.7), color=(0, 0, 0, 1), font_size='15sp', halign='center')
        voltar_button.bind(on_press=self.voltar_tela_especialidades)
        self.add_widget(voltar_button)

    def atualizar_imagem(self, instance, width, height):
        self.background.size = width, height

    def atualizar_interface(self, *args):
        self.label_psiquiatria.text_size = (Window.width, None)
        texto_width, texto_height = self.label_psiquiatria.texture_size  # Obtém o tamanho do texto
        texto_x, texto_y = self.label_psiquiatria.pos  # Obtém a posição do texto
        # Calcula a posição do botão para alinhá-lo com o texto e centralizá-lo
        botao_x = texto_x + (self.label_psiquiatria.width - texto_width) / 2  # Centraliza o botão horizontalmente
        botao_y = texto_y - texto_height  # Move o botão para baixo do texto
        self.label_psiquiatria.size = (texto_width, texto_height)
        self.label_psiquiatria.pos = (botao_x, botao_y)

    def voltar_tela_especialidades(self, instance):
        # Voltar para a tela de especialidades médicas
        self.manager.current = 'tela_especialidades_medicas'

class TelaDiario(Screen):
    # Define self.cur fora do método __init__
    cur = None
    conn = None


    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.nlp = spacy.load("pt_core_news_sm")
        self.title = 'Diário de Sentimentos e Pensamentos'
        self.sentimentos_positivos, self.sentimentos_negativos = self.load_sentimentos_from_file()
        self.reminder_hour = 00  # Horário padrão do lembrete: 00h
        
        # Conexão com o banco de dados SQLite
        if not TelaDiario.conn:
            TelaDiario.conn = sqlite3.connect('diary.db')
            TelaDiario.cur = TelaDiario.conn.cursor()
            TelaDiario.cur.execute('''CREATE TABLE IF NOT EXISTS entries
                                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                                date TEXT,
                                sentiment TEXT,
                                thought TEXT,
                                sentiment_score REAL)''')
                
        # Define a cor de fundo da tela como o azul especificado (#a3d7da)
        with self.canvas.before:
            Color(0.6392, 0.8431, 0.8549, 1)  # Valores RGB de #a3d7da
            self.rect = Rectangle(size=self.size, pos=self.pos)

        # Atualiza o retângulo quando o tamanho da tela é alterado
        self.bind(size=self.atualizar_retangulo, pos=self.atualizar_retangulo)

        self.layout = BoxLayout(orientation='vertical', spacing=10)
        self.add_widget(self.layout)

        # Widget para entrada de emoção
        self.sentiment_input = TextInput(hint_text='Sentimento')
        self.layout.add_widget(self.sentiment_input)

        # Widget para entrada de pensamento
        self.thought_input = TextInput(hint_text='Pensamento', multiline=True)
        self.layout.add_widget(self.thought_input)

        # Botão para adicionar entrada
        self.add_button = Button(text='Adicionar Entrada', background_normal='', background_color=(0.2, 0.8, 0.8, 1), color=(0, 0, 0, 1), font_size='15sp', halign='center')
        self.add_button.bind(on_press=self.add_entry)
        self.layout.add_widget(self.add_button)

        # Reminder layout
        self.reminder_layout = BoxLayout(orientation='horizontal', size_hint=(1, None), height=40)
        self.reminder_label = Label(text='Horário do Lembrete:', color=(0, 0, 0, 1), font_size='15sp', halign='center')
        self.reminder_hour_input = TextInput(text=str(self.reminder_hour), input_filter='int', multiline=False)
        self.reminder_layout.add_widget(self.reminder_label)
        self.reminder_layout.add_widget(self.reminder_hour_input)
        self.layout.add_widget(self.reminder_layout)

        # Set reminder button
        self.set_reminder_button = Button(text='Definir Lembrete', background_normal='', background_color=(0.2, 0.8, 0.8, 1), color=(0, 0, 0, 1), font_size='15sp', halign='center')
        self.set_reminder_button.bind(on_press=self.set_reminder)
        self.layout.add_widget(self.set_reminder_button)

        # Scrollview para exibir entradas
        self.scroll_view = ScrollView()
        self.entries_layout = GridLayout(cols=1, spacing=10, size_hint_y=None)
        self.entries_layout.bind(minimum_height=self.entries_layout.setter('height'))
        self.scroll_view.add_widget(self.entries_layout)
        self.layout.add_widget(self.scroll_view)

        # Lembrete agendado
        Clock.schedule_interval(self.remind_to_write_diary, 60)  # Lembrete a cada 60 segundos
        
    # Adiciona o botão para voltar à tela principal
        voltar_button = Button(text='Voltar à Tela Principal', size_hint=(None, None), size=(200, 50), pos_hint={'center_x': 0.5, 'center_y': 0.1}, 
                                  background_normal='', background_color=(0.2, 0.8, 0.8, 1), color=(0, 0, 0, 1), font_size='15sp', halign='center')
        voltar_button.bind(on_press=self.voltar_tela_principal)
        self.add_widget(voltar_button)

    def voltar_tela_principal(self, instance):
        self.manager.current = 'tela_principal'

    def add_entry(self, instance):
        thought = self.thought_input.text
        sentiment = self.sentiment_input.text
        if sentiment.strip() and thought.strip():  
            keywords = ['suicídio','suicidio', 'mutilação','mutilaçao','depressão','depressao','angústia','angustia']  # Adicione mais palavras-chave aqui
            if any(keyword in thought.lower() for keyword in keywords):
                self.manager.current = 'tela_videochamada'  # Redireciona para a tela de videochamada
            else:
                date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                sentiment_score = self.sentiment_analysis(sentiment)
                self.insert_entry(date, sentiment, thought, sentiment_score)
                self.display_entries()
                self.sentiment_input.text = ''
                self.thought_input.text = ''
        else:
            print('Por favor, preencha os campos de emoção e pensamento.')

    def set_reminder(self, instance):
        # Obter o horário do lembrete do campo de entrada de texto
        reminder_hour = int(self.reminder_hour_input.text)
        # Verificar se o horário do lembrete é válido
        if 0 <= reminder_hour <= 23:
            self.reminder_hour = reminder_hour
            print(f'Lembrete definido para as {reminder_hour}:00 horas.')
        else:
            print('Por favor, insira um horário válido para o lembrete (0-23).')

    def insert_entry(self, date, sentiment, thought, sentiment_score):
        TelaDiario.cur.execute('INSERT INTO entries (date, sentiment, thought, sentiment_score) VALUES (?, ?, ?, ?)',
                               (date, sentiment, thought, sentiment_score))
        TelaDiario.conn.commit()

    def display_entries(self):
        self.entries_layout.clear_widgets()
        TelaDiario.cur.execute('SELECT * FROM entries ORDER BY id DESC')
        entries = TelaDiario.cur.fetchall()
        for entry in entries:
            entry_text = f'Data: {entry[1]}\nSentimento: {entry[2]}\nPensamento: {entry[3]}\nAnálise de Sentimento: {entry[4]}\n'
            entry_label = Label(text=entry_text, size_hint_y=None, height=150)  # Altura fixa para cada entrada
            self.entries_layout.add_widget(entry_label)

    def remind_to_write_diary(self, dt):
        current_hour = datetime.now().hour
        if current_hour == self.reminder_hour:
            print('É hora de escrever no seu diário!')

    def atualizar_retangulo(self, instance, value):
        self.rect.size = instance.size
        self.rect.pos = instance.pos

    def sentiment_analysis(self, text):
        sentiment_score = 0.0
        total_words = 0
        for palavra in text.split(','):
            total_words += 1
            for sentimento in self.sentimentos_positivos:
                if sentimento.strip() in palavra:
                    sentiment_score += 1
            for sentimento in self.sentimentos_negativos:
                if sentimento.strip() in palavra:
                    sentiment_score -= 1
        if total_words > 0:
            return sentiment_score / total_words
        else:
            return 0.0  # Retorna 0 se não houver palavras no texto

    def load_sentimentos_from_file(self):
        sentimentos_positivos = []
        sentimentos_negativos = []
        file_path_positivos = "sentimentos_positivos.txt"
        file_path_negativos = "sentimentos_negativos.txt"
        with open(file_path_positivos, "r", encoding="utf-8") as file_positivos:
            lines = file_positivos.readlines()
            for line in lines:
                sentimentos = line.strip().split(',')
                sentimentos_positivos.extend(sentimentos)

        with open(file_path_negativos, "r", encoding="utf-8") as file_negativos:
            lines = file_negativos.readlines()
            for line in lines:
                sentimentos = line.strip().split(',')
                sentimentos_negativos.extend(sentimentos)

        return sentimentos_positivos, sentimentos_negativos

class TelaQuiz(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.questions = [
            "Sentes-te triste ou desanimado com frequência?",
            "Perdeste o interesse ou prazer em atividades que costumavas desfrutar?",
            "Tens dificuldade em dormir ou dormes demais?",
            "Tens mudanças significativas no apetite ou no peso?",
            "Tens dificuldade de concentração, indecisão ou perda de energia?",
            "Sentes sentimentos de inutilidade ou culpa excessiva?",
            "Tens pensamentos recorrentes de morte ou suicídio?"
        ]
        self.answers = []
        self.index = 0

    def on_enter(self):
        self.load_interface()

    def load_interface(self):
        layout = FloatLayout()
        background = Image(source='foto.jpg', allow_stretch=True, keep_ratio=False, size_hint=(1, 1), pos_hint={'center_x': 0.5, 'center_y': 0.5})
        layout.add_widget(background)

        self.question_label = Label(text=self.questions[self.index], font_size='20sp', size_hint=(1, 0.2), color=(0, 0, 0, 1), pos_hint={'center_x': 0.5, 'center_y': 0.8})
        layout.add_widget(self.question_label)

        self.yes_button = Button(text='Sim', on_press=self.answer_yes, size_hint=(0.4, None), height=50,
                                 background_color=(0, 1, 0, 1), color=(0, 0, 0, 1), pos_hint={'center_x': 0.3, 'center_y': 0.4})
        layout.add_widget(self.yes_button)

        self.no_button = Button(text='Não', on_press=self.answer_no, size_hint=(0.4, None), height=50,
                                background_color=(1, 0, 0, 1), color=(0, 0, 0, 1), pos_hint={'center_x': 0.7, 'center_y': 0.4})
        layout.add_widget(self.no_button)

        self.add_widget(layout)

    def answer_yes(self, instance):
        self.answers.append(1)
        self.next_question()

    def answer_no(self, instance):
        self.answers.append(0)
        self.next_question()

    def next_question(self):
        self.index += 1
        if self.index < len(self.questions):
            self.question_label.text = self.questions[self.index]
        else:
            self.display_results()

    def display_results(self):
        if len(self.answers) != len(self.questions):
            self.question_label.text = "Por favor, responda a todas as perguntas."
            return

        total_score = sum(self.answers)
        if total_score <= 3:
            message = "Sua pontuação total é {}. Não é necessária uma consulta no momento.".format(total_score)
        elif 4 <= total_score <= 5:
            message = ("Sua pontuação total é {}. "
                       "Recomendamos que você tome cuidado com sua saúde mental e considere procurar orientação profissional.".format(total_score))
        else:
            message = ("Sua pontuação total é {}. "
                       "Recomendamos que você consulte um profissional de saúde mental para obter orientação.".format(total_score))

        result_label = Label(text=message, font_size='20sp', color=(0, 0, 0, 1), size_hint=(1, 0.2), pos_hint={'center_x': 0.5, 'center_y': 0.5})
        self.add_widget(result_label)  # Adiciona o rótulo de resultado à própria tela

        # Limpa os widgets das perguntas e dos botões
        self.question_label.text = ''
        self.yes_button.text = ''
        self.no_button.text = ''
        self.yes_button.opacity = 0
        self.no_button.opacity = 0

        self.answers = []  # Limpa as respostas

        # Adiciona o botão para voltar à tela principal
        self.voltar_button = Button(text='Voltar à Tela Principal', size_hint=(None, None), size=(200, 50), pos_hint={'center_x': 0.5, 'center_y': 0.1}, 
                              background_normal='', background_color=(0.2, 0.8, 0.8, 1), color=(0, 0, 0, 1), font_size='15sp', halign='center')
        self.voltar_button.bind(on_press=self.voltar_tela_principal)
        self.add_widget(self.voltar_button)

    def voltar_tela_principal(self, instance):
        self.manager.current = 'tela_principal'

class ProjetoAuroraApp(App):
    def build(self):
        sm = ScreenManager()

        # Instanciando todas as telas necessárias
        tela_login = TelaLogin(name='tela_login')
        tela_perfil = TelaPerfil(name='tela_perfil')
        tela_redefinir_senha = TelaRedefinirSenha(name='tela_redefinir_senha')
        tela_principal = TelaPrincipal(name='tela_principal')
        tela_criar_perfil = TelaCriarPerfil(name='tela_criar_perfil')
        tela_projeto_aurora = TelaProjetoAurora(name='tela_projeto_aurora')
        tela_audios = TelaAudios(name='tela_audios')
        tela_quiz = TelaQuiz(name='tela_quiz')
        tela_mindfullness = Mindfullness(name='tela_mindfullness')
        tela_hipnose = TelaHipnose(name='tela_hipnose')
        tela_especialidades_medicas = TelaEspecialidadesMedicas(name='tela_especialidades_medicas')
        tela_parcerias = TelaParcerias(name='tela_parcerias')
        tela_diario = TelaDiario(name='tela_diario')
        tela_marcacao_de_consultas = TelaMarcacaoDeConsultas(name= 'tela_marcacao_de_consultas')
        tela_videochamada = VideoCapture(name='tela_videochamada')
        tela_forum = TelaForum (name='tela_forum')
        tela_neurologia = TelaNeurologia (name='tela_neurologia')
        tela_emergencia_e_crise = TelaEmergenciaeCrise (name='tela_emergenciaecrise')
        tela_nutricao = TelaNSF (name='tela_nutricao')
        tela_criar_utilizador = TelaCriarUtilizador(name='tela_criar_utilizador')  # Adicionei esta linha

        # Adicionando a tela TelaCriarUtilizador ao TelaLogin
        tela_login.tela_criar_utilizador = tela_criar_utilizador

        # Adicionando todas as telas ao ScreenManager
        sm.add_widget(tela_login)
        sm.add_widget(tela_redefinir_senha)
        sm.add_widget(tela_perfil)
        sm.add_widget(tela_principal)
        sm.add_widget(tela_criar_perfil)
        sm.add_widget(tela_projeto_aurora)
        sm.add_widget(tela_audios)
        sm.add_widget(tela_quiz)
        sm.add_widget(tela_mindfullness)
        sm.add_widget(tela_hipnose)
        sm.add_widget(tela_especialidades_medicas)
        sm.add_widget(tela_parcerias)
        sm.add_widget(tela_diario)
        sm.add_widget(tela_marcacao_de_consultas)
        sm.add_widget(tela_videochamada)
        sm.add_widget(tela_forum)
        sm.add_widget(tela_neurologia)
        sm.add_widget(tela_emergencia_e_crise)
        sm.add_widget(tela_nutricao)
        sm.add_widget(tela_criar_utilizador)  # Adicionei esta linha

        return sm

if __name__ == '__main__':
    ProjetoAuroraApp().run()
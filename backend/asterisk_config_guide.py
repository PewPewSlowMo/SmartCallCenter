"""
Конфигурация Asterisk для Smart Call Center
===============================================

Для полноценной работы системы необходимо настроить Asterisk с Stasis приложением.

1. PJSIP.CONF - Настройка endpoints для операторов
2. EXTENSIONS.CONF - Dialplan для входящих звонков
3. ARI.CONF - Настройка ARI интерфейса
4. HTTP.CONF - Настройка HTTP сервера для ARI
"""

# pjsip.conf
PJSIP_CONFIG = """
[global]
type=global
endpoint_identifier_order=ip,username,header

[0001]
type=endpoint
auth=0001
aors=0001
context=internal

[0001]
type=auth
auth_type=userpass
password=password123
username=0001

[0001]
type=aor
max_contacts=1

[0777]
type=endpoint
auth=0777
aors=0777
context=internal

[0777]
type=auth
auth_type=userpass
password=password123
username=0777

[0777]
type=aor
max_contacts=1
"""

# extensions.conf
EXTENSIONS_CONFIG = """
[general]
static=yes
writeprotect=no

[internal]
; Входящие звонки направляются в Stasis приложение SmartCallCenter
exten => _X.,1,NoOp(Incoming call to ${EXTEN})
same => n,Stasis(SmartCallCenter,${EXTEN})
same => n,Hangup()

; Исходящие звонки между операторами
exten => _0XXX,1,NoOp(Internal call to ${EXTEN})
same => n,Dial(PJSIP/${EXTEN},30)
same => n,Hangup()

[from-trunk]
; Входящие звонки с транка
exten => _X.,1,NoOp(External incoming call: ${CALLERID(num)} -> ${EXTEN})
same => n,Set(CALLERID(name)=External Call)
same => n,Goto(internal,${EXTEN},1)
"""

# ari.conf
ARI_CONFIG = """
[general]
enabled=yes
pretty=yes

[smart-call-center]
type=user
read_only=no
password=Almaty20252025
"""

# http.conf
HTTP_CONFIG = """
[general]
enabled=yes
bindaddr=0.0.0.0
bindport=8088
"""

# CLI команды для применения конфигурации
ASTERISK_CLI_COMMANDS = """
# Перезагрузка конфигурации
asterisk -rx "reload"

# Проверка PJSIP endpoints
asterisk -rx "pjsip show endpoints"

# Проверка ARI пользователей
asterisk -rx "ari show users"

# Проверка HTTP статуса
asterisk -rx "http show status"

# Просмотр активных каналов
asterisk -rx "core show channels"

# Тестирование Stasis приложения
asterisk -rx "stasis show apps"
"""

SETUP_INSTRUCTIONS = """
📋 ИНСТРУКЦИИ ПО НАСТРОЙКЕ ASTERISK

1. 📁 Скопируйте конфигурации в /etc/asterisk/:
   - pjsip.conf
   - extensions.conf  
   - ari.conf
   - http.conf

2. 🔄 Перезапустите Asterisk:
   systemctl restart asterisk

3. 🔍 Проверьте статус:
   asterisk -rx "pjsip show endpoints"
   asterisk -rx "ari show users"

4. 📞 Настройте SIP телефоны:
   Extension: 0001, Password: password123
   Extension: 0777, Password: password123
   Server: IP_ASTERISK:5060

5. ✅ Проверьте подключение в Smart Call Center:
   Админ панель -> Asterisk статус -> должно показывать "Connected"

⚠️  ВАЖНО: 
- Stasis приложение SmartCallCenter должно быть активно
- ARI пользователь smart-call-center должен иметь права на чтение/запись
- HTTP сервер должен быть доступен на порту 8088

🎯 РЕЗУЛЬТАТ:
После настройки входящие звонки будут автоматически:
1. Попадать в Stasis приложение SmartCallCenter
2. Отображаться в интерфейсе оператора
3. Записываться в базу данных
4. Передавать real-time уведомления через WebSocket
"""
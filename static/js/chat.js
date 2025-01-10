const link = document.getElementById("link_for_json");
const URL = link.href;  //"http://127.0.0.1:2025/ajax_messages";

const time = 500;



function sendRequest(method, url, body = null) {
    const headers = {
        "Content-Type": "application/json"
    };

    // Проверяем метод запроса и устанавливаем тело, если это не GET
    const requestOptions = {
        method: method,
        headers: headers
    };

    if (method !== 'GET' && body !== null) {
        requestOptions.body = JSON.stringify(body);
    }

    return fetch(url, requestOptions)
        .then(response => {
            if (!response.ok) {
                throw new Error(`Network response was not ok: ${response.status}`);
            }
            return response.json();
        })
        .catch(error => {
            console.error('Error during fetch:', error);
            throw error;
        });
}


let lastAvatars = {}; // Объект для хранения последних URL аватарок по имени пользователя

function updateChat() {
    sendRequest('GET', URL)
        .then(data => {
            const myBlock = document.getElementById('main_for_messages');
            let textHtml = "";

            for (let i = 1; i < data.messages.length; i++) {
                const message = data.messages[i];

                if (message.user_name === "Me") {
                    if (message.avatar === "") {
                        textHtml += `
                        <div class="msg right-msg">
                            <div class="msg-bubble">
                                <div class="msg-info">
                                    <div class="msg-info-time">${message.created_at}</div>
                                </div>
                                <div class="msg-text">${message.message}</div>
                            </div>
                        </div>`;
                    } else {

                        textHtml += `
                        <div class="msg right-msg">
                            <div class="msg-bubble">
                                <div class="msg-info">
                                    <div class="msg-info-time">${message.created_at}</div>
                                </div>
                                <div class="msg-text">${message.message}</div>
                            </div>
                        </div>`;
                    }
                } else {
                    if (message.avatar === "") {
                        textHtml += `
                        <div class="msg left-msg">
                            <div class="msg-bubble" style="margin: 0px 0px 0px 50px">
                                <div class="msg-info">
                                    <div class="msg-info-name">${message.user_name}</div>
                                    <div class="msg-info-time">${message.created_at}</div>
                                </div>
                                <div class="msg-text">${message.message}</div>
                            </div>
                        </div>`;
                    } else {
                        // Проверка изменения аватарки для других пользователей
                        if (lastAvatars[message.user_name] !== message.avatar) {
                            lastAvatars[message.user_name] = message.avatar;
                        }
                        textHtml += `
                        <div class="msg left-msg">
                            <div class="msg-img"><img src="${message.avatar}" alt="Avatar"></div>
                            <div class="msg-bubble">
                                <div class="msg-info">
                                    <div class="msg-info-name">${message.user_name}</div>
                                    <div class="msg-info-time">${message.created_at}</div>
                                </div>
                                <div class="msg-text">${message.message}</div>
                            </div>
                        </div>`;
                    }
                }
            }

            myBlock.innerHTML = textHtml;
        })
        .catch(error => {
            console.error('Error after fetch:', error);
        });
}


// Функция для отправки сообщения
async function addMessage() {
    const messageInput = document.getElementById('messageInput');
    const message = messageInput.value;

    // Проверяем, чтобы не отправлять пустые сообщения
    if (message.trim() !== '') {
        const data = { message: message };
        try {
            const response = await sendRequest("POST", URL, data);
            console.log(response);
            // После успешной отправки данных очищаем поле ввода
            messageInput.value = "";
        } catch (error) {
            console.error('Error after fetch:', error);
        }
    }
}

// Обработчик нажатия клавиши Enter
document.getElementById('messageInput').addEventListener('keydown', function (event) {
    if (event.key === 'Enter') {
        event.preventDefault(); // Предотвращаем стандартное поведение Enter (например, переход строки)
        addMessage(); // Вызываем функцию отправки сообщения
    }
});

// Получаем ссылку на кнопку отправки
const sendButton = document.getElementById('my_button');


// Добавляем обработчик события к кнопке
sendButton.addEventListener('click', addMessage);

// Инициировать первое обновление чата
updateChat();

// Запускать обновление чата каждую секунду
setInterval(updateChat, time);
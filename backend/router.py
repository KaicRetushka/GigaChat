from fastapi import APIRouter, Response, HTTPException, Path, Depends, Request, Body

from backend.pydantic_classes import BudyReg, BodyVhod, BodyMessage, BodyNewTitle
from backend.jwt import security, config
from backend.database.requests import insert_user, check_user, insert_message_create_chat, insert_message_with_history, delete_chat_db, update_chat_db

router = APIRouter()

@router.post("/reg", tags=["Регистрация"])
async def post_reg(body: BudyReg, response: Response):
    response_db = insert_user(body.login, body.name, body.surname, body.password)
    if response_db:
        token = security.create_access_token(uid=str(response_db))
        response.set_cookie(config.JWT_ACCESS_COOKIE_NAME, token)
        return {"detail": "Вы успешно зарегистрировались", "access_token": token}
    raise HTTPException(status_code=409, detail="Такой логин уже занят")

@router.post("/vhod", tags=["Вход"])
async def post_vhod(body: BodyVhod, response: Response):
    response_db = check_user(body.login, body.password)
    if response_db:
        token = security.create_access_token(uid=str(response_db))
        response.set_cookie(config.JWT_ACCESS_COOKIE_NAME, token)
        return {"detail": "Вы успешно вошли", "acces_token": token}
    raise HTTPException(status_code=404, detail="Неверный логин или пароль")


@router.post("/message", dependencies=[Depends(security.access_token_required)], tags=["Отправка первого сообщения в новый чат"])
async def post_message(request: Request, body: BodyMessage):
    token = request.cookies.get(config.JWT_ACCESS_COOKIE_NAME)
    user_id = security._decode_token(token).sub
    answer = insert_message_create_chat(user_id, body.text)
    return answer

@router.post("/message/{chat_id}", dependencies=[Depends(security.access_token_required)], tags=["Отпрака сообщения в существующий чат"])
async def post_message_chat_id(request: Request, chat_id: int, body: BodyMessage):
    token = request.cookies.get(config.JWT_ACCESS_COOKIE_NAME)
    user_id = security._decode_token(token).sub
    answer = insert_message_with_history(user_id, chat_id, body.text)
    if answer:
        return {"answer_ai": answer}
    raise HTTPException(status_code=404, detail="Чат не найден")

@router.delete("/chat/{id}", tags=["Удаление чата"])
async def delete_chat(request: Request, id: int):
    token = request.cookies.get(config.JWT_ACCESS_COOKIE_NAME)
    user_id = security._decode_token(token).sub
    data = delete_chat_db(user_id, id)
    if data:
        return {"detail": "Чат удалён"}
    raise HTTPException(status_code=404, detail="Неверный id чата")

@router.put("/chat/{id}", tags=["Изменение название чата"])
async def put_chat(request: Request, id: int, body: BodyNewTitle):
    token = request.cookies.get(config.JWT_ACCESS_COOKIE_NAME)
    user_id = security._decode_token(token).sub
    data = update_chat_db(user_id, id, body.new_title)
    if data:
        return {"detail": "Название чата изменено"}
    raise HTTPException(status_code=404, detail="Неверный id чата")

@router.delete("/exit", tags=["Выход"])
async def exit(response: Response):
    response.delete_cookie(config.JWT_ACCESS_COOKIE_NAME)
    return {"detail": "Вы успешно вышли"}
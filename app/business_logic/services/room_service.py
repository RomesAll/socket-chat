from datetime import datetime
from uuid import UUID
from app.business_logic.exceptions import ChangeOwnerRoomPermDenied
from app.business_logic.redis_adapter import Cache
from app.data_layer.exceptions import RemoveMemberInRoomPermDenied, RecordNotFound, DeleteRoomPermDenied
from app.data_layer.models import RoomRole, RoomMember
from app.business_logic.unit_of_work import UnitOfWork
from app.shared.dto.chat import ChatDtoGet, ChatDtoSave
from app.shared.dto.room import (
    RoomDtoSave,
    RoomMemberDtoSave,
    RoomDtoGet,
    RoomMemberDtoGet,
    RoomDtoGetWithChats,
    GenerateInviteToken
)
from app.shared.log_config import LogMixin
from app.shared.config import get_config, BaseConfig
import random


def _get_config() -> BaseConfig:
    return get_config()


class RoomService(LogMixin):
    """Сервис для управления комнатами"""
    def __init__(self, uow: UnitOfWork, cache: Cache):
        self._uow = uow
        self._cache = cache

    async def add_room(self, room_dto_save: RoomDtoSave, chat_dto_save: ChatDtoSave) -> RoomDtoGetWithChats:
        """
        Создание новой комнаты и и базовым чатом для пользователей.
        Алгоритм:\n
        - сохранение комнаты в бд
        - сохранение базового чата в бд
        - владелец комнаты автоматически добавляется в участники комнаты и чата
        - у владельца устанавливается возможность получить доступ к приватным чатам
        - информация о комнате и чатах сохраняется в кеш
        :param room_dto_save: dto для сохранения комнаты
        :param chat_dto_save: dto для сохранения базового чата
        :return:
        """
        async with self._uow as uow:
            room_orm = await uow.room_repo.save(room_dto_save)
            chat_orm = await uow.chat_repo.save(chat_dto_save)
            await uow.room_repo.add_room_member_owner(
                room_id=room_orm.id,
                user_id=room_orm.owner_id,
            )
            await uow.chat_repo.add_chat_member(
                chat_id=chat_orm.id,
                user_id=room_orm.owner_id
            )
            self.log_info(f'Пользователь {room_orm.owner_id} успешно создал комнату с id {room_orm.id}')
            result = RoomDtoGetWithChats(
                **room_orm.to_dict(), chats=[ChatDtoGet(**chat_orm.to_dict())]
            )
        is_saved = await self._cache.save_room(result)
        if not is_saved:
            self.log_warning(f'Комната {room_dto_save.id} не была сохранена в кеше')
        return result

    async def generate_invite_token(self, url_info: GenerateInviteToken) -> tuple[str, datetime]:
        """
        Генерация и сохранение url ссылки для вступления в комнату
        :param url_info: dto для генерации ссылки
        :return: токен и время истечения токена
        """
        async with self._uow as uow:
            token, exp = await uow.invite_url_repo.generate_url(url_info)
            self.log_info(f'Пользователь {url_info.actor_id} '
                          f'сгенерировал url для вступления в комнату {url_info.room_id}')
            return token, exp

    async def add_member_in_room(self, url_token: str, member: RoomMemberDtoSave) -> RoomMemberDtoGet:
        """
        Добавление нового участника в комнату по url токену.
        Алгоритм:
        - проверка существования и активности токена
        - проверка кол-во использований, если превышает, то исключение
        - увеличение счетчика в противном случае
        - добавление пользователя в комнату
        :param url_token: токен
        :param member: dto для сохранения участника
        :return:
        """
        async with self._uow as uow:
            await uow.invite_url_repo.accept_url_token(url_token)
            room_member_orm = await uow.room_repo.add_member_in_room(member)
            self.log_info(f'Пользователь {member.user_id} успешно добавлен в комнату {room_member_orm.room_id}')
            response = RoomMemberDtoGet(**room_member_orm.to_dict())
            return response

    async def remove_member_in_room(self, room_id: UUID, user_id: str, actor_id: str) -> RoomMemberDtoGet:
        """
        Удаление участника из комнаты. Алгоритм:
        - проверка существования комнаты и пользователя в комнате
        - если актер (тот кто вып. действие) удаляет не себя, то проверяется роль (удалять других может админ или владелец)
        - удаление участника из комнаты
        - удаление участника из всех чатов
        - если владелец удаляет сам себя, то запускается алг. смены владельца на случайного
        - если участников, помимо владельца, больше нет, то удаляется комната со всеми чатами
        :param room_id: id комнаты
        :param user_id: id пользователя
        :param actor_id: id пользователя, который вып. действие
        :return:
        """
        async with self._uow as uow:
            room_info = await uow.room_repo.get_record_by_id(room_id)
            member_room = await uow.room_repo.get_member_in_room_by_id(room_id, actor_id)
            if actor_id != user_id:
                if actor_id != room_info.owner_id and member_room.role != RoomRole.ADMIN:
                    raise RemoveMemberInRoomPermDenied(room_id, user_id, actor_id)
            chats = await uow.chat_repo.get_user_chat_in_room(room_id, user_id)
            room_member_orm = await uow.room_repo.remove_member_in_room(room_id, user_id)
            for chat in chats:
                try:
                    await uow.chat_repo.remove_chat_member(
                        chat_id=chat.id,
                        user_id=user_id
                    )
                except RecordNotFound:
                    continue
            if user_id == actor_id and user_id == room_info.owner_id:
                members = await uow.room_repo.get_room_members(room_id)
                if len(members) == 0:
                    await uow.room_repo.delete(room_id)
                    self.log_info(f'При удалении владельца {user_id} была удалена и комната {room_id}, '
                                  f'т.к. в ней больше нет участников')
                else:
                    new_owner: RoomMember = random.choice(members)
                    room_info.owner_id = new_owner.user_id
                    new_owner.is_access_private_chat = True
                    new_owner.role = RoomRole.OWNER
            self.log_info(f'Пользователь {user_id} успешно удален из комнаты {room_id}')
            response = RoomMemberDtoGet(**room_member_orm.to_dict())
            return response

    async def change_owner(self, room_id: UUID, new_owner: str, actor_id: str) -> RoomDtoGet:
        """
        Смена владельца комнаты. Алгоритм:
        - получение информации о комнате
        - если actor не является владельцем, то доступ запрещен
        - если actor владелец, то происходит процесс смены владельца
        :param room_id: id комнаты
        :param new_owner: id нового владельца
        :param actor_id: id пользователя, который вып. действие
        :return:
        """
        async with self._uow as uow:
            owner_id = await uow.room_repo.get_room_owner(room_id)
            if owner_id != actor_id:
                raise ChangeOwnerRoomPermDenied(actor_id, room_id)
            room_info = await uow.room_repo.change_owner(room_id, new_owner)
            self.log_info(f'Пользователь {actor_id} успешно сменил пользователя в комнате {room_id}')
            result = RoomDtoGet(**room_info.to_dict())
            return result

    async def delete_room(self, room_id: UUID, actor_id: str) -> RoomDtoGet:
        """
        Удаление комнаты. Алгоритм:
        - проверка существования комнаты
        - если удалить комнаты пытается не владелец, то исключение
        - удаление чатов в комнате
        - удаление комнаты
        :param actor_id: id пользователя, который выполнил действие
        :param room_id: id комнаты
        :return:
        """
        async with self._uow as uow:
            room_info = await uow.room_repo.get_record_by_id(room_id)
            if room_info.owner_id != actor_id:
                raise DeleteRoomPermDenied(room_id, actor_id)
            room_orm_deleted = await uow.room_repo.delete(room_id)
            chats = await uow.chat_repo.get_chat_by_room(room_id)
            for chat in chats:
                await uow.chat_repo.delete(chat.id)
            self.log_info(f'Комната была удалена {room_id}')
            response = RoomDtoGet(**room_orm_deleted.to_dict())
        is_saved = await self._cache.delete_room_info(room_id)
        if not is_saved:
            self.log_warning(f'Комната {room_id} не была удалена из кеша')
        return response

    async def get_user_rooms(self, user_id: str) -> list[RoomDtoGet]:
        """Получение информации о комнатах, в которых состоит пользователь"""
        async with self._uow as uow:
            rooms = await uow.room_repo.get_user_rooms(user_id)
            response = [
                RoomDtoGet(**room.to_dict())
                for room in rooms
            ]
            return response

    async def get_user_owner_rooms(self, user_id: str) -> list[RoomDtoGet]:
        """Получение информации о комнатах, в которых пользователь является владельцем"""
        async with self._uow as uow:
            rooms = await uow.room_repo.get_user_owner_rooms(user_id)
            response = [
                RoomDtoGet(**room.to_dict())
                for room in rooms
            ]
            return response

    async def get_member_in_room(self, room_id: UUID) -> list[RoomMemberDtoGet]:
        """Получить участников комнаты"""
        async with self._uow as uow:
            list_room_member_orm = await uow.room_repo.get_member_in_room(room_id)
            response = [
                RoomMemberDtoGet(**room_orm.to_dict())
                for room_orm in list_room_member_orm
            ]
            return response
import contextvars
import json
import logging
import os
from datetime import datetime
from typing import Any

from code_agent.core.session import Session

logger = logging.getLogger()

current_session = contextvars.ContextVar[Session]("current_session")


class SessionManager:
    """会话管理器
    管理会话的创建、保存、加载和切换
    """

    def __init__(self, sessions_dir: str):
        """初始化会话管理器

        Args:
            sessions_dir: 会话存储文件夹路径
        """
        logger.debug(f"初始化会话管理器, 存储目录: {sessions_dir}")
        self.sessions_dir = sessions_dir
        self.last_session_file = os.path.join(sessions_dir, "last_session.json")
        os.makedirs(sessions_dir, exist_ok=True)
        logger.info("会话管理器初始化完成")

    def create_session(self) -> Session:
        """创建新会话

        Returns:
            会话实例
        """
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        logger.info(f"创建新会话: {session_id}")
        session = Session(session_id)
        self.save_session(session)
        return session

    def save_session(self, session: Session):
        """保存会话"""
        logger.debug(f"保存会话: {session.session_id}")

        session.updated_at = datetime.now().isoformat()
        session_file = os.path.join(self.sessions_dir, f"{session.session_id}.json")

        try:
            with open(session_file, "w", encoding="utf-8") as f:
                json.dump(session.to_dict(), f, ensure_ascii=False, indent=2)

            with open(self.last_session_file, "w", encoding="utf-8") as f:
                json.dump({"last_session_id": session.session_id}, f)

            logger.debug(f"会话 {session.session_id} 保存成功")
        except Exception as e:
            logger.error(f"保存会话 {session.session_id} 失败: {e}", exc_info=True)
            raise

    def load_last_session(self) -> Session | None:
        """加载上次会话

        Returns:
            会话实例或 None
        """
        logger.debug("加载最后会话")

        if not os.path.exists(self.last_session_file):
            logger.debug("未找到 last_session.json")
            return None

        try:
            with open(self.last_session_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                session_id = data.get("last_session_id")
                if session_id:
                    logger.info(f"加载会话: {session_id}")
                    return self.load_session(session_id)
        except Exception as e:
            logger.error(f"加载最后会话失败: {e}", exc_info=True)

        return None

    def load_session(self, session_id: str) -> Session | None:
        """加载指定会话

        Args:
            session_id: 会话ID

        Returns:
            是否成功加载
        """
        logger.debug(f"加载指定会话: {session_id}")

        session_file = os.path.join(self.sessions_dir, f"{session_id}.json")
        if not os.path.exists(session_file):
            logger.warning(f"会话文件不存在: {session_file}")
            return None

        try:
            with open(session_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                session = Session.from_dict(data)
            logger.debug(f"会话 {session_id} 加载成功")
            return session
        except Exception as e:
            logger.error(f"加载会话 {session_id} 失败: {e}", exc_info=True)
            return None

    def delete_session(self, session_id: str) -> bool:
        """删除指定会话

        Args:
            session_id: 会话ID

        Returns:
            是否成功删除
        """
        logger.info(f"删除会话: {session_id}")

        session_file = os.path.join(self.sessions_dir, f"{session_id}.json")
        if os.path.exists(session_file):
            try:
                os.remove(session_file)
                logger.debug(f"会话文件已删除: {session_file}")

                if os.path.exists(self.last_session_file):
                    try:
                        with open(self.last_session_file, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            if data.get("last_session_id") == session_id:
                                sessions = self.get_session_list()
                                new_last = sessions[0]["id"] if sessions else None

                                with open(self.last_session_file, "w", encoding="utf-8") as f:
                                    json.dump({"last_session_id": new_last}, f)
                                logger.debug(f"更新最后会话为: {new_last}")
                    except Exception as e:
                        logger.error(f"更新 last_session.json 失败: {e}", exc_info=True)

                logger.info(f"会话 {session_id} 删除成功")
                return True
            except Exception as e:
                logger.error(f"删除会话 {session_id} 失败: {e}", exc_info=True)
                return False
        else:
            logger.warning(f"会话 {session_id} 不存在")
            return False

    def get_session_list(self) -> list[dict[str, Any]]:
        """获取所有会话列表"""
        sessions: list[dict[str, Any]] = []
        if not os.path.exists(self.sessions_dir):
            return sessions

        for filename in os.listdir(self.sessions_dir):
            if filename.endswith(".json") and filename != "last_session.json":
                session_id = filename[:-5]
                session_file = os.path.join(self.sessions_dir, filename)
                try:
                    with open(session_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        sessions.append(
                            {
                                "id": session_id,
                                "created_at": data.get("created_at", ""),
                                "updated_at": data.get("updated_at", ""),
                                "message_count": len(data.get("messages", [])),
                            }
                        )
                except Exception:
                    pass

        # 按更新时间排序
        sessions.sort(key=lambda x: x["updated_at"], reverse=True)
        return sessions

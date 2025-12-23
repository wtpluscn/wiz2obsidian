import datetime
import os
import sys
from log import log
import requests


class FileManager:
    # 应用程序根目录缓存
    _app_root = None

    @staticmethod
    def get_app_root():
        """获取应用程序根目录"""
        if FileManager._app_root is None:
            if getattr(sys, "frozen", False):
                # 如果是打包后的可执行文件
                FileManager._app_root = os.path.dirname(sys.executable)
            else:
                # 如果是开发环境
                FileManager._app_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return FileManager._app_root

    @staticmethod
    def _create_directory(directory_path):
        os.makedirs(directory_path, exist_ok=True)

    @staticmethod
    def _write_file(directory_path, file_name, content):
        file_path = os.path.join(directory_path, file_name)
        with open(file_path, "w", encoding='utf-8') as file:
            file.write(content)

    @staticmethod
    def _write_bfile(directory_path, file_name, content):
        file_path = os.path.join(directory_path, file_name)
        with open(file_path, "wb") as file:
            file.write(content)

    @staticmethod
    def sanitize_filename(filename):
        """
        清理文件名，确保跨平台兼容性
        :param filename: 原始文件名
        :return: 安全的文件名
        """
        # Windows禁用字符: < > : " | ? * / \
        # 其他系统主要是 /
        unsafe_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        
        safe_filename = filename
        for char in unsafe_chars:
            safe_filename = safe_filename.replace(char, '_')
        
        # 移除前后空白和点号（防止隐藏文件或路径问题）
        safe_filename = safe_filename.strip(' .')
        
        # 限制长度（大多数文件系统限制255字符）
        if len(safe_filename) > 200:  # 留一些余量给.md扩展名
            safe_filename = safe_filename[:200]
        
        # 确保不是空文件名
        if not safe_filename:
            safe_filename = "untitled"
            
        return safe_filename

    @staticmethod
    def save_md_to_file(category, title, content, create_time=None):
        """
        保存md文件
        :param category:  笔记的目录 eg: /xx1/xx2/
        :param title: 笔记标题
        :param content: 笔记内容
        :param create_time: 创建时间（datetime对象、时间戳或字符串）
        :return:
        """
        log.info(f"开始保存笔记: {title}, 分类: {category}, 创建时间: {create_time}")
        
        # 使用绝对路径
        app_root = FileManager.get_app_root()
        output_directory = os.path.join(app_root, "output", "note", category.strip("/").replace("/", os.path.sep))
        FileManager._create_directory(output_directory)
    
        # 清理标题，确保文件名安全
        safe_title = FileManager.sanitize_filename(title)
        
        # 如果 title 是以 .md 结尾, 新文件的文件名无需添加 .md
        if safe_title.endswith(".md"):
            safe_title = safe_title[:-3]
    
        file_path = os.path.join(output_directory, safe_title + '.md')
        FileManager._write_file(output_directory, safe_title + '.md', content)
        log.info(f"笔记内容已写入文件: {file_path}")
        
        # 设置文件的创建和修改时间
        if create_time is not None:
            log.info(f"尝试设置文件 {file_path} 的时间为: {create_time}")
            # 转换为时间戳
            if isinstance(create_time, str):
                # 如果是字符串格式的时间，先转换为datetime对象
                try:
                    create_time = datetime.strptime(create_time, "%Y-%m-%d %H:%M:%S")
                    log.info(f"将字符串时间转换为datetime对象: {create_time}")
                except ValueError:
                    # 如果格式不正确，尝试其他常见格式
                    try:
                        create_time = datetime.strptime(create_time, "%Y-%m-%d")
                        log.info(f"将字符串时间转换为datetime对象: {create_time}")
                    except ValueError:
                        # 如果还是无法解析，忽略时间设置
                        log.warning(f"无法解析时间字符串: {create_time}，跳过时间设置")
                        return
            
            if hasattr(create_time, 'timestamp'):
                # 如果是datetime对象
                timestamp = create_time.timestamp()
                log.info(f"将datetime对象转换为时间戳: {timestamp}")
            else:
                # 如果已经是时间戳
                timestamp = create_time
                log.info(f"使用原始时间戳: {timestamp}")
            
            # 设置文件的创建和修改时间
            try:
                os.utime(file_path, (timestamp, timestamp))
                log.info(f"成功设置文件 {file_path} 的时间为时间戳: {timestamp}")
            except Exception as e:
                log.error(f"设置文件时间失败: {e}")
        else:
            log.warning(f"没有提供创建时间，跳过时间设置")

    # 保存图片到本地
    @staticmethod
    def save_image_to_file(category, title, file_name, content, create_time=None):
        app_root = FileManager.get_app_root()
        # 清理标题，确保目录名安全
        safe_title = FileManager.sanitize_filename(title)
        output_directory = os.path.join(app_root, "output", "export_image", category.strip("/").replace("/", os.path.sep), safe_title)
        FileManager._create_directory(output_directory)
        full_path = os.path.join(output_directory, file_name)
        FileManager._write_bfile(output_directory, file_name, content)
        
        # 设置文件的创建和修改时间
        if create_time is not None:
            log.info(f"尝试设置图片文件 {full_path} 的时间为: {create_time}")
            # 转换为时间戳
            if isinstance(create_time, str):
                # 如果是字符串格式的时间，先转换为datetime对象
                try:
                    create_time = datetime.strptime(create_time, "%Y-%m-%d %H:%M:%S")
                    log.info(f"将字符串时间转换为datetime对象: {create_time}")
                except ValueError:
                    # 如果格式不正确，尝试其他常见格式
                    try:
                        create_time = datetime.strptime(create_time, "%Y-%m-%d")
                        log.info(f"将字符串时间转换为datetime对象: {create_time}")
                    except ValueError:
                        # 如果还是无法解析，忽略时间设置
                        log.warning(f"无法解析时间字符串: {create_time}，跳过时间设置")
                        return
            
            if hasattr(create_time, 'timestamp'):
                # 如果是datetime对象
                timestamp = create_time.timestamp()
                log.info(f"将datetime对象转换为时间戳: {timestamp}")
            else:
                # 如果已经是时间戳
                timestamp = create_time
                log.info(f"使用原始时间戳: {timestamp}")
            
            # 设置文件的创建和修改时间
            try:
                os.utime(full_path, (timestamp, timestamp))
                log.info(f"成功设置图片文件 {full_path} 的时间为时间戳: {timestamp}")
            except Exception as e:
                log.error(f"设置图片文件时间失败: {e}")

    @staticmethod
    def get_img_directory(record):
        """
        获取图片保存目录: 当前笔记同级目录下 ./images/
        :param record: 笔记同步记录
        :return:
        """
        app_root = FileManager.get_app_root()
        return os.path.join(app_root, "output", "note", record['category'].strip("/").replace("/", os.path.sep), "images")

    @staticmethod
    def get_attachments_directory(record):
        """
        获取附件保存目录: 当前笔记同级目录下 ./attachments/
        :param record: 笔记同步记录
        :return:
        """
        app_root = FileManager.get_app_root()
        return os.path.join(app_root, "output", "note", record['category'].strip("/").replace("/", os.path.sep), "attachments")

    @staticmethod
    def image_file_is_not_exist(record, img_file_name):
        img_directory = FileManager.get_img_directory(record)
        full_path = os.path.join(img_directory, img_file_name)
        return not os.path.exists(full_path)

    @staticmethod
    def download_img_from_url(record, img_file_name, url, create_time=None):
        img_directory = FileManager.get_img_directory(record)
        FileManager._create_directory(img_directory)
        full_path = os.path.join(img_directory, img_file_name)
        log.info(f"download_img_from_url {full_path}")

        response = requests.get(url)
        response.raise_for_status()  # 检查请求是否成功
        with open(full_path, 'wb') as file:
            file.write(response.content)
        log.info(f"文件下载完成 {img_file_name}")
        
        # 设置文件的创建和修改时间
        if create_time is not None:
            log.info(f"尝试设置图片文件 {full_path} 的时间为: {create_time}")
            # 转换为时间戳
            if isinstance(create_time, str):
                # 如果是字符串格式的时间，先转换为datetime对象
                try:
                    create_time = datetime.strptime(create_time, "%Y-%m-%d %H:%M:%S")
                    log.info(f"将字符串时间转换为datetime对象: {create_time}")
                except ValueError:
                    # 如果格式不正确，尝试其他常见格式
                    try:
                        create_time = datetime.strptime(create_time, "%Y-%m-%d")
                        log.info(f"将字符串时间转换为datetime对象: {create_time}")
                    except ValueError:
                        # 如果还是无法解析，忽略时间设置
                        log.warning(f"无法解析时间字符串: {create_time}，跳过时间设置")
                        return
            
            if hasattr(create_time, 'timestamp'):
                # 如果是datetime对象
                timestamp = create_time.timestamp()
                log.info(f"将datetime对象转换为时间戳: {timestamp}")
            else:
                # 如果已经是时间戳
                timestamp = create_time
                log.info(f"使用原始时间戳: {timestamp}")
            
            # 设置文件的创建和修改时间
            try:
                os.utime(full_path, (timestamp, timestamp))
                log.info(f"成功设置图片文件 {full_path} 的时间为时间戳: {timestamp}")
            except Exception as e:
                log.error(f"设置图片文件时间失败: {e}")

    @staticmethod
    def download_img_from_byte(record, img_file_name, byte, create_time=None):
        img_directory = FileManager.get_img_directory(record)
        FileManager._create_directory(img_directory)
        full_path = os.path.join(img_directory, img_file_name)
        log.info(f"download_img_from_byte {full_path}")
        with open(full_path, "wb") as file:
            file.write(byte)
        
        # 设置文件的创建和修改时间
        if create_time is not None:
            log.info(f"尝试设置图片文件 {full_path} 的时间为: {create_time}")
            # 转换为时间戳
            if isinstance(create_time, str):
                # 如果是字符串格式的时间，先转换为datetime对象
                try:
                    create_time = datetime.strptime(create_time, "%Y-%m-%d %H:%M:%S")
                    log.info(f"将字符串时间转换为datetime对象: {create_time}")
                except ValueError:
                    # 如果格式不正确，尝试其他常见格式
                    try:
                        create_time = datetime.strptime(create_time, "%Y-%m-%d")
                        log.info(f"将字符串时间转换为datetime对象: {create_time}")
                    except ValueError:
                        # 如果还是无法解析，忽略时间设置
                        log.warning(f"无法解析时间字符串: {create_time}，跳过时间设置")
                        return
            
            if hasattr(create_time, 'timestamp'):
                # 如果是datetime对象
                timestamp = create_time.timestamp()
                log.info(f"将datetime对象转换为时间戳: {timestamp}")
            else:
                # 如果已经是时间戳
                timestamp = create_time
                log.info(f"使用原始时间戳: {timestamp}")
            
            # 设置文件的创建和修改时间
            try:
                os.utime(full_path, (timestamp, timestamp))
                log.info(f"成功设置图片文件 {full_path} 的时间为时间戳: {timestamp}")
            except Exception as e:
                log.error(f"设置图片文件时间失败: {e}")

    @staticmethod
    def download_attachment_from_byte(record, att_file_name, byte_content, create_time=None):
        """
        从二进制内容下载附件到本地
        :param record: 笔记同步记录
        :param att_file_name: 附件文件名
        :param byte_content: 附件二进制内容
        :param create_time: 创建时间（datetime对象、时间戳或字符串）
        :return:
        """
        attachments_directory = FileManager.get_attachments_directory(record)
        FileManager._create_directory(attachments_directory)
        full_path = os.path.join(attachments_directory, att_file_name)
        log.info(f"download_attachment_from_byte {full_path}")
        with open(full_path, "wb") as file:
            file.write(byte_content)
        
        # 设置文件的创建和修改时间
        if create_time is not None:
            log.info(f"尝试设置附件文件 {full_path} 的时间为: {create_time}")
            # 转换为时间戳
            if isinstance(create_time, str):
                # 如果是字符串格式的时间，先转换为datetime对象
                try:
                    create_time = datetime.strptime(create_time, "%Y-%m-%d %H:%M:%S")
                    log.info(f"将字符串时间转换为datetime对象: {create_time}")
                except ValueError:
                    # 如果格式不正确，尝试其他常见格式
                    try:
                        create_time = datetime.strptime(create_time, "%Y-%m-%d")
                        log.info(f"将字符串时间转换为datetime对象: {create_time}")
                    except ValueError:
                        # 如果还是无法解析，忽略时间设置
                        log.warning(f"无法解析时间字符串: {create_time}，跳过时间设置")
                        return
            
            if hasattr(create_time, 'timestamp'):
                # 如果是datetime对象
                timestamp = create_time.timestamp()
                log.info(f"将datetime对象转换为时间戳: {timestamp}")
            else:
                # 如果已经是时间戳
                timestamp = create_time
                log.info(f"使用原始时间戳: {timestamp}")
            
            # 设置文件的创建和修改时间
            try:
                os.utime(full_path, (timestamp, timestamp))
                log.info(f"成功设置附件文件 {full_path} 的时间为时间戳: {timestamp}")
            except Exception as e:
                log.error(f"设置附件文件时间失败: {e}")

    @staticmethod
    def get_not_in_local_img(record, need_upload_images):
        """
        获取本地资源管理器不存在的图片
        :param record: 上传记录
        :param need_upload_images: 需要上传图片的文件名
        :return: 本地不存在的文件名
        """
        # 如果需要上传图片的集合为空, 直接返回空dict
        if not need_upload_images:
            return {}

        # 判断哪些图片文件没有保存到本地
        not_in_local_img = list(filter(lambda x: FileManager.image_file_is_not_exist(record, x), need_upload_images))
        log.info(f'not_in_local_img: {not_in_local_img} need_upload_images: {need_upload_images}')
        return not_in_local_img
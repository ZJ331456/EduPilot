#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EduPilot API 模块启动入口
支持通过 python -m src.interfaces.api 启动服务
"""

import sys
import argparse
import logging


def setup_logging(log_level: str = "INFO"):
    """配置日志系统"""
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {log_level}")
    
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="EduPilot API 服务器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 默认启动（127.0.0.1:8000）
  python -m src.interfaces.api
  
  # 自定义端口
  python -m src.interfaces.api --port 8080
  
  # 开发模式（自动重载）
  python -m src.interfaces.api --reload
  
  # 生产模式（所有网卡，多进程）
  python -m src.interfaces.api --host 0.0.0.0 --port 8000 --workers 4
  
  # 指定日志级别
  python -m src.interfaces.api --log-level DEBUG
  
  # 完整配置
  python -m src.interfaces.api --host 0.0.0.0 --port 8080 --reload --log-level INFO
        """,
    )
    
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="服务器主机地址 (默认: 127.0.0.1)",
    )
    
    parser.add_argument(
        "-p", "--port",
        type=int,
        default=8000,
        help="服务器端口 (默认: 8000)",
    )
    
    parser.add_argument(
        "-r", "--reload",
        action="store_true",
        help="启用自动重载（开发模式）",
    )
    
    parser.add_argument(
        "-w", "--workers",
        type=int,
        default=1,
        help="工作进程数（生产模式，默认: 1）",
    )
    
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="日志级别 (默认: INFO)",
    )
    
    parser.add_argument(
        "--no-access-log",
        action="store_true",
        help="禁用访问日志",
    )
    
    args = parser.parse_args()
    
    # 配置日志
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    # 打印启动信息
    print()
    print("=" * 70)
    print("🚀 EduPilot API 服务器")
    print("=" * 70)
    print(f"📍 地址: http://{args.host}:{args.port}")
    print(f"📖 API文档: http://{args.host}:{args.port}/api/agent/v1/docs")
    print(f"📊 健康检查: http://{args.host}:{args.port}/api/agent/v1/health")
    print(f"🔄 自动重载: {'✅ 开启' if args.reload else '❌ 关闭'}")
    print(f"👥 工作进程: {args.workers}")
    print(f"📝 日志级别: {args.log_level}")
    print("=" * 70)
    
    if args.host == "0.0.0.0":
        print("⚠️  警告: 服务器监听所有网卡，请确保防火墙配置正确")
        print("=" * 70)
    
    print()
    logger.info("正在启动服务器...")
    
    # 启动服务器
    try:
        if args.reload or args.workers == 1:
            # 开发模式或单进程模式：使用 uvicorn
            import uvicorn
            
            uvicorn.run(
                "src.interfaces.api.main:app",
                host=args.host,
                port=args.port,
                reload=args.reload,
                log_level=args.log_level.lower(),
                access_log=not args.no_access_log,
            )
        else:
            # 生产模式：尝试使用 gunicorn + uvicorn workers
            try:
                import gunicorn.app.base
                
                class StandaloneApplication(gunicorn.app.base.BaseApplication):
                    """自定义 Gunicorn 应用"""
                    
                    def __init__(self, app, options=None):
                        self.options = options or {}
                        self.application = app
                        super().__init__()
                    
                    def load_config(self):
                        for key, value in self.options.items():
                            if key in self.cfg.settings and value is not None:
                                self.cfg.set(key.lower(), value)
                    
                    def load(self):
                        return self.application
                
                options = {
                    "bind": f"{args.host}:{args.port}",
                    "workers": args.workers,
                    "worker_class": "uvicorn.workers.UvicornWorker",
                    "timeout": 300,
                    "loglevel": args.log_level.lower(),
                    "accesslog": "-" if not args.no_access_log else None,
                    "errorlog": "-",
                }
                
                from src.interfaces.api.main import app
                logger.info(f"使用 Gunicorn 启动，工作进程数: {args.workers}")
                StandaloneApplication(app, options).run()
                
            except ImportError:
                logger.warning("未安装 gunicorn，回退到单进程模式")
                logger.info("提示: 生产环境建议安装 gunicorn (pip install gunicorn)")
                
                import uvicorn
                
                uvicorn.run(
                    "src.interfaces.api.main:app",
                    host=args.host,
                    port=args.port,
                    log_level=args.log_level.lower(),
                    access_log=not args.no_access_log,
                )
    
    except KeyboardInterrupt:
        print("\n")
        logger.info("👋 服务器已停止")
        print()
    except Exception as e:
        print("\n")
        logger.error(f"❌ 服务器启动失败: {str(e)}", exc_info=True)
        print()
        sys.exit(1)


if __name__ == "__main__":
    main()


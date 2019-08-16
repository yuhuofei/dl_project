#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Author  : Joshua
@Time    : 2018/10/12 18:48
@File    : logger.py
@Desc    : log
"""
import logging
import logging.handlers
import sys
import datetime
from setting import DEFAULT_LOGGING_LEVEL, DEFAULT_LOGGING_FILE


class Logger(object):
    """Log wrapper class
    """

    def __init__(self, loggername,
                 loglevel2console=DEFAULT_LOGGING_LEVEL,
                 loglevel2file=DEFAULT_LOGGING_LEVEL,
                 log2console=True, log2file=False, logfile=None):
        """Logger initialization
        Args:
            loggername: Logger name, the same name gets the same logger instance
            loglevel2console: Console log level,default logging.DEBUG
            loglevel2file: File log level,default logging.INFO
            log2console: Output log to console,default True
            log2file: Output log to file,default False
            logfile: filename of logfile
        Returns:
            logger
        """

        self.file_level = loglevel2file
        self.console_level = loglevel2console
        if logfile:
            self.log_file = logfile
        else:
            self.log_file = DEFAULT_LOGGING_FILE

        # create logger
        self.logger = logging.getLogger(loggername)
        self.logger.setLevel(logging.DEBUG)

        # set formater
        # self.formatstr = '[%(asctime)s] [%(levelname)s] [%(filename)s-%(lineno)d] [PID:%(process)d-TID:%(thread)d] [%(message)s]'
        self.formatstr = '[%(asctime)s] [%(levelname)s] [%(filename)s-%(lineno)d] [%(message)s]'
        self.formatter = logging.Formatter(self.formatstr, "%Y-%m-%d %H:%M:%S")

        if log2console:
            # Create a handler for output to the console
            self._log2console()

        if log2file:
            # Create a handler for writing to the log file
            self._log2file()

    def _log2console(self):
        ch = logging.StreamHandler(sys.stderr)
        ch.setLevel(self.console_level)
        ch.setFormatter(self.formatter)
        self.logger.addHandler(ch)

    def _log2file(self):
        # fh = logging.FileHandler(self.log_file)
        # Create a handler for changing the log file once a day, up to 15, scroll delete
        fh = logging.handlers.TimedRotatingFileHandler(self.log_file, when='D', interval=1, backupCount=15, encoding='utf-8')
        fh.setLevel(self.file_level)
        fh.setFormatter(self.formatter)
        self.logger.addHandler(fh)

    def get_logger(self):
        return self.logger



class Logger_v1(object):
    """Log wrapper class
    """

    """Log wrapper class
        """

    def __init__(self, loggername,
                 loglevel2console=DEFAULT_LOGGING_LEVEL,
                 loglevel2file=DEFAULT_LOGGING_LEVEL,
                 log2console=True, log2file=False, logfile=None, logfile_err=None, formatstr=None):
        """Logger initialization
        Args:
            loggername: Logger name, the same name gets the same logger instance
            loglevel2console: Console log level,default logging.DEBUG
            loglevel2file: File log level,default logging.INFO
            log2console: Output log to console,default True
            log2file: Output log to file,default False
            logfile: filename of logfile
        Returns:
            logger
        """

        # create logger
        self.logger = logging.getLogger(loggername)
        self.logger.setLevel(logging.DEBUG)

        # set formater
        logging.Formatter.converter = self.beijing
        formatstr = '|%(asctime)s| [%(levelname)s] [%(filename)s-%(lineno)d] %(message)s' if formatstr is None else formatstr
        formatter = logging.Formatter(formatstr, "%Y-%m-%d %H:%M:%S")

        if log2console:
            # Create a handler for output to the console
            ch = logging.StreamHandler(sys.stderr)
            ch.setLevel(loglevel2console)
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)

        if log2file:
            # Create a handler for writing to the log file
            # fh = logging.FileHandler(logfile)
            # Create a handler for changing the log file once a day, up to 15, scroll delete
            fh_defualt = logging.handlers.TimedRotatingFileHandler(logfile, when='D', interval=1, backupCount=15,
                                                                   encoding='utf-8')
            fh_defualt.setLevel(loglevel2file)
            fh_defualt.setFormatter(formatter)
            if logfile_err is not None:
                # 1. 传err文件时，普通的handler只处理INFO级别
                info_filter = logging.Filter()
                info_filter.filter = lambda record: record.levelno < logging.WARNING  # 设置过滤等级
                fh_defualt.addFilter(info_filter)
                # 2. 新增一个专门处理 WARN和ERROR的handler
                err_filter = logging.Filter()
                err_filter.filter = lambda record: record.levelno >= logging.WARNING
                fh_err = logging.handlers.TimedRotatingFileHandler(logfile_err, when='D', interval=1, backupCount=15,
                                                                   encoding='utf-8')
                fh_err.setLevel(loglevel2file)
                fh_err.setFormatter(formatter)
                fh_err.addFilter(err_filter)
                self.logger.addHandler(fh_err)
            self.logger.addHandler(fh_defualt)

    def get_logger(self):
        return self.logger

    @staticmethod
    def beijing(sec, what):
        beijing_time = (datetime.datetime.utcnow() + datetime.timedelta(hours=8))
        return beijing_time.timetuple()
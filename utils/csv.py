import os
from typing import Optional, cast

import pandas as pd

from utils.config_manager import get_data_dir
from utils.logger import log

ENCODING = 'gbk'


def get_file_path(file_name: str) -> str:
    data_dir = get_data_dir()
    file_path = os.path.join(data_dir, file_name)
    log.debug(f"获取文件路径: {file_name} -> {file_path}")
    return file_path


def read_csv(file_name: str) -> Optional[pd.DataFrame]:
    try:
        file_path = get_file_path(file_name)
        return cast(pd.DataFrame, pd.read_csv(file_path, encoding=ENCODING))
    except FileNotFoundError:
        log.error(f"文件不存在: {file_name}")
        return None
    except pd.errors.EmptyDataError:
        log.error(f"文件为空: {file_name}")
        return None
    except UnicodeDecodeError:
        try:
            return cast(pd.DataFrame, pd.read_csv(file_path, encoding='gbk'))
        except Exception as e:
            log.error(f"读取CSV失败: {file_name}, 错误: {str(e)}")
            return None
    except Exception as e:
        log.error(f"读取CSV失败: {file_name}, 错误: {str(e)}")
        return None


def save_csv(df: pd.DataFrame, file_name: str, mode: str = 'w', header: bool = True) -> bool:
    try:
        file_path = get_file_path(file_name)
        df.to_csv(file_path, mode=mode, index=False, encoding=ENCODING, header=header)
        return True
    except Exception as e:
        log.error(f"保存CSV失败: {file_name}, 错误: {str(e)}")
        return False


def overwrite_csv(df: pd.DataFrame, file_name: str) -> bool:
    if save_csv(df, file_name):
        log.info(f"覆盖保存成功: {file_name}")
        return True
    return False


def append_row_csv(df: pd.DataFrame, file_name: str) -> bool:
    file_path = get_file_path(file_name)
    header = not os.path.exists(file_path)
    if save_csv(df, file_name, mode='a', header=header):
        log.info(f"追加行成功: {file_name}, 新增 {len(df)} 行数据")
        return True
    return False


def append_column_csv(file_name: str, new_col_df: pd.DataFrame) -> bool:
    original_df = read_csv(file_name)
    if original_df is None:
        return False
    
    result_df = pd.concat([original_df, new_col_df], axis=1)
    if save_csv(result_df, file_name):
        log.info(f"追加列成功: {file_name}, 新增 {len(new_col_df.columns)} 列")
        return True
    return False


def overwrite_row_csv(file_name: str, row_index: int, new_row_df: pd.DataFrame) -> bool:
    df = read_csv(file_name)
    if df is None:
        return False
    
    if row_index < 0 or row_index >= len(df):
        log.error(f"行号越界: {row_index}, 有效范围: 0 ~ {len(df)-1}")
        return False
    
    df.iloc[row_index] = new_row_df.iloc[0]
    if save_csv(df, file_name):
        log.info(f"覆盖第{row_index}行成功: {file_name}")
        return True
    return False


def overwrite_column_csv(file_name: str, col_name: str, new_col_df: pd.DataFrame) -> bool:
    df = read_csv(file_name)
    if df is None:
        return False
    
    if col_name not in df.columns:
        log.error(f"列不存在: {col_name}, 现有列: {list(df.columns)}")
        return False
    
    df[col_name] = new_col_df.iloc[:, 0].values
    if save_csv(df, file_name):
        log.info(f"覆盖列 {col_name} 成功: {file_name}")
        return True
    return False
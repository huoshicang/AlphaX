import pandas as pd
import os

# ===================== 核心：自动配置默认路径 =====================
# 获取【项目根目录】
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 默认数据文件夹：项目根目录/data
DEFAULT_DATA_DIR = os.path.join(BASE_DIR, "../data")
# 自动创建 data 文件夹（不存在则创建，存在则忽略）
os.makedirs(DEFAULT_DATA_DIR, exist_ok=True)

# 工具函数：自动拼接路径（传入文件名 → 自动保存到 data 文件夹）
def get_file_path(file_name: str) -> str:
    return os.path.join(DEFAULT_DATA_DIR, file_name)

# ===================== 1. 覆盖整个CSV文件 =====================
def overwrite_csv(df: pd.DataFrame, file_name: str):
    """【DF专用】覆盖保存（默认存到 ./data/xxx.csv）"""
    try:
        file_path = get_file_path(file_name)
        df.to_csv(file_path, index=False, encoding='utf-8-sig')
        print(f"✅ 覆盖保存成功：{file_name}")
    except Exception as e:
        print(f"❌ 保存失败：{str(e)}")

# ===================== 2. 追加行 =====================
def append_row_csv(new_df: pd.DataFrame, file_name: str):
    """【DF专用】末尾追加行（默认存到 ./data/xxx.csv）"""
    try:
        file_path = get_file_path(file_name)
        new_df.to_csv(
            file_path, mode='a', index=False, encoding='utf-8-sig',
            header=not os.path.exists(file_name)
        )
        print(f"✅ 追加行成功：{file_name}")
    except Exception as e:
        print(f"❌ 追加行失败：{str(e)}")

# ===================== 3. 追加列 =====================
def append_column_csv(file_name: str, new_col_df: pd.DataFrame):
    """【DF专用】右侧追加列（默认从 ./data/xxx.csv 读取）"""
    try:
        file_path = get_file_path(file_name)
        original_df = pd.read_csv(file_path, encoding='utf-8-sig')
        result_df = pd.concat([original_df, new_col_df], axis=1)
        result_df.to_csv(file_path, index=False, encoding='utf-8-sig')
        print(f"✅ 追加列成功：{file_name}")
    except Exception as e:
        print(f"❌ 追加列失败：{str(e)}")

# ===================== 4. 覆盖指定行 =====================
def overwrite_row_csv(file_name: str, row_index: int, new_row_df: pd.DataFrame):
    """【DF专用】覆盖指定行（索引从0开始）"""
    try:
        file_path = get_file_path(file_name)
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        if row_index < 0 or row_index >= len(df):
            print(f"❌ 行号越界！有效范围：0 ~ {len(df)-1}")
            return
        df.iloc[row_index] = new_row_df.iloc[0]
        df.to_csv(file_path, index=False, encoding='utf-8-sig')
        print(f"✅ 覆盖第{row_index}行成功：{file_name}")
    except Exception as e:
        print(f"❌ 覆盖行失败：{str(e)}")

# ===================== 5. 覆盖指定列 =====================
def overwrite_column_csv(file_name: str, col_name: str, new_col_df: pd.DataFrame):
    """【DF专用】覆盖指定列（按列名）"""
    try:
        file_path = get_file_path(file_name)
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        if col_name not in df.columns:
            print(f"❌ 列不存在！现有列：{list(df.columns)}")
            return
        df[col_name] = new_col_df.iloc[:, 0].values
        df.to_csv(file_path, index=False, encoding='utf-8-sig')
        print(f"✅ 覆盖列【{col_name}】成功：{file_name}")
    except Exception as e:
        print(f"❌ 覆盖列失败：{str(e)}")
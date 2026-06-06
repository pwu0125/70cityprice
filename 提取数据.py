#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
70城房价数据一键更新+校验工具
依次运行 tools/update_70cityprice.py 和 tools/validate_70cityprice.py

使用方法:
    python3 提取数据.py "<国家统计局发布页URL>"

例如:
    python3 提取数据.py "https://www.stats.gov.cn/sj/zxfb/202601/t20260119_1962319.html"
"""

import os
import subprocess
import sys


def main():
    if len(sys.argv) < 2:
        print("使用方法: python3 提取数据.py <URL>")
        print('例如: python3 提取数据.py "https://www.stats.gov.cn/sj/zxfb/202601/t20260119_1962319.html"')
        sys.exit(1)

    url = sys.argv[1]
    repo_root = os.path.dirname(os.path.abspath(__file__))
    tools_dir = os.path.join(repo_root, "tools")
    update_script = os.path.join(tools_dir, "update_70cityprice.py")
    validate_script = os.path.join(tools_dir, "validate_70cityprice.py")

    # 步骤 1: 更新数据
    print("=" * 50)
    print("步骤 1/2: 更新数据")
    print("=" * 50)
    result = subprocess.run([sys.executable, update_script, url])
    if result.returncode != 0:
        print("\n❌ 更新失败，跳过校验。请检查上方错误信息。")
        sys.exit(1)

    # 步骤 2: 校验数据
    print("\n" + "=" * 50)
    print("步骤 2/2: 校验数据")
    print("=" * 50)
    result = subprocess.run([sys.executable, validate_script])
    if result.returncode != 0:
        print("\n❌ 校验未通过，请检查上方问题明细。")
        sys.exit(1)

    print("\n✅ 数据更新与校验全部完成。")


if __name__ == "__main__":
    main()
